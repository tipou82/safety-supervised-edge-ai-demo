# Safety-Supervised Edge AI Demo — Architecture Diagrams

**Single source of truth for all architecture diagrams.**
Mermaid notation — renders in GitHub and VS Code Markdown Preview.
Last updated: 2026-05-11 (reflects final system M0–M8).

> Educational demonstrator — not ISO 26262 certified.
> ASIL-B-inspired patterns. FFI-inspired architectural measures. No LLM/cloud AI in runtime safety path.

---

## Static Diagrams

### 1. Block Definition Diagram (BDD) — Hardware Blocks

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
        +nodes : 7 ROS2 nodes
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
        +resolution : 4608 x 2592
        +interface : CSI ribbon cable
        +focal_length_px : 1200 (calibrated)
    }

    class UltrasonicSensor {
        <<block>>
        +model : Grove Ultrasonic Ranger
        +protocol : Single-wire SIG
        +range_min_m : 0.02
        +range_max_m : 3.50
        +gpio_sig : 23
        +publish_hz : 20
    }

    class LedBuzzerOutput {
        <<block>>
        +green_gpio : 17  NORMAL indicator
        +yellow_gpio : 27 DEGRADED indicator
        +red_gpio : 22    SAFE STATE wired-OR
        +buzzer_gpio : 18 WARNING and DEGRADED
    }

    SafetySupervisedEdgeAIDemo *-- "1" RaspberryPi5
    SafetySupervisedEdgeAIDemo *-- "1" RaspberryPi400
    SafetySupervisedEdgeAIDemo *-- "1" CameraModule3
    SafetySupervisedEdgeAIDemo *-- "1" UltrasonicSensor
    SafetySupervisedEdgeAIDemo *-- "1" LedBuzzerOutput
```

---

### 2. Block Definition Diagram (BDD) — Software Nodes

M7: camera_ai_node split into two MMU-isolated processes for spatial FFI.

```mermaid
classDiagram
    direction TB

    class LinuxROSDomain {
        <<domain>>
        +processor : Raspberry Pi 5
        +os : RPi OS Bookworm
        +middleware : ROS2 Humble
        +nodes : 7
    }

    class QNXSupervisorDomain {
        <<domain>>
        +processor : Raspberry Pi 400
        +os : Ubuntu 22.04 (QNX-inspired)
    }

    class HealthMonitorNode {
        <<rclpy node>>
        +udp_port : 9001
        +wdg_window_ms : 30
        +wdg_cycle_ms : 20
        +flow_check : decision + ultrasonic deadlines
        +gpio_green : 17
        +gpio_yellow : 27
        +gpio_buzzer : 18
    }

    class UltrasonicNode {
        <<rclpy node>>
        +publish_hz : 20
        +gpio_sig : 23
        +timeout_s : 0.1
    }

    class HandDetectionNode {
        <<rclpy node MMU-isolated>>
        +model : MediaPipe Hands
        +owns : picamera2 IMX708
        +publish_hz : 10
        +mjpeg_port : 8080
        +focal_length_px : 1200
    }

    class ObjectDetectionNode {
        <<rclpy node MMU-isolated>>
        +model : YOLOv8n
        +input : hand ROI via CompressedImage
        +publish_hz : 10
    }

    class DecisionNode {
        <<rclpy + C++20 node>>
        +eval_hz : 50
        +warn_distance_m : 0.50
        +safe_distance_m : 0.15
        +camera_safe_distance_m : 0.20
        +ultrasonic_timeout_s : 0.1
        +camera_timeout_s : 2.0
    }

    class ActuatorNode {
        <<rclpy node>>
        +estop_poll_hz : 100
        +gpio_estop : 25
        +gpio_red_led : 22
    }

    class StateEvaluator {
        <<C++20 pure class>>
        +states : INIT NORMAL WARNING DEGRADED SAFE_STATE
        +gtest_cases : 33
        +evaluate(input) EvaluatorOutput
        +velocity_scale(state) double
    }

    class QAWatchdogServer {
        <<supervisor>>
        +transport : UDP port 9001
        +window_total_ms : 30
        +window_open_ms : 15
        +window_close_ms : 30
        +e2e : CRC-16 plus seq counter
        +failure_threshold : 3
        +gpio_estop : 25
        +gpio_red_led : 22
    }

    LinuxROSDomain  *-- HealthMonitorNode
    LinuxROSDomain  *-- UltrasonicNode
    LinuxROSDomain  *-- HandDetectionNode
    LinuxROSDomain  *-- ObjectDetectionNode
    LinuxROSDomain  *-- DecisionNode
    LinuxROSDomain  *-- ActuatorNode
    DecisionNode    *-- StateEvaluator

    QNXSupervisorDomain *-- QAWatchdogServer

    HandDetectionNode --> ObjectDetectionNode : hand_roi CompressedImage
    QAWatchdogServer  --> ActuatorNode        : GPIO 25 e-stop
```

---

### 3. Internal Block Diagram (IBD) — Inter-Processor Connections

```mermaid
graph LR
    subgraph Pi5["Raspberry Pi 5 — Linux / ROS2 Domain"]
        HN["health_node\nUDP Q&A client 20ms\nFlow check gate\nGPIO 17/27/18"]
        HDN["hand_detection_node\nMediaPipe Hands\npicamera2 IMX708\nMJPEG :8080"]
        ODN["object_detection_node\nYOLOv8n\n/detections 10Hz"]
        UN["ultrasonic_node\n20Hz GPIO 23\n100ms timeout"]
        DN["decision_node\nStateEvaluator C++20\n50Hz evaluation"]
        AN["actuator_node\nGPIO 25 poll 100Hz\nRed LED GPIO 22"]
        GREEN["Green LED GPIO 17"]
        YELLOW["Yellow LED GPIO 27"]
        BUZZER["Buzzer GPIO 18"]
        RED_PI5["Red LED GPIO 22 via D1"]
    end

    subgraph Pi400["Raspberry Pi 400 — QNX-Inspired Supervisor"]
        WDG["qnx_wdg_server\nUDP 30ms window\nCRC-16 plus seq\nfailure counter"]
        RED_PI400["Red LED GPIO 22 via D2"]
    end

    HN  -->|"UDP Q&A seed/response\n192.168.50.x port 9001"| WDG
    WDG -->|"UDP status\nfailure_counter"| HN
    WDG -->|"GPIO 25 active-low\ne-stop"| AN

    RED_PI5   -->|"1N4148 D1"| REDLED(["Red LED wired-OR"])
    RED_PI400 -->|"1N4148 D2"| REDLED

    HDN -->|"/hand_detections\n/hand_roi CompressedImage"| ODN
    ODN -->|"/detections 10Hz\nhand_distance_m"| DN
    UN  -->|"/obstacles 20Hz"| DN
    HN  -->|"/watchdog_failure_counter\n10Hz"| DN
    DN  -->|"/system_state 50Hz"| HN
    DN  -->|"/system_state 50Hz"| AN
    DN  -->|"/cmd_vel 50Hz"| AN

    HN  -->|"GPIO 17"| GREEN
    HN  -->|"GPIO 27"| YELLOW
    HN  -->|"GPIO 18"| BUZZER
    AN  -->|"GPIO 22"| RED_PI5
    WDG -->|"GPIO 22"| RED_PI400
```

---

### 4. Package Diagram — Domain Separation

```mermaid
graph TB
    subgraph SYS["SafetySupervisedEdgeAIDemo"]
        subgraph LINUX["Linux / ROS2 Domain  Pi5"]
            subgraph PERCEPTION["Perception  MMU-isolated processes"]
                HDN2["hand_detection_node\nMediaPipe Hands"]
                ODN2["object_detection_node\nYOLOv8n"]
                USN["ultrasonic_node\n20Hz"]
            end
            subgraph CONTROL["Decision and Control"]
                DEC["decision_node\nStateEvaluator C++20 50Hz"]
                ACT["actuator_node\nGPIO 25 poll 100Hz"]
            end
            subgraph HEALTH["Health Watchdog and Indicators"]
                HLT["health_node\nUDP Q&A 20ms\nFlow check\nGPIO 17/27/18"]
            end
        end

        subgraph QNX["QNX-Inspired Supervisor Domain  Pi400"]
            subgraph MONITOR["Safety Monitor"]
                WDG2["qnx_wdg_server\nUDP 30ms window\nCRC-16 plus seq"]
            end
            subgraph SAFETY["Safe State Enforcement"]
                SSC["GPIO 25 active-low e-stop\nGPIO 22 red LED"]
            end
        end

        subgraph HW["Hardware Layer"]
            I2C_UNUSED["I2C GPIO 2/3 unused\n(BSC slave not feasible BCM2711)"]
            GPIO_ESTOP["E-Stop GPIO 25\nPi400 to Pi5"]
            GPIO_LEDS["LEDs GPIO 17/27/22\nBuzzer GPIO 18"]
            UDP_ETH["UDP Ethernet\n192.168.50.x port 9001"]
            CSI_BUS["CSI camera bus"]
        end
    end

    HEALTH  -->|"UDP Q&A"| UDP_ETH
    UDP_ETH -->|"challenge response"| MONITOR
    MONITOR --> SAFETY
    SAFETY  -->|"assert"| GPIO_ESTOP
    GPIO_ESTOP -->|"poll 100Hz"| ACT
    CONTROL -->|"drive"| GPIO_LEDS
    SAFETY  -->|"drive"| GPIO_LEDS
    PERCEPTION -->|"CSI"| CSI_BUS
    HDN2 --> ODN2
```

---

### 5. Requirements Diagram

```mermaid
requirementDiagram

    requirement SYS_SAFE_007 {
        id: SYS_SAFE_007
        text: State machine 5 states INIT NORMAL WARNING DEGRADED SAFE_STATE
        risk: High
        verifymethod: Test
    }

    requirement SYS_SAFE_004 {
        id: SYS_SAFE_004
        text: QA watchdog window 30ms total 15ms closed 15ms open
        risk: High
        verifymethod: Test
    }

    requirement SYS_SAFE_006 {
        id: SYS_SAFE_006
        text: Safe state latency less than 150ms from fault to motor disable
        risk: High
        verifymethod: Test
    }

    requirement SYS_SAFE_011 {
        id: SYS_SAFE_011
        text: Proximity FTTI 100ms ultrasonic 20Hz plus decision 50Hz
        risk: High
        verifymethod: Test
    }

    requirement SYS_SAFE_012 {
        id: SYS_SAFE_012
        text: Camera hand distance less than 20cm triggers SAFE_STATE
        risk: High
        verifymethod: Test
    }

    requirement SYS_SAFE_001 {
        id: SYS_SAFE_001
        text: AI inference shall not influence runtime safety decisions
        risk: High
        verifymethod: Analysis
    }

    element stateEvaluator {
        type: C++20 pure class
        docref: src/decision_node/src/state_evaluator.cpp
    }

    element healthNode {
        type: rclpy node
        docref: src/health_node/health_node/health_node.py
    }

    element qaWatchdog {
        type: supervisor
        docref: pi400_supervisor/scripts/qnx_wdg_server.py
    }

    element handDetection {
        type: rclpy node
        docref: src/hand_detection_node
    }

    stateEvaluator - satisfies -> SYS_SAFE_007
    stateEvaluator - satisfies -> SYS_SAFE_006
    stateEvaluator - satisfies -> SYS_SAFE_011
    stateEvaluator - satisfies -> SYS_SAFE_012
    stateEvaluator - satisfies -> SYS_SAFE_001
    healthNode - satisfies -> SYS_SAFE_004
    qaWatchdog - satisfies -> SYS_SAFE_006
    handDetection - satisfies -> SYS_SAFE_012
```

---

## Dynamic Diagrams

### 6. State Machine Diagram

Evaluated at 50 Hz by StateEvaluator C++20. SAFE_STATE latches — manual reset required.
Buzzer: ON in WARNING and DEGRADED. Yellow LED: ON in DEGRADED only.

```mermaid
stateDiagram-v2
    direction TB

    [*] --> INIT

    INIT --> SAFE_STATE   : both_sensors_invalid OR\ncritical_distance OR watchdog_fail
    INIT --> DEGRADED     : system_ready AND one sensor invalid
    INIT --> WARNING      : system_ready AND distance < 0.50m
    INIT --> NORMAL       : system_ready AND both sensors valid AND clear

    NORMAL --> WARNING    : distance < 0.50m
    NORMAL --> DEGRADED   : one sensor lost
    NORMAL --> SAFE_STATE : critical_distance OR camera_hand_critical OR\nwatchdog_fail OR both_sensors_invalid

    WARNING --> NORMAL    : distance >= 0.50m AND both sensors valid
    WARNING --> DEGRADED  : one sensor lost
    WARNING --> SAFE_STATE : critical_distance OR camera_hand_critical OR\nwatchdog_fail

    DEGRADED --> NORMAL   : both sensors recovered AND clear
    DEGRADED --> WARNING  : both recovered AND distance < 0.50m
    DEGRADED --> SAFE_STATE : critical_distance OR camera_hand_critical OR\nwatchdog_fail

    SAFE_STATE --> INIT   : manual_reset AND all conditions cleared\n(failure_counter < 3 AND sensors valid AND distance clear)

    state NORMAL {
        [*] : vel 1.0  Green ON
    }
    state WARNING {
        [*] : vel 0.5  Green ON  Buzzer ON
    }
    state DEGRADED {
        [*] : vel 0.2  Green ON  Yellow ON  Buzzer ON
    }
    state SAFE_STATE {
        [*] : vel 0.0  Green OFF  Red ON  Latches
    }
    state INIT {
        [*] : vel 0.0  Green ON
    }
```

---

### 7. Sequence Diagram — System Startup

```mermaid
sequenceDiagram
    participant Pi400 as Pi400 qnx_wdg_server
    participant HN as health_node
    participant UN as ultrasonic_node
    participant HDN as hand_detection_node
    participant ODN as object_detection_node
    participant DN as decision_node
    participant AN as actuator_node

    Pi400->>Pi400: GPIO 25 LOW (e-stop asserted)
    Pi400->>Pi400: GPIO 22 HIGH (red LED ON)
    Note over Pi400: Fail-safe boot state

    HN->>HN: GPIO 17 ON (green LED)
    Note over DN: both sensors invalid\nboth_sensors_invalid rule
    DN->>HN: /system_state = SAFE_STATE
    DN->>AN: /system_state = SAFE_STATE
    HN->>HN: GPIO 17 OFF (green LED)
    AN->>AN: GPIO 22 HIGH (red LED)

    UN->>DN: /obstacles (first valid reading)
    Note over DN: system_ready = true\nultrasonic_valid = true\ncamera_valid = false still
    Note over DN: SAFE_STATE LATCHES

    ODN->>DN: /detections (camera pipeline alive)
    Note over DN: camera_valid = true\nbut SAFE_STATE still latches

    Note over HN: Q&A watchdog serviced\nfailure_counter drops to 0
    Note over DN: Operator publishes /reset

    DN->>DN: SAFE_STATE to INIT to DEGRADED
    DN->>HN: /system_state = DEGRADED
    HN->>HN: GPIO 17 ON  GPIO 27 ON  GPIO 18 ON
    AN->>AN: GPIO 22 LOW (red LED OFF)
    Pi400->>Pi400: GPIO 25 HIGH (e-stop released)
```

---

### 8. Sequence Diagram — UDP Q&A Watchdog Protocol

```mermaid
sequenceDiagram
    participant Pi400 as Pi400 qnx_wdg_server
    participant UDP as UDP Ethernet 192.168.50.x
    participant HN as health_node UDP thread
    participant FC as health_node flow check
    participant DN as decision_node

    loop Every ~20ms (health_node cycle)
        Pi400->>UDP: seed packet\njson type=seed seed=N seq=S crc=CRC16
        UDP->>HN: receive seed

        FC->>FC: check /system_state age < 60ms
        FC->>FC: check /obstacles age < 150ms

        alt flow_ok = true
            Note over HN: wait until 15ms elapsed\n(closed window end)
            HN->>HN: response = seed XOR 0xA5A5A5A5
            HN->>HN: attach seq=S crc=CRC16
            HN->>UDP: response packet
            UDP->>Pi400: receive response
            Pi400->>Pi400: validate timing 15-30ms AND value AND seq AND crc
            alt correct in window
                Pi400->>Pi400: consecutive_ok++\nif >=2 failure_counter--
            else wrong or out of window
                Pi400->>Pi400: failure_counter++
            end
        else flow_ok = false (pipeline node missed deadline)
            Note over HN: withhold response
            Pi400->>Pi400: timeout failure_counter++
        end

        Pi400->>UDP: status packet failure_counter state released
        UDP->>HN: receive status
        HN->>DN: /watchdog_failure_counter
    end

    alt failure_counter >= 3
        Pi400->>Pi400: GPIO 25 LOW (e-stop)
        Pi400->>Pi400: GPIO 22 HIGH (red LED)
    end
```

---

### 9. Sequence Diagram — Obstacle Detection and SAFE_STATE

Both sensor paths (ultrasonic distance + camera hand distance) can independently trigger.

```mermaid
sequenceDiagram
    participant UN as ultrasonic_node
    participant HDN as hand_detection_node
    participant ODN as object_detection_node
    participant DN as decision_node StateEvaluator
    participant HN as health_node
    participant AN as actuator_node

    Note over DN: Running in NORMAL state\nboth sensors valid clear distance

    UN->>DN: /obstacles range = 0.45m
    Note over DN: distance < 0.50m\nRule 5 WARNING
    DN->>HN: /system_state = WARNING
    HN->>HN: GPIO 18 ON (buzzer ON)

    HDN->>HDN: hand detected at 18cm
    HDN->>ODN: /hand_roi
    ODN->>DN: /detections hand_distance_m = 0.18
    Note over DN: camera_valid=true AND\ncamera_distance_m 0.18 < 0.20m\nRule 3 CAMERA_HAND_CRITICAL

    DN->>DN: WARNING to SAFE_STATE
    DN->>HN: /system_state = SAFE_STATE
    DN->>AN: /system_state = SAFE_STATE
    HN->>HN: GPIO 17 OFF  GPIO 18 OFF  GPIO 27 OFF
    AN->>AN: GPIO 22 HIGH (red LED ON)

    Note over DN: SAFE_STATE LATCHES

    Note over DN: Hand removed reset published

    DN->>DN: SAFE_STATE to INIT to NORMAL
    DN->>HN: /system_state = NORMAL
    HN->>HN: GPIO 17 ON (green ON only)
```

---

### 10. Sequence Diagram — Hardware E-Stop (Independent Safety Layer)

GPIO 25 path is independent of decision_node and StateEvaluator (FFI boundary).

```mermaid
sequenceDiagram
    participant Pi400 as Pi400 qnx_wdg_server
    participant GPIO as GPIO 25 Wire Pi400 to Pi5
    participant AN as Pi5 actuator_node poll 100Hz
    participant DN as Pi5 decision_node StateEvaluator
    participant MOTOR as Motor Commands

    Note over DN: Any software state\nNORMAL DEGRADED etc

    Pi400->>GPIO: assert GPIO 25 LOW (active-low)
    Note over GPIO: Latency less than 10ms

    AN->>GPIO: poll GPIO 25 at 100Hz
    GPIO->>AN: reads LOW
    AN->>MOTOR: force cmd_vel = zero
    AN->>AN: GPIO 22 HIGH (red LED ON)

    Note over DN: decision_node state UNCHANGED\nFFI boundary maintained

    Pi400->>GPIO: release GPIO 25 HIGH
    AN->>GPIO: poll GPIO 25
    GPIO->>AN: reads HIGH
    AN->>MOTOR: commands accepted
    AN->>AN: GPIO 22 LOW (if sw state not SAFE_STATE)
```

---

### 11. Activity Diagram — StateEvaluator Priority Rules

C++20 pure function in `src/decision_node/src/state_evaluator.cpp`. 33 gtest cases.

```mermaid
flowchart TD
    START([evaluate input]) --> R1{previous_state\n== SAFE_STATE?}

    R1 -- Yes --> LATCH{manual_reset\nAND all_clear?}
    LATCH -- No --> OUT_SS([return SAFE_STATE\nvel=0.0\ntrigger=safe_state_latch])
    LATCH -- Yes --> OUT_INIT1([return INIT\nvel=0.0\ntrigger=safe_state_reset])

    R1 -- No --> R3A{watchdog_counter\n>= 3?}
    R3A -- Yes --> OUT_WDG([return SAFE_STATE\nvel=0.0\ntrigger=watchdog_failure])
    R3A -- No --> R3B{ultrasonic_valid AND\ndistance < 0.15m?}
    R3B -- Yes --> OUT_DIST([return SAFE_STATE\nvel=0.0\ntrigger=critical_distance])
    R3B -- No --> R3C{camera_valid AND\ncamera_distance < 0.20m?}
    R3C -- Yes --> OUT_CAM([return SAFE_STATE\nvel=0.0\ntrigger=camera_hand_critical])
    R3C -- No --> R3D{both sensors\ninvalid?}
    R3D -- Yes --> OUT_BOTH([return SAFE_STATE\nvel=0.0\ntrigger=both_sensors_invalid])

    R3D -- No --> R2{system_ready?}
    R2 -- No --> OUT_INIT2([return INIT\nvel=0.0\ntrigger=not_ready])

    R2 -- Yes --> R4{exactly one\nsensor valid?}
    R4 -- Yes --> OUT_DEG([return DEGRADED\nvel=0.2\ntrigger=degraded_one_sensor])

    R4 -- No --> R5{ultrasonic_valid AND\ndistance < 0.50m?}
    R5 -- Yes --> OUT_WARN([return WARNING\nvel=0.5\ntrigger=warning_distance])

    R5 -- No --> OUT_NORM([return NORMAL\nvel=1.0\ntrigger=normal_fallback])

    style OUT_SS fill:#ff6666
    style OUT_WDG fill:#ff6666
    style OUT_DIST fill:#ff6666
    style OUT_CAM fill:#ff9999
    style OUT_BOTH fill:#ff6666
    style OUT_INIT1 fill:#ffcc66
    style OUT_INIT2 fill:#ffcc66
    style OUT_DEG fill:#ffaa33
    style OUT_WARN fill:#ffee66
    style OUT_NORM fill:#66cc66
```

---

*Diagrams maintained in this file — single source of truth.*
*Rendered by Mermaid — GitHub and VS Code Markdown Preview.*
*Last updated: 2026-05-11*
