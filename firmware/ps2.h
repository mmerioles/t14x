#ifndef T14_PS2_H
#define T14_PS2_H
#include <stdint.h>

// Interrupt-driven PS/2 host for the TrackPoint. Lines are open-drain:
// "high" is input with pull-up, "low" is driven low. Nothing is driven high.
namespace ps2 {
typedef void (*idle_fn)(void);
void begin(uint8_t clk,uint8_t data,uint8_t rst);
// Received bytes; bit 8 is set when the byte followed an idle line (packet start).
int read();
// Power-on reset pulse, device reset, defaults, and streaming. Keeps calling idle while waiting.
bool start(idle_fn idle);
}
#endif
