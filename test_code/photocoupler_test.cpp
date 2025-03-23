#include <gpiod.h>
#include <iostream>
#include <unistd.h> // for sleep()
#include <csignal>

#define GPIO_CHIP "/dev/gpiochip0"
#define GPIO_LINE 17 // BCM GPIO17

/*
g++ -o photocoupler_test photocoupler_test.cpp -lgpiod
*/

bool keep_running = true;

void handle_sigint(int) {
    keep_running = false;
}

int main() {
    signal(SIGINT, handle_sigint); // Graceful exit on Ctrl+C

    gpiod_chip *chip = gpiod_chip_open(GPIO_CHIP);
    if (!chip) {
        std::cerr << "Failed to open GPIO chip: " << GPIO_CHIP << std::endl;
        return 1;
    }

    gpiod_line *line = gpiod_chip_get_line(chip, GPIO_LINE);
    if (!line) {
        std::cerr << "Failed to get GPIO line: " << GPIO_LINE << std::endl;
        gpiod_chip_close(chip);
        return 1;
    }

    if (gpiod_line_request_output(line, "photocoupler_control", 0) < 0) {
        std::cerr << "Failed to request GPIO line as output." << std::endl;
        gpiod_chip_close(chip);
        return 1;
    }

    std::cout << "Starting 4N35 control loop on GPIO17..." << std::endl;

    while (keep_running) {
        std::cout << "Turning ON 4N35 input LED" << std::endl;
        gpiod_line_set_value(line, 1);
        sleep(20);

        std::cout << "Turning OFF 4N35 input LED" << std::endl;
        gpiod_line_set_value(line, 0);
        sleep(20);
    }

    std::cout << "\nExiting program. Cleaning up..." << std::endl;
    gpiod_line_release(line);
    gpiod_chip_close(chip);

    return 0;
}
