#ifndef T14_MOUSE_CORE_H
#define T14_MOUSE_CORE_H
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define MS_LEFT 1
#define MS_RIGHT 2
#define MS_MIDDLE 4
#define MS_DEBOUNCE_MS 10
#define MS_SCROLL_DIVISOR 8 // TrackPoint counts per wheel step while Middle is held
#define MS_SCROLL_START 8   // travel that turns a Middle press into scrolling

typedef enum { MS_PS2_NONE, MS_PS2_PACKET, MS_PS2_RESET } ms_ps2_result_t;

typedef struct {
    uint8_t bytes[3];
    uint8_t count;
} ms_ps2_parser_t;

typedef struct {
    uint8_t candidate, stable;
    uint32_t changed_ms;
    bool middle_used;
    uint8_t click_phase; // 1: report a Middle press, 2: report its release
    uint8_t sent_buttons;
    int32_t x, y, wheel, pan, scroll_x, scroll_y, travel;
} ms_state_t;

typedef struct {
    uint8_t buttons;
    int8_t x, y, wheel, pan;
} ms_report_t;

// gap: the byte started after the line was idle, so it must begin a packet.
// Motion uses PS/2 directions: dx right-positive, dy up-positive.
ms_ps2_result_t ms_ps2_feed(ms_ps2_parser_t *parser,uint8_t byte,bool gap,int16_t *dx,int16_t *dy);
void ms_buttons(ms_state_t *state,uint8_t raw,uint32_t now_ms);
void ms_motion(ms_state_t *state,int dx,int dy);
// Build the next report without changing state; commit it only once USB accepted it,
// so a dropped report (for example a button release) is sent again.
bool ms_peek_report(const ms_state_t *state,ms_report_t *report);
void ms_commit_report(ms_state_t *state,const ms_report_t *report);
bool ms_take_report(ms_state_t *state,ms_report_t *report);
void ms_discard_motion(ms_state_t *state);
#ifdef __cplusplus
}
#endif
#endif
