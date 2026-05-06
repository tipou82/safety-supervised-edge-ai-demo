#!/usr/bin/env python3
# M1.0b – Direct Ethernet communication smoke test only.
# This script verifies basic UDP connectivity between Pi5 and Pi400.
# It is NOT a watchdog, heartbeat, or safety mechanism.
# It makes no runtime safety decisions.

import socket
import datetime


BIND_IP = "192.168.50.20"
BIND_PORT = 5005


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((BIND_IP, BIND_PORT))

    print(f"[udp_receiver] M1.0b smoke test — UDP receiver started")
    print(f"[udp_receiver] Listening on {BIND_IP}:{BIND_PORT}")
    print(f"[udp_receiver] Press Ctrl+C to stop")
    print()

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            timestamp = datetime.datetime.now().isoformat(timespec="milliseconds")
            payload = data.decode("utf-8", errors="replace")
            print(f"[{timestamp}] from {addr[0]}:{addr[1]} | {payload}")
    except KeyboardInterrupt:
        print("\n[udp_receiver] Stopped by user.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
