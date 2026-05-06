# M1 Hardware Bring-up Test Plan

**Project**: Safety-Supervised Edge AI Demo on Raspberry Pi with QNX/Linux Concepts
**Milestone**: M1 – Platform Access and Hardware Bring-up
**Status**: M1.0 complete — M1.1 not started
**Scope**: Manual bring-up tests only. No ROS2, no automated test framework.

---

## Structure

| Sub-milestone | Scope |
|---|---|
| M1.0 | Platform Access Baseline — host PC connectivity, OS documentation, direct Ethernet, repo sync |
| M1.1 | Pi 5 Hardware Component Bring-up — camera, LEDs, buzzer, ultrasonic sensor |

---

## M1.0 – Platform Access Baseline

### TC-M10-001: Host PC to Pi 5 SSH Connectivity

| Field | Value |
|---|---|
| **Test ID** | TC-M10-001 |
| **Objective** | Confirm the host PC can reach Pi 5 via SSH |
| **Preconditions** | Pi 5 is powered on, connected to home LAN or Wi-Fi, SSH enabled |
| **Procedure** | From host PC: `ssh <user>@<pi5-ip>` |
| **Expected Result** | Shell prompt on Pi 5 without errors |
| **Evidence** | Terminal screenshot or log entry with hostname output |
| **Pass/Fail** | |

---

### TC-M10-002: Host PC to Pi 400 SSH Connectivity

| Field | Value |
|---|---|
| **Test ID** | TC-M10-002 |
| **Objective** | Confirm the host PC can reach Pi 400 via SSH |
| **Preconditions** | Pi 400 is powered on, connected to home LAN or Wi-Fi, OS installed, SSH enabled |
| **Procedure** | From host PC: `ssh <user>@<pi400-ip>` |
| **Expected Result** | Shell prompt on Pi 400 without errors |
| **Evidence** | Terminal screenshot or log entry; if no OS installed, document status explicitly |
| **Pass/Fail** | |
| **Notes** | N/A if Pi 400 OS is not yet installed; document this in logbook |

---

### TC-M10-003: Pi 5 OS Version Capture

| Field | Value |
|---|---|
| **Test ID** | TC-M10-003 |
| **Objective** | Document the Pi 5 operating system version |
| **Preconditions** | SSH access to Pi 5 confirmed (TC-M10-001 passed) |
| **Procedure** | On Pi 5: `cat /etc/os-release && uname -r && hostname` |
| **Expected Result** | Output shows Ubuntu 22.04 LTS (or Raspberry Pi OS 64-bit), kernel version, and hostname |
| **Evidence** | Command output pasted into logbook |
| **Pass/Fail** | |

---

### TC-M10-004: Pi 400 OS Status Capture

| Field | Value |
|---|---|
| **Test ID** | TC-M10-004 |
| **Objective** | Document the Pi 400 OS (QNX or Linux fallback) |
| **Preconditions** | Pi 400 is accessible (TC-M10-002) or status is known |
| **Procedure** | On Pi 400 (Linux): `cat /etc/os-release && uname -r` — On Pi 400 (QNX): `uname -a` |
| **Expected Result** | OS name, version, and kernel version captured |
| **Evidence** | Command output pasted into logbook; QNX or Linux fallback decision explicitly noted |
| **Pass/Fail** | |
| **Notes** | QNX supervisor is planned and optional. Linux fallback is acceptable and must be documented honestly. |

---

### TC-M10-005: Direct Ethernet Static IP Configuration

| Field | Value |
|---|---|
| **Test ID** | TC-M10-005 |
| **Objective** | Assign static IPs on the direct Pi 5 ↔ Pi 400 Ethernet link |
| **Preconditions** | Ethernet cable connected between Pi 5 and Pi 400; SSH access to both boards |
| **Procedure** | On Pi 5: configure 192.168.50.10/24 on the Ethernet interface. On Pi 400: configure 192.168.50.20/24. Verify with `ip addr show` on each board. |
| **Expected Result** | Pi 5 shows 192.168.50.10/24; Pi 400 shows 192.168.50.20/24 on the direct Ethernet interface |
| **Evidence** | `ip addr show` output from both boards, pasted into logbook |
| **Pass/Fail** | |
| **Notes** | Actual interface name may differ from eth0. Confirm with `ip link show` before configuring. |

---

### TC-M10-006: Pi 5 to Pi 400 Ping

| Field | Value |
|---|---|
| **Test ID** | TC-M10-006 |
| **Objective** | Verify Pi 5 can reach Pi 400 over the direct Ethernet link |
| **Preconditions** | TC-M10-005 passed; both IPs configured |
| **Procedure** | On Pi 5: `ping -c 4 192.168.50.20` |
| **Expected Result** | 4 packets transmitted, 4 received, 0% packet loss |
| **Evidence** | Ping output pasted into logbook |
| **Pass/Fail** | |

---

### TC-M10-007: Pi 400 to Pi 5 Ping

| Field | Value |
|---|---|
| **Test ID** | TC-M10-007 |
| **Objective** | Verify Pi 400 can reach Pi 5 over the direct Ethernet link |
| **Preconditions** | TC-M10-005 passed; both IPs configured |
| **Procedure** | On Pi 400: `ping -c 4 192.168.50.10` |
| **Expected Result** | 4 packets transmitted, 4 received, 0% packet loss |
| **Evidence** | Ping output pasted into logbook |
| **Pass/Fail** | |

---

### TC-M10-008: Repository Clone/Sync to Pi 5

| Field | Value |
|---|---|
| **Test ID** | TC-M10-008 |
| **Objective** | Verify the project repository is available on Pi 5 |
| **Preconditions** | Pi 5 has internet access; git installed |
| **Procedure** | On Pi 5: `git clone https://github.com/tipou82/safety-supervised-edge-ai-demo.git` then `git log --oneline -5` |
| **Expected Result** | Repository cloned successfully; recent commits visible |
| **Evidence** | `git log` output pasted into logbook |
| **Pass/Fail** | |

---

### TC-M10-009: VS Code Remote SSH to Pi 5

| Field | Value |
|---|---|
| **Test ID** | TC-M10-009 |
| **Objective** | Confirm VS Code Remote SSH development workflow is functional |
| **Preconditions** | VS Code with Remote — SSH extension installed on host PC; TC-M10-001 passed |
| **Procedure** | On host PC: open VS Code → F1 → `Remote-SSH: Connect to Host` → enter `<user>@<pi5-ip>` → open repository folder |
| **Expected Result** | VS Code connects to Pi 5 and the repository folder is browsable |
| **Evidence** | Note VS Code version, Remote SSH extension version, and connection outcome in logbook |
| **Pass/Fail** | |

---

## M1.1 – Pi 5 Hardware Component Bring-up

### TC-M11-001: Camera Detection

| Field | Value |
|---|---|
| **Test ID** | TC-M11-001 |
| **Objective** | Confirm the Raspberry Pi Camera Module 3 is detected by Pi 5 |
| **Preconditions** | Camera module connected via CSI ribbon cable; Pi 5 booted |
| **Procedure** | On Pi 5: `rpicam-hello --list-cameras` (or `libcamera-hello --list-cameras` on older OS) |
| **Expected Result** | Camera module listed without errors |
| **Evidence** | Command output pasted into logbook |
| **Pass/Fail** | |

---

### TC-M11-002: Camera Preview or Still Capture

| Field | Value |
|---|---|
| **Test ID** | TC-M11-002 |
| **Objective** | Confirm the camera can capture a usable image |
| **Preconditions** | TC-M11-001 passed |
| **Procedure** | On Pi 5: `rpicam-still -o test_capture.jpg` (or equivalent) |
| **Expected Result** | Image file created without errors; file size > 0 bytes |
| **Evidence** | `ls -lh test_capture.jpg` output; optionally transfer image to host PC for visual check |
| **Pass/Fail** | |

---

### TC-M11-003: Green LED GPIO Toggle

| Field | Value |
|---|---|
| **Test ID** | TC-M11-003 |
| **Objective** | Confirm the green LED responds to GPIO control |
| **Preconditions** | Green LED wired to correct GPIO pin per `hardware/gpio_mapping.md`; Pi 5 booted |
| **Procedure** | Toggle the GPIO pin high and low using `gpiod` or Python RPi.GPIO. Observe LED state. |
| **Expected Result** | LED turns on when GPIO is high; turns off when GPIO is low |
| **Evidence** | Visual observation noted in logbook; wiring photo if available |
| **Pass/Fail** | |

---

### TC-M11-004: Yellow LED GPIO Toggle

| Field | Value |
|---|---|
| **Test ID** | TC-M11-004 |
| **Objective** | Confirm the yellow LED responds to GPIO control |
| **Preconditions** | Yellow LED wired to correct GPIO pin per `hardware/gpio_mapping.md`; Pi 5 booted |
| **Procedure** | Toggle the GPIO pin high and low. Observe LED state. |
| **Expected Result** | LED turns on when GPIO is high; turns off when GPIO is low |
| **Evidence** | Visual observation noted in logbook |
| **Pass/Fail** | |

---

### TC-M11-005: Red LED GPIO Toggle

| Field | Value |
|---|---|
| **Test ID** | TC-M11-005 |
| **Objective** | Confirm the red LED responds to GPIO control |
| **Preconditions** | Red LED wired to correct GPIO pin per `hardware/gpio_mapping.md`; Pi 5 booted |
| **Procedure** | Toggle the GPIO pin high and low. Observe LED state. |
| **Expected Result** | LED turns on when GPIO is high; turns off when GPIO is low |
| **Evidence** | Visual observation noted in logbook |
| **Pass/Fail** | |

---

### TC-M11-006: Buzzer GPIO Toggle

| Field | Value |
|---|---|
| **Test ID** | TC-M11-006 |
| **Objective** | Confirm the active 3.3 V buzzer responds to GPIO control |
| **Preconditions** | Buzzer wired to correct GPIO pin; Pi 5 booted |
| **Procedure** | Assert GPIO pin high for ~1 second, then low. Listen for buzzer tone. |
| **Expected Result** | Buzzer produces audible tone when GPIO is high; silent when low |
| **Evidence** | Audible observation noted in logbook; wiring photo if available |
| **Pass/Fail** | |

---

### TC-M11-007: Ultrasonic Distance Reading

| Field | Value |
|---|---|
| **Test ID** | TC-M11-007 |
| **Objective** | Confirm the Grove Ultrasonic Ranger provides plausible distance readings |
| **Preconditions** | Ultrasonic sensor wired per `hardware/gpio_mapping.md`; Pi 5 booted |
| **Procedure** | Run a minimal Python script to trigger the sensor and read distance. Place an object at a known distance (e.g., 20 cm, 50 cm). Record readings. |
| **Expected Result** | Readings within ±10% of the known distance; readings stable over 5 samples |
| **Evidence** | Sample readings (at least 3 distances) pasted into logbook |
| **Pass/Fail** | |
| **Notes** | Expected range: 2–400 cm. Check voltage on ECHO line is ≤ 3.3 V before connecting to GPIO. |

---

### TC-M11-008: Wiring Deviation Review

| Field | Value |
|---|---|
| **Test ID** | TC-M11-008 |
| **Objective** | Confirm actual wiring matches `hardware/gpio_mapping.md` and `hardware/wiring.md`, or document deviations |
| **Preconditions** | All hardware components connected |
| **Procedure** | Visually inspect all connections against documented pin assignments. Note any deviations. |
| **Expected Result** | All connections match documentation, or deviations are documented and wiring.md is updated |
| **Evidence** | Wiring review checklist completed in logbook; `hardware/wiring.md` updated if needed |
| **Pass/Fail** | |

---

## Summary Table

| Test ID | Sub-milestone | Description | Pass/Fail | Date |
|---|---|---|---|---|
| TC-M10-001 | M1.0 | Host PC → Pi 5 SSH | Pass | 2026-05-05 |
| TC-M10-002 | M1.0 | Host PC → Pi 400 SSH | Pass | 2026-05-05 |
| TC-M10-003 | M1.0 | Pi 5 OS version capture | Pass | 2026-05-05 |
| TC-M10-004 | M1.0 | Pi 400 OS status capture | Pass (Linux fallback) | 2026-05-05 |
| TC-M10-005 | M1.0 | Direct Ethernet static IP configuration | Pass | 2026-05-05 |
| TC-M10-006 | M1.0 | Pi 5 → Pi 400 ping | Pass | 2026-05-05 |
| TC-M10-007 | M1.0 | Pi 400 → Pi 5 ping | Pass | 2026-05-05 |
| TC-M10-008 | M1.0 | Repository clone/sync to Pi 5 | Pass | 2026-05-05 |
| TC-M10-009 | M1.0 | VS Code Remote SSH to Pi 5 | Pass | 2026-05-05 |
| TC-M11-001 | M1.1 | Camera detection | Pass | 2026-05-07 |
| TC-M11-002 | M1.1 | Camera preview or still capture | Pass | 2026-05-07 |
| TC-M11-003 | M1.1 | Green LED GPIO toggle | Pass | 2026-05-07 |
| TC-M11-004 | M1.1 | Yellow LED GPIO toggle | Pass | 2026-05-07 |
| TC-M11-005 | M1.1 | Red LED GPIO toggle | Pass | 2026-05-07 |
| TC-M11-006 | M1.1 | Buzzer GPIO toggle | Pass | 2026-05-07 |
| TC-M11-007 | M1.1 | Ultrasonic distance reading | Pass | 2026-05-07 |
| TC-M11-008 | M1.1 | Wiring deviation review | Pass | 2026-05-07 |

---

## Out of Scope

The following are explicitly not part of M1:

- ROS2 workspace setup or any ROS2 node
- Object detection or AI model inference
- QNX-specific supervisor implementation
- Ethernet heartbeat or watchdog protocol implementation
- Raspberry Pi 400 supervisor logic
- Fault injection campaign
- Motor driver bring-up (deferred to M2)
