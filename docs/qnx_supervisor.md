# QNX-Inspired Supervisor Design

## Overview

The supervisor implements the ASIL-B-inspired monitoring path using QNX RTOS design principles. For demonstration purposes, a Linux fallback implementation is provided using POSIX real-time extensions.

## QNX RTOS Rationale

**Why QNX?**
- Microkernel architecture provides fault isolation
- POSIX PSE52 profile suitable for safety-critical systems
- Certified to IEC 61508 SIL 3, ISO 26262 ASIL D (when properly qualified)
- Deterministic scheduling with priority inheritance
- Memory protection between processes

**Why NOT claiming certification?**
- Raspberry Pi 400 BSP is not qualified
- Development environment not tool-qualified
- This is a demonstrator, not a production system

## Supervisor Architecture

### Process Structure (QNX)

```
qnx_supervisor
├── qnx_wdg_server (priority 250)
│   ├── GPIO heartbeat reader
│   ├── Timeout detection
│   └── State machine logic
├── safe_state_controller (priority 255)
│   ├── Emergency stop GPIO output
│   └── Safe state enforcement
└── shared_memory (protected)
    └── system_state (with CRC)
```

### Thread Model

**Watchdog Server Thread**
- **Priority**: 250 (high priority)
- **Scheduling**: FIFO, pinned to CPU core 0
- **Period**: 10 ms monitoring cycle
- **Stack**: Static allocation, 16 KB
- **Responsibilities**:
  - Read GPIO heartbeat input
  - Check timeout condition (>500 ms since last transition)
  - Evaluate state transition rules
  - Write to shared state region

**Safe State Controller Thread**
- **Priority**: 255 (highest priority)
- **Scheduling**: FIFO, pinned to CPU core 0
- **Trigger**: Event-driven on state change or timer
- **Stack**: Static allocation, 8 KB
- **Responsibilities**:
  - Monitor shared state for SAFE_STATE command
  - Assert emergency stop GPIO
  - Maintain safe state until reset

### Communication with Linux Domain

**GPIO Heartbeat (Primary)**
- **Signal**: GPIO pin from Pi5 to Pi400 (e.g., GPIO 17)
- **Pattern**: 10 Hz square wave (50 ms high, 50 ms low)
- **Detection**: Edge-triggered interrupt or polled at 1 kHz
- **Timeout**: 500 ms (5 missed heartbeats)

**Shared Memory (Secondary)**
- **Implementation**: POSIX shared memory mapped between domains
- **Structure**:
  ```c
  typedef struct {
      uint32_t magic;           // 0xCAFEBABE
      uint8_t  linux_state;     // NORMAL, WARNING, DEGRADED
      uint32_t heartbeat_count;
      uint32_t timestamp_ms;
      uint32_t crc32;
  } shared_state_t;
  ```
- **Validation**: CRC32 checked on every read, stale data detected by timestamp

### State Machine Implementation

The supervisor state machine runs at 10 ms cycle time with deterministic transitions.

**Inputs**:
- Heartbeat GPIO edge timestamp
- Shared memory health indicators
- Local timer (monotonic clock)

**Outputs**:
- Emergency stop GPIO (active-low to motor controller)
- Status LED (optional, for debugging)

**Transition Logic** (simplified pseudocode):
```c
void supervisor_cycle(void) {
    uint64_t now = get_monotonic_time_ms();
    uint64_t last_hb = get_last_heartbeat_time_ms();

    if ((now - last_hb) > WATCHDOG_TIMEOUT_MS) {
        transition_to_safe_state();
        assert_emergency_stop();
        return;
    }

    // Read shared state with validation
    shared_state_t state;
    if (!read_shared_state(&state)) {
        // Communication fault
        transition_to_safe_state();
        return;
    }

    switch (state.linux_state) {
        case LINUX_STATE_NORMAL:
            supervisor_state = SUPERVISOR_OK;
            break;
        case LINUX_STATE_DEGRADED:
            supervisor_state = SUPERVISOR_WARNING;
            break;
        default:
            // Invalid state
            transition_to_safe_state();
            break;
    }
}
```

## QNX-Specific Features Used

### 1. Microkernel Message Passing

**Channel/Connection Model**: Safe State Controller subscribes to state changes from Watchdog Server using QNX message passing (MsgReceive/MsgReply).

**Benefits**:
- Synchronous, deterministic IPC
- Priority inheritance prevents priority inversion
- Kernel-mediated, no shared memory corruption

### 2. Interrupt Handling

**Hardware Interrupts**: GPIO heartbeat connected to interrupt controller.

**InterruptAttach()**: Attach ISR to GPIO interrupt line with high priority.

**Pulse Notification**: ISR sends pulse to Watchdog Server thread, no blocking in ISR.

### 3. Deterministic Scheduling

**Adaptive Partitioning**: Supervisor runs in dedicated partition with guaranteed CPU budget.

**Budget**: 10% CPU time reserved for safety partition (not starved by Linux domain).

### 4. Memory Protection

**MMU Configuration**: Supervisor memory protected from user-space processes.

**No Dynamic Allocation**: All memory statically allocated at startup.

## Linux Fallback Implementation

For development and testing on non-QNX systems, a Linux implementation using POSIX real-time features is provided.

### Differences from QNX

| Feature | QNX | Linux Fallback |
|---------|-----|----------------|
| Process isolation | Microkernel | Separate process, best-effort |
| Scheduling | Guaranteed FIFO | SCHED_FIFO (requires root) |
| IPC | Message passing | POSIX shared memory + semaphores |
| Interrupts | Native ISR | GPIO polling via sysfs or libgpiod |
| Determinism | Hard real-time | Soft real-time (PREEMPT_RT kernel recommended) |

### Linux Implementation Notes

**Real-Time Kernel**: Use `PREEMPT_RT` patched kernel for better determinism.

**CPU Affinity**: Pin supervisor process to dedicated core (isolcpus).

**Priority**: Run with `SCHED_FIFO` priority 80-90 (requires CAP_SYS_NICE).

**GPIO**: Use `libgpiod` for direct GPIO access, not sysfs.

**Limitations**: No guaranteed timing, interrupt latency variable, not suitable for ASIL-B certification.

## Timing Analysis

### Worst-Case Execution Time (WCET)

Preliminary estimates for supervisor cycle:

| Function | WCET (µs) | Notes |
|----------|-----------|-------|
| Read GPIO state | 5 | Direct register access |
| Read shared memory | 10 | Cache miss considered |
| Validate CRC32 | 20 | Software CRC |
| State machine logic | 15 | Simple branching |
| Write emergency stop GPIO | 5 | Direct register access |
| **Total** | **55** | Well within 10 ms cycle |

**Safety Margin**: 55 µs / 10,000 µs = 0.55% CPU utilization per cycle.

### Latency Requirements

| Event | Latency Requirement | Measured (QNX) | Measured (Linux) |
|-------|---------------------|----------------|------------------|
| Heartbeat miss → Detection | <100 ms | TBD | TBD |
| Detection → Safe state | <50 ms | TBD | TBD |
| End-to-end (miss → stop) | <150 ms | TBD | TBD |

Measured values to be determined during integration testing.

## Safety Properties

### Independence

**Separate Processor**: Supervisor cannot be corrupted by Linux kernel panic or memory corruption.

**Separate Power Domain** (optional): Pi400 can be powered independently for fail-operational scenarios.

### Determinism

**No AI in Safety Path**: Supervisor logic is rule-based only, no machine learning inference.

**Bounded Execution**: All code paths have WCET analysis.

**Static Memory**: No dynamic allocation, no heap fragmentation.

### Fail-Safe

**Default State**: Emergency stop asserted on startup until Linux domain proves health.

**Watchdog Reset**: If supervisor itself hangs, external hardware watchdog resets system (future work).

## Testing Strategy

### Unit Tests
- State machine transitions with mock inputs
- CRC validation with corrupted data
- Timeout detection with simulated heartbeat loss

### Integration Tests
- GPIO communication loop with actual Pi5
- Latency measurements under load
- Interference testing (CPU stress on Linux domain)

### Fault Injection
- Heartbeat stop (immediate, gradual)
- Shared memory corruption (bit flips, wrong CRC)
- Priority inversion scenarios (Linux fallback only)

## Future Enhancements

**Dual Watchdog**: Mutual monitoring between Linux and QNX domains.

**Diagnostic Logging**: Store fault events to non-volatile memory for post-mortem analysis.

**Graceful Degradation**: Allow limited operation in DEGRADED state with ultrasonic sensors only.

**Self-Test**: Power-on self-test (POST) for supervisor hardware and software.

## References

- QNX Neutrino RTOS System Architecture Guide
- QNX Safety Manual for IEC 61508 / ISO 26262
- ISO 26262-6:2018 Clause 7 (Software architectural design)
- POSIX IEEE 1003.13-2003 (PSE52 profile)
