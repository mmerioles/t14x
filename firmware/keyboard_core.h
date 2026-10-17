#ifndef T14_KEYBOARD_CORE_H
#define T14_KEYBOARD_CORE_H
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define KB_ROWS 17
#define KB_COLS 9
#define KB_FN 255
#define KB_DEBOUNCE_MS 10
#define KB_BACKLIGHT_LEVELS 3

typedef struct {
    uint16_t stable[KB_ROWS];
    uint16_t candidate[KB_ROWS];
    uint32_t changed[KB_ROWS][KB_COLS];
} kb_state_t;

typedef struct {
    uint8_t modifiers;
    uint8_t reserved;
    uint8_t keys[6];
} kb_report_t;

typedef struct {
    bool fn_lock;          // true: F1-F12 are standard keys (Lenovo's Fn Lock LED on)
    uint8_t backlight;     // 0 off, 1 low, 2 high
    bool speaker_muted;    // local mirror of the last mute/volume key
    bool mic_muted;        // local mirror of the mic-mute key
    uint16_t held[KB_ROWS];    // matrix seen by the previous report
    uint16_t special[KB_ROWS]; // held keys latched to their Fn function at press time
} kb_layer_t;

void kb_layer_init(kb_layer_t *layer);
void kb_filter_ghosts(const uint16_t raw[KB_ROWS],const uint16_t previous[KB_ROWS],uint16_t filtered[KB_ROWS]);
void kb_update(kb_state_t *state,const uint16_t raw[KB_ROWS],uint32_t now_ms);
// Returns true when a setting worth saving (Fn Lock, backlight) changed.
bool kb_build_report(kb_layer_t *layer,const uint16_t matrix[KB_ROWS],kb_report_t *report,uint16_t *consumer);
#ifdef __cplusplus
}
#endif
#endif
