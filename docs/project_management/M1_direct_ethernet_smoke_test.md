# M1.0b – Direct Ethernet Software Smoke Test

> **Scope notice**: This smoke test verifies basic UDP communication only. It is not a watchdog
> implementation and does not make runtime safety decisions. It is part of the M1.0b sub-step
> to confirm that the application layer can exchange messages over the dedicated Pi5 ↔ Pi400
> direct Ethernet link established in M1.0.

---

## Purpose

Confirm that a simple UDP message exchange works end-to-end over the dedicated direct Ethernet
link between Raspberry Pi 5 and Raspberry Pi 400. This validates the software communication
path before any protocol (heartbeat, watchdog) is implemented.

---

## Scope

| In scope | Out of scope |
|---|---|
| UDP socket bind and send on the direct Ethernet IPs | Heartbeat protocol |
| Message delivery and reception confirmation | Watchdog logic |
| Sequence counter increment (basic integrity check) | Runtime safety decisions |
| Logging of received messages with timestamp and sender IP | ISO 26262 compliance |
| | QNX supervisor functionality |

This is an educational demonstrator. No certification claims are made.

---

## Network Setup

| Parameter | Value |
|---|---|
| Link type | Dedicated direct Ethernet cable (Pi 5 ↔ Pi 400) |
| Pi 5 direct Ethernet IP | 192.168.50.10/24 |
| Pi 400 direct Ethernet IP | 192.168.50.20/24 |
| UDP port | 5005 |
| Development / SSH access | Separate LAN (192.168.0.x) — independent of this link |

---

## Preconditions

- [ ] M1.0 Platform Access Baseline is complete (bidirectional ping verified).
- [ ] Pi 5 IP 192.168.50.10 is configured and reachable from Pi 400.
- [ ] Pi 400 IP 192.168.50.20 is configured and reachable from Pi 5.
- [ ] Python 3 is installed on both boards.
- [ ] Repository is cloned on both Pi 5 (`pi5_linux/scripts/udp_sender.py`) and Pi 400
  (`pi400_supervisor/scripts/udp_receiver.py`), **or** the scripts are transferred manually.
- [ ] UDP port 5005 is not blocked by any firewall rule on Pi 400.

---

## Test Procedure

### Step 1 – Verify ping (both directions)

On Pi 5:
```bash
ping -c 4 192.168.50.20
```

On Pi 400:
```bash
ping -c 4 192.168.50.10
```

Expected: 4/4 packets received, 0% packet loss.

### Step 2 – Start UDP receiver on Pi 400

SSH into Pi 400, then:
```bash
python3 pi400_supervisor/scripts/udp_receiver.py
```

Expected startup output:
```
[udp_receiver] M1.0b smoke test — UDP receiver started
[udp_receiver] Listening on 192.168.50.20:5005
[udp_receiver] Press Ctrl+C to stop
```

### Step 3 – Start UDP sender on Pi 5

SSH into Pi 5 (separate terminal), then:
```bash
python3 pi5_linux/scripts/udp_sender.py
```

Expected startup output:
```
[udp_sender] M1.0b smoke test — UDP sender started
[udp_sender] Target: 192.168.50.20:5005
[udp_sender] Interval: 1.0s  |  Press Ctrl+C to stop
```

### Step 4 – Observe reception on Pi 400

Watch the Pi 400 terminal. Each second a line similar to this should appear:
```
[2026-05-06T14:23:01.042] from 192.168.50.10:XXXXX | seq=0 ts=2026-05-06T14:23:01.041+00:00 src=pi5-main type=COMM_SMOKE_TEST
[2026-05-06T14:23:02.043] from 192.168.50.10:XXXXX | seq=1 ts=2026-05-06T14:23:02.042+00:00 src=pi5-main type=COMM_SMOKE_TEST
...
```

Verify: sequence numbers increment by 1 each line, no gaps.

### Step 5 – Stop both scripts

Press Ctrl+C on each terminal. Both scripts should print a clean stop message.

---

## Expected Result

| Check | Expected |
|---|---|
| Pi 5 → Pi 400 ping | 0% packet loss |
| Pi 400 → Pi 5 ping | 0% packet loss |
| Receiver starts without error | Yes |
| Sender starts without error | Yes |
| Messages appear on Pi 400 with correct sender IP | Yes |
| Sequence numbers increment monotonically | Yes |
| Both scripts stop cleanly on Ctrl+C | Yes |

---

## Evidence to Collect

- Ping output from Pi 5 and Pi 400 (copy/paste into engineering logbook).
- First 5 lines of receiver output on Pi 400 (copy/paste into engineering logbook).
- First 5 lines of sender output on Pi 5 (copy/paste into engineering logbook).
- Note any packet loss or error messages.

---

## Limitations and Explicit Non-Claims

- This smoke test verifies basic UDP communication only. It is **not** a watchdog implementation
  and does **not** make runtime safety decisions.
- UDP is connectionless and unreliable by design. Packet loss in this test indicates a link
  or configuration problem, not a safety event.
- The sequence counter confirms delivery order but is not a safety-grade integrity check.
- This demonstrator is **not** ISO 26262 certified and **not** ASIL-B compliant. All
  ASIL-B-inspired language refers to architectural patterns only.
- QNX supervisor functionality is planned/optional and is **not** exercised by this smoke test.

---

## Files

| File | Role |
|---|---|
| `pi5_linux/scripts/udp_sender.py` | Run on Pi 5 — sends UDP messages |
| `pi400_supervisor/scripts/udp_receiver.py` | Run on Pi 400 — receives and prints messages |
| `engineering_logbook/2026-05-06.md` | Evidence record |
