#include <Arduino.h>
#include "ps2.h"

namespace ps2 {
namespace {
uint8_t clk_pin,data_pin,rst_pin;
volatile uint16_t ring[64];
volatile uint8_t head,tail;
uint8_t bit_index,shift,ones;
bool frame_gap;
uint32_t last_edge;

void release(uint8_t pin) { pinMode(pin,INPUT_PULLUP); }
void drive_low(uint8_t pin) { digitalWriteFast(pin,LOW); pinMode(pin,OUTPUT); }

// Device-to-host frame: start 0, 8 data bits LSB first, odd parity, stop 1.
// The device changes DATA while CLK is high; sample on the falling edge.
void on_clock() {
    uint32_t now=micros(),idle=now-last_edge;
    last_edge=now;
    if (idle>250) bit_index=0; // bits are 60-100 us apart; a pause starts a new frame
    uint8_t bit=digitalReadFast(data_pin);
    if (bit_index==0) {
        if (bit) return;
        frame_gap=idle>3000; // packets are ~10 ms apart, their bytes much closer
        shift=0; ones=0; bit_index=1;
    } else if (bit_index<=8) {
        shift|=(uint8_t)(bit<<(bit_index-1)); ones+=bit; bit_index++;
    } else if (bit_index==9) {
        ones+=bit; bit_index++;
    } else {
        bit_index=0;
        if (!bit || !(ones&1)) return; // framing or parity error
        uint8_t next=(uint8_t)((head+1)&63);
        if (next!=tail) { ring[head]=(uint16_t)(shift|(frame_gap?0x100:0)); head=next; }
    }
}

bool wait_line(uint8_t pin,uint8_t level,uint32_t timeout_us) {
    uint32_t start=micros();
    while (digitalReadFast(pin)!=level) if (micros()-start>timeout_us) return false;
    return true;
}

// Host-to-device frame: hold CLK low to claim the bus, then send each bit
// while the device clocks it in, and finally wait for the device's ACK bit.
bool write(uint8_t value) {
    detachInterrupt(digitalPinToInterrupt(clk_pin));
    drive_low(clk_pin); delayMicroseconds(150);
    drive_low(data_pin); delayMicroseconds(10);
    release(clk_pin);
    // Let CLK rise through the pull-up first; a 600 MHz core reads it before it does.
    bool ok=wait_line(clk_pin,HIGH,100) && wait_line(clk_pin,LOW,15000);
    uint8_t count=0;
    for (int i=0;i<9 && ok;i++) {
        uint8_t bit=i<8?(uint8_t)((value>>i)&1):(uint8_t)!(count&1);
        count+=bit;
        if (bit) release(data_pin); else drive_low(data_pin);
        ok=wait_line(clk_pin,HIGH,2000) && wait_line(clk_pin,LOW,2000);
    }
    release(data_pin);
    ok=ok && wait_line(clk_pin,HIGH,2000) && wait_line(data_pin,LOW,2000) && wait_line(clk_pin,LOW,2000)
          && wait_line(data_pin,HIGH,2000) && wait_line(clk_pin,HIGH,2000);
    release(clk_pin); release(data_pin);
    bit_index=0; last_edge=micros();
    attachInterrupt(digitalPinToInterrupt(clk_pin),on_clock,FALLING);
    return ok;
}

void pause(uint32_t ms,idle_fn idle) {
    uint32_t start=millis();
    while (millis()-start<ms) if (idle) idle();
}

int wait_byte(uint32_t timeout_ms,idle_fn idle) {
    uint32_t start=millis();
    while (millis()-start<timeout_ms) {
        int value=read();
        if (value>=0) return value&0xff;
        if (idle) idle();
    }
    return -1;
}

int wait_for_any(uint32_t timeout_ms,idle_fn idle) {
    for (uint32_t start=millis(),elapsed;(elapsed=millis()-start)<timeout_ms;) {
        int reply=wait_byte(timeout_ms-elapsed,idle);
        if (reply==0xfa || reply==0xfe) return reply;
    }
    return -1;
}

bool command(uint8_t value,idle_fn idle) {
    for (int attempt=0;attempt<3;attempt++) {
        if (!write(value)) continue;
        // Skip stray movement or self-test bytes until ACK (0xFA) or resend (0xFE).
        int reply=wait_for_any(30,idle);
        if (reply==0xfa) return true;
    }
    return false;
}

bool wait_for(uint8_t expected,uint32_t timeout_ms,idle_fn idle) {
    for (uint32_t start=millis(),elapsed;(elapsed=millis()-start)<timeout_ms;)
        if (wait_byte(timeout_ms-elapsed,idle)==expected) return true;
    return false;
}
}

void begin(uint8_t clk,uint8_t data,uint8_t rst) {
    clk_pin=clk; data_pin=data; rst_pin=rst;
    release(clk_pin); release(data_pin);
    digitalWriteFast(rst_pin,LOW); pinMode(rst_pin,OUTPUT);
    last_edge=micros();
    attachInterrupt(digitalPinToInterrupt(clk_pin),on_clock,FALLING);
}

int read() {
    if (tail==head) return -1;
    int value=ring[tail];
    tail=(uint8_t)((tail+1)&63);
    return value;
}

bool start(idle_fn idle) {
    // The TrackPoint controller needs a high pulse on RST after power-up.
    digitalWriteFast(rst_pin,HIGH); pause(300,idle);
    digitalWriteFast(rst_pin,LOW);
    if (wait_for(0xaa,1000,idle)) wait_byte(100,idle); // power-on self-test and ID, if sent
    while (read()>=0) {}
    if (!command(0xff,idle)) return false;           // reset
    if (!wait_for(0xaa,1500,idle)) return false;     // self-test passed
    wait_byte(100,idle);                             // device ID
    return command(0xf4,idle);                       // start streaming movement
}
}
