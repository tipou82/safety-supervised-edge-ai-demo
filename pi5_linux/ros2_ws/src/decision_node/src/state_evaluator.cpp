#include "decision_node/state_evaluator.hpp"

EvaluatorOutput StateEvaluator::evaluate(const EvaluatorInput& in) const noexcept
{
    auto out = [](SystemState s, TriggerReason t) -> EvaluatorOutput {
        return {s, velocity_scale(s), t};
    };

    // ── Rule 1: SAFE_STATE latching ──────────────────────────────────────────
    if (in.previous_state == SystemState::SAFE_STATE) {
        const bool all_clear =
            (in.watchdog_failure_counter < WATCHDOG_FAIL_THRESHOLD) &&
            !(in.ultrasonic_valid && in.distance_m < SAFE_DISTANCE_M) &&
            (in.camera_valid || in.ultrasonic_valid);
        return (in.manual_reset_requested && all_clear)
            ? out(SystemState::INIT,       TriggerReason::SAFE_STATE_RESET)
            : out(SystemState::SAFE_STATE, TriggerReason::SAFE_STATE_LATCH);
    }

    // ── Rule 3: SAFE_STATE conditions ────────────────────────────────────────
    if (in.watchdog_failure_counter >= WATCHDOG_FAIL_THRESHOLD)
        return out(SystemState::SAFE_STATE, TriggerReason::WATCHDOG_FAILURE);

    if (in.ultrasonic_valid && in.distance_m < SAFE_DISTANCE_M)
        return out(SystemState::SAFE_STATE, TriggerReason::CRITICAL_DISTANCE);

    if (!in.camera_valid && !in.ultrasonic_valid)
        return out(SystemState::SAFE_STATE, TriggerReason::BOTH_SENSORS_INVALID);

    // ── Rule 2: INIT ─────────────────────────────────────────────────────────
    if (!in.system_ready)
        return out(SystemState::INIT, TriggerReason::NOT_READY);

    // ── Rule 4: DEGRADED ─────────────────────────────────────────────────────
    if ((!in.camera_valid && in.ultrasonic_valid) ||
        (in.camera_valid  && !in.ultrasonic_valid))
        return out(SystemState::DEGRADED, TriggerReason::DEGRADED_ONE_SENSOR);

    // ── Rule 5: WARNING ───────────────────────────────────────────────────────
    if (in.ultrasonic_valid && in.distance_m < WARN_DISTANCE_M)
        return out(SystemState::WARNING, TriggerReason::WARNING_DISTANCE);

    // ── Rule 6: NORMAL fallback ───────────────────────────────────────────────
    return out(SystemState::NORMAL, TriggerReason::NORMAL_FALLBACK);
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
