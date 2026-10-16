#include <string.h>
#include "keyboard_core.h"
#include "keymap.h"

void kb_filter_ghosts(const uint16_t raw[KB_ROWS],const uint16_t previous[KB_ROWS],uint16_t filtered[KB_ROWS]) {
    uint16_t ambiguous[KB_ROWS]={0};
    for (unsigned a=0;a<KB_ROWS;a++) for (unsigned b=a+1;b<KB_ROWS;b++) {
        uint16_t common=raw[a]&raw[b];
        if (common && (common & (common-1))) {
            ambiguous[a]|=common;
            ambiguous[b]|=common;
        }
    }
    // Never invent a new key inside an electrically ambiguous rectangle.
    // Retain previously accepted held keys; remove them when their path opens.
    for (unsigned r=0;r<KB_ROWS;r++) filtered[r]=raw[r]&(~ambiguous[r]|previous[r]);
}

void kb_update(kb_state_t *state,const uint16_t raw[KB_ROWS],uint32_t now_ms) {
    uint16_t filtered[KB_ROWS];
    kb_filter_ghosts(raw,state->stable,filtered);
    for (unsigned r=0;r<KB_ROWS;r++) for (unsigned c=0;c<KB_COLS;c++) {
        uint16_t bit=(uint16_t)(1u<<c);
        if ((filtered[r]^state->candidate[r])&bit) {
            state->candidate[r]^=bit;
            state->changed[r][c]=now_ms;
        }
        if ((uint32_t)(now_ms-state->changed[r][c])>=KB_DEBOUNCE_MS) {
            state->stable[r]=(state->stable[r]&~bit)|(state->candidate[r]&bit);
        }
    }
}

static uint16_t fn_usage(uint8_t key) {
    switch(key) {
        case 0x3a: return 0x00e2; // F1: mute
        case 0x3b: return 0x00ea; // F2: volume down
        case 0x3c: return 0x00e9; // F3: volume up
        case 0x3e: return 0x0070; // F5: brightness down
        case 0x3f: return 0x006f; // F6: brightness up
        default: return 0;
    }
}

void kb_build_report(const uint16_t matrix[KB_ROWS],kb_report_t *report,uint16_t *consumer) {
    memset(report,0,sizeof *report); *consumer=0;
    bool fn=false;
    for (unsigned r=0;r<KB_ROWS;r++) for (unsigned c=0;c<KB_COLS;c++)
        if ((matrix[r]&(1u<<c)) && keymap[r][c]==KB_FN) fn=true;
    unsigned count=0;
    for (unsigned r=0;r<KB_ROWS;r++) for (unsigned c=0;c<KB_COLS;c++) {
        if (!(matrix[r]&(1u<<c))) continue;
        uint8_t key=keymap[r][c];
        if (!key || key==KB_FN) continue;
        if (key>=0xe0 && key<=0xe7) { report->modifiers|=1u<<(key-0xe0); continue; }
        uint16_t usage=fn?fn_usage(key):0;
        if (usage) { if (!*consumer) *consumer=usage; continue; }
        if (count<6) report->keys[count]=key;
        count++;
    }
    // USB boot keyboard rollover, rather than silently dropping extra keys.
    if (count>6) memset(report->keys,1,sizeof report->keys);
}
