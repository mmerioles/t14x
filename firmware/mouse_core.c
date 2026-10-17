#include <stdlib.h>
#include <string.h>
#include "mouse_core.h"

ms_ps2_result_t ms_ps2_feed(ms_ps2_parser_t *parser,uint8_t byte,bool gap,int16_t *dx,int16_t *dy) {
    if (gap) parser->count=0;
    // Byte 0 always has bit 3 set; anything else means we joined mid-packet.
    if (parser->count==0 && !(byte&0x08)) return MS_PS2_NONE;
    parser->bytes[parser->count++]=byte;
    // 0xAA 0x00 is the self-test result a TrackPoint sends after it resets itself.
    if (parser->count==2 && parser->bytes[0]==0xaa && byte==0x00) { parser->count=0; return MS_PS2_RESET; }
    if (parser->count<3) return MS_PS2_NONE;
    parser->count=0;
    uint8_t head=parser->bytes[0];
    if (head&0xc0) return MS_PS2_NONE; // overflowed counts are meaningless
    *dx=(int16_t)(parser->bytes[1]-((head&0x10)?256:0));
    *dy=(int16_t)(parser->bytes[2]-((head&0x20)?256:0));
    return MS_PS2_PACKET;
}

void ms_buttons(ms_state_t *state,uint8_t raw,uint32_t now_ms) {
    if (raw!=state->candidate) { state->candidate=raw; state->changed_ms=now_ms; }
    if ((uint32_t)(now_ms-state->changed_ms)<MS_DEBOUNCE_MS || state->candidate==state->stable) return;
    uint8_t pressed=(uint8_t)(state->candidate&~state->stable),released=(uint8_t)(state->stable&~state->candidate);
    state->stable=state->candidate;
    if (pressed&MS_MIDDLE) { state->middle_used=false; state->travel=state->scroll_x=state->scroll_y=0; }
    // Like a ThinkPad: Middle alone clicks; Middle plus TrackPoint scrolls.
    if ((released&MS_MIDDLE) && !state->middle_used) state->click_phase=1;
}

void ms_motion(ms_state_t *state,int dx,int dy) {
    if (!(state->stable&MS_MIDDLE)) { state->x+=dx; state->y-=dy; return; }
    state->travel+=abs(dx)+abs(dy);
    if (state->travel>=MS_SCROLL_START) state->middle_used=true;
    if (!state->middle_used) return;
    state->scroll_x+=dx; state->scroll_y+=dy;
    state->pan+=state->scroll_x/MS_SCROLL_DIVISOR; state->scroll_x%=MS_SCROLL_DIVISOR;
    state->wheel+=state->scroll_y/MS_SCROLL_DIVISOR; state->scroll_y%=MS_SCROLL_DIVISOR;
}

static int8_t clamp(int32_t value) { return (int8_t)(value>127?127:value<-127?-127:value); }

bool ms_peek_report(const ms_state_t *state,ms_report_t *report) {
    uint8_t buttons=(uint8_t)((state->stable&(MS_LEFT|MS_RIGHT))|(state->click_phase==1?MS_MIDDLE:0));
    if (buttons==state->sent_buttons && !state->x && !state->y && !state->wheel && !state->pan) return false;
    report->buttons=buttons;
    report->x=clamp(state->x); report->y=clamp(state->y);
    report->wheel=clamp(state->wheel); report->pan=clamp(state->pan);
    return true;
}

void ms_commit_report(ms_state_t *state,const ms_report_t *report) {
    state->x-=report->x; state->y-=report->y;
    state->wheel-=report->wheel; state->pan-=report->pan;
    state->sent_buttons=report->buttons;
    if (state->click_phase) state->click_phase=state->click_phase==1?2:0;
}

bool ms_take_report(ms_state_t *state,ms_report_t *report) {
    if (!ms_peek_report(state,report)) return false;
    ms_commit_report(state,report);
    return true;
}

void ms_discard_motion(ms_state_t *state) { state->x=state->y=state->wheel=state->pan=0; }
