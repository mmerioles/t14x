#ifndef T14_KEYMAP_H
#define T14_KEYMAP_H
#include "keyboard_core.h"
#ifdef __cplusplus
extern "C" {
#endif
extern const uint8_t row_pins[KB_ROWS];
extern const uint8_t col_pins[KB_COLS];
extern const uint8_t keymap[KB_ROWS][KB_COLS];
#ifdef __cplusplus
}
#endif
#endif
