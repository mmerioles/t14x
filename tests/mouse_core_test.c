#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "mouse_core.h"

static ms_ps2_result_t feed(ms_ps2_parser_t *p,const uint8_t *bytes,unsigned count,int16_t *dx,int16_t *dy) {
    ms_ps2_result_t result=MS_PS2_NONE;
    for (unsigned i=0;i<count;i++) result=ms_ps2_feed(p,bytes[i],i==0,dx,dy);
    return result;
}

static void packets(void) {
    ms_ps2_parser_t p={0}; int16_t dx=0,dy=0;
    const uint8_t right_up[]={0x08,5,3},left_down[]={0x38,0xfb,0xfd},overflow[]={0x48,1,1},reset[]={0xaa,0x00};
    assert(feed(&p,right_up,3,&dx,&dy)==MS_PS2_PACKET && dx==5 && dy==3);
    assert(feed(&p,left_down,3,&dx,&dy)==MS_PS2_PACKET && dx==-5 && dy==-3);
    assert(feed(&p,overflow,3,&dx,&dy)==MS_PS2_NONE);
    assert(feed(&p,reset,2,&dx,&dy)==MS_PS2_RESET && p.count==0);
    // A byte without bit 3 cannot start a packet, so the parser resynchronises.
    assert(ms_ps2_feed(&p,0x05,false,&dx,&dy)==MS_PS2_NONE && p.count==0);
    // An idle gap always restarts packet assembly.
    ms_ps2_feed(&p,0x08,false,&dx,&dy);
    assert(feed(&p,right_up,3,&dx,&dy)==MS_PS2_PACKET && dx==5);
}

static ms_state_t pressed(uint8_t buttons) {
    ms_state_t s; memset(&s,0,sizeof s);
    ms_buttons(&s,buttons,0); ms_buttons(&s,buttons,MS_DEBOUNCE_MS);
    return s;
}

static void movement_and_buttons(void) {
    ms_state_t s; memset(&s,0,sizeof s); ms_report_t r;
    assert(!ms_take_report(&s,&r));
    ms_motion(&s,10,4); // PS/2 up is USB negative y
    assert(ms_take_report(&s,&r) && r.x==10 && r.y==-4 && r.buttons==0);
    assert(!ms_take_report(&s,&r));
    ms_motion(&s,300,0);
    assert(ms_take_report(&s,&r) && r.x==127);
    assert(ms_take_report(&s,&r) && r.x==127);
    assert(ms_take_report(&s,&r) && r.x==46 && !ms_take_report(&s,&r));
    ms_buttons(&s,MS_LEFT,100); assert(!ms_take_report(&s,&r)); // debouncing
    ms_buttons(&s,MS_LEFT,110); assert(ms_take_report(&s,&r) && r.buttons==MS_LEFT);
    ms_buttons(&s,0,120); ms_buttons(&s,0,130); assert(ms_take_report(&s,&r) && r.buttons==0);
}

static void middle_click_and_scroll(void) {
    ms_report_t r;
    ms_state_t s=pressed(MS_MIDDLE);
    assert(!ms_take_report(&s,&r)); // Middle is held back until we know click or scroll
    ms_buttons(&s,0,20); ms_buttons(&s,0,30);
    assert(ms_take_report(&s,&r) && r.buttons==MS_MIDDLE);
    assert(ms_take_report(&s,&r) && r.buttons==0 && !ms_take_report(&s,&r));

    s=pressed(MS_MIDDLE);
    ms_motion(&s,0,MS_SCROLL_DIVISOR*2); // push up: scroll up, pointer stays put
    assert(ms_take_report(&s,&r) && r.wheel==2 && r.x==0 && r.y==0 && r.buttons==0);
    ms_motion(&s,-MS_SCROLL_DIVISOR,0);
    assert(ms_take_report(&s,&r) && r.pan==-1);
    ms_buttons(&s,0,20); ms_buttons(&s,0,30);
    assert(!ms_take_report(&s,&r)); // scrolling cancels the middle click

    s=pressed(MS_MIDDLE);
    ms_motion(&s,1,0); // jitter below the scroll threshold keeps the click
    ms_buttons(&s,0,20); ms_buttons(&s,0,30);
    assert(ms_take_report(&s,&r) && r.buttons==MS_MIDDLE);
}

static void dropped_reports_are_resent(void) {
    ms_report_t r;
    ms_state_t s=pressed(MS_LEFT);
    assert(ms_take_report(&s,&r) && r.buttons==MS_LEFT);
    ms_buttons(&s,0,20); ms_buttons(&s,0,30);
    assert(ms_peek_report(&s,&r) && r.buttons==0); // USB refused this release...
    assert(ms_peek_report(&s,&r) && r.buttons==0); // ...so it is still pending
    ms_commit_report(&s,&r);
    assert(!ms_peek_report(&s,&r));
    ms_motion(&s,5,5); ms_discard_motion(&s);
    assert(!ms_peek_report(&s,&r)); // nothing replayed after sleep
}

int main(void) {
    packets(); movement_and_buttons(); middle_click_and_scroll(); dropped_reports_are_resent();
    puts("PASS: PS/2 packets, resync, reset detection, movement, buttons, middle click, scrolling, dropped-report retry");
    return 0;
}
