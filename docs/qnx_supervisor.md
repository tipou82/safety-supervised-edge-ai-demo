# QNX-Inspired Supervisor Design

> **Implementation details** (watchdog protocol, timing, failure counter) are in
> `docs/safety_mechanisms.md` SM-1 and SM-2.
> This document covers the QNX RTOS rationale and process architecture.

## QNX RTOS Rationale

**Why QNX?**
- Microkernel architecture provides fault isolation
- POSIX PSE52 profile suitable for safety-critical systems
- Certifiable to IEC 61508 SIL 3, ISO 26262 ASIL D as a product
  (requires qualified BSP and tool chain — **NOT applicable to this Pi400 demonstrator**)
- Deterministic scheduling with priority inheritance

**Why NOT claiming certification?**
- Raspberry Pi 400 BSP is not qualified
- Development environment not tool-qualified
- This is a demonstrator, not a production system

**Current implementation**: Linux on Pi400 (Ubuntu 22.04), Python supervisor
(`qnx_wdg_server.py`). QNX RTOS is the intended production target pattern.

---

## Supervisor Architecture

### Process Structure

```
qnx_wdg_server.py (Pi400)
├── UDP Q&A watchdog server (port 9001)
│   ├── Seed generation (random 32-bit)
│   ├── Response validation (value + timing + seq + CRC-16)
│   └── Failure counter management
└── Safe state controller
    ├── GPIO 25 output (e-stop, active-low, default LOW)
    └── GPIO 22 output (red LED, diode-OR)
```

### Priority Model (QNX target)

| Thread | Priority | Scheduling |
|---|---|---|
| Watchdog server | 250 | FIFO, CPU core 0 |
| Safe state controller | 255 | FIFO, CPU core 0 (highest) |

In the current Linux fallback: single Python process, no FIFO scheduling.
PREEMPT_RT kernel recommended for tighter timing guarantees.

---

## QNX-Specific Features (Production Target)

### Microkernel Message Passing

Safe state controller subscribes to watchdog faults via QNX message passing
(MsgReceive/MsgReply) — synchronous, priority-inheriting, kernel-mediated.

### Interrupt Handling

GPIO e-stop assertion via hardware interrupt → ISR sends pulse to safe state
controller thread with guaranteed latency.

### Adaptive Partitioning

Supervisor runs in a dedicated CPU partition with guaranteed budget (e.g., 10% CPU),
immune to starvation by AI inference workload.

### Static Memory Allocation

No dynamic allocation (no heap fragmentation). All buffers pre-allocated at startup.

---

## Linux Fallback Differences

| Feature | QNX (target) | Linux fallback (current) |
|---|---|---|
| Scheduling | Guaranteed FIFO | SCHED_FIFO (requires root) |
| IPC | Message passing | UDP socket |
| Interrupts | Native ISR | GPIO polling via lgpio |
| Determinism | Hard real-time | Soft real-time |
| Watchdog channel | I2C BSC slave (target) | UDP Ethernet (DD-002) |

---

## Testing Strategy

### Unit Tests
- State machine transitions with mock inputs
- Failure counter logic (increment/decrement/threshold)
- CRC-16 validation

### Integration Tests
- Q&A watchdog end-to-end: Pi5 ↔ Pi400 (M5 verified)
- Latency measurements under Pi5 CPU load (M7 FFI-TEMPORAL)
- ROS2 flood test (M7 FFI-COMM)

### Fault Injection
- health_node stop → watchdog timeout → SAFE_STATE (FI-05, verified M6)

---

## References

- `docs/safety_mechanisms.md` — watchdog protocol and FTTI analysis
- `pi400_supervisor/scripts/qnx_wdg_server.py` — current implementation
- QNX Neutrino RTOS System Architecture Guide
- POSIX IEEE 1003.13-2003 (PSE52 profile)
