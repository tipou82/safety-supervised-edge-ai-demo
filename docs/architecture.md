# System Architecture

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

    Health -->|Heartbeat GPIO| WDG
    Decision -->|State Info| WDG
    WDG -->|Monitor Status| SafeCtrl
    SafeCtrl -->|Emergency Stop| Actuator

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
- Generates periodic heartbeat signal via GPIO
- Monitors ROS2 node liveness
- Reports system state to supervisor

### QNX-Inspired Domain (Raspberry Pi 400 or Linux Fallback)

**Watchdog Server**
- Monitors heartbeat signal from Linux domain
- Applies deterministic safety rules (timeout thresholds)
- Triggers safe state transition on failure detection

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
- Watchdog uses simple GPIO heartbeat (not complex IPC)
- Fallback: Shared memory region with CRC checking

**Design Independence**
- Safety logic designed and reviewed separately from AI perception
- Different programming languages/frameworks acceptable (C++ ROS2 vs C QNX)

## Safety Architecture Patterns

### 1. Independent Safety Monitor
The QNX supervisor does NOT process AI outputs. It only monitors:
- Aliveness (heartbeat presence)
- Timing (heartbeat period within bounds)
- State consistency (system health indicators)

### 2. Deterministic Safe State
When faults are detected, the supervisor transitions to a predefined safe state:
- **Immediate**: Motor disable via GPIO override
- **Deterministic**: No AI decision-making in safety path

### 3. Fail-Safe Design
System defaults to safe state (motors disabled) on:
- Watchdog timeout
- Health monitor failure
- Communication loss

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

### Linux → QNX
- **GPIO Heartbeat**: Periodic pulse (e.g., 10 Hz)
- **Shared State** (optional): System health enum + CRC

### QNX → Linux
- **Emergency Stop GPIO**: Active-low signal to actuator node

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
