#include <string.h>
#include "pico/unique_id.h"
#include "tusb.h"

// TinyUSB development VID for this personal prototype, not a production allocation.
static const tusb_desc_device_t device={
    .bLength=sizeof(tusb_desc_device_t), .bDescriptorType=TUSB_DESC_DEVICE,
    .bcdUSB=0x0200, .bMaxPacketSize0=64, .idVendor=0xcafe, .idProduct=0x4010,
    .bcdDevice=0x0100, .iManufacturer=1, .iProduct=2, .iSerialNumber=3,
    .bNumConfigurations=1
};
static const uint8_t keyboard_descriptor[]={TUD_HID_REPORT_DESC_KEYBOARD()};
static const uint8_t consumer_descriptor[]={TUD_HID_REPORT_DESC_CONSUMER()};
static const uint8_t configuration[]={
    TUD_CONFIG_DESCRIPTOR(1,2,0,TUD_CONFIG_DESC_LEN+2*TUD_HID_DESC_LEN,0,100),
    TUD_HID_DESCRIPTOR(0,0,HID_ITF_PROTOCOL_KEYBOARD,sizeof keyboard_descriptor,0x81,16,1),
    TUD_HID_DESCRIPTOR(1,0,HID_ITF_PROTOCOL_NONE,sizeof consumer_descriptor,0x82,16,1)
};

uint8_t const *tud_descriptor_device_cb(void) { return (const uint8_t *)&device; }
uint8_t const *tud_descriptor_configuration_cb(uint8_t index) { (void)index; return configuration; }
uint8_t const *tud_hid_descriptor_report_cb(uint8_t instance) {
    return instance==0?keyboard_descriptor:instance==1?consumer_descriptor:NULL;
}
uint16_t const *tud_descriptor_string_cb(uint8_t index,uint16_t language) {
    (void)language;
    static uint16_t descriptor[33];
    char serial[2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES+1];
    if (index==0) { descriptor[0]=0x0304; descriptor[1]=0x0409; return descriptor; }
    const char *text;
    switch(index) {
        case 1: text="T14 Pico Project"; break;
        case 2: text="T14 USB Keyboard"; break;
        case 3: pico_get_unique_board_id_string(serial,sizeof serial); text=serial; break;
        default: return NULL;
    }
    size_t length=strlen(text); if (length>32) length=32;
    descriptor[0]=(uint16_t)((TUSB_DESC_STRING<<8)|(2*length+2));
    for (size_t i=0;i<length;i++) descriptor[i+1]=(uint8_t)text[i];
    return descriptor;
}
