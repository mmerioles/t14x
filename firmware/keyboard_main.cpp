// Everyday firmware: USB keyboard, media keys, TrackPoint mouse, indicator LEDs, backlight.
#include <Arduino.h>
#include <string.h>
#include "keyboard_core.h"
#include "keymap.h"
#include "mouse_core.h"
#include "pins.h"
#include "ps2.h"

static const uint8_t SETTINGS_MAGIC=0x14;
static const uint8_t BACKLIGHT_PWM[KB_BACKLIGHT_LEVELS]={0,60,255};
static kb_state_t keys;
static kb_layer_t layer;
static ms_state_t mouse;
static ms_ps2_parser_t parser;
static kb_report_t sent_report;
static uint16_t sent_consumer;
static bool resend=true,trackpoint_ready,save_pending;
static uint8_t was_configured,lights=0xff,backlight=0xff,trackpoint_failures;
static uint32_t trackpoint_retry_at;

static bool awake() { return usb_configuration && !(USB1_PORTSC1&USB_PORTSC1_SUSP); }

static void scan(uint16_t rows[KB_ROWS]) {
    for (unsigned r=0;r<KB_ROWS;r++) {
        rows[r]=0;
        digitalWriteFast(row_pins[r],LOW); pinMode(row_pins[r],OUTPUT);
        delayMicroseconds(30);
        for (unsigned c=0;c<KB_COLS;c++) if (!digitalReadFast(col_pins[c])) rows[r]|=(uint16_t)(1u<<c);
        pinMode(row_pins[r],INPUT);
        delayMicroseconds(10);
    }
}

// LED cathodes sink through their resistors; high impedance turns them off.
static void set_led(uint8_t pin,bool on) {
    if (on) { digitalWriteFast(pin,LOW); pinMode(pin,OUTPUT); }
    else pinMode(pin,INPUT);
}

static void update_lights() {
    bool on=awake();
    uint8_t state=(uint8_t)(on?((keyboard_leds&2)?1:0)|(layer.mic_muted?2:0)|(layer.speaker_muted?4:0)|(layer.fn_lock?8:0):0);
    if (state!=lights) {
        lights=state;
        set_led(PIN_LED_CAPS,state&1); set_led(PIN_LED_MIC,state&2);
        set_led(PIN_LED_SPEAKER,state&4); set_led(PIN_LED_FN_LOCK,state&8);
        digitalWriteFast(LED_BUILTIN,state&1);
    }
    uint8_t level=on?BACKLIGHT_PWM[layer.backlight]:0;
    if (level!=backlight) { backlight=level; analogWrite(PIN_BACKLIGHT,level); }
}

static uint8_t *setting(uintptr_t address) { return (uint8_t *)address; }

static void load_settings() {
    if (eeprom_read_byte(setting(0))!=SETTINGS_MAGIC) return;
    layer.fn_lock=eeprom_read_byte(setting(1))!=0;
    uint8_t level=eeprom_read_byte(setting(2));
    layer.backlight=level<KB_BACKLIGHT_LEVELS?level:0;
}

static void save_settings() {
    const uint8_t values[3]={SETTINGS_MAGIC,layer.fn_lock,layer.backlight};
    for (uintptr_t i=0;i<3;i++) if (eeprom_read_byte(setting(i))!=values[i]) eeprom_write_byte(setting(i),values[i]);
}

static void send_mouse() {
    ms_report_t report;
    if (!awake()) { ms_discard_motion(&mouse); return; } // don't replay movement after sleep
    if (!ms_peek_report(&mouse,&report)) return;
    usb_mouse_buttons_state=report.buttons;
    if (usb_mouse_move(report.x,report.y,report.wheel,report.pan)==0) ms_commit_report(&mouse,&report);
}

// Also runs while the TrackPoint is starting, so typing never pauses.
static void keyboard_task() {
    uint16_t raw[KB_ROWS];
    scan(raw);
    uint32_t now=millis();
    kb_update(&keys,raw,now);
    kb_report_t report; uint16_t consumer;
    if (kb_build_report(&layer,keys.stable,&report,&consumer)) save_pending=true;
    if (usb_configuration!=was_configured) { was_configured=usb_configuration; resend=true; }
    if (awake() && (resend || memcmp(&report,&sent_report,sizeof report))) {
        keyboard_modifier_keys=report.modifiers;
        memcpy(keyboard_keys,report.keys,sizeof report.keys);
        if (usb_keyboard_send()==0) { sent_report=report; resend=false; }
    }
    if (awake() && consumer!=sent_consumer) {
        if (sent_consumer) usb_keyboard_release_keycode((uint16_t)(0xe400|sent_consumer));
        if (consumer) usb_keyboard_press_keycode((uint16_t)(0xe400|consumer));
        sent_consumer=consumer;
    }
    uint8_t buttons=(uint8_t)((digitalReadFast(PIN_BUTTON_LEFT)?0:MS_LEFT)|(digitalReadFast(PIN_BUTTON_RIGHT)?0:MS_RIGHT)|
                              (digitalReadFast(PIN_BUTTON_MIDDLE)?0:MS_MIDDLE));
    ms_buttons(&mouse,buttons,now);
    send_mouse();
    update_lights();
}

static void trackpoint_task() {
    int value;
    while ((value=ps2::read())>=0) {
        int16_t dx,dy;
        switch (ms_ps2_feed(&parser,(uint8_t)value,value&0x100,&dx,&dy)) {
            case MS_PS2_PACKET: ms_motion(&mouse,dx,dy); break;
            case MS_PS2_RESET: trackpoint_ready=false; break; // re-enable after a power glitch
            default: break;
        }
    }
    if (trackpoint_ready || (int32_t)(millis()-trackpoint_retry_at)<0) return;
    trackpoint_ready=ps2::start(keyboard_task);
    trackpoint_failures=trackpoint_ready?0:(uint8_t)min(trackpoint_failures+1,10);
    // Keep trying if it is unplugged, but less often after a few failures.
    trackpoint_retry_at=millis()+(trackpoint_failures<3?2000:10000);
}

void setup() {
    for (unsigned r=0;r<KB_ROWS;r++) pinMode(row_pins[r],INPUT);
    for (unsigned c=0;c<KB_COLS;c++) pinMode(col_pins[c],INPUT_PULLUP);
    pinMode(PIN_BUTTON_LEFT,INPUT_PULLUP); pinMode(PIN_BUTTON_MIDDLE,INPUT_PULLUP); pinMode(PIN_BUTTON_RIGHT,INPUT_PULLUP);
    digitalWriteFast(PIN_BUTTON_COMMON,LOW); pinMode(PIN_BUTTON_COMMON,OUTPUT);
    pinMode(LED_BUILTIN,OUTPUT);
    analogWriteFrequency(PIN_BACKLIGHT,25000); // above hearing, no visible flicker
    kb_layer_init(&layer);
    load_settings();
    update_lights();
    ps2::begin(PIN_TP_CLK,PIN_TP_DATA,PIN_TP_RST);
    trackpoint_retry_at=millis();
}

void loop() {
    keyboard_task();
    trackpoint_task();
    // Flash writes pause interrupts, so never do them while the TrackPoint is starting.
    if (save_pending) { save_pending=false; save_settings(); }
}
