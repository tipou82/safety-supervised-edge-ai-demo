# GPIO Pin Mapping

## Raspberry Pi 5 (Linux/ROS2 Domain)

### GPIO Allocation Table

| GPIO # | Physical Pin | Function | Direction | Signal Type | Node | Safety Critical |
|--------|-------------|----------|-----------|-------------|------|-----------------|
| GPIO 17 | Pin 11 | **NORMAL state LED** (M1.1 bring-up) / Heartbeat output (planned M2+) | Output | Digital | actuator_node / health_node | No (LED) / **YES** (heartbeat) |
| GPIO 27 | Pin 13 | **DEGRADED state LED** (M1.1 bring-up) / Emergency stop input (planned M2+) | Output/Input | Digital | actuator_node | No (LED) / **YES** (e-stop) |
| GPIO 22 | Pin 15 | **SAFE STATE LED** (M1.1 bring-up) / Motor A IN1 (planned M2+) | Output | Digital | actuator_node | No |
| GPIO 18 | Pin 12 | Motor A PWM (ENA) | Output | PWM | actuator_node | No |
| GPIO 10 | Pin 19 | Motor A IN2 | Output | Digital | actuator_node | No |
| GPIO 9 | Pin 21 | Motor B IN3 | Output | Digital | actuator_node | No |
| GPIO 11 | Pin 23 | Motor B IN4 | Output | Digital | actuator_node | No |
| GPIO 12 | Pin 32 | Motor B PWM (ENB) | Output | PWM | actuator_node | No |
| GPIO 23 | Pin 16 | Ultrasonic 1 TRIG | Output | Digital pulse | ultrasonic_node | No |
| GPIO 24 | Pin 18 | Ultrasonic 1 ECHO | Input | Digital pulse | ultrasonic_node | No |
| GPIO 5 | Pin 29 | Ultrasonic 2 TRIG | Output | Digital pulse | ultrasonic_node | No |
| GPIO 6 | Pin 31 | Ultrasonic 2 ECHO | Input | Digital pulse | ultrasonic_node | No |
| GPIO 13 | Pin 33 | Ultrasonic 3 TRIG | Output | Digital pulse | ultrasonic_node | No |
| GPIO 19 | Pin 35 | Ultrasonic 3 ECHO | Input | Digital pulse | ultrasonic_node | No |

### Power and Ground Pins

| Physical Pin | Function | Connection |
|-------------|----------|------------|
| Pin 2 | 5V Power | Ultrasonic sensor 1 VCC |
| Pin 4 | 5V Power | Ultrasonic sensors 2, 3 VCC |
| Pin 6 | Ground | Common ground (Pi400, sensors, motors) |
| Pin 9 | Ground | Ultrasonic sensor 2 GND |
| Pin 14 | Ground | Ultrasonic sensor 3 GND |

### GPIO Configuration Details

**Heartbeat Output (GPIO 17)**
- **Mode**: GPIO output, initially LOW
- **Drive Strength**: 2 mA (default)
- **Pull**: None
- **Pattern**: 10 Hz square wave (50 ms HIGH, 50 ms LOW)
- **Implementation**: Software toggled by health_node at 10 Hz
- **Failure Mode**: Stuck-at-low or no transitions → watchdog timeout

**Emergency Stop Input (GPIO 27)**
- **Mode**: GPIO input
- **Pull**: Pull-up resistor (internal 50 kΩ)
- **Active State**: Active-low (0V = emergency stop)
- **Polling Rate**: 100 Hz by actuator_node
- **Response Time**: <30 ms from assertion to motor disable
- **Failure Mode**: Fail-safe (missing connection = pulled HIGH = stop)

**Motor Control GPIOs**
- **IN1-IN4 (GPIO 22, 10, 9, 11)**: Direction control, digital outputs
- **ENA/ENB (GPIO 18, 12)**: Speed control, hardware PWM outputs
- **PWM Frequency**: 1 kHz (motor driver compatible)
- **PWM Range**: 0-100% duty cycle

**Ultrasonic Sensor GPIOs**
- **TRIG (GPIO 23, 5, 13)**: 10 µs pulse to trigger measurement
- **ECHO (GPIO 24, 6, 19)**: Input, measures pulse width (distance)
- **Pull**: None on TRIG, pull-down on ECHO
- **Voltage Divider**: Required on ECHO (5V → 3.3V)

### Pinout Diagram (Pi5 GPIO Header)

```
     3.3V  (1) (2)  5V
    GPIO2  (3) (4)  5V
    GPIO3  (5) (6)  GND ──────────┐ Common Ground
    GPIO4  (7) (8)  GPIO14        │
      GND  (9) (10) GPIO15        │
   GPIO17 (11) (12) GPIO18 ──┐    │ Heartbeat out
   GPIO27 (13) (14) GND      │    │ E-Stop in
   GPIO22 (15) (16) GPIO23   │    │ Motor A IN1
     3.3V (17) (18) GPIO24   │    │ Motor A PWM
   GPIO10 (19) (20) GND      │    │ Motor A IN2
    GPIO9 (21) (22) GPIO25   │    │ Motor B IN3
   GPIO11 (23) (24) GPIO8    │    │ Motor B IN4
      GND (25) (26) GPIO7    │    │
    GPIO0 (27) (28) GPIO1    │    │
    GPIO5 (29) (30) GND      │    │ Ultrasonic 2 TRIG
    GPIO6 (31) (32) GPIO12 ──┘    │ Ultrasonic 2 ECHO
   GPIO13 (33) (34) GND ──────────┘ Motor B PWM
   GPIO19 (35) (36) GPIO16          Ultrasonic 3 TRIG
   GPIO26 (37) (38) GPIO20          Ultrasonic 3 ECHO
      GND (39) (40) GPIO21
```

## Raspberry Pi 400 (QNX Supervisor Domain)

### GPIO Allocation Table

| GPIO # | Physical Pin | Function | Direction | Signal Type | Component | Safety Critical |
|--------|-------------|----------|-----------|-------------|-----------|-----------------|
| TBD | TBD | Heartbeat input | Input | Digital (10 Hz) | qnx_wdg_server | **YES** |
| TBD | TBD | Emergency stop output | Output | Active-low | safe_state_controller | **YES** |
| TBD | TBD | Status LED (optional) | Output | Digital | Diagnostic | No |

**Note**: Exact GPIO pin numbers for Pi400 TBD based on available pins and physical wiring convenience. Update this document during hardware integration.

### GPIO Configuration Details

**Heartbeat Input (GPIO TBD)**
- **Mode**: GPIO input
- **Pull**: Pull-down resistor (internal 50 kΩ)
- **Edge Detection**: Both edges (for frequency analysis)
- **Interrupt**: Edge-triggered interrupt (optional for low latency)
- **Polling**: 1 kHz if no interrupt support
- **Timeout Threshold**: 500 ms since last edge

**Emergency Stop Output (GPIO TBD)**
- **Mode**: GPIO output, initially LOW (asserted)
- **Drive Strength**: 2 mA
- **Pull**: None
- **Active State**: Active-low (0V = emergency stop)
- **Assertion Latency**: <20 ms from fault detection
- **Default State**: LOW (safe) until system ready

**Status LED (Optional)**
- **Mode**: GPIO output
- **Pattern**:
  - Steady ON: NORMAL state
  - Slow blink (1 Hz): WARNING state
  - Fast blink (5 Hz): DEGRADED state
  - OFF: SAFE_STATE

### Pinout Diagram (Pi400 GPIO Header)

TBD - Update after physical hardware integration.

## GPIO Design Rationale

### Safety-Critical Signals

**Why GPIO for Heartbeat?**
- Simple, deterministic protocol
- No complex middleware or network stack
- Easy to monitor with edge detection or polling
- Single-bit error obvious (stuck-at fault)

**Why Active-Low for Emergency Stop?**
- Fail-safe: wire disconnection = LOW = emergency stop
- Pulled-up on receiver (Pi5 GPIO 27), so missing signal → safe state
- Common pattern in safety-critical systems

### Failure Mode Analysis

| Signal | Fault | Detection | Mitigation |
|--------|-------|-----------|------------|
| Heartbeat out | GPIO driver failure (stuck) | Watchdog timeout | Safe state transition |
| Heartbeat in | Wire disconnection | No edges, timeout | Safe state transition |
| E-Stop out | GPIO driver failure (stuck high) | Cannot enter safe state | **SPOF - Accepted for demo** |
| E-Stop in | Wire disconnection | Pull-up → HIGH = safe | Fail-safe by design |
| Ultrasonic ECHO | 5V damage to GPIO | Voltage divider required | Hardware protection |
| Motor control | GPIO stuck | Motor runaway possible | E-Stop provides mitigation |

## GPIO Testing Procedure

### Continuity Test
1. Power off both Pis
2. Use multimeter to verify:
   - Pi5 GPIO 17 connected to Pi400 heartbeat input
   - Pi400 emergency stop output connected to Pi5 GPIO 27
   - Common ground between Pi5 Pin 6 and Pi400 GND

### Voltage Test
1. Power on both Pis
2. Measure voltage on heartbeat GPIO (Pi5 GPIO 17):
   - Should toggle between 0V and 3.3V at 10 Hz after ROS2 startup
3. Measure voltage on emergency stop GPIO (Pi400 output):
   - Should be 0V (LOW) initially (safe state asserted)
   - Should go to 3.3V (HIGH) after supervisor releases

### Functional Test
1. Run `gpio readall` on Pi5 (requires WiringPi or similar tool)
2. Verify GPIO 17 is configured as OUTPUT
3. Verify GPIO 27 is configured as INPUT with PULL-UP
4. Run health_node, observe GPIO 17 toggling with oscilloscope or logic analyzer
5. Manually assert emergency stop (set Pi400 GPIO LOW), verify GPIO 27 reads LOW on Pi5

## GPIO Code Snippets

### Linux (Pi5) - Heartbeat Generation
```cpp
// Using libgpiod (recommended)
#include <gpiod.h>

struct gpiod_chip *chip;
struct gpiod_line *heartbeat_line;

chip = gpiod_chip_open_by_name("gpiochip0");
heartbeat_line = gpiod_chip_get_line(chip, 17);
gpiod_line_request_output(heartbeat_line, "heartbeat", 0);

// Toggle at 10 Hz
while (true) {
    gpiod_line_set_value(heartbeat_line, 1);
    sleep_ms(50);
    gpiod_line_set_value(heartbeat_line, 0);
    sleep_ms(50);
}
```

### Linux (Pi5) - Emergency Stop Read
```cpp
// Using libgpiod
struct gpiod_line *estop_line;

estop_line = gpiod_chip_get_line(chip, 27);
gpiod_line_request_input(estop_line, "estop_in");

// Poll at 100 Hz
while (true) {
    int estop_state = gpiod_line_get_value(estop_line);
    if (estop_state == 0) {
        // Emergency stop asserted
        disable_motors();
    }
    sleep_ms(10);
}
```

### QNX (Pi400) - Heartbeat Monitor
```c
// Using QNX GPIO API (pseudocode, actual API depends on BSP)
#include <hw/gpio.h>

int gpio_fd;
uint32_t heartbeat_gpio = GPIO_TBD;

gpio_fd = open("/dev/gpio", O_RDWR);
gpio_set_direction(gpio_fd, heartbeat_gpio, GPIO_INPUT);

uint64_t last_edge_time = get_monotonic_time_ms();
while (true) {
    int state = gpio_read(gpio_fd, heartbeat_gpio);
    // Detect edges, update last_edge_time

    uint64_t now = get_monotonic_time_ms();
    if ((now - last_edge_time) > 500) {
        // Watchdog timeout
        trigger_safe_state();
    }
    delay_ms(1); // 1 kHz polling
}
```

## References

- Raspberry Pi GPIO Documentation: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html
- libgpiod User Guide: https://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.git/about/
- WiringPi (deprecated but useful reference): http://wiringpi.com/pins/
- BCM2835 GPIO Datasheet: https://datasheets.raspberrypi.com/bcm2835/bcm2835-peripherals.pdf
