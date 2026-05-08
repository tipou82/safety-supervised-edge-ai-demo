from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='health_node',
            executable='health_node',
            name='health_node',
            output='screen',
        ),
        Node(
            package='ultrasonic_node',
            executable='ultrasonic_node',
            name='ultrasonic_node',
            output='screen',
        ),
        # M7 Spatial FFI: camera AI split into two MMU-isolated processes
        Node(
            package='hand_detection_node',
            executable='hand_detection_node',
            name='hand_detection_node',
            output='screen',
        ),
        Node(
            package='object_detection_node',
            executable='object_detection_node',
            name='object_detection_node',
            output='screen',
        ),
        Node(
            package='decision_node',
            executable='decision_node',
            name='decision_node',
            output='screen',
        ),
        Node(
            package='actuator_node',
            executable='actuator_node',
            name='actuator_node',
            output='screen',
        ),
    ])
