// Wiring test firmware for the diagnostics app: newline-delimited JSON over USB serial.
#include <Arduino.h>
#include <string.h>
#include "mouse_core.h"
#include "pins.h"
#include "ps2.h"

static const uint8_t fpc[SCAN_COUNT]=SCAN_FPC;
static const uint8_t pins[SCAN_COUNT]=SCAN_PINS;
static const uint8_t led_pins[4]={PIN_LED_CAPS,PIN_LED_MIC,PIN_LED_SPEAKER,PIN_LED_FN_LOCK};
static const uint8_t BACKLIGHT_PWM[3]={0,60,255};
static uint32_t candidate[SCAN_COUNT],stable[SCAN_COUNT];
static uint32_t changed_at,last_contact,last_report,motion_at;
static bool running,trackpoint;
static int32_t motion_x,motion_y;
static unsigned led_mask,backlight_level;
static ms_ps2_parser_t parser;

static void stop_scan() {
    for (int i=0;i<SCAN_COUNT;i++) pinMode(pins[i],INPUT);
    running=false;
}

static void set_lights(unsigned mask,unsigned level) {
    for (int i=0;i<4;i++) {
        if (mask&(1u<<i)) { digitalWriteFast(led_pins[i],LOW); pinMode(led_pins[i],OUTPUT); }
        else pinMode(led_pins[i],INPUT);
    }
    analogWrite(PIN_BACKLIGHT,BACKLIGHT_PWM[level]);
}

static void stop_all() {
    stop_scan();
    led_mask=backlight_level=0; set_lights(0,0);
    trackpoint=false;
}

static void report() {
    Serial.print("{\"type\":\"state\",\"pairs\":[");
    bool comma=false;
    for (int a=0;a<SCAN_COUNT;a++) for (int b=a+1;b<SCAN_COUNT;b++) if (stable[a]&(1u<<b)) {
        Serial.printf("%s[%u,%u]",comma?",":"",fpc[a],fpc[b]);
        comma=true;
    }
    Serial.println("]}");
    last_report=millis();
}

// Drive exactly one line low at a time; all others are pulled-up inputs.
// Scanning both directions finds pairs without assuming rows or columns.
static void scan() {
    uint32_t found[SCAN_COUNT]={0};
    for (int i=0;i<SCAN_COUNT;i++) {
        digitalWriteFast(pins[i],LOW); pinMode(pins[i],OUTPUT);
        delayMicroseconds(40);
        for (int j=0;j<SCAN_COUNT;j++) if (i!=j && !digitalReadFast(pins[j])) {
            int a=i<j?i:j,b=i<j?j:i;
            found[a]|=1u<<b;
        }
        pinMode(pins[i],INPUT_PULLUP);
        delayMicroseconds(40);
    }
    uint32_t now=millis();
    if (memcmp(candidate,found,sizeof found)) { memcpy(candidate,found,sizeof found); changed_at=now; }
    if (now-changed_at>=20 && memcmp(stable,candidate,sizeof stable)) { memcpy(stable,candidate,sizeof stable); report(); }
    else if (now-last_report>=250) report();
}

// Keeps scanning, or at least the app's connection alive, while the TrackPoint starts.
static void trackpoint_idle() {
    static uint32_t alive_at;
    if (running) scan();
    else if (millis()-alive_at>=500) { Serial.println("{\"type\":\"pong\"}"); alive_at=millis(); }
}

static void start_scan() {
    stop_scan();
    memset(candidate,0,sizeof candidate);
    memset(stable,0,sizeof stable);
    for (int i=0;i<SCAN_COUNT;i++) pinMode(pins[i],INPUT_PULLUP);
    delayMicroseconds(100);
    // A passive switch matrix should have no low lines with all pins input.
    for (int i=0;i<SCAN_COUNT;i++) if (!digitalReadFast(pins[i])) {
        stop_all();
        Serial.printf("{\"type\":\"fault\",\"fpc\":%u,\"message\":\"line low with all drivers off\"}\n",fpc[i]);
        return;
    }
    changed_at=millis();
    running=true;
    Serial.println("{\"type\":\"started\"}");
    report();
}

static bool number(const char *text,unsigned limit,unsigned *value) {
    char *end;
    unsigned long parsed=strtoul(text,&end,10);
    if (end==text || *end || parsed>limit) return false;
    *value=(unsigned)parsed;
    return true;
}

static void command(const char *line) {
    last_contact=millis();
    unsigned value;
    if (!strcmp(line,"HELLO")) {
        Serial.println("{\"type\":\"hello\",\"protocol\":2,\"firmware\":\"t14-diagnostics\",\"board\":\"teensy41\",\"wiring\":\"" T14_WIRING_ID "\"}");
    } else if (!strcmp(line,"START " T14_WIRING_ID)) start_scan();
    else if (!strcmp(line,"STOP")) { stop_all(); Serial.println("{\"type\":\"stopped\"}"); }
    else if (!strcmp(line,"PING")) Serial.println("{\"type\":\"pong\"}");
    else if (!strncmp(line,"LED ",4) && number(line+4,15,&value)) {
        led_mask=value; set_lights(led_mask,backlight_level);
        Serial.printf("{\"type\":\"leds\",\"mask\":%u}\n",value);
    } else if (!strncmp(line,"BACKLIGHT ",10) && number(line+10,2,&value)) {
        backlight_level=value; set_lights(led_mask,backlight_level);
        Serial.printf("{\"type\":\"backlight\",\"level\":%u}\n",value);
    } else if (!strcmp(line,"TRACKPOINT")) {
        Serial.println("{\"type\":\"trackpoint\",\"status\":\"starting\"}");
        trackpoint=ps2::start(trackpoint_idle);
        parser.count=0; motion_x=motion_y=0;
        Serial.printf("{\"type\":\"trackpoint\",\"status\":\"%s\"}\n",trackpoint?"ready":"no response");
    } else { stop_all(); Serial.println("{\"type\":\"error\",\"message\":\"unknown command\"}"); }
}

static void trackpoint_task() {
    int value;
    while ((value=ps2::read())>=0) {
        int16_t dx,dy;
        switch (ms_ps2_feed(&parser,(uint8_t)value,value&0x100,&dx,&dy)) {
            case MS_PS2_PACKET: motion_x+=dx; motion_y-=dy; break; // report screen directions
            case MS_PS2_RESET:
                if (trackpoint) Serial.println("{\"type\":\"trackpoint\",\"status\":\"reset\"}");
                trackpoint=false; break;
            default: break;
        }
    }
    if (!trackpoint) { motion_x=motion_y=0; return; }
    if ((motion_x || motion_y) && millis()-motion_at>=30) {
        Serial.printf("{\"type\":\"motion\",\"dx\":%ld,\"dy\":%ld}\n",(long)motion_x,(long)motion_y);
        motion_x=motion_y=0; motion_at=millis();
    }
}

void setup() {
    for (int i=0;i<SCAN_COUNT;i++) pinMode(pins[i],INPUT);
    analogWriteFrequency(PIN_BACKLIGHT,25000);
    set_lights(0,0);
    ps2::begin(PIN_TP_CLK,PIN_TP_DATA,PIN_TP_RST);
    pinMode(LED_BUILTIN,OUTPUT);
    Serial.begin(115200);
}

void loop() {
    static char line[96];
    static size_t length;
    static bool overflow;
    if (!Serial.dtr()) { if (running || trackpoint || led_mask || backlight_level) stop_all(); length=0; overflow=false; }
    while (Serial.available()) {
        int c=Serial.read();
        if (c=='\r') continue;
        if (c=='\n') {
            line[length]=0;
            if (overflow) { stop_all(); Serial.println("{\"type\":\"error\",\"message\":\"command too long\"}"); }
            else command(line);
            length=0; overflow=false;
        } else if (length<sizeof line-1) line[length++]=(char)c;
        else overflow=true;
    }
    if ((running || trackpoint || led_mask || backlight_level) && millis()-last_contact>3000) {
        stop_all(); Serial.println("{\"type\":\"stopped\",\"reason\":\"heartbeat timeout\"}");
    }
    if (running) scan();
    trackpoint_task();
    digitalWriteFast(LED_BUILTIN,running);
    delay(1);
}
