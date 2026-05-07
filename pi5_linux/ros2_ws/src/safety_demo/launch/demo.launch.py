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
        Node(
            package='camera_ai_node',
            executable='camera_ai_node',
            name='camera_ai_node',
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
