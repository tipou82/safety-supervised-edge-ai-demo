// minimal_test.sysml
// Minimal SysML v2 validation file for the Safety-Supervised Edge AI Demonstrator.
// Purpose: test that the SysML v2 Pilot Implementation accepts basic syntax
//          before importing the full architecture.sysml.
//
// Educational demonstrator — not ISO 26262 certified.
// ASIL-B-inspired patterns only. No safety certification claims.

package SafetyDemoMinimal {

    // ── Hardware Part Definitions ─────────────────────────────────────────────

    part def RaspberryPi5 {
        doc /* Main perception processor. Runs Linux/ROS2. */
        attribute os      : String = "Raspberry Pi OS Bookworm";
        attribute ros     : String = "ROS2 Humble (built from source)";
        attribute ram_gb  : Integer = 8;
    }

    part def RaspberryPi400 {
        doc /* Safety supervisor. Runs QNX-inspired deterministic monitor. */
        attribute os       : String = "Ubuntu 22.04 LTS";
        attribute role     : String = "Safety supervisor (QNX-inspired)";
    }

    part def CameraModule3 {
        doc /* Raspberry Pi Camera Module 3. IMX708 sensor. */
        attribute sensor      : String = "IMX708";
        attribute resolution  : String = "4608x2592";
        attribute interface   : String = "CSI ribbon cable";
    }

    part def UltrasonicSensor {
        doc /* Grove Ultrasonic Ranger. Single-wire SIG protocol. */
        attribute model       : String = "Grove Ultrasonic Ranger";
        attribute range_min_m : Real = 0.02;
        attribute range_max_m : Real = 3.50;
        attribute gpio_sig    : Integer = 23;
    }

    part def LedBuzzerOutput {
        doc /* Traffic-light LED module (Green/Yellow/Red) and active buzzer. */
        attribute green_gpio  : Integer = 17;  // NORMAL indicator
        attribute yellow_gpio : Integer = 27;  // DEGRADED indicator
        attribute red_gpio    : Integer = 22;  // SAFE_STATE indicator (diode-OR)
        attribute buzzer_gpio : Integer = 18;
    }

    // ── Top-Level System ──────────────────────────────────────────────────────

    part def SafetySupervisedEdgeAIDemo {
        doc /* Dual-processor ASIL-B-inspired edge AI demonstrator.
                Pi5 handles AI perception. Pi400 handles deterministic safety supervision.
                Educational demonstrator only — not ISO 26262 certified. */

        part pi5       : RaspberryPi5;
        part pi400     : RaspberryPi400;
        part camera    : CameraModule3;
        part ultrasonic: UltrasonicSensor;
        part leds      : LedBuzzerOutput;
    }

    // ── Top-Level Instance ────────────────────────────────────────────────────

    part demo : SafetySupervisedEdgeAIDemo;

}
