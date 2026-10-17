#include <string.h>
#include "keyboard_core.h"
#include "keymap.h"

enum { ACT_NONE, ACT_FN_LOCK, ACT_BACKLIGHT, ACT_MUTE, ACT_VOLUME, ACT_MIC };

typedef struct {
    uint8_t modifiers, key, action;
    uint16_t consumer;
} special_t;

void kb_layer_init(kb_layer_t *layer) {
    memset(layer,0,sizeof *layer);
    layer->fn_lock=true;
}

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

// The printed T14 functions. F8, F10-F12 have no portable USB equivalent.
static special_t special_for(uint8_t key) {
    special_t s={0,0,ACT_NONE,0};
    switch(key) {
        case 0x3a: s.consumer=0x00e2; s.action=ACT_MUTE; break;   // F1 mute
        case 0x3b: s.consumer=0x00ea; s.action=ACT_VOLUME; break; // F2 volume down
        case 0x3c: s.consumer=0x00e9; s.action=ACT_VOLUME; break; // F3 volume up
        case 0x3d: s.key=0x6f; s.action=ACT_MIC; break;           // F4 mic mute (F20)
        case 0x3e: s.consumer=0x0070; break;                      // F5 brightness down
        case 0x3f: s.consumer=0x006f; break;                      // F6 brightness up
        case 0x40: s.modifiers=0x08; s.key=0x13; break;           // F7 display: Super+P
        case 0x42: s.modifiers=0x08; s.key=0x0c; break;           // F9 settings: Super+I
        case 0x29: s.action=ACT_FN_LOCK; break;                   // Esc
        case 0x2c: s.action=ACT_BACKLIGHT; break;                 // Space
        case 0x13: s.key=0x48; break;                             // P: Pause
        case 0x0e: s.key=0x47; break;                             // K: Scroll Lock
        default: break;
    }
    return s;
}

static bool has_special(special_t s) { return s.modifiers || s.key || s.action || s.consumer; }

static bool use_special(const kb_layer_t *layer,uint8_t key,bool fn) {
    if (!has_special(special_for(key))) return false;
    // Fn Lock swaps the F-row default; Fn always inverts it, like the laptop.
    if (key>=0x3a && key<=0x45) return fn==layer->fn_lock;
    return fn;
}

static bool run_action(kb_layer_t *layer,uint8_t action) {
    switch(action) {
        case ACT_FN_LOCK: layer->fn_lock=!layer->fn_lock; return true;
        case ACT_BACKLIGHT: layer->backlight=(uint8_t)((layer->backlight+1)%KB_BACKLIGHT_LEVELS); return true;
        case ACT_MUTE: layer->speaker_muted=!layer->speaker_muted; return false;
        case ACT_VOLUME: layer->speaker_muted=false; return false;
        case ACT_MIC: layer->mic_muted=!layer->mic_muted; return false;
        default: return false;
    }
}

static void add_key(kb_report_t *report,unsigned *count,uint8_t key) {
    for (unsigned i=0;i<*count && i<6;i++) if (report->keys[i]==key) return;
    if (*count<6) report->keys[*count]=key;
    (*count)++;
}

bool kb_build_report(kb_layer_t *layer,const uint16_t matrix[KB_ROWS],kb_report_t *report,uint16_t *consumer) {
    memset(report,0,sizeof *report); *consumer=0;
    bool fn=false,changed=false;
    for (unsigned r=0;r<KB_ROWS;r++) for (unsigned c=0;c<KB_COLS;c++)
        if ((matrix[r]&(1u<<c)) && keymap[r][c]==KB_FN) fn=true;
    unsigned count=0;
    for (unsigned r=0;r<KB_ROWS;r++) {
        layer->special[r]&=matrix[r];
        for (unsigned c=0;c<KB_COLS;c++) {
            uint16_t bit=(uint16_t)(1u<<c);
            uint8_t key=keymap[r][c];
            if (!(matrix[r]&bit) || !key || key==KB_FN) continue;
            // Decide normal or Fn function once, at press; a held key keeps it.
            if (!(layer->held[r]&bit) && use_special(layer,key,fn)) {
                layer->special[r]|=bit;
                changed|=run_action(layer,special_for(key).action);
            }
            if (layer->special[r]&bit) {
                special_t s=special_for(key);
                report->modifiers|=s.modifiers;
                if (s.consumer && !*consumer) *consumer=s.consumer;
                if (s.key) add_key(report,&count,s.key);
            } else if (key>=0xe0 && key<=0xe7) report->modifiers|=(uint8_t)(1u<<(key-0xe0));
            else add_key(report,&count,key);
        }
    }
    memcpy(layer->held,matrix,sizeof layer->held);
    // USB boot keyboard rollover, rather than silently dropping extra keys.
    if (count>6) memset(report->keys,1,sizeof report->keys);
    return changed;
}
