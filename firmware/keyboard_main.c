#include <string.h>
#include "pico/stdlib.h"
#include "tusb.h"
#include "keyboard_core.h"
#include "keymap.h"

static kb_state_t state;
static kb_report_t current,last;
static uint16_t consumer,last_consumer;
static bool sent[2];
static uint8_t idle[2],leds;
static uint32_t sent_at[2];

static void scan(uint16_t rows[KB_ROWS]) {
    for (unsigned r=0;r<KB_ROWS;r++) {
        rows[r]=0;
        gpio_put(row_gpio[r],0);
        gpio_set_dir(row_gpio[r],GPIO_OUT);
        sleep_us(40);
        for (unsigned c=0;c<KB_COLS;c++) if (!gpio_get(col_gpio[c])) rows[r]|=1u<<c;
        gpio_set_dir(row_gpio[r],GPIO_IN);
        sleep_us(20);
    }
}

void tud_mount_cb(void) { sent[0]=sent[1]=false; }
void tud_umount_cb(void) { sent[0]=sent[1]=false; leds=0; }
void tud_resume_cb(void) { sent[0]=sent[1]=false; }
bool tud_hid_set_idle_cb(uint8_t instance,uint8_t rate) {
    if (instance>=2) return false;
    idle[instance]=rate;
    return true;
}
void tud_hid_set_protocol_cb(uint8_t instance,uint8_t protocol) {
    (void)protocol;
    if (instance<2) sent[instance]=false;
}
uint16_t tud_hid_get_report_cb(uint8_t instance,uint8_t id,hid_report_type_t type,uint8_t *buffer,uint16_t requested) {
    if (id || instance>=2) return 0;
    const void *data; uint16_t length;
    if (type==HID_REPORT_TYPE_OUTPUT && instance==0) { data=&leds; length=1; }
    else if (type==HID_REPORT_TYPE_INPUT) {
        data=instance==0?(const void *)&current:(const void *)&consumer;
        length=instance==0?sizeof current:sizeof consumer;
    } else return 0;
    if (length>requested) length=requested;
    memcpy(buffer,data,length);
    return length;
}
void tud_hid_set_report_cb(uint8_t instance,uint8_t id,hid_report_type_t type,uint8_t const *buffer,uint16_t length) {
    if (instance==0 && id==0 && type==HID_REPORT_TYPE_OUTPUT && length) leds=buffer[0];
}

int main(void) {
    for (unsigned r=0;r<KB_ROWS;r++) { gpio_init(row_gpio[r]); gpio_disable_pulls(row_gpio[r]); }
    for (unsigned c=0;c<KB_COLS;c++) { gpio_init(col_gpio[c]); gpio_pull_up(col_gpio[c]); }
    gpio_init(PICO_DEFAULT_LED_PIN); gpio_set_dir(PICO_DEFAULT_LED_PIN,GPIO_OUT);
    tusb_init();
    while (true) {
        tud_task();
        uint16_t raw[KB_ROWS];
        scan(raw);
        uint32_t now=to_ms_since_boot(get_absolute_time());
        kb_update(&state,raw,now);
        kb_build_report(state.stable,&current,&consumer);
        gpio_put(PICO_DEFAULT_LED_PIN,tud_mounted() && !tud_suspended() && (leds&KEYBOARD_LED_CAPSLOCK));
        if (!tud_mounted() || tud_suspended()) continue;
        bool due=idle[0] && (uint32_t)(now-sent_at[0])>=(uint32_t)idle[0]*4;
        if (tud_hid_n_ready(0) && (!sent[0] || memcmp(&current,&last,sizeof current) || due)) {
            if (tud_hid_n_report(0,0,&current,sizeof current)) {
                last=current; sent[0]=true; sent_at[0]=now;
            }
        }
        due=idle[1] && (uint32_t)(now-sent_at[1])>=(uint32_t)idle[1]*4;
        if (tud_hid_n_ready(1) && (!sent[1] || consumer!=last_consumer || due)) {
            if (tud_hid_n_report(1,0,&consumer,sizeof consumer)) {
                last_consumer=consumer; sent[1]=true; sent_at[1]=now;
            }
        }
    }
}
