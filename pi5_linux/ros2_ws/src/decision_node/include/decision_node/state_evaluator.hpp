#pragma once
// StateEvaluator — pure deterministic state machine for ASIL-B-inspired supervision.
// No ROS2, no GPIO, no side effects. Callable from unit tests and the ROS2 node.
// Educational demonstrator — not ISO 26262 certified.
//
// Distance thresholds are bench-test assumptions only.
// They are NOT derived from a formal hazard analysis and are NOT safety-validated.

#include <cstdint>

inline constexpr float  WARN_DISTANCE_M       = 0.50f;  // WARNING threshold (m)
inline constexpr float  SAFE_DISTANCE_M       = 0.15f;  // SAFE_STATE critical threshold (m)
inline constexpr int    WATCHDOG_FAIL_THRESHOLD = 3;     // Pi400 Q&A failure counter limit

enum class SystemState : uint8_t {
    INIT       = 0,
    NORMAL     = 1,
    WARNING    = 2,
    DEGRADED   = 3,
    SAFE_STATE = 4,
};

struct EvaluatorInput {
    SystemState previous_state           = SystemState::INIT;
    bool        manual_reset_requested   = false;
    bool        system_ready             = false;
    // Pi400 Q&A watchdog server-side failure counter.
    // Wired to Pi400 supervisor in M5; always 0 in M3.
    int         watchdog_failure_counter = 0;
    bool        ultrasonic_valid         = false;
    float       distance_m               = 9.9f;
    bool        camera_valid             = false;
};

struct EvaluatorOutput {
    SystemState next_state;
    double      velocity_scale;
};

class StateEvaluator {
public:
    // Pure function — deterministic, no side effects.
    [[nodiscard]] EvaluatorOutput evaluate(const EvaluatorInput& input) const noexcept;

    // Deterministic velocity scale lookup.
    // INIT=0.0  NORMAL=1.0  WARNING=0.5  DEGRADED=0.2  SAFE_STATE=0.0
    [[nodiscard]] static double velocity_scale(SystemState state) noexcept;
};
