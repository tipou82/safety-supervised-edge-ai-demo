cmake_minimum_required(VERSION 3.20)
project(decision_node CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(diagnostic_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# StateEvaluator — pure logic library, no ROS2 dependencies
add_library(state_evaluator src/state_evaluator.cpp)
target_include_directories(state_evaluator PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)

# decision_node executable
add_executable(decision_node src/decision_node.cpp)
target_link_libraries(decision_node state_evaluator)
ament_target_dependencies(decision_node
  rclcpp sensor_msgs geometry_msgs diagnostic_msgs std_msgs)

install(TARGETS decision_node DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY include/ DESTINATION include)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(test_state_evaluator test/test_state_evaluator.cpp)
  target_link_libraries(test_state_evaluator state_evaluator)
endif()

ament_package()
