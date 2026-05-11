#pragma once
// StateEvaluator — pure deterministic state machine for ASIL-B-inspired supervision.
// No ROS2, no GPIO, no side effects. Callable from unit tests and the ROS2 node.
// Educational demonstrator — not ISO 26262 certified.
//
// Distance thresholds are bench-test assumptions only.
// They are NOT derived from a formal hazard analysis and are NOT safety-validated.
//
// Camera-based distance (camera_distance_m) is AI-derived: it depends on
// MediaPipe bounding box accuracy. Accuracy ±30% — supplementary trigger only.
// It does NOT replace the ultrasonic safety path (SAFE_DISTANCE_M).

#include <cfloat>
#include <cstdint>

inline constexpr float  WARN_DISTANCE_M         = 0.50f;  // ultrasonic WARNING threshold (m)
inline constexpr float  SAFE_DISTANCE_M         = 0.15f;  // ultrasonic SAFE_STATE threshold (m)
inline constexpr float  CAMERA_SAFE_DISTANCE_M  = 0.20f;  // camera hand SAFE_STATE threshold (m)
                                                           // wider margin for lower accuracy
inline constexpr int    WATCHDOG_FAIL_THRESHOLD  = 3;

enum class SystemState : uint8_t {
    INIT       = 0,
    NORMAL     = 1,
    WARNING    = 2,
    DEGRADED   = 3,
    SAFE_STATE = 4,
};

enum class TriggerReason : uint8_t {
    SAFE_STATE_LATCH,        // Rule 1: was SAFE_STATE, no reset
    SAFE_STATE_RESET,        // Rule 1: was SAFE_STATE, reset accepted
    WATCHDOG_FAILURE,        // Rule 3: watchdog_failure_counter >= threshold
    CRITICAL_DISTANCE,       // Rule 3: ultrasonic distance < SAFE_DISTANCE_M
    CAMERA_HAND_CRITICAL,    // Rule 3: camera hand distance < CAMERA_SAFE_DISTANCE_M (AI-derived)
    BOTH_SENSORS_INVALID,    // Rule 3: !camera_valid && !ultrasonic_valid
    NOT_READY,               // Rule 2: !system_ready
    DEGRADED_ONE_SENSOR,     // Rule 4: exactly one sensor path valid
    WARNING_DISTANCE,        // Rule 5: distance < WARN_DISTANCE_M
    NORMAL_FALLBACK,         // Rule 6: all clear
};

inline const char* trigger_name(TriggerReason r) noexcept
{
    switch (r) {
        case TriggerReason::SAFE_STATE_LATCH:      return "safe_state_latch";
        case TriggerReason::SAFE_STATE_RESET:      return "safe_state_reset";
        case TriggerReason::WATCHDOG_FAILURE:      return "watchdog_failure";
        case TriggerReason::CRITICAL_DISTANCE:     return "critical_distance";
        case TriggerReason::CAMERA_HAND_CRITICAL:  return "camera_hand_critical";
        case TriggerReason::BOTH_SENSORS_INVALID:  return "both_sensors_invalid";
        case TriggerReason::NOT_READY:             return "not_ready";
        case TriggerReason::DEGRADED_ONE_SENSOR:   return "degraded_one_sensor";
        case TriggerReason::WARNING_DISTANCE:      return "warning_distance";
        case TriggerReason::NORMAL_FALLBACK:       return "normal_fallback";
        default:                                   return "unknown";
    }
}

struct EvaluatorInput {
    SystemState previous_state           = SystemState::INIT;
    bool        manual_reset_requested   = false;
    bool        system_ready             = false;
    int         watchdog_failure_counter = 0;
    bool        ultrasonic_valid         = false;
    float       distance_m               = 9.9f;
    bool        camera_valid             = false;
    // Camera-estimated hand distance (m). FLT_MAX when no hand detected.
    // AI-derived from MediaPipe bounding box — accuracy ±30%.
    // Supplementary trigger: does NOT replace ultrasonic safety path.
    float       camera_distance_m        = FLT_MAX;
};

struct EvaluatorOutput {
    SystemState   next_state;
    double        velocity_scale;
    TriggerReason trigger;
};

class StateEvaluator {
public:
    [[nodiscard]] EvaluatorOutput evaluate(const EvaluatorInput& input) const noexcept;
    [[nodiscard]] static double   velocity_scale(SystemState state) noexcept;
};
