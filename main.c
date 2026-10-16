#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"

#define N 26
static const uint8_t fpc[N] = {11,12,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40};
static const uint8_t gp[N] = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28};
static uint32_t candidate[N], stable[N];
static uint64_t changed_at, last_contact, last_report;
static bool running;

static void stop(void) {
    for (int i=0;i<N;i++) {
        gpio_set_dir(gp[i],GPIO_IN);
        gpio_disable_pulls(gp[i]);
    }
    running=false;
}

static void report(void) {
    printf("{\"type\":\"state\",\"pairs\":[");
    bool comma=false;
    for (int a=0;a<N;a++) for (int b=a+1;b<N;b++) if (stable[a] & (1u<<b)) {
        printf("%s[%u,%u]",comma?",":"",fpc[a],fpc[b]);
        comma=true;
    }
    puts("]}");
    last_report=time_us_64();
}

static void command(const char *line) {
    last_contact=time_us_64();
    if (!strcmp(line,"HELLO")) {
        puts("{\"type\":\"hello\",\"protocol\":1,\"firmware\":\"t14-diagnostics\",\"wiring\":\"t14-fpc-v1\"}");
    } else if (!strcmp(line,"START t14-fpc-v1")) {
        stop();
        memset(candidate,0,sizeof candidate);
        memset(stable,0,sizeof stable);
        for (int i=0;i<N;i++) gpio_pull_up(gp[i]);
        sleep_us(100);
        // A passive switch matrix should have no low lines with all pins input.
        for (int i=0;i<N;i++) if (!gpio_get(gp[i])) {
            stop();
            printf("{\"type\":\"fault\",\"fpc\":%u,\"message\":\"line low with all drivers off\"}\n",fpc[i]);
            return;
        }
        changed_at=time_us_64();
        running=true;
        puts("{\"type\":\"started\"}");
        report();
    } else if (!strcmp(line,"STOP")) {
        stop(); puts("{\"type\":\"stopped\"}");
    } else if (!strcmp(line,"PING")) puts("{\"type\":\"pong\"}");
    else puts("{\"type\":\"error\",\"message\":\"unknown command\"}");
}

static void scan(void) {
    uint32_t found[N]={0};
    // Scan both directions to discover pairs without assuming row/column roles.
    // Exactly one output LOW at a time; all other pins are pulled-up inputs.
    for (int i=0;i<N;i++) {
        gpio_put(gp[i],0);
        gpio_set_dir(gp[i],GPIO_OUT);
        sleep_us(40);
        for (int j=0;j<N;j++) if (i!=j && !gpio_get(gp[j])) {
            int a=i<j?i:j, b=i<j?j:i;
            found[a] |= 1u<<b;
        }
        gpio_set_dir(gp[i],GPIO_IN);
        sleep_us(40);
    }
    uint64_t now=time_us_64();
    if (memcmp(candidate,found,sizeof found)) {
        memcpy(candidate,found,sizeof found);
        changed_at=now;
    }
    if (now-changed_at>=20000 && memcmp(stable,candidate,sizeof stable)) {
        memcpy(stable,candidate,sizeof stable);
        report();
    } else if (now-last_report>=250000) report();
}

int main(void) {
    for (int i=0;i<N;i++) gpio_init(gp[i]);
    stop();
    stdio_init_all();
    char line[96];
    size_t length=0;
    bool overflow=false;
    while (true) {
        if (!stdio_usb_connected()) { stop(); length=0; overflow=false; }
        for (int n=0;n<96;n++) {
            int c=getchar_timeout_us(0);
            if (c==PICO_ERROR_TIMEOUT) break;
            if (c=='\r') continue;
            if (c=='\n') {
                line[length]=0;
                if (overflow) { stop(); puts("{\"type\":\"error\",\"message\":\"command too long\"}"); }
                else command(line);
                length=0; overflow=false;
            } else if (length<sizeof line-1) line[length++]=(char)c;
            else overflow=true;
        }
        if (running && time_us_64()-last_contact>3000000) {
            stop(); puts("{\"type\":\"stopped\",\"reason\":\"heartbeat timeout\"}");
        }
        if (running) scan();
        sleep_ms(1);
    }
}

