#include <gpiod.h>
#include <stdio.h>
#include <unistd.h>

#define GPIO_CHIP "/dev/gpiochip0"
#define GPIO_LINE1 12
#define GPIO_LINE2 13
#define CONSUMER "dual_gpio_toggle"

// Uses GPIO 12 AND 13
// Toggles Brake every 20 seconds
 
// In linux terminal
// gcc toggle_brake.c -o toggle_brake -lgpiod
// sudo ./toggle_brake


int main() {
    struct gpiod_chip *chip;
    struct gpiod_line *line1, *line2;
    int ret;

    // Open GPIO chip
    chip = gpiod_chip_open(GPIO_CHIP);
    if (!chip) {
        perror("Failed to open GPIO chip");
        return 1;
    }

    // Get both GPIO lines
    line1 = gpiod_chip_get_line(chip, GPIO_LINE1);
    line2 = gpiod_chip_get_line(chip, GPIO_LINE2);

    if (!line1 || !line2) {
        perror("Failed to get GPIO lines");
        gpiod_chip_close(chip);
        return 1;
    }

    // Request both lines as outputs
    ret = gpiod_line_request_output(line1, CONSUMER, 0);
    if (ret < 0) {
        perror("Failed to request GPIO line 12");
        gpiod_chip_close(chip);
        return 1;
    }

    ret = gpiod_line_request_output(line2, CONSUMER, 0);
    if (ret < 0) {
        perror("Failed to request GPIO line 13");
        gpiod_line_release(line1);
        gpiod_chip_close(chip);
        return 1;
    }

    printf("Alternating GPIO 12 and 13 every 20 seconds...\n");

    while (1) {
        // GPIO 12 HIGH, GPIO 13 LOW
        gpiod_line_set_value(line1, 1);
        gpiod_line_set_value(line2, 0);
        printf("GPIO 12: HIGH | GPIO 13: LOW\n");
        sleep(20);

        // GPIO 12 LOW, GPIO 13 HIGH
        gpiod_line_set_value(line1, 0);
        gpiod_line_set_value(line2, 1);
        printf("GPIO 12: LOW  | GPIO 13: HIGH\n");
        sleep(20);
    }

    // Cleanup (unreachable in this example, but good practice)
    gpiod_line_release(line1);
    gpiod_line_release(line2);
    gpiod_chip_close(chip);

    return 0;
}
