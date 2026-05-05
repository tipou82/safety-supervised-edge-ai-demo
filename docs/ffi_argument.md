# FFI-Inspired Architectural Measures

## Purpose

This document explains how this demonstrator implements Freedom from Interference (FFI) inspired measures across the dual-processor architecture, and honestly addresses what is and is not achieved.

## What is Freedom from Interference?

Per ISO 26262-6:2018 Clause 7.4.7, FFI ensures that a lower-ASIL or non-safety element cannot corrupt a higher-ASIL safety element. This is achieved through architectural measures providing:

1. **Spatial independence** (memory, processor resources)
2. **Temporal independence** (timing, scheduling)
3. **Communication independence** (data exchange)
4. **Design independence** (separate development, review)

## FFI in Dual-Processor Architecture

### 1. Spatial Independence

**Measure**: Physical processor separation between Linux (Pi5) and QNX (Pi400).

**Implementation**:
- Linux/ROS2 domain runs entirely on Pi5 processor
- QNX-inspired supervisor runs entirely on Pi400 processor
- No shared memory within the same address space
- No DMA between processors

**Interference Prevention**:
- Linux kernel panic cannot corrupt QNX supervisor memory
- AI inference memory exhaustion (e.g., GPU OOM) isolated to Pi5
- Buffer overflows in ROS2 nodes do not affect supervisor

**Limitation**:
- GPIO communication pins are shared physical resource
- Power supply common (no redundant power domains in this demo)
- Not equivalent to certified partitioning within single processor

### 2. Temporal Independence

**Measure**: Deterministic watchdog timeout independent of Linux timing.

**Implementation**:
- Supervisor runs on QNX RTOS with deterministic scheduling (or PREEMPT_RT Linux)
- Watchdog timeout threshold (500 ms) based on supervisor's local monotonic clock
- Safety decisions bounded to <150 ms regardless of Linux load

**Interference Prevention**:
- AI inference delays (e.g., thermal throttling) do not delay safety response
- Linux scheduler jitter does not affect supervisor cycle time
- ROS2 message queue backlog cannot stall supervisor

**Limitation**:
- Pi400 supervisor shares CPU cores with its own tasks (no hardware core reservation)
- GPIO interrupt latency depends on Linux kernel (for heartbeat generation on Pi5)
- Absolute timing guarantees require WCET analysis not performed in this demo

### 3. Communication Independence

**Measure**: Simple, validated communication protocol with error detection.

**Implementation**:
- **Primary**: GPIO heartbeat (binary signal, edge-triggered)
- **Secondary**: Shared memory with CRC32 validation
- Supervisor validates data integrity before use
- Invalid data treated as communication fault → SAFE_STATE

**Interference Prevention**:
- Corrupted ROS2 messages do not reach supervisor (different communication path)
- DDS middleware faults isolated to Linux domain
- Bit flips in shared memory detected by CRC check

**Limitation**:
- No cryptographic authentication (CRC32 detects errors, not malicious tampering)
- GPIO signal integrity depends on hardware (no redundant pins)
- Shared memory requires careful cache coherency management

### 4. Design Independence

**Measure**: Supervisor developed with separate requirements, design, and review.

**Implementation**:
- Supervisor requirements derived from system safety requirements (see requirements/safety_requirements.md)
- Supervisor designed without knowledge of AI model internals
- Different programming paradigms (deterministic C vs. ROS2 C++)
- Separate code reviews for supervisor vs. perception nodes

**Interference Prevention**:
- Common-cause failures in software design reduced
- AI model updates do not require supervisor changes
- Supervisor can be reviewed by safety engineer without AI expertise

**Limitation**:
- This is a single-person project, so true design independence not achieved
- No independent safety assessment (would require third-party review)
- Common development tools (compiler, OS) introduce common-cause risk

## FFI Argument Summary

### Spatial Interference

| Source | Target | Mitigation | Effectiveness |
|--------|--------|-----------|---------------|
| Linux memory fault | QNX memory | Separate processors | **Strong** |
| AI GPU OOM | Supervisor execution | Separate processors | **Strong** |
| ROS2 process crash | Supervisor process | Separate processors | **Strong** |
| Power supply fault | Both processors | None (common PSU) | **Weak** |

### Temporal Interference

| Source | Target | Mitigation | Effectiveness |
|--------|--------|-----------|---------------|
| AI inference delay | Watchdog detection | Local timeout on supervisor | **Strong** |
| Linux scheduler jitter | Supervisor cycle | QNX deterministic scheduling | **Moderate** (QNX) / **Weak** (Linux fallback) |
| ROS2 callback storm | Safety latency | Independent supervisor clock | **Strong** |
| Thermal throttling | Supervisor timing | Separate processor | **Moderate** (shared environment) |

### Communication Interference

| Source | Target | Mitigation | Effectiveness |
|--------|--------|-----------|---------------|
| DDS middleware fault | Supervisor data | No shared middleware | **Strong** |
| Shared memory corruption | Supervisor decision | CRC32 validation | **Moderate** |
| GPIO noise | Heartbeat detection | Edge filtering, timeout tolerance | **Moderate** |
| Cosmic ray bit flip | Safety data | CRC32 (no ECC RAM) | **Weak** |

## What This Demonstrates vs. What It Does Not

### ✅ Demonstrated

- Physical separation prevents memory corruption between domains
- Deterministic safety monitoring independent of AI timing
- Validated communication with error detection
- Safe state achievable even with complete Linux failure

### ❌ NOT Demonstrated

- **Quantitative FFI metrics** (e.g., probability of interference <10^-9/hr)
- **Hardware fault coverage** (no redundant processors, ECC RAM, lockstep cores)
- **Certified partitioning** (no qualified hypervisor or separation kernel)
- **Common-cause analysis** (no systematic analysis of shared components)
- **Tool qualification** (compiler, OS, libraries not safety-certified)

## FFI for AI Safety

This architecture addresses specific challenges of AI in safety-critical systems:

**Challenge 1: Non-deterministic AI inference**
- **Solution**: AI operates in development domain, supervisor is deterministic

**Challenge 2: Unverified AI perception errors**
- **Solution**: Supervisor does not trust AI outputs, only monitors liveness

**Challenge 3: AI model updates**
- **Solution**: Supervisor interface unchanged by model updates

**Challenge 4: Inference latency variability**
- **Solution**: Supervisor timeout does not depend on AI inference time

## Gap Analysis: Demo vs. Production

| ISO 26262 Requirement | This Demo | Production System |
|----------------------|-----------|-------------------|
| Partitioning (6.4.7) | Physical processors | Hypervisor or MPU partitions |
| Timing analysis (6.4.4) | Estimates only | Full WCET analysis |
| Memory protection (6.4.6) | OS-level | MMU with certified config |
| Communication protection (6.4.8) | CRC32 | CRC + authentication + encryption |
| Common cause analysis (9.4.3) | Not performed | Systematic analysis required |

## Interview Talking Points

**"How does your architecture provide FFI?"**
> "I use physical processor separation to prevent spatial interference between the AI perception domain on Linux and the safety supervisor on QNX. The supervisor makes safety decisions based on its own local clock, so temporal interference from AI inference delays doesn't affect safety response time. Communication uses simple GPIO heartbeat with CRC-validated shared memory as backup, avoiding complex middleware that could introduce interference."

**"Is this approach sufficient for ASIL-B?"**
> "The architectural pattern is inspired by ASIL-B approaches, but this demonstrator doesn't achieve full ASIL-B compliance. I'd need quantitative interference analysis, certified RTOS and tools, hardware fault coverage with redundancy, and a formal development process with independent assessment. This demo shows I understand the concepts and can implement the technical measures."

**"What are the main limitations?"**
> "Main limitation is the common-cause failures I haven't addressed: shared power supply, no hardware redundancy, and development tools that aren't qualified. Also, my CRC32 check detects bit errors but wouldn't detect malicious tampering. For production, I'd need ECC memory, dual power supplies, and probably cryptographic message authentication."

## References

- ISO 26262-6:2018 Clause 7.4.7 (Freedom from interference)
- ISO 26262-9:2018 Clause 6 (ASIL-oriented and safety-oriented analyses)
- IEC 61508-3:2010 Clause 7.4.2.4 (Software modules with different SILs)
- AUTOSAR AP R20-11 (Partitioning in adaptive platform)
