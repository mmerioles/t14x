#ifndef T14_KEYBOARD_CORE_H
#define T14_KEYBOARD_CORE_H
#include <stdbool.h>
#include <stdint.h>
#define KB_ROWS 17
#define KB_COLS 9
#define KB_FN 255
#define KB_DEBOUNCE_MS 10

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

void kb_filter_ghosts(const uint16_t raw[KB_ROWS],const uint16_t previous[KB_ROWS],uint16_t filtered[KB_ROWS]);
void kb_update(kb_state_t *state,const uint16_t raw[KB_ROWS],uint32_t now_ms);
void kb_build_report(const uint16_t matrix[KB_ROWS],kb_report_t *report,uint16_t *consumer);
#endif
