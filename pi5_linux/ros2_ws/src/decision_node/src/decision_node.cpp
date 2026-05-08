#include <chrono>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/range.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "diagnostic_msgs/msg/diagnostic_array.hpp"
#include "std_msgs/msg/bool.hpp"
#include "std_msgs/msg/string.hpp"

#include "decision_node/state_evaluator.hpp"

using namespace std::chrono_literals;

static const char* state_name(SystemState s)
{
    switch (s) {
        case SystemState::INIT:       return "INIT";
        case SystemState::NORMAL:     return "NORMAL";
        case SystemState::WARNING:    return "WARNING";
        case SystemState::DEGRADED:   return "DEGRADED";
        case SystemState::SAFE_STATE: return "SAFE_STATE";
        default:                      return "UNKNOWN";
    }
}

class DecisionNode : public rclcpp::Node
{
public:
    DecisionNode()
    : Node("decision_node"),
      current_state_(SystemState::INIT)
    {
        // Publishers
        cmd_vel_pub_   = create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 1);
        sys_state_pub_ = create_publisher<std_msgs::msg::String>("/system_state", 5);

        // Subscriptions
        obstacles_sub_ = create_subscription<sensor_msgs::msg::Range>(
            "/obstacles", 5,
            [this](sensor_msgs::msg::Range::SharedPtr msg) { on_obstacles(msg); });

        health_sub_ = create_subscription<diagnostic_msgs::msg::DiagnosticArray>(
            "/system_health", 5,
            [this](diagnostic_msgs::msg::DiagnosticArray::SharedPtr msg) { on_health(msg); });

        reset_sub_ = create_subscription<std_msgs::msg::Bool>(
            "/reset", 1,
            [this](std_msgs::msg::Bool::SharedPtr msg) {
                if (msg->data) pending_reset_ = true;
            });

        // /detections liveness — placeholder subscription (M3+).
        // camera_ai_node does not publish in M3; camera_valid stays false until M4.
        // In M4: change std_msgs/String to vision_msgs/Detection2DArray.
        detections_sub_ = create_subscription<std_msgs::msg::String>(
            "/detections", 5,
            [this](std_msgs::msg::String::SharedPtr) {
                last_detection_time_ = now();
                if (!camera_valid_) {
                    camera_valid_ = true;
                    RCLCPP_INFO(get_logger(), "camera_valid — /detections active");
                }
            });

        // 50 Hz evaluation + publish timer — increased from 20 Hz for SYS-SAFE-011 proximity FTTI
        timer_ = create_wall_timer(20ms, [this]() { tick(); });

        RCLCPP_INFO(get_logger(), "decision_node started — StateEvaluator C++20");
        RCLCPP_INFO(get_logger(),
            "camera_valid wired to /detections (2s timeout); watchdog_failure_counter=0 (M5)");
    }

private:
    void on_obstacles(const sensor_msgs::msg::Range::SharedPtr& msg)
    {
        last_obstacle_time_ = now();
        if (std::isfinite(msg->range) &&
            msg->range >= msg->min_range && msg->range <= msg->max_range) {
            distance_m_       = msg->range;
            ultrasonic_valid_ = true;
        } else {
            ultrasonic_valid_ = false;
        }
        if (!system_ready_) {
            system_ready_ = true;
            RCLCPP_INFO(get_logger(), "system_ready — first valid ultrasonic reading");
        }
    }

    void on_health(const diagnostic_msgs::msg::DiagnosticArray::SharedPtr& /*msg*/)
    {
        // watchdog_failure_counter deferred to M5 (Pi400 slave not yet implemented)
    }

    void tick()
    {
        // Expire ultrasonic if no message received within 1 s
        if (ultrasonic_valid_) {
            if ((now() - last_obstacle_time_).seconds() > 1.0) {
                ultrasonic_valid_ = false;
                RCLCPP_WARN(get_logger(), "Ultrasonic timeout — marking invalid");
            }
        }

        // Expire camera_valid if no /detections received within 2 s
        if (camera_valid_) {
            if ((now() - last_detection_time_).seconds() > 2.0) {
                camera_valid_ = false;
                RCLCPP_WARN(get_logger(), "Camera timeout — marking invalid");
            }
        }

        EvaluatorInput input;
        input.previous_state           = current_state_;
        input.manual_reset_requested   = pending_reset_;
        input.system_ready             = system_ready_;
        input.watchdog_failure_counter = 0;   // TODO M5: subscribe to Pi400 counter
        input.ultrasonic_valid         = ultrasonic_valid_;
        input.distance_m               = distance_m_;
        input.camera_valid             = camera_valid_;

        pending_reset_ = false;

        auto output = evaluator_.evaluate(input);

        if (output.next_state != current_state_) {
            RCLCPP_INFO(get_logger(), "State: %s → %s  (vel_scale=%.1f)",
                state_name(current_state_),
                state_name(output.next_state),
                output.velocity_scale);
            current_state_ = output.next_state;
        }

        // Publish scaled velocity (base motion deferred — publishes zero for now)
        geometry_msgs::msg::Twist cmd;
        cmd.linear.x  = 0.0 * output.velocity_scale;
        cmd.angular.z = 0.0 * output.velocity_scale;
        cmd_vel_pub_->publish(cmd);

        // Publish state string for observability
        std_msgs::msg::String state_msg;
        state_msg.data = state_name(output.next_state);
        sys_state_pub_->publish(state_msg);
    }

    StateEvaluator  evaluator_;
    SystemState     current_state_;

    bool   system_ready_     = false;
    bool   ultrasonic_valid_ = false;
    float  distance_m_       = 9.9f;
    bool   camera_valid_     = false;
    bool   pending_reset_    = false;

    rclcpp::Time last_obstacle_time_{0, 0, RCL_ROS_TIME};
    rclcpp::Time last_detection_time_{0, 0, RCL_ROS_TIME};

    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr    cmd_vel_pub_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr        sys_state_pub_;
    rclcpp::Subscription<sensor_msgs::msg::Range>::SharedPtr   obstacles_sub_;
    rclcpp::Subscription<diagnostic_msgs::msg::DiagnosticArray>::SharedPtr health_sub_;
    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr       reset_sub_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr     detections_sub_;
    rclcpp::TimerBase::SharedPtr                               timer_;
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<DecisionNode>());
    rclcpp::shutdown();
    return 0;
}
