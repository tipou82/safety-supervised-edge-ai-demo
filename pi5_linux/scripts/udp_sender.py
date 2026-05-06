#!/usr/bin/env python3
# M1.0b – Direct Ethernet communication smoke test only.
# This script verifies basic UDP connectivity between Pi5 and Pi400.
# It is NOT a watchdog, heartbeat, or safety mechanism.
# It makes no runtime safety decisions.

import socket
import time
import datetime


TARGET_IP = "192.168.50.20"
TARGET_PORT = 5005
SOURCE_LABEL = "pi5-main"
MESSAGE_TYPE = "COMM_SMOKE_TEST"
INTERVAL_S = 1.0


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"[udp_sender] M1.0b smoke test — UDP sender started")
    print(f"[udp_sender] Target: {TARGET_IP}:{TARGET_PORT}")
    print(f"[udp_sender] Interval: {INTERVAL_S}s  |  Press Ctrl+C to stop")
    print()

    seq = 0
    try:
        while True:
            ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")
            payload = f"seq={seq} ts={ts} src={SOURCE_LABEL} type={MESSAGE_TYPE}"
            sock.sendto(payload.encode("utf-8"), (TARGET_IP, TARGET_PORT))
            print(f"[udp_sender] sent | {payload}")
            seq += 1
            time.sleep(INTERVAL_S)
    except KeyboardInterrupt:
        print("\n[udp_sender] Stopped by user.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
