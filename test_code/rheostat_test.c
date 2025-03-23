#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <linux/spi/spidev.h>
#include <sys/ioctl.h>
#include <string.h>
#include <errno.h>
#include <wiringPi.h>

#define SPI_DEVICE "/dev/spidev1.0"
#define CS_PIN 0  // WiringPi pin 0 = BCM GPIO 17
#define SPI_SPEED 1000000  // 1 MHz

int spi_fd;

// MCP4162 command
#define MCP4162_VOLATILE_WIPER 0x00

/*
CS → GPIO17
SCK → GPIO21 (SPI1_SCLK)
MOSI → GPIO20 (SPI1_MOSI)
MISO → GPIO19 (SPI1_MISO)
VDD → 5V
VSS → GND
P0W → Alltrax Throttle 1
P0B → Alltrax Throttle 2
*/

void set_wiper(uint8_t value) {
    uint8_t tx[] = { MCP4162_VOLATILE_WIPER, value };
    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = 0,
        .len = sizeof(tx),
        .speed_hz = SPI_SPEED,
        .bits_per_word = 8,
    };

    digitalWrite(CS_PIN, LOW);
    ioctl(spi_fd, SPI_IOC_MESSAGE(1), &tr);
    digitalWrite(CS_PIN, HIGH);

    printf("Wiper set to: %d\n", value);
}

int main() {
    // Initialize WiringPi (uses BCM GPIO numbering)
    if (wiringPiSetup() == -1) {
        fprintf(stderr, "Failed to initialize WiringPi\n");
        return 1;
    }

    pinMode(CS_PIN, OUTPUT);
    digitalWrite(CS_PIN, HIGH); // deselect by default

    // Open SPI device
    spi_fd = open(SPI_DEVICE, O_RDWR);
    if (spi_fd < 0) {
        perror("Failed to open SPI device");
        return 1;
    }

    uint8_t mode = SPI_MODE_0;
    uint8_t bits = 8;

    if (ioctl(spi_fd, SPI_IOC_WR_MODE, &mode) < 0 ||
        ioctl(spi_fd, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0 ||
        ioctl(spi_fd, SPI_IOC_WR_MAX_SPEED_HZ, &SPI_SPEED) < 0) {
        perror("Failed to configure SPI");
        close(spi_fd);
        return 1;
    }

    const useconds_t delay_us = 78125;  // 78.125 ms in microseconds

    printf("Starting MCP4162 ramp loop (0 to 255 to 0 over 40 seconds total)...\n");

    while (1) {
        // Ramp up
        for (int val = 0; val <= 255; val++) {
            set_wiper((uint8_t)val);
            usleep(delay_us);
        }

        // Ramp down
        for (int val = 255; val >= 0; val--) {
            set_wiper((uint8_t)val);
            usleep(delay_us);
        }
    }


    // Cleanup (unreachable here, but good practice)
    close(spi_fd);
    return 0;
}
