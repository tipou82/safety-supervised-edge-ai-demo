#pragma once
// StateEvaluator — pure deterministic state machine for ASIL-B-inspired supervision.
// No ROS2, no GPIO, no side effects. Callable from unit tests and the ROS2 node.
// Educational demonstrator — not ISO 26262 certified.
//
// Distance thresholds are bench-test assumptions only.
// They are NOT derived from a formal hazard analysis and are NOT safety-validated.

#include <cstdint>

inline constexpr float  WARN_DISTANCE_M        = 0.50f;  // WARNING threshold (m)
inline constexpr float  SAFE_DISTANCE_M        = 0.15f;  // SAFE_STATE critical threshold (m)
inline constexpr int    WATCHDOG_FAIL_THRESHOLD = 3;      // Pi400 Q&A failure counter limit

enum class SystemState : uint8_t {
    INIT       = 0,
    NORMAL     = 1,
    WARNING    = 2,
    DEGRADED   = 3,
    SAFE_STATE = 4,
};

// Reason the StateEvaluator chose the returned next_state.
// Used for diagnostics — does not affect the safety decision path.
enum class TriggerReason : uint8_t {
    SAFE_STATE_LATCH,        // Rule 1: was SAFE_STATE, no reset
    SAFE_STATE_RESET,        // Rule 1: was SAFE_STATE, reset accepted
    WATCHDOG_FAILURE,        // Rule 3: watchdog_failure_counter >= threshold
    CRITICAL_DISTANCE,       // Rule 3: ultrasonic distance < SAFE_DISTANCE_M
    BOTH_SENSORS_INVALID,    // Rule 3: !camera_valid && !ultrasonic_valid
    NOT_READY,               // Rule 2: !system_ready
    DEGRADED_ONE_SENSOR,     // Rule 4: exactly one sensor path valid
    WARNING_DISTANCE,        // Rule 5: distance < WARN_DISTANCE_M
    NORMAL_FALLBACK,         // Rule 6: all clear
};

// Human-readable name for a TriggerReason — for diagnostics and logging only.
inline const char* trigger_name(TriggerReason r) noexcept
{
    switch (r) {
        case TriggerReason::SAFE_STATE_LATCH:     return "safe_state_latch";
        case TriggerReason::SAFE_STATE_RESET:     return "safe_state_reset";
        case TriggerReason::WATCHDOG_FAILURE:     return "watchdog_failure";
        case TriggerReason::CRITICAL_DISTANCE:    return "critical_distance";
        case TriggerReason::BOTH_SENSORS_INVALID: return "both_sensors_invalid";
        case TriggerReason::NOT_READY:            return "not_ready";
        case TriggerReason::DEGRADED_ONE_SENSOR:  return "degraded_one_sensor";
        case TriggerReason::WARNING_DISTANCE:     return "warning_distance";
        case TriggerReason::NORMAL_FALLBACK:      return "normal_fallback";
        default:                                  return "unknown";
    }
}

struct EvaluatorInput {
    SystemState previous_state           = SystemState::INIT;
    bool        manual_reset_requested   = false;
    bool        system_ready             = false;
    // Pi400 Q&A watchdog server-side failure counter.
    // Wired to Pi400 supervisor in M5; always 0 in M4.
    int         watchdog_failure_counter = 0;
    bool        ultrasonic_valid         = false;
    float       distance_m               = 9.9f;
    bool        camera_valid             = false;
};

struct EvaluatorOutput {
    SystemState   next_state;
    double        velocity_scale;
    TriggerReason trigger;      // which rule fired — for diagnostics only
};

class StateEvaluator {
public:
    // Pure function — deterministic, no side effects.
    [[nodiscard]] EvaluatorOutput evaluate(const EvaluatorInput& input) const noexcept;

    // Deterministic velocity scale lookup.
    // INIT=0.0  NORMAL=1.0  WARNING=0.5  DEGRADED=0.2  SAFE_STATE=0.0
    [[nodiscard]] static double velocity_scale(SystemState state) noexcept;
};
