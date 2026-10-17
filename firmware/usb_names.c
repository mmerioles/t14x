// Shown by the operating system instead of Teensyduino's default names.
#include "usb_names.h"

struct usb_string_descriptor_struct usb_string_manufacturer_name={2+2*11,3,{'T','1','4',' ','P','r','o','j','e','c','t'}};
#ifdef T14_DIAGNOSTICS
struct usb_string_descriptor_struct usb_string_product_name={2+2*15,3,{'T','1','4',' ','D','i','a','g','n','o','s','t','i','c','s'}};
#else
struct usb_string_descriptor_struct usb_string_product_name={2+2*16,3,{'T','1','4',' ','U','S','B',' ','K','e','y','b','o','a','r','d'}};
#endif
