#!/usr/bin/env python3
# Health node — Pi5 Linux domain, M5.
# Responsibilities:
#   1. UDP Q&A watchdog client: receives seed from Pi400, computes
#      response = seed XOR 0xA5A5A5A5, sends back within 50–100ms window.
#      Transport: UDP port 9001, dedicated Ethernet 192.168.50.x (DD-002 Option B).
#   2. Publishes /watchdog_failure_counter (std_msgs/Int32) — read by decision_node.
#   3. Green LED (GPIO 17): ON except in SAFE_STATE.
#   4. Yellow LED (GPIO 27): ON in DEGRADED state.
#   5. Publishes /system_health (diagnostic_msgs/DiagnosticArray) at 1 Hz.
#
# Educational demonstrator — not ISO 26262 certified.

import json
import socket
import threading
import time

import lgpio
import rclpy
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from std_msgs.msg import String, Int32

# ── Constants ─────────────────────────────────────────────────────────────────
PI400_IP        = '192.168.50.20'
WDG_PORT        = 9001
RESP_MASK       = 0xA5A5A5A5
TARGET_SEND_MS  = 70.0   # aim for 70ms — middle of 50–100ms window


class _WatchdogUDPThread:
    """Background thread: receives Pi400 seeds, sends responses, receives status."""

    def __init__(self, pi400_ip: str, port: int):
        self._ip   = pi400_ip
        self._port = port
        self._lock = threading.Lock()

        self._failure_counter: int  = 0
        self._wdg_ok: bool          = False
        self._attempts: int         = 0
        self._responses_sent: int   = 0
        self._running: bool         = True

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(('0.0.0.0', port))
        self._sock.settimeout(0.15)   # 150ms receive timeout

        self._thread = threading.Thread(target=self._run, daemon=True, name='wdg_udp')
        self._thread.start()

    def _run(self) -> None:
        while self._running:
            try:
                data, _ = self._sock.recvfrom(256)
                msg = json.loads(data.decode())
                mtype = msg.get('type')

                if mtype == 'seed':
                    self._attempts += 1
                    recv_time = time.monotonic()
                    seed      = msg['seed']
                    response  = (seed ^ RESP_MASK) & 0xFFFFFFFF

                    # Wait until TARGET_SEND_MS after receiving seed
                    elapsed_ms = (time.monotonic() - recv_time) * 1000.0
                    remaining  = TARGET_SEND_MS - elapsed_ms
                    if remaining > 0:
                        time.sleep(remaining / 1000.0)

                    pkt = json.dumps({'type': 'response', 'seed': seed,
                                      'response': response}).encode()
                    self._sock.sendto(pkt, (self._ip, self._port))
                    self._responses_sent += 1

                elif mtype == 'status':
                    with self._lock:
                        self._failure_counter = msg.get('failure_counter', 0)
                        self._wdg_ok = (self._failure_counter == 0 and
                                        msg.get('released', False))

            except socket.timeout:
                pass
            except (json.JSONDecodeError, KeyError, OSError):
                pass

    @property
    def failure_counter(self) -> int:
        with self._lock:
            return self._failure_counter

    @property
    def ok(self) -> bool:
        with self._lock:
            return self._wdg_ok

    @property
    def attempts(self) -> int:
        return self._attempts

    @property
    def responses_sent(self) -> int:
        return self._responses_sent

    def stop(self) -> None:
        self._running = False
        try:
            self._sock.close()
        except OSError:
            pass


# ── ROS2 node ─────────────────────────────────────────────────────────────────

class HealthNode(Node):

    GPIO_CHIP       = 4   # Pi5 RP1 southbridge
    GPIO_GREEN_LED  = 17  # Pin 11
    GPIO_YELLOW_LED = 27  # Pin 13

    def __init__(self):
        super().__init__('health_node')

        # GPIO
        self._gpio = lgpio.gpiochip_open(self.GPIO_CHIP)
        lgpio.gpio_claim_output(self._gpio, self.GPIO_GREEN_LED,  1)
        lgpio.gpio_claim_output(self._gpio, self.GPIO_YELLOW_LED, 0)
        self.get_logger().info('Green LED ON (GPIO 17), Yellow LED OFF (GPIO 27)')

        # UDP watchdog client
        self._wdg = _WatchdogUDPThread(PI400_IP, WDG_PORT)
        self.get_logger().info(
            f'UDP Q&A watchdog client started — Pi400 {PI400_IP}:{WDG_PORT}')

        self._system_state: str = 'INIT'

        # Publishers
        self._health_pub   = self.create_publisher(DiagnosticArray, '/system_health', 5)
        self._wdg_ctr_pub  = self.create_publisher(Int32, '/watchdog_failure_counter', 5)

        # Timers
        self.create_timer(1.0,   self._publish_health)
        self.create_timer(0.1,   self._publish_wdg_counter)  # 10 Hz

        # Subscriptions
        self.create_subscription(String, '/system_state', self._on_system_state, 5)

        self.get_logger().info(
            'health_node M5 started — UDP Q&A watchdog, target 70ms window')

    # ── LED control ───────────────────────────────────────────────────────────

    def _on_system_state(self, msg: String) -> None:
        self._system_state = msg.data
        green  = (msg.data != 'SAFE_STATE')
        yellow = (msg.data == 'DEGRADED')
        lgpio.gpio_write(self._gpio, self.GPIO_GREEN_LED,  1 if green  else 0)
        lgpio.gpio_write(self._gpio, self.GPIO_YELLOW_LED, 1 if yellow else 0)

    # ── Publishers ────────────────────────────────────────────────────────────

    def _publish_wdg_counter(self) -> None:
        msg = Int32()
        msg.data = self._wdg.failure_counter
        self._wdg_ctr_pub.publish(msg)

    def _publish_health(self) -> None:
        msg = DiagnosticArray()
        msg.header.stamp = self.get_clock().now().to_msg()

        s = DiagnosticStatus()
        s.name        = 'health_node/watchdog'
        s.hardware_id = 'pi5'
        s.level   = DiagnosticStatus.OK if self._wdg.ok else DiagnosticStatus.WARN
        s.message = ('watchdog OK' if self._wdg.ok
                     else f'watchdog WARN — failure_counter={self._wdg.failure_counter}')
        s.values = [
            KeyValue(key='transport',        value='UDP'),
            KeyValue(key='pi400_ip',         value=PI400_IP),
            KeyValue(key='wdg_ok',           value=str(self._wdg.ok)),
            KeyValue(key='failure_counter',  value=str(self._wdg.failure_counter)),
            KeyValue(key='seeds_received',   value=str(self._wdg.attempts)),
            KeyValue(key='responses_sent',   value=str(self._wdg.responses_sent)),
        ]
        msg.status.append(s)
        self._health_pub.publish(msg)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def destroy_node(self) -> None:
        self._wdg.stop()
        lgpio.gpio_write(self._gpio, self.GPIO_GREEN_LED,  0)
        lgpio.gpio_write(self._gpio, self.GPIO_YELLOW_LED, 0)
        lgpio.gpio_free(self._gpio, self.GPIO_GREEN_LED)
        lgpio.gpio_free(self._gpio, self.GPIO_YELLOW_LED)
        lgpio.gpiochip_close(self._gpio)
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
