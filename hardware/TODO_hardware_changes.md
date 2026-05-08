# Hardware Change TODO — M2 Wiring Changes

**Status**: Pending physical implementation
**Baseline**: M1.1 bring-up wiring (2026-05-07, all tests PASS)
**Target**: M2 Q&A watchdog + wired-OR red LED architecture

---

## Changes Required

### 1. Add I2C Wiring (Q&A Watchdog Bus)

| Action | Detail |
|---|---|
| Wire | Pi5 GPIO 2 (Pin 3) ↔ Pi400 GPIO 2 (Pin 3) — SDA |
| Wire | Pi5 GPIO 3 (Pin 5) ↔ Pi400 GPIO 3 (Pin 5) — SCL |
| Wire | Pi5 GND (Pin 6) ↔ Pi400 GND (Pin 6) — common ground |
| Add resistor | 4.7 kΩ from SDA line to 3.3V (use Pi5 Pin 1 or 17) |
| Add resistor | 4.7 kΩ from SCL line to 3.3V |

**Notes**:
- Use the breadboard for pull-up resistors.
- Keep I2C wires short (<20 cm) to minimize noise.
- Verify with `i2cdetect -y 1` on Pi5 after wiring (should show `0x40`).

### 2. Add Emergency Stop GPIO Wire

| Action | Detail |
|---|---|
| Wire | Pi400 GPIO 25 (Pin 22) → Pi5 GPIO 25 (Pin 22) |
| Verify | GND already shared from I2C common ground wire above |

**Notes**:
- Pi400 GPIO 25 is active-low output; Pi5 GPIO 25 is input with internal pull-up.
- Pi400 asserts LOW at boot; Pi5 should read LOW before supervisor releases.
- Old e-stop wiring (if any was installed) can be removed — there was no e-stop wire in M1.1.

### 3. Modify Red LED Circuit (Wired-OR)

The red LED was previously driven by Pi5 GPIO 22 alone with a 330 Ω resistor.
Change to a diode-OR circuit so both Pi5 and Pi400 can independently assert it.

| Action | Detail |
|---|---|
| Remove | 330 Ω resistor from Pi5 GPIO 22 to red LED anode |
| Add | 150 Ω resistor + 1N4148 diode in series: Pi5 GPIO 22 → 150 Ω → D1 (1N4148) → red LED anode |
| Add | 150 Ω resistor + 1N4148 diode in series: Pi400 GPIO 22 (Pin 15) → 150 Ω → D2 (1N4148) → red LED anode |
| New wire | Pi400 GPIO 22 (Pin 15) → breadboard (diode D2 and 150 Ω) |

**Diode orientation**: Anode toward GPIO/resistor, cathode toward LED anode.

**Why 150 Ω instead of 330 Ω**: Diode Vf ≈ 0.7V drops available voltage.
- With 150 Ω: (3.3V − 0.7V − 2.0V) / 150 Ω ≈ 4 mA — visible brightness.
- With 330 Ω: ≈ 1.8 mA — too dim.

### 4. No Change Required

| Item | Status |
|---|---|
| Green LED (GPIO 17, Pin 11) | No change — 330 Ω and wiring unchanged |
| Yellow LED (GPIO 27, Pin 13) | No change — 330 Ω and wiring unchanged |
| Buzzer (GPIO 18, Pin 12) | No change |
| Ultrasonic SIG (GPIO 23, Pin 16) | No change |
| Camera CSI ribbon cable | No change |
| Ethernet Pi5 ↔ Pi400 | No change |

---

## M5 Update: I2C wires no longer required for watchdog

DD-002 Option B selected (UDP over Ethernet). BCM2711 BSC slave not
supported by pigpio. The I2C wires (GPIO 2/3) can be removed.
GPIO 25 (e-stop) and GPIO 22 (red LED) wires remain in place.

## Summary Checklist

- [x] ~~I2C SDA wire: Pi5 Pin 3 ↔ Pi400 Pin 3~~ — removed (UDP replaces I2C for watchdog)
- [x] ~~I2C SCL wire: Pi5 Pin 5 ↔ Pi400 Pin 5~~ — removed
- [x] ~~4.7 kΩ pull-up on SDA to 3.3V~~ — removed
- [x] ~~4.7 kΩ pull-up on SCL to 3.3V~~ — removed
- [ ] Common GND wire confirmed (Pi5 Pin 6 ↔ Pi400 Pin 6)
- [ ] E-stop wire: Pi400 GPIO 25 (Pin 22) → Pi5 GPIO 25 (Pin 22)
- [ ] Red LED: remove old 330 Ω resistor
- [ ] Red LED: add D1 (1N4148) + 150 Ω on Pi5 GPIO 22 leg
- [ ] Red LED: add D2 (1N4148) + 150 Ω on Pi400 GPIO 22 leg
- [ ] Red LED: add wire from Pi400 GPIO 22 (Pin 15) to breadboard
- [ ] Verify I2C: `i2cdetect -y 1` on Pi5 shows 0x40
- [ ] Verify e-stop: Pi5 GPIO 25 reads LOW before supervisor releases
- [ ] Verify red LED: both Pi5 and Pi400 can independently illuminate it
- [ ] Re-run M1.1 LED test after circuit change to confirm correct brightness

---

*Created: 2026-05-08*
*Author: Yunpeng*
*Reference: gpio_mapping.md, wiring.md*
