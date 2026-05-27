#!/usr/bin/env python3
"""
test_motor_direct.py — DRV8833 Hardware-Direkttest (KEIN ROS2 nötig)

Testet DRV8833 IN1/IN2 direkt über GPIO 12 und 16.
Voraussetzungen:
  - DRV8833 verdrahtet: GPIO 12 → IN1, GPIO 16 → IN2
  - GND gemeinsam: Pi5 Pin 34 → DRV8833 GND → 4xAA Batterie (-)
  - Motor Switch (4xAA Batteriebox) eingeschaltet
  - Auf Pi5 ausführen: python3 tests/manual/test_motor_direct.py

Installation lgpio (falls fehlt):
  sudo apt install python3-lgpio
  # oder: pip3 install lgpio
"""

import lgpio
import time
import sys

GPIO_IN1 = 12   # Physical Pin 32 → DRV8833 IN1
GPIO_IN2 = 16   # Physical Pin 36 → DRV8833 IN2

def cleanup(h):
    lgpio.gpio_write(h, GPIO_IN1, 0)
    lgpio.gpio_write(h, GPIO_IN2, 0)
    lgpio.gpiochip_close(h)

def main():
    print("=== DRV8833 Motor-Direkttest ===")
    print(f"GPIO {GPIO_IN1} (Pin 32) → IN1")
    print(f"GPIO {GPIO_IN2} (Pin 36) → IN2")
    print("Motor Switch (4xAA) muss eingeschaltet sein!\n")

    try:
        h = lgpio.gpiochip_open(0)
    except Exception as e:
        print(f"FEHLER: GPIO konnte nicht geöffnet werden: {e}")
        print("Tipp: sudo python3 test_motor_direct.py")
        sys.exit(1)

    lgpio.gpio_claim_output(h, GPIO_IN1, 0)
    lgpio.gpio_claim_output(h, GPIO_IN2, 0)

    try:
        # --- Test 1: Vorwärts ---
        print("Test 1: Vorwärts 3 Sekunden (IN1=HIGH, IN2=LOW)")
        lgpio.gpio_write(h, GPIO_IN1, 1)
        lgpio.gpio_write(h, GPIO_IN2, 0)
        time.sleep(3)

        # --- Stopp ---
        print("Stopp 1 Sekunde...")
        lgpio.gpio_write(h, GPIO_IN1, 0)
        lgpio.gpio_write(h, GPIO_IN2, 0)
        time.sleep(1)

        # --- Test 2: Rückwärts ---
        print("Test 2: Rückwärts 3 Sekunden (IN1=LOW, IN2=HIGH)")
        lgpio.gpio_write(h, GPIO_IN1, 0)
        lgpio.gpio_write(h, GPIO_IN2, 1)
        time.sleep(3)

        # --- Stopp ---
        print("Stopp...")
        lgpio.gpio_write(h, GPIO_IN1, 0)
        lgpio.gpio_write(h, GPIO_IN2, 0)
        time.sleep(1)

        # --- Test 3: Software-PWM vorwärts ---
        print("Test 3: Software-PWM Vorwärts (50% Geschwindigkeit, 3 Sekunden)")
        FREQ = 1000   # Hz
        DUTY = 50     # %
        lgpio.tx_pwm(h, GPIO_IN1, FREQ, DUTY)
        lgpio.gpio_write(h, GPIO_IN2, 0)
        time.sleep(3)

        print("Stopp...")
        lgpio.tx_pwm(h, GPIO_IN1, 0, 0)
        lgpio.gpio_write(h, GPIO_IN1, 0)
        lgpio.gpio_write(h, GPIO_IN2, 0)

        print("\n✓ Alle Tests abgeschlossen.")
        print("  Motor dreht? → Hardware OK.")
        print("  Motor dreht nicht? → GND, EEP-Pin oder Motor Switch prüfen.")

    except KeyboardInterrupt:
        print("\nAbgebrochen.")
    finally:
        cleanup(h)
        print("GPIO freigegeben.")

if __name__ == "__main__":
    main()
