#!/usr/bin/env python3
# Health node — Pi5 Linux domain.
# Responsibilities:
#   1. I2C Q&A watchdog client: reads seed from Pi400 (0x40 reg 0x00),
#      computes response = seed XOR 0xA5A5A5A5, writes to reg 0x01.
#      Target send: ~70 ms after last attempt (valid window: 50–100 ms).
#   2. Green LED (GPIO 17): ON while node is running in NORMAL state.
#   3. Publishes /system_health (diagnostic_msgs/DiagnosticArray) at 1 Hz.
#
# Pi400 I2C slave (address 0x40) is not yet implemented — watchdog transactions
# will fail gracefully with a DEBUG log. Full watchdog validation active from M5.
#
# Educational demonstrator — not ISO 26262 certified.

import time

import lgpio
import rclpy
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from std_msgs.msg import String

try:
    import smbus2
    _SMBUS2_OK = True
except ImportError:
    _SMBUS2_OK = False


class HealthNode(Node):

    GPIO_CHIP      = 4          # Pi5 RP1 southbridge
    GPIO_GREEN_LED = 17         # Pin 11 — NORMAL state indicator
    I2C_BUS        = 1          # /dev/i2c-1 (GPIO 2 SDA, GPIO 3 SCL)
    I2C_ADDR       = 0x40       # Pi400 Q&A watchdog slave
    REG_SEED       = 0x00
    REG_RESPONSE   = 0x01
    RESP_MASK      = 0xA5A5A5A5
    WINDOW_OPEN_MS = 50.0       # response must not arrive before this
    TARGET_SEND_MS = 70.0       # aim to send at ~70 ms

    def __init__(self):
        super().__init__('health_node')

        # GPIO — green LED ON immediately
        self._gpio = lgpio.gpiochip_open(self.GPIO_CHIP)
        lgpio.gpio_claim_output(self._gpio, self.GPIO_GREEN_LED, 1)
        self.get_logger().info('Green LED ON (GPIO 17, Pin 11)')

        # I2C
        self._i2c = None
        if not _SMBUS2_OK:
            self.get_logger().warn(
                'smbus2 not installed — watchdog inactive. '
                'Fix: sudo apt install python3-smbus2')
        else:
            try:
                self._i2c = smbus2.SMBus(self.I2C_BUS)
                self.get_logger().info('I2C /dev/i2c-1 opened (GPIO 2/3)')
            except Exception as e:
                self.get_logger().warn(f'I2C open failed: {e} — watchdog inactive')

        self._last_send_ms: float = self._ms()
        self._wdg_ok: bool = False
        self._wdg_attempts: int = 0
        self._wdg_failures: int = 0
        self._system_state: str = 'INIT'

        # Watchdog timer: fires every TARGET_SEND_MS
        self.create_timer(self.TARGET_SEND_MS / 1000.0, self._wdg_tick)

        # Health publisher at 1 Hz
        self._health_pub = self.create_publisher(DiagnosticArray, '/system_health', 5)
        self.create_timer(1.0, self._publish_health)

        # Subscribe to system_state to control green LED
        self.create_subscription(String, '/system_state', self._on_system_state, 5)

        self.get_logger().info(
            'health_node started — I2C Q&A watchdog client, target 70 ms window')

    # ----------------------------------------------------------------

    def _ms(self) -> float:
        return time.monotonic() * 1000.0

    def _wdg_tick(self) -> None:
        if self._i2c is None:
            return

        elapsed = self._ms() - self._last_send_ms
        if elapsed < self.WINDOW_OPEN_MS:
            return  # closed window — too early

        self._wdg_attempts += 1
        try:
            raw = self._i2c.read_i2c_block_data(self.I2C_ADDR, self.REG_SEED, 4)
            seed = int.from_bytes(bytes(raw), byteorder='little')
            response = (seed ^ self.RESP_MASK) & 0xFFFFFFFF
            self._i2c.write_i2c_block_data(
                self.I2C_ADDR, self.REG_RESPONSE,
                list(response.to_bytes(4, byteorder='little')))
            self._wdg_ok = True
        except Exception as e:
            self._wdg_failures += 1
            self._wdg_ok = False
            self.get_logger().debug(
                f'WDG I2C failed ({self._wdg_failures}): {e}')

        self._last_send_ms = self._ms()  # reset on both success and failure

    def _on_system_state(self, msg: String) -> None:
        self._system_state = msg.data
        # Green LED: ON in NORMAL/WARNING/DEGRADED/INIT, OFF in SAFE_STATE
        led_on = (msg.data != 'SAFE_STATE')
        lgpio.gpio_write(self._gpio, self.GPIO_GREEN_LED, 1 if led_on else 0)

    def _publish_health(self) -> None:
        msg = DiagnosticArray()
        msg.header.stamp = self.get_clock().now().to_msg()

        s = DiagnosticStatus()
        s.name = 'health_node/watchdog'
        s.hardware_id = 'pi5'
        s.level = DiagnosticStatus.OK if self._wdg_ok else DiagnosticStatus.WARN
        s.message = ('watchdog OK' if self._wdg_ok
                     else 'watchdog inactive — Pi400 slave not yet running')
        s.values = [
            KeyValue(key='i2c_available', value=str(self._i2c is not None)),
            KeyValue(key='wdg_ok',        value=str(self._wdg_ok)),
            KeyValue(key='wdg_attempts',  value=str(self._wdg_attempts)),
            KeyValue(key='wdg_failures',  value=str(self._wdg_failures)),
        ]
        msg.status.append(s)
        self._health_pub.publish(msg)

    # ----------------------------------------------------------------

    def destroy_node(self) -> None:
        lgpio.gpio_write(self._gpio, self.GPIO_GREEN_LED, 0)
        lgpio.gpio_free(self._gpio, self.GPIO_GREEN_LED)
        lgpio.gpiochip_close(self._gpio)
        if self._i2c is not None:
            self._i2c.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HealthNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
