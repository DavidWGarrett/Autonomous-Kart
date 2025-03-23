#include <iostream>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#include <sstream>
#include <vector>
#include <string.h>

#define SERIAL_PORT "/dev/ttyACM0"
#define BAUDRATE B115200

/*
g++ -o wireless_receiver_test wireless_receiver_test.cpp
./wireless_receiver_test
*/

std::vector<int> parseCSVLine(const std::string& line) {
    std::vector<int> values;
    std::stringstream ss(line);
    std::string item;

    while (std::getline(ss, item, ',')) {
        try {
            values.push_back(std::stoi(item));
        } catch (...) {
            values.push_back(-1); // fallback for invalid entries
        }
    }

    return values;
}

int main() {
    int fd = open(SERIAL_PORT, O_RDWR | O_NOCTTY);
    if (fd < 0) {
        perror("❌ Failed to open serial port");
        return 1;
    }

    struct termios tty{};
    if (tcgetattr(fd, &tty) != 0) {
        perror("❌ Error getting termios attributes");
        return 1;
    }

    cfsetospeed(&tty, BAUDRATE);
    cfsetispeed(&tty, BAUDRATE);

    tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;     // 8-bit chars
    tty.c_iflag &= ~IGNBRK;                         // disable break processing
    tty.c_lflag = 0;                                // no signaling chars, no echo, no canonical processing
    tty.c_oflag = 0;                                // no remapping, no delays
    tty.c_cc[VMIN]  = 1;                            // read doesn't block
    tty.c_cc[VTIME] = 1;                            // 0.1s read timeout

    tty.c_iflag &= ~(IXON | IXOFF | IXANY);         // shut off xon/xoff ctrl

    tty.c_cflag |= (CLOCAL | CREAD);                // ignore modem controls
    tty.c_cflag &= ~(PARENB | PARODD);              // shut off parity
    tty.c_cflag &= ~CSTOPB;
    tty.c_cflag &= ~CRTSCTS;

    if (tcsetattr(fd, TCSANOW, &tty) != 0) {
        perror("Error setting termios attributes");
        return 1;
    }

    std::cout << "Listening on " << SERIAL_PORT << " at 115200 baud...\n\n";

    std::string line;
    char buf = 0;
    while (true) {
        line.clear();
        while (read(fd, &buf, 1) == 1) {
            if (buf == '\n') break;
            if (buf != '\r') line += buf;
        }

        if (line.empty()) continue;

        std::cout << "Raw: " << line << std::endl;

        auto values = parseCSVLine(line);
        if (values.size() == 9) {
            std::cout << "Parsed: ";
            for (int v : values) std::cout << v << " ";
            std::cout << std::endl;
        } else {
            std::cout << "Unexpected format (not 9 values)\n";
        }
    }

    close(fd);
    return 0;
}
