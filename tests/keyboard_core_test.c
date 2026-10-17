#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "keyboard_core.h"
#include "keymap.h"

static kb_layer_t layer;

static bool build(const uint16_t matrix[KB_ROWS],kb_report_t *report,uint16_t *consumer) {
    return kb_build_report(&layer,matrix,report,consumer);
}

static void press(unsigned row,unsigned col,kb_report_t *report,uint16_t *consumer) {
    uint16_t matrix[KB_ROWS]={0};
    matrix[row]=(uint16_t)(1u<<col);
    build(matrix,report,consumer);
}

static void release_all(void) {
    uint16_t matrix[KB_ROWS]={0},consumer; kb_report_t report;
    build(matrix,&report,&consumer);
}

static void single_keys(void) {
    unsigned count=0;
    for (unsigned r=0;r<KB_ROWS;r++) for (unsigned c=0;c<KB_COLS;c++) {
        uint8_t code=keymap[r][c];
        if (!code) continue;
        count++;
        uint16_t matrix[KB_ROWS]={0},consumer;
        kb_report_t report;
        matrix[r]=(uint16_t)(1u<<c);
        build(matrix,&report,&consumer);
        assert(consumer==0 && report.reserved==0);
        if (code==KB_FN) assert(report.modifiers==0 && report.keys[0]==0);
        else if (code>=0xe0) assert(report.modifiers==(1u<<(code-0xe0)) && report.keys[0]==0);
        else assert(report.modifiers==0 && report.keys[0]==code);
        for (unsigned i=1;i<6;i++) assert(report.keys[i]==0);
        memset(matrix,0,sizeof matrix);
        build(matrix,&report,&consumer);
        for (unsigned i=0;i<6;i++) assert(report.keys[i]==0);
        assert(report.modifiers==0 && consumer==0);
    }
    assert(count==84);
    assert(keymap[0][1]==4); // A
    assert(keymap[0][0]==41); // Esc
    assert(keymap[8][7]==40); // Enter
    assert(keymap[16][8]==KB_FN);
}

static void modifiers_and_rollover(void) {
    uint16_t matrix[KB_ROWS]={0},consumer;
    kb_report_t report;
    matrix[0]=2; matrix[14]=4; matrix[13]=16;
    build(matrix,&report,&consumer);
    assert(report.keys[0]==4 && report.modifiers==3); // Ctrl+Shift+A
    matrix[14]=0;
    build(matrix,&report,&consumer);
    assert(report.modifiers==2); // Ctrl release does not lose Shift
    memset(matrix,0,sizeof matrix);
    matrix[0]=0x3f; build(matrix,&report,&consumer);
    for (unsigned i=0;i<6;i++) assert(report.keys[i]>1);
    matrix[0]=0xbf; build(matrix,&report,&consumer);
    for (unsigned i=0;i<6;i++) assert(report.keys[i]==1);
    matrix[0]=2; build(matrix,&report,&consumer);
    assert(report.keys[0]==4 && report.keys[1]==0);
}

static void media(void) {
    const unsigned rows[]={1,2,2,8,5},cols[]={2,2,4,0,0};
    const uint16_t usages[]={0xe2,0xea,0xe9,0x70,0x6f};
    kb_layer_init(&layer);
    for (unsigned i=0;i<5;i++) {
        uint16_t matrix[KB_ROWS]={0},consumer;
        kb_report_t report;
        matrix[16]=256; build(matrix,&report,&consumer); // Fn first
        matrix[rows[i]]=(uint16_t)(1u<<cols[i]);
        build(matrix,&report,&consumer);
        assert(consumer==usages[i] && report.keys[0]==0);
        matrix[16]=0; build(matrix,&report,&consumer);
        assert(consumer==usages[i] && report.keys[0]==0); // latched until released
        release_all();
        press(rows[i],cols[i],&report,&consumer);
        assert(consumer==0 && report.keys[0]==keymap[rows[i]][cols[i]]);
        release_all();
    }
}

static void fn_layer(void) {
    uint16_t matrix[KB_ROWS]={0},consumer;
    kb_report_t report;
    kb_layer_init(&layer);
    assert(layer.fn_lock && layer.backlight==0);
    // Fn+Space cycles the backlight and is never typed.
    matrix[16]=256; matrix[8]=64;
    assert(build(matrix,&report,&consumer) && layer.backlight==1 && report.keys[0]==0);
    assert(!build(matrix,&report,&consumer) && layer.backlight==1); // held: no repeat
    matrix[8]=0; build(matrix,&report,&consumer);
    matrix[8]=64; build(matrix,&report,&consumer); assert(layer.backlight==2);
    matrix[8]=0; build(matrix,&report,&consumer);
    matrix[8]=64; build(matrix,&report,&consumer); assert(layer.backlight==0);
    // Fn+Esc toggles Fn Lock: F1 becomes Mute without Fn, and Fn+F1 is F1.
    memset(matrix,0,sizeof matrix); matrix[16]=256; matrix[0]=1;
    assert(build(matrix,&report,&consumer) && !layer.fn_lock && report.keys[0]==0);
    release_all();
    press(1,2,&report,&consumer); assert(consumer==0xe2 && layer.speaker_muted);
    release_all();
    memset(matrix,0,sizeof matrix); matrix[16]=256; build(matrix,&report,&consumer);
    matrix[1]=4; build(matrix,&report,&consumer); assert(consumer==0 && report.keys[0]==0x3a);
    release_all();
    press(2,2,&report,&consumer); assert(consumer==0xea && !layer.speaker_muted); // volume clears mute
    release_all();
    // F4 sends F20 for mic mute; F7 and F9 send Super shortcuts.
    press(2,0,&report,&consumer); assert(report.keys[0]==0x6f && layer.mic_muted); release_all();
    press(6,4,&report,&consumer); assert(report.modifiers==0x08 && report.keys[0]==0x13); release_all();
    press(8,2,&report,&consumer); assert(report.modifiers==0x08 && report.keys[0]==0x0c); release_all();
    press(6,2,&report,&consumer); assert(report.keys[0]==0x41); release_all(); // F8 has no special
    // Non-F keys only change with Fn held: P -> Pause, K -> Scroll Lock, A unchanged.
    press(7,5,&report,&consumer); assert(report.keys[0]==0x13); release_all();
    memset(matrix,0,sizeof matrix); matrix[16]=256; matrix[7]=32;
    build(matrix,&report,&consumer); assert(report.keys[0]==0x48);
    matrix[7]=0; matrix[5]=2; build(matrix,&report,&consumer); assert(report.keys[0]==0x47);
    matrix[5]=0; matrix[0]=2; build(matrix,&report,&consumer); assert(report.keys[0]==4);
    release_all();
    kb_layer_init(&layer);
}

static void debounce(void) {
    kb_state_t state={0}; uint16_t raw[KB_ROWS]={0};
    raw[0]=2; kb_update(&state,raw,0);
    kb_update(&state,raw,9); assert(!state.stable[0]);
    raw[0]=0; kb_update(&state,raw,10);
    raw[0]=2; kb_update(&state,raw,11);
    kb_update(&state,raw,20); assert(!state.stable[0]);
    kb_update(&state,raw,21); assert(state.stable[0]==2);
    raw[0]=0; kb_update(&state,raw,22);
    kb_update(&state,raw,31); assert(state.stable[0]==2);
    kb_update(&state,raw,32); assert(!state.stable[0]);
    memset(&state,0,sizeof state);
    raw[0]=2; kb_update(&state,raw,UINT32_MAX-5);
    kb_update(&state,raw,5); assert(state.stable[0]==2); // timer wrap
}

static void ghosting(void) {
    uint16_t raw[KB_ROWS]={0},prior[KB_ROWS]={0},filtered[KB_ROWS];
    raw[0]=raw[1]=3;
    kb_filter_ghosts(raw,prior,filtered);
    assert(!filtered[0] && !filtered[1]);
    prior[0]=1; kb_filter_ghosts(raw,prior,filtered);
    assert(filtered[0]==1 && !filtered[1]);
    raw[0]=1; raw[1]=2; kb_filter_ghosts(raw,prior,filtered);
    assert(filtered[0]==1 && filtered[1]==2);
    raw[0]=3; raw[1]=1; kb_filter_ghosts(raw,prior,filtered);
    assert(filtered[0]==3 && filtered[1]==1); // no complete rectangle
    memset(raw,0,sizeof raw); kb_filter_ghosts(raw,prior,filtered);
    assert(!filtered[0]);
}

int main(void) {
    assert(sizeof(kb_report_t)==8);
    kb_layer_init(&layer);
    single_keys(); modifiers_and_rollover(); media(); fn_layer(); debounce(); ghosting();
    puts("PASS: 84 keys, modifiers, releases, rollover, Fn layer, Fn Lock, backlight, debounce, timer wrap, ghost suppression");
    return 0;
}
