# M1: Hardware Bring-Up

## Goal

Verify that all individual hardware components connected to the Raspberry Pi 5 operate correctly in isolation before any software integration begins. Produce documented test evidence for each component.

## Scope

- Physical assembly and wiring of Raspberry Pi 5 with all peripherals
- Manual GPIO verification for camera, ultrasonic sensors (HC-SR04 ×3), LED, and buzzer
- Wiring diagram review against `hardware/wiring.md` and `hardware/gpio_mapping.md`
- Voltage-divider verification for ultrasonic ECHO lines (5 V → 3.3 V)
- Photographic or written test evidence per component
- Logbook entries for each test result

## Out of Scope

- ROS2 node integration or workspace setup
- Object detection or AI model inference
- QNX supervisor or Pi 400 bring-up
- Motor driver (L298N) bring-up (deferred to M2 actuator node)
- Any deterministic decision logic

## Engineering Tasks

- [ ] Assemble Raspberry Pi 5 with camera module
- [ ] Wire three HC-SR04 ultrasonic sensors with voltage dividers
- [ ] Wire LED and buzzer on breadboard
- [ ] Confirm GPIO pin assignments against `hardware/gpio_mapping.md`
- [ ] Test camera: capture a still image and confirm output
- [ ] Test each ultrasonic sensor: measure a known distance and record result
- [ ] Test LED: toggle GPIO and confirm visual output
- [ ] Test buzzer: assert GPIO and confirm audio output
- [ ] Record all results in `docs/logbook.md`
- [ ] Update `hardware/wiring.md` if any wiring deviates from the plan

## Acceptance Criteria

- [ ] Camera captures at least one image without error
- [ ] Each of the three HC-SR04 sensors returns a plausible distance reading (2–400 cm range)
- [ ] Voltage on ultrasonic ECHO lines is confirmed ≤ 3.3 V before connecting to GPIO
- [ ] LED responds to GPIO toggle (on/off confirmed visually)
- [ ] Buzzer responds to GPIO assert (audio confirmed or measured)
- [ ] All GPIO assignments are consistent with `hardware/gpio_mapping.md`
- [ ] Test results are recorded in `docs/logbook.md` with date and outcome
- [ ] No unexplained hardware faults remain open at milestone close

## Related Requirements

- HW-001 (Camera module compatibility)
- HW-002 (Ultrasonic sensor range 2–400 cm)
- HW-003 (Voltage protection on ECHO lines)
- To be linked: LED and buzzer hardware requirements

## Related Documents

- `hardware/wiring.md`
- `hardware/gpio_mapping.md`
- `docs/logbook.md`
- `requirements/interfaces.yaml` (GPIO pin assignments)

## Test Evidence

- Logbook entries with date, component, test procedure, and pass/fail outcome
- Photograph or terminal output for each component test
- Written confirmation that ECHO voltage is within safe limits

## Safety / AI Boundary

- AI agents may assist with wiring review, documentation, and logbook formatting.
- AI agents shall not make hardware decisions or interpret sensor readings as safety-valid inputs.
- No safety decision logic is present in this milestone.
- Physical hardware tests must be performed and verified by the engineer, not inferred by an AI agent.

## Suggested Labels

`hardware` `documentation` `portfolio`

## Suggested Branch Name

`feature/m1-hardware-bringup`

## Suggested Commit Message

```
docs: add M1 hardware bring-up test evidence and logbook entries
```
