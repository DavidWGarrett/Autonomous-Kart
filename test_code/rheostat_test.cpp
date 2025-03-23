#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <linux/spi/spidev.h>
#include <sys/ioctl.h>
#include <string.h>
#include <errno.h>
#include <gpiod.h>

#define SPI_DEVICE "/dev/spidev1.0"
#define CS_GPIO_CHIP "/dev/gpiochip0"
#define CS_GPIO_LINE 17  // BCM GPIO17 (used as CS manually)
#define SPI_SPEED 1000000  // 1 MHz


/*
g++ -o rheostat_test rheostat_test.cpp -lgpiod
*/

int spi_fd;
gpiod_line *cs_line;
gpiod_chip *chip;

// MCP4162 command
#define MCP4162_VOLATILE_WIPER 0x00

void set_wiper(uint8_t value) {
    uint8_t tx[] = { MCP4162_VOLATILE_WIPER, value };
    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)tx,
        .rx_buf = 0,
        .len = sizeof(tx),
        .speed_hz = SPI_SPEED,
        .bits_per_word = 8,
    };

    // Set CS LOW
    gpiod_line_set_value(cs_line, 0);
    ioctl(spi_fd, SPI_IOC_MESSAGE(1), &tr);
    // Set CS HIGH
    gpiod_line_set_value(cs_line, 1);

    printf("Wiper set to: %d\n", value);
}

int main() {
    // Open GPIO chip and line
    chip = gpiod_chip_open(CS_GPIO_CHIP);
    if (!chip) {
        perror("Failed to open GPIO chip");
        return 1;
    }

    cs_line = gpiod_chip_get_line(chip, CS_GPIO_LINE);
    if (!cs_line) {
        perror("Failed to get CS GPIO line");
        gpiod_chip_close(chip);
        return 1;
    }

    if (gpiod_line_request_output(cs_line, "mcp4162_cs", 1) < 0) {
        perror("Failed to request CS line as output");
        gpiod_chip_close(chip);
        return 1;
    }

    // Open SPI device
    spi_fd = open(SPI_DEVICE, O_RDWR);
    if (spi_fd < 0) {
        perror("Failed to open SPI device");
        gpiod_line_release(cs_line);
        gpiod_chip_close(chip);
        return 1;
    }

    uint8_t mode = SPI_MODE_0;
    uint8_t bits = 8;

    if (ioctl(spi_fd, SPI_IOC_WR_MODE, &mode) < 0 ||
        ioctl(spi_fd, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0 ||
        ioctl(spi_fd, SPI_IOC_WR_MAX_SPEED_HZ, &SPI_SPEED) < 0) {
        perror("Failed to configure SPI");
        close(spi_fd);
        gpiod_line_release(cs_line);
        gpiod_chip_close(chip);
        return 1;
    }

    const useconds_t delay_us = 78125;  // 78.125 ms

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
    gpiod_line_release(cs_line);
    gpiod_chip_close(chip);
    return 0;
}
