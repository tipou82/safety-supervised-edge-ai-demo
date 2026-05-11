# AUTOSAR E2E Protection — Comparison and Mapping

**Document**: E2E-001
**Project**: Safety-Supervised Edge AI Demonstrator
**Reference**: AUTOSAR Classic Platform R22-11, Specification of E2E Library (AUTOSAR_SWS_E2ELibrary)
**Date**: 2026-05-11
**Author**: Yunpeng Yang
**Status**: COMPLETE

> **Purpose**: Map the UDP Q&A watchdog protocol implemented in this demonstrator
> against AUTOSAR E2E profile concepts. This demonstrates understanding of automotive
> communication protection standards and where the demonstrator aligns with or diverges
> from production practice.

---

## 1. What is AUTOSAR E2E Protection?

AUTOSAR E2E (End-to-End) protection is a standardised set of communication safety
mechanisms defined in AUTOSAR SWS E2ELibrary. It protects safety-relevant data
transmitted between software components — detecting transmission errors introduced by
hardware, software, or communication media.

### 1.1 Error classes detected by E2E

| Error class | Description |
|---|---|
| Corruption | Bit flips in payload or header |
| Loss | Message not received |
| Repetition | Same message received more than once (replay) |
| Insertion | Unexpected additional message |
| Incorrect sequence | Messages received out of order |
| Delay | Message arrives outside expected timing window |
| Masquerading | Wrong sender |
| Asymmetric information | Different receivers see different data |

### 1.2 AUTOSAR E2E profiles

| Profile | CRC | Counter | Use case |
|---|---|---|---|
| E2EProfile01 | CRC8 | 4-bit (0–14) | Classical ECU-to-ECU, low overhead |
| E2EProfile02 | CRC8 | 4-bit | Byte array protection |
| E2EProfile04 | CRC32 | 16-bit | High data volume, long messages |
| E2EProfile05 | CRC16 | — | SOME/IP services |
| E2EProfile06 | CRC32 | 16-bit | Adaptive platform |
| E2EProfile07 | CRC64 | 16-bit | High-integrity |
| E2EProfile11 | CRC32P4 | 16-bit | AUTOSAR Adaptive |
| **E2EProfile22** | **CRC8** | **8-bit** | **Modern Classic platform, compact** |

**Most relevant to this demonstrator**: E2EProfile01 (conceptual mapping) and E2EProfile22 (counter size match).

---

## 2. Demonstrator UDP Q&A Protocol — Recap

```
Seed packet (Pi400 → Pi5):
  { "type": "seed", "seed": <uint32>, "seq": <uint8>, "crc": <uint16> }

Response packet (Pi5 → Pi400):
  { "type": "response", "seed": <uint32>, "response": <uint32>,
    "seq": <uint8>, "crc": <uint16> }

Status packet (Pi400 → Pi5):
  { "type": "status", "failure_counter": <int>, "state": <str>,
    "released": <bool>, "cycle": <int> }
```

**CRC algorithm**: CRC-16/CCITT-FALSE (polynomial 0x1021, init 0xFFFF)
**Counter**: uint8 (0–255, wraps), incremented by Pi400 each cycle
**Timing window**: 15ms closed + 15ms open = 30ms total
**Failure threshold**: 3 consecutive failures → SAFE_STATE

---

## 3. Feature-by-Feature Mapping

### 3.1 E2EProfile01 vs. Demonstrator UDP Q&A

| E2E Feature | E2EProfile01 | Demonstrator UDP Q&A | Match? |
|---|---|---|---|
| **CRC algorithm** | CRC8 (polynomial 0x1D) | CRC-16/CCITT-FALSE | ⚠️ Stronger (16-bit vs 8-bit) |
| **CRC scope** | Header + data bytes | `{seed, seq}` payload | ✅ Equivalent concept |
| **Counter width** | 4-bit (0–14, value 15 = not used) | 8-bit (0–255, full wrap) | ✅ Counter present; wider range |
| **Counter increment** | +1 per transmission | +1 per Pi400 cycle | ✅ Monotonic increment |
| **Counter check** | Receiver verifies increment | Pi400 verifies echo'd seq | ✅ Verified by receiver |
| **Max delta** | Configurable (typically 1–3) | Exactly 1 (strict) | ✅ Strict = safer |
| **Data ID** | 16-bit Data ID in header | Seed value (implicitly unique) | ⚠️ No explicit Data ID |
| **Length check** | Not in Profile01 | Implicit via JSON structure | ✅ Equivalent |
| **Alive counter** | Counter stops → error | Seq stops → timeout → failure | ✅ Equivalent |
| **Status reporting** | E2E_PCheckStatusType enum | `failure_counter` integer | ✅ Equivalent concept |
| **Error classification** | OK/REPEATED/WRONG_SEQUENCE/ERROR/NOT_AVAILABLE | Too early / timeout / wrong value / malformed | ✅ Full classification |
| **Receiver state machine** | INIT/VALID/INVALID | Released/Unreleased/SAFE_STATE | ✅ Equivalent |

### 3.2 Timing protection (not in standard E2E profiles — added here)

AUTOSAR E2E profiles protect against **data corruption and loss** but do NOT define
**timing window enforcement**. The demonstrator adds this on top:

| Feature | Standard E2E | Demonstrator | Notes |
|---|---|---|---|
| Closed window (too early) | Not defined | 0–15ms → failure_counter++ | **Extension beyond E2E** |
| Open window (valid) | Not defined | 15–30ms → validate | **Extension beyond E2E** |
| Timeout window | Implicit via alive counter | >30ms → failure_counter++ | Equivalent |

This timing layer corresponds to what automotive systems implement separately as
**alive supervision** in AUTOSAR Watchdog Manager (WdgM), distinct from E2E.

### 3.3 Challenge-response (Q&A) — not in standard E2E

Standard AUTOSAR E2E is **unidirectional** — sender applies protection, receiver checks.
The Q&A pattern (sender requests seed, receiver computes response) is NOT part of the
AUTOSAR E2E library. It corresponds instead to:

| Automotive concept | Standard | Demonstrator mapping |
|---|---|---|
| Challenge-response watchdog | ISO 11898-1 / IEC 61508 | UDP Q&A (seed XOR mask) |
| External watchdog IC | MAX6369, TPS3813 (SPI/I2C) | Pi400 qnx_wdg_server via UDP |
| Watchdog Manager (WdgM) | AUTOSAR BSW WdgM | health_node + flow check |
| Supervised entities | WdgM alive supervision | Flow check on decision_node + ultrasonic_node |

---

## 4. Demonstrator vs. AUTOSAR WdgM

The AUTOSAR Watchdog Manager (WdgM) is the production equivalent of the demonstrator's
watchdog architecture. Mapping:

| WdgM concept | Demonstrator equivalent |
|---|---|
| Supervised Entity (SE) | decision_node, ultrasonic_node |
| Alive Indication | `/system_state` and `/obstacles` topic publication |
| Alive Supervision deadline | 60ms (decision_node), 150ms (ultrasonic_node) |
| Checkpoint | health_node flow check tick (20ms) |
| Mode manager | StateEvaluator state (NORMAL/DEGRADED/SAFE_STATE) |
| Watchdog trigger (WdgIf) | UDP Q&A response to Pi400 |
| External watchdog | Pi400 qnx_wdg_server |
| Safe state action | GPIO 25 assertion (hardware) |

**Key difference**: AUTOSAR WdgM runs on the same ECU and uses hardware watchdog timers.
The demonstrator uses a separate processor (Pi400) connected via UDP — architecturally
stronger (true spatial independence) but using a software channel (weaker than HW timer).

---

## 5. AUTOSAR E2E Error State Machine Mapping

AUTOSAR E2E defines a receiver state machine with states:

```
INIT → VALID ↔ INVALID → ERROR
```

The demonstrator's Pi400 failure counter implements an equivalent:

```
INIT (GPIO 25 LOW) → RELEASED (failure_counter=0) ↔ DEGRADED (counter 1-2) → SAFE_STATE (counter≥3)
```

| AUTOSAR E2E state | Demonstrator equivalent | Transition |
|---|---|---|
| INIT | Boot — GPIO 25 asserted | System start |
| VALID | Released (failure_counter=0) | First correct Q&A |
| INVALID | failure_counter 1–2 | Missed/wrong response |
| ERROR | SAFE_STATE (failure_counter≥3) | 3 consecutive failures |
| Recovery | failure_counter-- (2 consecutive OK) | Hysteresis |

**Notable enhancement**: AUTOSAR E2E does not specify hysteresis (recovery after error).
The demonstrator adds 2-consecutive-correct-then-decrement, which is closer to
automotive watchdog IC behaviour than standard E2E.

---

## 6. CRC Comparison

| CRC | Polynomial | Width | HD (Hamming Distance) | Use |
|---|---|---|---|---|
| CRC8 (E2EProfile01) | 0x1D | 8-bit | HD=4 up to 119 bits | Low-overhead ECU comms |
| CRC8H2F (AUTOSAR) | 0x2F | 8-bit | HD=6 up to 119 bits | Preferred in automotive |
| **CRC-16/CCITT-FALSE** | **0x1021** | **16-bit** | **HD=4 up to 32767 bits** | **Demonstrator** |
| CRC32 (E2EProfile04) | 0x04C11DB7 | 32-bit | HD=6 up to ~4 billion bits | High-volume data |
| CRC32P4 (AUTOSAR) | 0xF4ACFB13 | 32-bit | HD=6 | Adaptive platform |

**Assessment**: CRC-16/CCITT-FALSE provides better error detection than E2EProfile01's
CRC8 for longer payloads, at the cost of 1 extra byte. For a 9-byte payload (seed+seq),
HD=4 is achieved — identical Hamming distance to E2EProfile01 on comparable payload sizes.

The choice of CRC-16 over CRC8H2F (AUTOSAR preferred) is a pragmatic one: CRC-16/CCITT-FALSE
is widely available in Python standard library and well-documented. For production,
migrating to CRC8H2F would align with AUTOSAR requirements.

---

## 7. Gap Assessment

| AUTOSAR E2E feature | Demonstrator | Gap |
|---|---|---|
| Standardised CRC algorithm (CRC8H2F) | CRC-16/CCITT-FALSE | Non-standard algorithm — equivalent quality |
| Explicit Data ID in header | Implicit (seed uniqueness) | No formal Data ID — replay from different data source undetected |
| Length field | Not present | Short packet corruption not detected if length unchanged |
| AUTOSAR API compliance | Not applicable | Demonstrator is not AUTOSAR-based |
| WdgM integration | Custom implementation | Functionally equivalent but not AUTOSAR BSW |
| Hardware watchdog timer | Pi400 software timer | Software timer less deterministic than HW timer |

---

## 8. Production Upgrade Path

To evolve the demonstrator protocol toward AUTOSAR compliance:

| Step | Change | Effort |
|---|---|---|
| 1 | Replace CRC-16 with CRC8H2F | Low — algorithm swap |
| 2 | Add explicit 16-bit Data ID field | Low — header addition |
| 3 | Add length field | Low — 1 byte addition |
| 4 | Map to AUTOSAR E2E API (E2E_P01Protect / E2E_P01Check) | Medium — API alignment |
| 5 | Replace Python UDP with C AUTOSAR BSW module | High — full BSW implementation |
| 6 | Integrate with AUTOSAR WdgM and WdgIf | High — requires AUTOSAR stack |
| 7 | Replace Pi400 soft timer with hardware watchdog IC | Medium — hardware change |

---

## 9. Summary

| Dimension | Assessment |
|---|---|
| **Conceptual alignment** | High — demonstrator implements all core E2E concepts |
| **CRC strength** | Equivalent to E2EProfile01; stronger than minimum |
| **Counter mechanism** | Equivalent; wider (8-bit vs 4-bit) |
| **Timing supervision** | Extension beyond standard E2E (adds closed window + alive supervision) |
| **Challenge-response** | Extension beyond E2E (maps to external watchdog IC pattern) |
| **AUTOSAR API compliance** | Not applicable (non-AUTOSAR platform) |
| **Production readiness** | 7 steps to full AUTOSAR alignment |

The demonstrator protocol is **more sophisticated than standard E2E** in some dimensions
(timing window, challenge-response, hysteresis recovery) and **less formal** in others
(non-standard CRC, no Data ID, software timer). It correctly demonstrates the principles
that AUTOSAR E2E and WdgM implement in production automotive systems.

---

## 10. References

- AUTOSAR SWS E2ELibrary R22-11 (Specification of E2E Library)
- AUTOSAR SWS WatchdogManager R22-11
- ISO 11898-1:2015 (CAN data link layer)
- IEC 61508-2:2010 Clause 7.4.2 (Communication integrity)
- CRC Polynomial Zoo: https://crccalc.com
- `docs/safety_mechanisms.md` SM-1 (UDP Q&A protocol details)
- `pi400_supervisor/scripts/qnx_wdg_server.py` (implementation)
- `pi5_linux/ros2_ws/src/health_node/health_node/health_node.py` (client)
