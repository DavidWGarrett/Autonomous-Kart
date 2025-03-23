#include <gpiod.h>
#include <iostream>
#include <unistd.h>
#include <csignal>

#define GPIO_CHIP_PATH "/dev/gpiochip0"
#define GPIO_LINE1_NUM 12
#define GPIO_LINE2_NUM 13
#define CONSUMER_LABEL "dual_gpio_toggle"


/*
g++ toggle_brake.cpp -o toggle_brake -lgpiod
sudo ./toggle_brake

*/
bool keep_running = true;

void handle_sigint(int) {
    std::cout << "\nStopping toggling...\n";
    keep_running = false;
}

int main() {
    signal(SIGINT, handle_sigint);

    gpiod_chip *chip = gpiod_chip_open(GPIO_CHIP_PATH);
    if (!chip) {
        perror("Failed to open GPIO chip");
        return 1;
    }

    gpiod_line *line1 = gpiod_chip_get_line(chip, GPIO_LINE1_NUM);
    gpiod_line *line2 = gpiod_chip_get_line(chip, GPIO_LINE2_NUM);

    if (!line1 || !line2) {
        perror("Failed to get GPIO lines");
        gpiod_chip_close(chip);
        return 1;
    }

    if (gpiod_line_request_output(line1, CONSUMER_LABEL, 0) < 0) {
        perror("Failed to request GPIO line 12 as output");
        gpiod_chip_close(chip);
        return 1;
    }

    if (gpiod_line_request_output(line2, CONSUMER_LABEL, 0) < 0) {
        perror("Failed to request GPIO line 13 as output");
        gpiod_line_release(line1);
        gpiod_chip_close(chip);
        return 1;
    }

    std::cout << "Alternating GPIO 12 and 13 every 20 seconds...\n";

    while (keep_running) {
        gpiod_line_set_value(line1, 1);
        gpiod_line_set_value(line2, 0);
        std::cout << "GPIO 12: HIGH | GPIO 13: LOW\n";
        sleep(20);

        gpiod_line_set_value(line1, 0);
        gpiod_line_set_value(line2, 1);
        std::cout << "GPIO 12: LOW  | GPIO 13: HIGH\n";
        sleep(20);
    }

    // Cleanup
    gpiod_line_set_value(line1, 0);
    gpiod_line_set_value(line2, 0);
    gpiod_line_release(line1);
    gpiod_line_release(line2);
    gpiod_chip_close(chip);

    std::cout << "GPIO lines released. Program exited cleanly.\n";
    return 0;
}
