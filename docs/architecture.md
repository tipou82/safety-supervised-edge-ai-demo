# System Architecture

> **Educational demonstrator — ASIL-B-inspired patterns only. Not ISO 26262 certified. Not production-ready.**

## Overview

This demonstrator implements a dual-processor architecture with FFI-inspired separation between the AI perception domain (Linux/ROS2) and the safety monitoring domain (Linux supervisor).

### System Power and Startup Concept

**Main Switch (shared power strip):**
Both Raspberry Pi boards are powered through the same power strip, controlled by the **Main Switch**.
When the Main Switch is ON, both Pi5 and Pi400 boot simultaneously. When OFF, both power down.

**Motor Switch (4×AA battery box):**
The DRV8833 motor driver is powered **separately** from a 4×AA battery box with its own
**Motor Switch**. The motor can only rotate if the Motor Switch is ON AND the software state
allows it. The Raspberry Pi supplies only 3.3 V logic signals to DRV8833 IN1/IN2 — never motor
supply voltage.

**Startup release criterion:**
The system enters NORMAL only after all of the following are satisfied:
1. Pi400 Q&A watchdog communication is healthy (failure_counter < 3).
2. All required ROS2 application nodes on Pi5 are alive.
3. Sensor validity checks pass (ultrasonic valid, camera optional/supplementary).

If startup criteria are not met, the system remains in SAFE_STATE. Manual `/reset` is required.

**Pi400 watchdog role:**
The Pi400 supervisor is external to the Pi5 application stack. It operates independently,
using only rule-based deterministic logic. AI perception outputs never reach the Pi400 supervisor.
On watchdog fault or startup failure, the Pi400 asserts GPIO 25 LOW (e-stop, active-low) and
illuminates the red LED via GPIO 22 — independently of Pi5 software.

## High-Level Architecture

```mermaid
graph TB
    subgraph Pi5["Raspberry Pi 5 - Linux/ROS2 Domain"]
        Camera[Camera AI Node<br/>YOLOv8/MobileNet]
        Ultra[Ultrasonic Node<br/>Grove Ultrasonic Ranger]
        Decision[Decision Node<br/>Path Planning]
        Actuator[Actuator Node<br/>Motor Control]
        Health[Health Monitor<br/>Aliveness Beacon]
    end

    subgraph Pi400["Raspberry Pi 400 - Linux Supervisor Domain"]
        WDG[Watchdog Server<br/>Deterministic Monitor]
        SafeCtrl[Safe State Controller<br/>Emergency Brake]
    end

    subgraph MainSwitch["Main Switch (shared power strip)"]
        PSU5["Pi5 USB-C PSU"]
        PSU400["Pi400 USB-C PSU"]
    end

    subgraph MotorDomain["Motor Domain (separate 4xAA supply)"]
        MotorSwitch["Motor Switch\n4xAA battery box"]
        DRV["DRV8833\nDual H-Bridge"]
        TT["AEDIKO TT Motor\n+ Wheel"]
    end

    subgraph External
        Env[Environment]
    end

    PSU5 --> Pi5
    PSU400 --> Pi400
    Env -->|Image| Camera
    Env -->|Distance| Ultra
    Camera -->|DetectionArray| Decision
    Ultra -->|ObstacleMsg| Decision
    Decision -->|velocity_scale / CmdVel| Actuator
    Actuator -->|GPIO12 IN1\nGPIO16 IN2\n3.3V logic only| DRV
    MotorSwitch -->|VCC motor supply| DRV
    DRV -->|OUT1/OUT2| TT

    Health -->|UDP Q&A Watchdog seed/response\n192.168.50.x| WDG
    Decision -->|State Info| WDG
    WDG -->|Monitor Status| SafeCtrl
    SafeCtrl -->|Emergency Stop GPIO 25\nactive-low| Actuator
    SafeCtrl -->|Red LED GPIO 22| RedLED[Red LED SAFE STATE]
    Health -->|Green LED GPIO 17| GreenLED[Green LED NORMAL]
    Decision -->|Yellow LED GPIO 27| YellowLED[Yellow LED WARNING/DEGRADED]

    style Pi5 fill:#e1f5e1
    style Pi400 fill:#ffe1e1
    style WDG fill:#ffcccc
    style SafeCtrl fill:#ffcccc
    style MotorDomain fill:#fff8e1
    style MainSwitch fill:#f3f3f3
```

## Component Descriptions

### Linux/ROS2 Domain (Raspberry Pi 5)

**Camera AI Node**
- Runs object detection inference (YOLOv8 or MobileNet)
- Publishes detection results on `/detections` topic
- NOT part of safety decision path (development domain)

**Ultrasonic Node**
- Reads Grove Ultrasonic Ranger via GPIO 23 (single-wire SIG protocol)
- Publishes obstacle distances on `/obstacles` topic
- Provides redundant perception for close-range obstacles (2–350 cm)

**Decision Node**
- Receives perception inputs from Camera AI and Ultrasonic nodes
- Performs path planning and generates velocity commands
- Publishes on `/cmd_vel` topic

**Actuator Node**
- Receives velocity commands (`velocity_scale`) from Decision Node
- Controls DRV8833 IN1/IN2 via GPIO 12 and GPIO 16 (3.3 V logic signals only — no motor supply on Pi GPIO)
- Enforces `velocity_scale = 0.0` (motor stop) in SAFE_STATE, INIT, and any unhandled state
- **Critical**: Accepts emergency stop from Pi400 supervisor (GPIO 25 active-low, polled at 100 Hz)
- Motor rotates only if: (a) system state is NORMAL or allowed WARNING/DEGRADED, AND (b) Motor Switch is ON

**Health Monitor**
- Manages UDP Q&A watchdog as client (dedicated Ethernet, port 9001)
- Reads seed from Pi400, computes response (`seed XOR 0xA5A5A5A5`), sends within valid window
- Drives Green/Yellow LED (GPIO 17/27) and buzzer (GPIO 18) based on system state
- Monitors ROS2 node liveness (flow check)

### Supervisor Domain (Raspberry Pi 400)

**Watchdog Server** (`pi400_supervisor/scripts/watchdog_server.py`)
- Acts as UDP server (port 9001, dedicated Ethernet 192.168.50.20)
- Issues seeds, validates Pi5 responses for timing (30ms window: 15ms closed + 15ms open) and correctness (CRC-16, sequence counter)
- Manages failure counter: +1 on bad/late/early response, −1 after 2 consecutive correct; ≥3 → SAFE_STATE
- Asserts GPIO 25 LOW (e-stop, active-low) at boot as fail-safe default
- Releases GPIO 25 HIGH only after first valid Q&A exchange
- Drives red LED (GPIO 22) independently of Pi5

## FFI-Inspired Measures

### Freedom from Interference (FFI-Inspired)

**Spatial Independence**
- Physically separate processors for perception and supervisor domains
- Linux supervisor process cannot be corrupted by Pi5 kernel panics or AI inference failures

**Temporal Independence**
- Deterministic watchdog timeout thresholds based on supervisor's local monotonic clock
- Safety decisions do not depend on AI inference timing

**Communication Independence**
- Watchdog uses UDP Q&A challenge/response over dedicated Ethernet (independent of ROS2/DDS)
- Emergency stop uses direct GPIO wire (GPIO 25 Pi400 → GPIO 25 Pi5) — no software stack on e-stop path

**Design Independence**
- Safety logic designed and reviewed separately from AI perception
- Different programming paradigms (C++20 ROS2 vs Python deterministic supervisor)

## Safety Architecture Patterns

> Safety mechanism implementation details (watchdog protocol, state machine rules,
> thresholds, FTTI) are in **`docs/safety_mechanisms.md`**.

Three core patterns:

1. **Independent Safety Monitor** — Pi400 supervisor makes decisions based solely on watchdog
   liveness. AI outputs never reach the supervisor.
2. **Deterministic Safe State** — Rule-based StateEvaluator (C++20), no probabilistic logic.
3. **Fail-Safe Default** — GPIO 25 asserted LOW at Pi400 boot; released only after valid Q&A.

## State Machine

```mermaid
stateDiagram-v2
    [*] --> INIT
    INIT --> NORMAL: Startup OK
    NORMAL --> WARNING: Sensor degraded
    NORMAL --> DEGRADED: AI node failed
    WARNING --> NORMAL: Fault cleared
    WARNING --> DEGRADED: Multiple faults
    DEGRADED --> SAFE_STATE: Critical fault
    NORMAL --> SAFE_STATE: Watchdog timeout
    WARNING --> SAFE_STATE: Watchdog timeout
    DEGRADED --> SAFE_STATE: Supervisor command
    SAFE_STATE --> INIT: Manual reset
```

## Interface Boundaries

### Pi5 → Pi400
- **UDP Q&A Watchdog** (Ethernet 192.168.50.x, port 9001): response to seed within 15–30 ms window

### Pi400 → Pi5
- **Emergency Stop GPIO 25** (active-low): Direct wire Pi400 GPIO 25 → Pi5 GPIO 25
- **UDP status packet**: `failure_counter`, `state`, `released`, `cycle` after each watchdog cycle

### Shared Visual Output
- **Red LED** (wired-OR): Pi5 GPIO 22 and Pi400 GPIO 22 both drive the red LED via 1N4148 diodes; either domain can independently assert SAFE STATE indication

See [interfaces.yaml](../requirements/interfaces.yaml) for detailed message specifications.

## Deployment Notes

### Development Setup
- Pi 5: Raspberry Pi OS Bookworm + ROS2 Humble (built from source)
- Pi 400: Raspberry Pi OS Bookworm, Python supervisor (`pi400_supervisor/systemd/`)

### Production Considerations
- ASIL-B qualification would require full process compliance, certified RTOS, WCET analysis — not demonstrated here
- The supervisor role (Pi400) could be replaced by a dedicated MCU (e.g., STM32, Infineon TC3xx) for sub-100 ms startup and deterministic scheduling

## References

- ISO 26262:2018 Part 6 (Software), Part 9 (ASIL-oriented, safety-oriented analyses)
- IEC 61508 Functional Safety Standard
- AUTOSAR Adaptive Platform specifications
