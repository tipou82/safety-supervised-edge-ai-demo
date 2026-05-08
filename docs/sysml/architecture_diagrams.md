# Safety-Supervised Edge AI Demo — Architecture Diagrams

**Single source of truth for all architecture diagrams.**
Mermaid notation — renders in GitHub and VS Code Markdown Preview.

> Educational demonstrator — not ISO 26262 certified.
> ASIL-B-inspired patterns. FFI-inspired architectural measures. No LLM/cloud AI in runtime safety path.

---

## Static Diagrams

### 1. Block Definition Diagram (BDD) — Hardware Blocks

Maps SysML `part def` blocks and their attributes.
Shows system composition: `SafetySupervisedEdgeAIDemo` is composed of five hardware blocks.

```mermaid
classDiagram
    direction TB

    class SafetySupervisedEdgeAIDemo {
        <<system>>
    }

    class RaspberryPi5 {
        <<block>>
        +os : RPi OS Bookworm
        +ros : ROS2 Humble (from source)
        +ram_gb : 8
        +gpio_chip : gpiochip4 (RP1)
    }

    class RaspberryPi400 {
        <<block>>
        +os : Ubuntu 22.04
        +role : Safety supervisor (QNX-inspired)
        +gpio_chip : gpiochip0 (BCM2711)
    }

    class CameraModule3 {
        <<block>>
        +sensor : IMX708
        +resolution : 4608 × 2592
        +interface : CSI ribbon cable
        +max_fps : 120 at 1536x864
    }

    class UltrasonicSensor {
        <<block>>
        +model : Grove Ultrasonic Ranger
        +protocol : Single-wire SIG
        +range_min_m : 0.02
        +range_max_m : 3.50
        +gpio_sig : 23
    }

    class LedBuzzerOutput {
        <<block>>
        +green_gpio : 17  (NORMAL)
        +yellow_gpio : 27 (DEGRADED)
        +red_gpio : 22    (SAFE_STATE, diode-OR)
        +buzzer_gpio : 18
    }

    SafetySupervisedEdgeAIDemo *-- "1" RaspberryPi5       : pi5
    SafetySupervisedEdgeAIDemo *-- "1" RaspberryPi400     : pi400
    SafetySupervisedEdgeAIDemo *-- "1" CameraModule3      : camera
    SafetySupervisedEdgeAIDemo *-- "1" UltrasonicSensor   : ultrasonic
    SafetySupervisedEdgeAIDemo *-- "1" LedBuzzerOutput    : leds
```

---

### 2. Block Definition Diagram (BDD) — Software Nodes

Maps ROS2 nodes (Linux domain) and supervisor components (QNX domain).

```mermaid
classDiagram
    direction TB

    class LinuxROSDomain {
        <<domain>>
        +processor : Raspberry Pi 5
        +os : RPi OS Bookworm
        +middleware : ROS2 Humble
    }

    class QNXSupervisorDomain {
        <<domain>>
        +processor : Raspberry Pi 400
        +os : Ubuntu 22.04 (QNX-inspired)
    }

    class HealthMonitorNode {
        <<rclpy node>>
        +i2c_slave_addr : 0x40
        +response_mask : 0xA5A5A5A5
        +target_send_ms : 70
        +gpio_green : 17
    }

    class UltrasonicNode {
        <<rclpy node>>
        +publish_hz : 10
        +gpio_sig : 23
        +range_m : 0.02–3.50
    }

    class CameraAINode {
        <<rclpy node>>
        +inference_hz : 10
        +model : YOLOv8n
    }

    class DecisionNode {
        <<rclpy + C++20 node>>
        +eval_hz : 20
        +warn_distance_m : 0.50
        +safe_distance_m : 0.15
    }

    class ActuatorNode {
        <<rclpy node>>
        +estop_poll_hz : 100
        +gpio_estop : 25
        +gpio_red_led : 22
    }

    class StateEvaluator {
        <<C++20 pure class>>
        +warn_distance_m : 0.50
        +safe_distance_m : 0.15
        +watchdog_threshold : 3
        +evaluate(input) EvaluatorOutput
        +velocity_scale(state) double
    }

    class QAWatchdogServer {
        <<supervisor>>
        +i2c_addr : 0x40
        +window_open_ms : 50
        +window_close_ms : 100
        +failure_threshold : 3
        +priority : 250
    }

    class SafeStateController {
        <<supervisor>>
        +gpio_estop : 25
        +gpio_red_led : 22
        +priority : 255
    }

    LinuxROSDomain  *-- HealthMonitorNode
    LinuxROSDomain  *-- UltrasonicNode
    LinuxROSDomain  *-- CameraAINode
    LinuxROSDomain  *-- DecisionNode
    LinuxROSDomain  *-- ActuatorNode
    DecisionNode    *-- StateEvaluator : owns

    QNXSupervisorDomain *-- QAWatchdogServer
    QNXSupervisorDomain *-- SafeStateController

    QAWatchdogServer --> SafeStateController : fault_detected
```

---

### 3. Internal Block Diagram (IBD) — Inter-Processor Connections

Maps SysML `connect` statements and port flows between domains.

```mermaid
graph LR
    subgraph Pi5["Raspberry Pi 5 — Linux / ROS2 Domain"]
        HN["health_node\nI2C master GPIO 2/3"]
        UN["ultrasonic_node\nGPIO 23"]
        CA["camera_ai_node\nCSI"]
        DN["decision_node\nStateEvaluator C++20"]
        AN["actuator_node\nGPIO 25 poll 100Hz"]
        GREEN["Green LED\nGPIO 17"]
        YELLOW["Yellow LED\nGPIO 27"]
        RED_PI5["Red LED\nGPIO 22 via D1"]
    end

    subgraph Pi400["Raspberry Pi 400 — QNX-Inspired Supervisor"]
        WDG["Q&A Watchdog\nI2C slave 0x40"]
        SC["Safe State Ctrl\nGPIO 25 out"]
        RED_PI400["Red LED\nGPIO 22 via D2"]
    end

    subgraph Sensors
        CAM["Camera Module 3\nIMX708"]
        ULT["Grove Ultrasonic\nRanger"]
    end

    HN  -->|"I2C seed/response\nGPIO 2/3 — 50–100ms window"| WDG
    WDG -->|"fault_detected"| SC
    SC  -->|"E-Stop GPIO 25\nactive-low, default LOW"| AN

    RED_PI5   -->|"1N4148 diode D1"| REDLED(["Red LED\n(wired-OR)"])
    RED_PI400 -->|"1N4148 diode D2"| REDLED

    CAM -->|"CSI ribbon"| CA
    ULT -->|"SIG GPIO 23"| UN

    UN  -->|"/obstacles 10Hz"| DN
    CA  -->|"/detections 10Hz"| DN
    DN  -->|"/cmd_vel 20Hz"| AN
    HN  -->|"/system_health 1Hz"| DN
    DN  -->|"/system_state 20Hz"| HN
    DN  -->|"/system_state 20Hz"| AN

    AN  -->|"GPIO 17"| GREEN
    DN  -->|"GPIO 27"| YELLOW
    AN  -->|"GPIO 22"| RED_PI5
    SC  -->|"GPIO 22"| RED_PI400
```

---

### 4. Package Diagram

Shows domain separation — the key FFI-inspired architectural measure.

```mermaid
graph TB
    subgraph SYS["SafetySupervisedEdgeAIDemo"]
        subgraph LINUX["Linux / ROS2 Domain  (Pi5)"]
            subgraph PERCEPTION["Perception"]
                CAI["camera_ai_node"]
                USN["ultrasonic_node"]
            end
            subgraph CONTROL["Decision & Control"]
                DEC["decision_node\n+ StateEvaluator"]
                ACT["actuator_node"]
            end
            subgraph HEALTH["Health & Watchdog"]
                HLT["health_node\n(I2C master)"]
            end
        end

        subgraph QNX["QNX-Inspired Supervisor Domain  (Pi400)"]
            subgraph MONITOR["Safety Monitor"]
                WDG2["QAWatchdogServer\n(I2C slave 0x40)"]
            end
            subgraph SAFETY["Safe State Enforcement"]
                SSC["SafeStateController\n(GPIO 25 + GPIO 22)"]
            end
        end

        subgraph HW["Hardware Layer"]
            GPIO_I2C["I2C GPIO 2/3"]
            GPIO_ESTOP["E-Stop GPIO 25"]
            GPIO_LEDS["LEDs GPIO 17/27/22"]
            CSI_BUS["CSI camera bus"]
        end
    end

    HEALTH  -->|"I2C Q&A"| GPIO_I2C
    GPIO_I2C -->|"challenge/response"| MONITOR
    MONITOR --> SAFETY
    SAFETY  -->|"assert"| GPIO_ESTOP
    GPIO_ESTOP -->|"poll 100Hz"| ACT
    CONTROL -->|"drive"| GPIO_LEDS
    SAFETY  -->|"drive"| GPIO_LEDS
    PERCEPTION -->|"CSI"| CSI_BUS
```

---

### 5. Requirements Diagram

Maps key safety requirements to implementing components and verification methods.

```mermaid
requirementDiagram

    requirement SYS_SAFE_007 {
        id: SYS_SAFE_007
        text: State machine with 5 states INIT NORMAL WARNING DEGRADED SAFE_STATE
        risk: High
        verifymethod: Test
    }

    requirement SYS_SAFE_004 {
        id: SYS_SAFE_004
        text: QA watchdog valid response window 50 to 100ms
        risk: High
        verifymethod: Test
    }

    requirement SYS_SAFE_004a {
        id: SYS_SAFE_004a
        text: failure counter threshold 3 triggers SAFE STATE
        risk: High
        verifymethod: Test
    }

    requirement SYS_SAFE_006 {
        id: SYS_SAFE_006
        text: Safe state latency less than 150ms from fault to motor disable
        risk: High
        verifymethod: Test
    }

    requirement SYS_SAFE_010 {
        id: SYS_SAFE_010
        text: Red LED assertable independently by Pi5 and Pi400
        risk: Medium
        verifymethod: Inspection
    }

    requirement SYS_SAFE_001 {
        id: SYS_SAFE_001
        text: AI inference shall not influence runtime safety decisions
        risk: High
        verifymethod: Analysis
    }

    element stateEvaluator {
        type: C++20 class
        docref: src/decision_node/src/state_evaluator.cpp
    }

    element healthNode {
        type: rclpy node
        docref: src/health_node/health_node/health_node.py
    }

    element actuatorNode {
        type: rclpy node
        docref: src/actuator_node/actuator_node/actuator_node.py
    }

    element qaWatchdog {
        type: supervisor component
        docref: pi400_supervisor/qnx_wdg_server
    }

    element diodeOrCircuit {
        type: hardware circuit
        docref: hardware/wiring.md
    }

    stateEvaluator - satisfies -> SYS_SAFE_007
    stateEvaluator - satisfies -> SYS_SAFE_006
    stateEvaluator - satisfies -> SYS_SAFE_001
    healthNode - satisfies -> SYS_SAFE_004
    qaWatchdog - satisfies -> SYS_SAFE_004a
    actuatorNode - satisfies -> SYS_SAFE_006
    diodeOrCircuit - satisfies -> SYS_SAFE_010
```

---

## Dynamic Diagrams

### 6. State Machine Diagram

Software state machine implemented in `StateEvaluator` (C++20), evaluated at 20 Hz.
Priority rules enforced top-down. GPIO 25 e-stop is an independent hardware layer below this.

```mermaid
stateDiagram-v2
    direction TB

    [*] --> INIT

    INIT --> SAFE_STATE   : critical_fault\n(both sensors gone OR distance < 0.15m\nOR watchdog_counter ≥ 3)
    INIT --> DEGRADED     : system_ready AND\nexactly one sensor valid
    INIT --> WARNING      : system_ready AND\ndistance < 0.50m
    INIT --> NORMAL       : system_ready AND\nboth sensors valid AND clear

    NORMAL --> WARNING    : distance < 0.50m
    NORMAL --> DEGRADED   : one sensor lost
    NORMAL --> SAFE_STATE : critical_fault

    WARNING --> NORMAL    : distance ≥ 0.50m AND\nboth sensors valid
    WARNING --> DEGRADED  : one sensor lost
    WARNING --> SAFE_STATE : critical_fault

    DEGRADED --> NORMAL   : both sensors recovered AND clear
    DEGRADED --> WARNING  : both sensors recovered AND\ndistance < 0.50m
    DEGRADED --> SAFE_STATE : critical_fault

    SAFE_STATE --> INIT   : manual_reset AND\nall conditions cleared

    state NORMAL {
        [*] : vel_scale = 1.0\nGreen LED ON
    }
    state WARNING {
        [*] : vel_scale = 0.5\nGreen LED ON
    }
    state DEGRADED {
        [*] : vel_scale = 0.2\nGreen LED ON · Yellow LED ON
    }
    state SAFE_STATE {
        [*] : vel_scale = 0.0\nGreen LED OFF · Red LED ON\nLatches — manual reset required
    }
    state INIT {
        [*] : vel_scale = 0.0\nGreen LED ON
    }
```

---

### 7. Sequence Diagram — System Startup (M3)

Verified on hardware 2026-05-08. Camera is a placeholder in M3 → system starts in DEGRADED.

```mermaid
sequenceDiagram
    participant Boot as System Boot
    participant DEC as decision_node
    participant HLT as health_node
    participant ACT as actuator_node
    participant ULT as ultrasonic_node
    participant LED as LEDs (GPIO)

    Boot->>DEC: nodes start
    Boot->>HLT: nodes start
    Boot->>ACT: nodes start
    Boot->>ULT: nodes start

    Note over DEC: camera_valid=false, ultrasonic_valid=false
    Note over DEC: both sensors invalid → SAFE_STATE (Rule 3)

    DEC->>HLT: /system_state = SAFE_STATE
    DEC->>ACT: /system_state = SAFE_STATE
    HLT->>LED: GPIO 17 LOW (green OFF)
    ACT->>LED: GPIO 22 HIGH (red ON)

    ULT->>DEC: /obstacles (first reading)
    Note over DEC: system_ready=true, ultrasonic_valid=true\nState LATCHES — manual reset required

    Note over DEC,ACT: Operator publishes /reset true

    DEC->>DEC: SAFE_STATE → INIT
    DEC->>DEC: INIT → DEGRADED\n(camera_valid=false, ultrasonic_valid=true)
    DEC->>HLT: /system_state = DEGRADED
    DEC->>ACT: /system_state = DEGRADED
    HLT->>LED: GPIO 17 HIGH (green ON)
    ACT->>LED: GPIO 22 LOW (red OFF)
```

---

### 8. Sequence Diagram — I2C Q&A Watchdog Protocol

Pi5 is I2C master. Pi400 is I2C slave at address 0x40. Not yet active in M3 — Pi400 slave deferred to M5.

```mermaid
sequenceDiagram
    participant PI5 as Pi5 health_node\n(I2C master)
    participant I2C as I2C Bus\n(GPIO 2/3, 100kHz)
    participant PI400 as Pi400 QAWatchdogServer\n(I2C slave 0x40)
    participant SC as SafeStateController

    PI400->>PI400: generate seed (32-bit random)
    PI400->>PI400: store seed in register 0x00

    PI5->>I2C: read register 0x00 (4 bytes)
    I2C->>PI400: I2C read request
    PI400->>I2C: return seed
    I2C->>PI5: seed value

    PI5->>PI5: response = seed XOR 0xA5A5A5A5
    Note over PI5: wait until ~70ms after\nlast acknowledged response

    PI5->>I2C: write register 0x01 (response, 4 bytes)
    I2C->>PI400: I2C write request

    alt Response in valid window (50–100ms) AND answer correct
        PI400->>PI400: consecutive_correct++\nif >= 2: failure_counter--
    else Too early OR too late OR wrong answer
        PI400->>PI400: failure_counter++
        alt failure_counter >= 3
            PI400->>SC: assert safe state
            SC->>SC: GPIO 25 LOW (e-stop)
            SC->>SC: GPIO 22 HIGH (red LED)
        end
    end
```

---

### 9. Sequence Diagram — Obstacle Detection → SAFE_STATE → Reset

Verified on hardware 2026-05-08.

```mermaid
sequenceDiagram
    participant ULT as ultrasonic_node
    participant DEC as decision_node\nStateEvaluator
    participant HLT as health_node
    participant ACT as actuator_node
    participant LED as LEDs (GPIO)

    Note over DEC: Running in DEGRADED\n(camera invalid, ultrasonic valid)

    ULT->>DEC: /obstacles range = 0.10m
    Note over DEC: distance 0.10m < SAFE_DISTANCE 0.15m\nRule 3 → SAFE_STATE
    DEC->>DEC: DEGRADED → SAFE_STATE

    DEC->>HLT: /system_state = SAFE_STATE
    DEC->>ACT: /system_state = SAFE_STATE
    HLT->>LED: GPIO 17 LOW (green OFF)
    ACT->>LED: GPIO 22 HIGH (red ON)

    ULT->>DEC: /obstacles range = 2.0m (obstacle removed)
    Note over DEC: SAFE_STATE LATCHES\nRule 1 — ignores cleared condition\nwithout manual reset

    Note over DEC: Operator publishes /reset true

    DEC->>DEC: all_clear=true → SAFE_STATE → INIT
    DEC->>DEC: INIT → DEGRADED
    DEC->>HLT: /system_state = DEGRADED
    DEC->>ACT: /system_state = DEGRADED
    HLT->>LED: GPIO 17 HIGH (green ON)
    ACT->>LED: GPIO 22 LOW (red OFF)
```

---

### 10. Sequence Diagram — Hardware E-Stop (Independent Safety Layer)

GPIO 25 e-stop bypasses the software state machine entirely.
This is the key FFI measure: Pi400 can stop motors regardless of Pi5 software state.

```mermaid
sequenceDiagram
    participant PI400 as Pi400\nSafeStateController
    participant GPIO as GPIO 25 Wire\n(Pi400 → Pi5)
    participant ACT as Pi5 actuator_node\n(polls at 100Hz)
    participant DEC as Pi5 decision_node\nStateEvaluator
    participant MOTOR as Motor Commands

    Note over DEC: decision_node in any software state\n(NORMAL, DEGRADED, etc.)

    PI400->>GPIO: assert GPIO 25 LOW (active-low)
    Note over GPIO: Latency < 10ms

    ACT->>GPIO: poll GPIO 25 (100Hz)
    GPIO->>ACT: reads LOW

    ACT->>MOTOR: force cmd_vel = zero
    ACT->>ACT: GPIO 22 HIGH (red LED ON)
    ACT-->>ACT: log E-STOP ASSERTED

    Note over DEC: decision_node state UNCHANGED\nsoftware state machine unaware\nFFI boundary maintained

    PI400->>GPIO: release GPIO 25 HIGH
    ACT->>GPIO: poll GPIO 25 (100Hz)
    GPIO->>ACT: reads HIGH
    ACT->>MOTOR: commands accepted again
    ACT->>ACT: GPIO 22 LOW (if sw state not SAFE_STATE)
    ACT-->>ACT: log E-stop released
```

---

### 11. Activity Diagram — StateEvaluator Priority Rules

Maps the C++20 `StateEvaluator::evaluate()` logic. Implemented in
`pi5_linux/ros2_ws/src/decision_node/src/state_evaluator.cpp`.

```mermaid
flowchart TD
    START([evaluate input]) --> R1{previous_state\n== SAFE_STATE?}

    R1 -- Yes --> LATCH{manual_reset\nAND all_clear?}
    LATCH -- No --> OUT_SS([return SAFE_STATE\nvel=0.0])
    LATCH -- Yes --> OUT_INIT1([return INIT\nvel=0.0])

    R1 -- No --> R3{SAFE_STATE\nconditions?}

    R3 -- "watchdog_counter ≥ 3\nOR distance < 0.15m\nOR both sensors gone" --> OUT_SS2([return SAFE_STATE\nvel=0.0])

    R3 -- No --> R2{system_ready?}
    R2 -- No --> OUT_INIT2([return INIT\nvel=0.0])

    R2 -- Yes --> R4{exactly one\nsensor valid?}
    R4 -- Yes --> OUT_DEG([return DEGRADED\nvel=0.2])

    R4 -- No --> R5{"ultrasonic_valid\nAND distance < 0.50m?"}
    R5 -- Yes --> OUT_WARN([return WARNING\nvel=0.5])

    R5 -- No --> OUT_NORM([return NORMAL\nvel=1.0])

    style OUT_SS fill:#ff6666
    style OUT_SS2 fill:#ff6666
    style OUT_INIT1 fill:#ffcc66
    style OUT_INIT2 fill:#ffcc66
    style OUT_DEG fill:#ffaa33
    style OUT_WARN fill:#ffee66
    style OUT_NORM fill:#66cc66
```

---

*Diagrams maintained in this file — single source of truth.*
*Rendered by Mermaid — GitHub and VS Code Markdown Preview.*
*Last updated: 2026-05-08*
