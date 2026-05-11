# System Architecture

> **Educational demonstrator — ASIL-B-inspired patterns only. Not ISO 26262 certified. Not production-ready.**

## Overview

This demonstrator implements a dual-processor architecture with FFI-inspired separation between the AI perception domain (Linux/ROS2) and the safety monitoring domain (QNX-inspired supervisor).

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

    subgraph Pi400["Raspberry Pi 400 - QNX-Inspired Domain"]
        WDG[Watchdog Server<br/>Deterministic Monitor]
        SafeCtrl[Safe State Controller<br/>Emergency Brake]
    end

    subgraph External
        Env[Environment]
        Motors[Motors/Actuators]
    end

    Env -->|Image| Camera
    Env -->|Distance| Ultra
    Camera -->|DetectionArray| Decision
    Ultra -->|ObstacleMsg| Decision
    Decision -->|CmdVel| Actuator
    Actuator -->|PWM| Motors

    Health -->|I2C Q&A Watchdog seed/response| WDG
    Decision -->|State Info| WDG
    WDG -->|Monitor Status| SafeCtrl
    SafeCtrl -->|Emergency Stop GPIO 25| Actuator
    SafeCtrl -->|Red LED GPIO 22| RedLED[Red LED SAFE STATE]
    Health -->|Green LED GPIO 17| GreenLED[Green LED NORMAL]
    Decision -->|Yellow LED GPIO 27| YellowLED[Yellow LED DEGRADED]

    style Pi5 fill:#e1f5e1
    style Pi400 fill:#ffe1e1
    style WDG fill:#ffcccc
    style SafeCtrl fill:#ffcccc
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
- Receives velocity commands from Decision Node
- Controls motor PWM signals
- **Critical**: Accepts emergency stop from QNX supervisor

**Health Monitor**
- Manages I2C Q&A watchdog as I2C master (GPIO 2/3)
- Reads seed from Pi400, computes response (`seed XOR 0xA5A5A5A5`), sends within valid window
- Drives Green LED (GPIO 17) to indicate NORMAL state
- Monitors ROS2 node liveness

### QNX-Inspired Domain (Raspberry Pi 400 or Linux Fallback)

**Watchdog Server**
- Operates as I2C slave (address `0x40`, GPIO 2/3) — Q&A watchdog monitor
- Issues seeds, validates Pi5 responses for timing (50–100 ms window) and correctness
- Manages failure counter: +1 on bad/late/early response, −1 after 2 consecutive correct
- Triggers SAFE_STATE when failure counter reaches 3

**Safe State Controller**
- Executes safe state (emergency brake, motor disable)
- Independent of AI inference results
- Deterministic, rule-based logic only

## FFI-Inspired Measures

### Freedom from Interference (FFI-Inspired)

**Spatial Independence**
- Physically separate processors for development and safety domains
- QNX supervisor cannot be corrupted by Linux kernel panics or AI inference failures

**Temporal Independence**
- Deterministic watchdog timeout thresholds (configurable, e.g., 500ms)
- Safety decisions do not depend on AI inference timing

**Communication Independence**
- Watchdog uses I2C Q&A challenge/response (not reliant on ROS2 or shared memory)
- Emergency stop uses direct GPIO (GPIO 25 Pi400 → GPIO 25 Pi5), independent of I2C
- Shared memory region with CRC checking for state reporting (secondary channel)

**Design Independence**
- Safety logic designed and reviewed separately from AI perception
- Different programming languages/frameworks acceptable (C++ ROS2 vs C QNX)

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

### Linux → QNX (Pi5 → Pi400)
- **I2C Q&A Watchdog** (GPIO 2/3, I2C master): Seed read + response write, 50–100 ms window
- **Shared State** (optional): System health enum + CRC via `/dev/shm/safety_state`

### QNX → Linux (Pi400 → Pi5)
- **Emergency Stop GPIO 25** (active-low): Direct wire Pi400 GPIO 25 → Pi5 GPIO 25

### Shared Visual Output
- **Red LED** (wired-OR): Pi5 GPIO 22 and Pi400 GPIO 22 both drive the red LED via 1N4148 diodes; either domain can independently assert SAFE STATE indication

See [interfaces.yaml](../requirements/interfaces.yaml) for detailed message specifications.

## Deployment Notes

### Development Setup
- Pi 5: Ubuntu 22.04 + ROS2 Humble
- Pi 400: Linux with QNX-inspired watchdog patterns (POSIX timers, deterministic scheduling)

### Future Production Considerations
- Pi 400 could run QNX RTOS with certified BSP
- ASIL-B qualification would require full process compliance (not demonstrated here)

## References

- ISO 26262:2018 Part 6 (Software), Part 9 (ASIL-oriented, safety-oriented analyses)
- IEC 61508 Functional Safety Standard
- AUTOSAR Adaptive Platform specifications
