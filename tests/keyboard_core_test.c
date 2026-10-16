#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "keyboard_core.h"
#include "keymap.h"

static void single_keys(void) {
    unsigned count=0;
    for (unsigned r=0;r<KB_ROWS;r++) for (unsigned c=0;c<KB_COLS;c++) {
        uint8_t code=keymap[r][c];
        if (!code) continue;
        count++;
        uint16_t matrix[KB_ROWS]={0},consumer;
        kb_report_t report;
        matrix[r]=(uint16_t)(1u<<c);
        kb_build_report(matrix,&report,&consumer);
        assert(consumer==0 && report.reserved==0);
        if (code==KB_FN) assert(report.modifiers==0 && report.keys[0]==0);
        else if (code>=0xe0) assert(report.modifiers==(1u<<(code-0xe0)) && report.keys[0]==0);
        else assert(report.modifiers==0 && report.keys[0]==code);
        for (unsigned i=1;i<6;i++) assert(report.keys[i]==0);
        memset(matrix,0,sizeof matrix);
        kb_build_report(matrix,&report,&consumer);
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
    kb_build_report(matrix,&report,&consumer);
    assert(report.keys[0]==4 && report.modifiers==3); // Ctrl+Shift+A
    matrix[14]=0;
    kb_build_report(matrix,&report,&consumer);
    assert(report.modifiers==2); // Ctrl release does not lose Shift
    memset(matrix,0,sizeof matrix);
    matrix[0]=0x3f; kb_build_report(matrix,&report,&consumer);
    for (unsigned i=0;i<6;i++) assert(report.keys[i]>1);
    matrix[0]=0xbf; kb_build_report(matrix,&report,&consumer);
    for (unsigned i=0;i<6;i++) assert(report.keys[i]==1);
    matrix[0]=2; kb_build_report(matrix,&report,&consumer);
    assert(report.keys[0]==4 && report.keys[1]==0);
}

static void media(void) {
    const unsigned rows[]={1,2,2,8,5},cols[]={2,2,4,0,0};
    const uint16_t usages[]={0xe2,0xea,0xe9,0x70,0x6f};
    for (unsigned i=0;i<5;i++) {
        uint16_t matrix[KB_ROWS]={0},consumer;
        kb_report_t report;
        matrix[rows[i]]=(uint16_t)(1u<<cols[i]); matrix[16]=256;
        kb_build_report(matrix,&report,&consumer);
        assert(consumer==usages[i] && report.keys[0]==0);
        matrix[16]=0; kb_build_report(matrix,&report,&consumer);
        assert(consumer==0 && report.keys[0]==keymap[rows[i]][cols[i]]);
        matrix[rows[i]]=0; kb_build_report(matrix,&report,&consumer);
        assert(consumer==0 && report.keys[0]==0);
    }
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
    single_keys(); modifiers_and_rollover(); media(); debounce(); ghosting();
    puts("PASS: 84 keys, modifiers, releases, rollover, Fn media, debounce, timer wrap, ghost suppression");
    return 0;
}
