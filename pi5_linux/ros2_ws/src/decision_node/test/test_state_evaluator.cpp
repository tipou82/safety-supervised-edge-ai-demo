#include <gtest/gtest.h>
#include "decision_node/state_evaluator.hpp"

// Helper: all-clear NORMAL input (both sensors valid, clear distance, system ready)
static EvaluatorInput normal_input()
{
    EvaluatorInput in;
    in.previous_state           = SystemState::NORMAL;
    in.manual_reset_requested   = false;
    in.system_ready             = true;
    in.watchdog_failure_counter = 0;
    in.ultrasonic_valid         = true;
    in.distance_m               = 1.0f;
    in.camera_valid             = true;
    return in;
}

class StateEvaluatorTest : public ::testing::Test {
protected:
    StateEvaluator ev;
};

// ── Velocity scale mapping ────────────────────────────────────────────────────

TEST_F(StateEvaluatorTest, VelocityScaleInit)       { EXPECT_DOUBLE_EQ(StateEvaluator::velocity_scale(SystemState::INIT),       0.0); }
TEST_F(StateEvaluatorTest, VelocityScaleNormal)     { EXPECT_DOUBLE_EQ(StateEvaluator::velocity_scale(SystemState::NORMAL),     1.0); }
TEST_F(StateEvaluatorTest, VelocityScaleWarning)    { EXPECT_DOUBLE_EQ(StateEvaluator::velocity_scale(SystemState::WARNING),    0.5); }
TEST_F(StateEvaluatorTest, VelocityScaleDegraded)   { EXPECT_DOUBLE_EQ(StateEvaluator::velocity_scale(SystemState::DEGRADED),  0.2); }
TEST_F(StateEvaluatorTest, VelocityScaleSafeState)  { EXPECT_DOUBLE_EQ(StateEvaluator::velocity_scale(SystemState::SAFE_STATE),0.0); }

// ── NORMAL fallback ───────────────────────────────────────────────────────────

TEST_F(StateEvaluatorTest, AllClearIsNormal)
{
    auto out = ev.evaluate(normal_input());
    EXPECT_EQ(out.next_state, SystemState::NORMAL);
    EXPECT_DOUBLE_EQ(out.velocity_scale, 1.0);
}

// ── INIT ─────────────────────────────────────────────────────────────────────

TEST_F(StateEvaluatorTest, RemainsInitWhenNotReady)
{
    auto in = normal_input();
    in.previous_state = SystemState::INIT;
    in.system_ready   = false;
    auto out = ev.evaluate(in);
    EXPECT_EQ(out.next_state, SystemState::INIT);
    EXPECT_DOUBLE_EQ(out.velocity_scale, 0.0);
}

TEST_F(StateEvaluatorTest, InitTransitionsToNormalWhenReady)
{
    auto in = normal_input();
    in.previous_state = SystemState::INIT;
    in.system_ready   = true;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::NORMAL);
}

TEST_F(StateEvaluatorTest, InitTriggersSafeStateOnCriticalDistance)
{
    auto in = normal_input();
    in.previous_state = SystemState::INIT;
    in.system_ready   = false;
    in.distance_m     = 0.10f;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

TEST_F(StateEvaluatorTest, InitTriggersSafeStateWhenBothSensorsGone)
{
    auto in = normal_input();
    in.previous_state    = SystemState::INIT;
    in.system_ready      = false;
    in.camera_valid      = false;
    in.ultrasonic_valid  = false;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

// ── SAFE_STATE conditions ─────────────────────────────────────────────────────

TEST_F(StateEvaluatorTest, WatchdogThresholdTriggersSafeState)
{
    auto in = normal_input();
    in.watchdog_failure_counter = WATCHDOG_FAIL_THRESHOLD;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

TEST_F(StateEvaluatorTest, WatchdogBelowThresholdDoesNotTrigger)
{
    auto in = normal_input();
    in.watchdog_failure_counter = WATCHDOG_FAIL_THRESHOLD - 1;
    EXPECT_NE(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

TEST_F(StateEvaluatorTest, CriticalDistanceTriggersSafeState)
{
    auto in = normal_input();
    in.distance_m = 0.10f;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

TEST_F(StateEvaluatorTest, BothSensorsInvalidTriggersSafeState)
{
    auto in = normal_input();
    in.camera_valid     = false;
    in.ultrasonic_valid = false;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

TEST_F(StateEvaluatorTest, CriticalDistanceBoundaryExact_NotTriggered)
{
    // distance_m == SAFE_DISTANCE_M is NOT a trigger (condition is strictly <)
    auto in = normal_input();
    in.distance_m = SAFE_DISTANCE_M;
    EXPECT_NE(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

TEST_F(StateEvaluatorTest, CriticalDistanceBoundaryJustBelow_Triggered)
{
    auto in = normal_input();
    in.distance_m = SAFE_DISTANCE_M - 0.001f;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

TEST_F(StateEvaluatorTest, InvalidUltrasonicDoesNotTriggerCriticalDistance)
{
    // distance < SAFE threshold but ultrasonic_valid == false → not triggered
    auto in = normal_input();
    in.ultrasonic_valid = false;
    in.distance_m       = 0.05f;
    in.camera_valid     = true;   // camera still valid → DEGRADED, not SAFE_STATE
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::DEGRADED);
}

// ── SAFE_STATE latching ───────────────────────────────────────────────────────

TEST_F(StateEvaluatorTest, SafeStateLatchesWithoutReset)
{
    auto in = normal_input();
    in.previous_state           = SystemState::SAFE_STATE;
    in.manual_reset_requested   = false;
    auto out = ev.evaluate(in);
    EXPECT_EQ(out.next_state, SystemState::SAFE_STATE);
    EXPECT_DOUBLE_EQ(out.velocity_scale, 0.0);
}

TEST_F(StateEvaluatorTest, SafeStateExitsToInitOnManualReset)
{
    auto in = normal_input();
    in.previous_state           = SystemState::SAFE_STATE;
    in.manual_reset_requested   = true;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::INIT);
}

TEST_F(StateEvaluatorTest, SafeStateDoesNotExitIfConditionStillActive)
{
    auto in = normal_input();
    in.previous_state           = SystemState::SAFE_STATE;
    in.manual_reset_requested   = true;
    in.distance_m               = 0.05f;   // critical condition still active
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

TEST_F(StateEvaluatorTest, SafeStateDoesNotExitIfWatchdogStillFailing)
{
    auto in = normal_input();
    in.previous_state           = SystemState::SAFE_STATE;
    in.manual_reset_requested   = true;
    in.watchdog_failure_counter = WATCHDOG_FAIL_THRESHOLD;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

// ── DEGRADED ─────────────────────────────────────────────────────────────────

TEST_F(StateEvaluatorTest, CameraInvalidUltrasonicValidIsDegraded)
{
    auto in = normal_input();
    in.camera_valid     = false;
    in.ultrasonic_valid = true;
    in.distance_m       = 1.0f;
    auto out = ev.evaluate(in);
    EXPECT_EQ(out.next_state, SystemState::DEGRADED);
    EXPECT_DOUBLE_EQ(out.velocity_scale, 0.2);
}

TEST_F(StateEvaluatorTest, CameraValidUltrasonicInvalidIsDegraded)
{
    auto in = normal_input();
    in.camera_valid     = true;
    in.ultrasonic_valid = false;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::DEGRADED);
}

// ── WARNING ───────────────────────────────────────────────────────────────────

TEST_F(StateEvaluatorTest, DistanceBelowWarnThresholdIsWarning)
{
    auto in = normal_input();
    in.distance_m = 0.49f;
    auto out = ev.evaluate(in);
    EXPECT_EQ(out.next_state, SystemState::WARNING);
    EXPECT_DOUBLE_EQ(out.velocity_scale, 0.5);
}

TEST_F(StateEvaluatorTest, DistanceAtWarnThresholdIsNotWarning)
{
    // distance_m == WARN_DISTANCE_M is NOT a trigger (condition is strictly <)
    auto in = normal_input();
    in.distance_m = WARN_DISTANCE_M;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::NORMAL);
}

TEST_F(StateEvaluatorTest, DistanceJustBelowWarnThreshold_Triggered)
{
    auto in = normal_input();
    in.distance_m = WARN_DISTANCE_M - 0.001f;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::WARNING);
}

TEST_F(StateEvaluatorTest, InvalidUltrasonicDoesNotTriggerWarning)
{
    auto in = normal_input();
    in.ultrasonic_valid = false;
    in.distance_m       = 0.30f;
    in.camera_valid     = true;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::DEGRADED);
}

// ── Rule priority: SAFE_STATE > DEGRADED ─────────────────────────────────────

TEST_F(StateEvaluatorTest, CriticalDistanceTakesPriorityOverDegraded)
{
    auto in = normal_input();
    in.camera_valid     = false;   // would be DEGRADED
    in.ultrasonic_valid = true;
    in.distance_m       = 0.05f;   // but critical distance → SAFE_STATE
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

// ── Rule priority: SAFE_STATE > WARNING ──────────────────────────────────────

TEST_F(StateEvaluatorTest, CriticalDistanceTakesPriorityOverWarning)
{
    auto in = normal_input();
    in.distance_m = 0.05f;  // < SAFE (0.15) → SAFE_STATE, not WARNING
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

int main(int argc, char** argv)
{
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

// ── Camera hand distance (supplementary AI-derived trigger) ───────────────────

TEST_F(StateEvaluatorTest, CameraHandCritical_TriggersSafeState)
{
    auto in = normal_input();
    in.camera_distance_m = CAMERA_SAFE_DISTANCE_M - 0.01f;  // 0.19m < 0.20m
    auto out = ev.evaluate(in);
    EXPECT_EQ(out.next_state, SystemState::SAFE_STATE);
    EXPECT_EQ(out.trigger,    TriggerReason::CAMERA_HAND_CRITICAL);
}

TEST_F(StateEvaluatorTest, CameraHandAtThreshold_NotTriggered)
{
    // Strictly < threshold required
    auto in = normal_input();
    in.camera_distance_m = CAMERA_SAFE_DISTANCE_M;  // exactly 0.20m — not triggered
    EXPECT_NE(ev.evaluate(in).next_state, SystemState::SAFE_STATE);
}

TEST_F(StateEvaluatorTest, CameraHandCritical_RequiresCameraValid)
{
    // camera_valid=false — camera distance must NOT trigger SAFE_STATE
    auto in = normal_input();
    in.camera_valid      = false;
    in.camera_distance_m = 0.05f;   // very close but camera invalid
    in.ultrasonic_valid  = true;    // keep one sensor valid (→ DEGRADED, not SAFE_STATE)
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::DEGRADED);
}

TEST_F(StateEvaluatorTest, CameraHandFarAway_NoTrigger)
{
    auto in = normal_input();
    in.camera_distance_m = 1.0f;   // 1m — no trigger
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::NORMAL);
}

TEST_F(StateEvaluatorTest, CameraHandNoHand_NoTrigger)
{
    // FLT_MAX = no hand detected
    auto in = normal_input();
    in.camera_distance_m = FLT_MAX;
    EXPECT_EQ(ev.evaluate(in).next_state, SystemState::NORMAL);
}

TEST_F(StateEvaluatorTest, UltrasonicCritical_TakesPriorityOverCameraHand)
{
    // Both ultrasonic < 0.15m AND camera < 0.20m — ultrasonic fires first
    auto in = normal_input();
    in.distance_m        = 0.10f;
    in.camera_distance_m = 0.15f;
    auto out = ev.evaluate(in);
    EXPECT_EQ(out.next_state, SystemState::SAFE_STATE);
    EXPECT_EQ(out.trigger,    TriggerReason::CRITICAL_DISTANCE);
}
