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
import struct
import threading
import time

import lgpio
import rclpy
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from sensor_msgs.msg import Range
from std_msgs.msg import String, Int32

# ── Constants ─────────────────────────────────────────────────────────────────
PI400_IP        = '192.168.50.20'
WDG_PORT        = 9001
RESP_MASK       = 0xA5A5A5A5
WINDOW_OPEN_MS  = 15.0   # closed window end — must not respond before this
WINDOW_CLOSE_MS = 30.0   # window timeout — response must arrive before this
TARGET_SEND_MS  = 20.0   # aim for 20ms (health_node 20ms cycle)


class _WatchdogUDPThread:
    """Background thread: receives Pi400 seeds, sends responses, receives status."""

    def __init__(self, pi400_ip: str, port: int):
        self._ip   = pi400_ip
        self._port = port
        self._lock = threading.Lock()

        self._failure_counter: int  = 0
        self._wdg_ok: bool          = False
        self._flow_ok: bool         = False   # set by ROS2 node flow monitor
        self._attempts: int         = 0
        self._responses_sent: int   = 0
        self._running: bool         = True

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(('0.0.0.0', port))
        self._sock.settimeout(0.005)  # 5ms — must check pending seed within 15ms open window

        self._thread = threading.Thread(target=self._run, daemon=True, name='wdg_udp')
        self._thread.start()

    @staticmethod
    def _crc16(data: bytes) -> int:
        crc = 0xFFFF
        for b in data:
            crc ^= b << 8
            for _ in range(8):
                crc = ((crc << 1) ^ 0x1021) if (crc & 0x8000) else (crc << 1)
        return crc & 0xFFFF

    def _run(self) -> None:
        pending_seed = None
        pending_seq  = None
        seed_recv_t  = None

        while self._running:
            try:
                data, _ = self._sock.recvfrom(512)
                msg   = json.loads(data.decode())
                mtype = msg.get('type')

                if mtype == 'seed':
                    seed    = msg['seed']
                    seq     = msg.get('seq', 0)
                    rx_crc  = msg.get('crc', -1)

                    # Validate incoming seed CRC
                    payload = struct.pack('>IB', seed, seq & 0xFF)
                    if rx_crc != self._crc16(payload):
                        continue  # discard malformed seed

                    pending_seed = seed
                    pending_seq  = seq
                    seed_recv_t  = time.monotonic()
                    self._attempts += 1

                elif mtype == 'status':
                    with self._lock:
                        self._failure_counter = msg.get('failure_counter', 0)
                        self._wdg_ok = (self._failure_counter == 0 and
                                        msg.get('released', False))

            except socket.timeout:
                pass
            except (json.JSONDecodeError, KeyError, struct.error, OSError):
                pass

            # ── Send response if seed is pending and window is open ───────────
            if pending_seed is not None and seed_recv_t is not None:
                elapsed_ms = (time.monotonic() - seed_recv_t) * 1000.0

                if elapsed_ms >= WINDOW_OPEN_MS:
                    if elapsed_ms < WINDOW_CLOSE_MS:
                        # Flow check gate — only send if pipeline is healthy
                        if self._flow_ok:
                            response = (pending_seed ^ RESP_MASK) & 0xFFFFFFFF
                            resp_payload = struct.pack('>IBI',
                                pending_seed, pending_seq & 0xFF,
                                response & 0xFFFFFFFF)
                            crc = self._crc16(resp_payload)
                            pkt = json.dumps({
                                'type':     'response',
                                'seed':     pending_seed,
                                'response': response,
                                'seq':      pending_seq,
                                'crc':      crc,
                            }).encode()
                            self._sock.sendto(pkt, (self._ip, self._port))
                            self._responses_sent += 1
                        # Clear pending regardless (only one response per seed)
                        pending_seed = None
                        pending_seq  = None
                        seed_recv_t  = None
                    else:
                        # Window expired without sending — clear
                        pending_seed = None
                        pending_seq  = None
                        seed_recv_t  = None

    def set_flow_ok(self, ok: bool) -> None:
        with self._lock:
            self._flow_ok = ok

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

        self._system_state: str  = 'INIT'

        # Flow monitor state — tracks liveness of safety-critical nodes
        self._last_system_state_t: float = time.monotonic()   # decision_node
        self._last_obstacles_t: float    = time.monotonic()   # ultrasonic_node
        # Deadlines: 3× nominal period for tolerance
        self._SYSTEM_STATE_DEADLINE_S = 0.060   # decision_node 20ms × 3
        self._OBSTACLES_DEADLINE_S    = 0.150   # ultrasonic_node 50ms × 3

        # Publishers
        self._health_pub   = self.create_publisher(DiagnosticArray, '/system_health', 5)
        self._wdg_ctr_pub  = self.create_publisher(Int32, '/watchdog_failure_counter', 5)

        # Timers
        self.create_timer(1.0,   self._publish_health)
        self.create_timer(0.1,   self._publish_wdg_counter)   # 10 Hz
        self.create_timer(0.020, self._flow_check_tick)        # 20 Hz — WDG gate

        # Subscriptions
        self.create_subscription(String, '/system_state', self._on_system_state, 5)
        self.create_subscription(Range, '/obstacles', self._on_obstacles, 5)

        self.get_logger().info(
            'health_node M5 started — UDP Q&A watchdog, target 70ms window')

    # ── Flow monitor — WDG gate ───────────────────────────────────────────────

    def _on_obstacles(self, msg) -> None:
        self._last_obstacles_t = time.monotonic()

    def _flow_check_tick(self) -> None:
        """20 Hz — evaluate flow check and update WDG gate."""
        now = time.monotonic()
        decision_ok   = (now - self._last_system_state_t) < self._SYSTEM_STATE_DEADLINE_S
        ultrasonic_ok = (now - self._last_obstacles_t)    < self._OBSTACLES_DEADLINE_S
        flow_ok = decision_ok and ultrasonic_ok
        self._wdg.set_flow_ok(flow_ok)

        if not flow_ok:
            self.get_logger().warn(
                f'Flow check FAIL — decision={decision_ok} ultrasonic={ultrasonic_ok}'
                ' — WDG response withheld')

    # ── LED control ───────────────────────────────────────────────────────────

    def _on_system_state(self, msg: String) -> None:
        self._last_system_state_t = time.monotonic()
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
        now = time.monotonic()
        decision_ok   = (now - self._last_system_state_t) < self._SYSTEM_STATE_DEADLINE_S
        ultrasonic_ok = (now - self._last_obstacles_t)    < self._OBSTACLES_DEADLINE_S
        s.values = [
            KeyValue(key='transport',          value='UDP'),
            KeyValue(key='pi400_ip',           value=PI400_IP),
            KeyValue(key='wdg_ok',             value=str(self._wdg.ok)),
            KeyValue(key='failure_counter',    value=str(self._wdg.failure_counter)),
            KeyValue(key='seeds_received',     value=str(self._wdg.attempts)),
            KeyValue(key='responses_sent',     value=str(self._wdg.responses_sent)),
            KeyValue(key='flow_decision_ok',   value=str(decision_ok)),
            KeyValue(key='flow_ultrasonic_ok', value=str(ultrasonic_ok)),
            KeyValue(key='window_open_ms',     value=str(WINDOW_OPEN_MS)),
            KeyValue(key='window_close_ms',    value=str(WINDOW_CLOSE_MS)),
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
