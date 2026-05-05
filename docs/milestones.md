# Project Milestones

**Project**: Safety-Supervised Edge AI Demonstrator
**Status**: M0 complete — M1.0 complete — M1.1 pending

---

| ID | Milestone | Key Deliverables | Status |
|----|-----------|-----------------|--------|
| M0 | **Repository Baseline** | Documentation skeleton, requirements, traceability matrix, SysML model, engineering logbook, `.gitignore` | Complete |
| M1 | **Platform Access and Hardware Bring-up** | M1.0: Host PC → Pi5/Pi400 SSH; Pi5 ↔ Pi400 direct Ethernet (192.168.50.x/24) ping verified; OS versions documented; repo synced to Pi5. M1.1: Camera, LEDs, buzzer, ultrasonic sensor tested individually on Pi5 | M1.0 complete — M1.1 pending |
| M2 | **ROS2 Sensor Pipeline** | `health_node`, `ultrasonic_node`, `camera_ai_node` implemented and passing unit tests; ROS2 topics confirmed per `interfaces.yaml` | Planned |
| M3 | **Deterministic Decision Logic** | `decision_node`, `actuator_node` implemented; Linux-fallback supervisor running; state machine transitions manually validated | Planned |
| M4 | **Fault Injection** | FI-001 through FI-005 executed; end-to-end latency measured (<150 ms target); timing interference test passed; traceability CSV updated | Planned |
| M5 | **External Supervisor** (optional) | QNX supervisor ported (or Linux PREEMPT_RT fallback confirmed); re-run fault injection suite on supervisor implementation; latency comparison documented | Optional |
| M6 | **Portfolio-Ready Demo** | Demo video recorded; documentation complete with measured values; `v1.0-demo` tag; interview presentation deck prepared | Planned |

---

## Notes

- **M5 is optional**: If QNX 7.1 BSP for Raspberry Pi 400 is unavailable or impractical, the Linux PREEMPT_RT fallback is the primary implementation target. QNX design remains fully documented.
- **M0 → M1 dependency**: Hardware bring-up cannot start until the Pi 400 GPIO pin mapping (currently TBD in `hardware/gpio_mapping.md`) is confirmed on physical hardware.
- **Safety disclaimer**: None of these milestones constitute ISO 26262 certification or production readiness. This is an ASIL-B-inspired educational demonstrator.
