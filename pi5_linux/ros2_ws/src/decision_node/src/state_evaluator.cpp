#include "decision_node/state_evaluator.hpp"

EvaluatorOutput StateEvaluator::evaluate(const EvaluatorInput& in) const noexcept
{
    // ── Rule 1: SAFE_STATE latching ──────────────────────────────────────────
    // Highest priority. SAFE_STATE can only be exited by an explicit manual
    // reset when all triggering conditions are cleared.
    if (in.previous_state == SystemState::SAFE_STATE) {
        const bool all_clear =
            (in.watchdog_failure_counter < WATCHDOG_FAIL_THRESHOLD) &&
            !(in.ultrasonic_valid && in.distance_m < SAFE_DISTANCE_M) &&
            (in.camera_valid || in.ultrasonic_valid);
        const auto next = (in.manual_reset_requested && all_clear)
                          ? SystemState::INIT
                          : SystemState::SAFE_STATE;
        return {next, velocity_scale(next)};
    }

    // ── Rule 3: SAFE_STATE conditions ────────────────────────────────────────
    // Evaluated before system_ready check so that critical faults from INIT
    // are captured (Rule 2: "remain INIT unless a higher-priority condition").
    const bool safe_triggered =
        (in.watchdog_failure_counter >= WATCHDOG_FAIL_THRESHOLD) ||
        (in.ultrasonic_valid && in.distance_m < SAFE_DISTANCE_M) ||
        (!in.camera_valid && !in.ultrasonic_valid);
    if (safe_triggered) {
        return {SystemState::SAFE_STATE, velocity_scale(SystemState::SAFE_STATE)};
    }

    // ── Rule 2: INIT — remain until system is ready ───────────────────────────
    if (!in.system_ready) {
        return {SystemState::INIT, velocity_scale(SystemState::INIT)};
    }

    // ── Rule 4: DEGRADED — exactly one sensor path valid ─────────────────────
    const bool degraded =
        (!in.camera_valid && in.ultrasonic_valid) ||
        (in.camera_valid && !in.ultrasonic_valid);
    if (degraded) {
        return {SystemState::DEGRADED, velocity_scale(SystemState::DEGRADED)};
    }

    // ── Rule 5: WARNING — obstacle within warning distance ───────────────────
    if (in.ultrasonic_valid && in.distance_m < WARN_DISTANCE_M) {
        return {SystemState::WARNING, velocity_scale(SystemState::WARNING)};
    }

    // ── Rule 6: NORMAL fallback ───────────────────────────────────────────────
    return {SystemState::NORMAL, velocity_scale(SystemState::NORMAL)};
}

double StateEvaluator::velocity_scale(SystemState state) noexcept
{
    switch (state) {
        case SystemState::NORMAL:     return 1.0;
        case SystemState::WARNING:    return 0.5;
        case SystemState::DEGRADED:   return 0.2;
        case SystemState::INIT:       [[fallthrough]];
        case SystemState::SAFE_STATE: [[fallthrough]];
        default:                      return 0.0;
    }
}
