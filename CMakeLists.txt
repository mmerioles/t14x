cmake_minimum_required(VERSION 3.13)

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(t14_keyboard C CXX ASM)

pico_sdk_init()

add_executable(t14_diagnostics
    main.c
)

target_link_libraries(t14_diagnostics pico_stdlib)
target_compile_options(t14_diagnostics PRIVATE -Wall -Wextra -Werror)

# Enable USB output, disable UART
pico_enable_stdio_usb(t14_diagnostics 1)
pico_enable_stdio_uart(t14_diagnostics 0)

pico_add_extra_outputs(t14_diagnostics)

add_executable(t14_keyboard
    firmware/keyboard_main.c
    firmware/keyboard_core.c
    firmware/keymap.c
    firmware/usb_descriptors.c
)
target_include_directories(t14_keyboard PRIVATE firmware)
target_link_libraries(t14_keyboard pico_stdlib pico_unique_id tinyusb_device)
target_compile_options(t14_keyboard PRIVATE -Wall -Wextra -Werror)
pico_enable_stdio_usb(t14_keyboard 0)
pico_enable_stdio_uart(t14_keyboard 0)
pico_add_extra_outputs(t14_keyboard)

