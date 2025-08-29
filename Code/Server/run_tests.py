#!/usr/bin/env python3
"""
Comprehensive Test Suite for Freenove Tank Robot

This script provides a unified interface for running all tests for the robot components.
It includes both unit tests for individual components and integration tests.

Note: Some tests require a Raspberry Pi with specific hardware. These tests will be
skipped when not running on a Raspberry Pi.
"""

import argparse
import importlib
import platform
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Type, Any, Callable, Optional

# Check if running on Raspberry Pi
IS_RASPBERRY_PI = platform.machine().startswith('arm')

if not IS_RASPBERRY_PI:
    print("\n" + "!" * 80)
    print("WARNING: Not running on a Raspberry Pi.")
    print("Hardware-dependent tests will be skipped or run in simulation mode.")
    print("Run this on a Raspberry Pi with the required hardware for full testing.")
    print("!" * 80 + "\n")

# Test result statuses
PASS = "✅"  # Green checkmark
FAIL = "❌"  # Red X
SKIP = "⏸"  # Skip symbol

@dataclass
class TestResult:
    """Container for test results."""
    name: str
    status: str
    message: str = ""
    duration: float = 0.0

def run_test(test_func: Callable, test_name: str, requires_pi: bool = False) -> TestResult:
    """Run a single test and return the result."""
    start_time = time.time()
    
    # Skip tests that require Raspberry Pi if not on a Pi
    if requires_pi and not IS_RASPBERRY_PI:
        return TestResult(
            name=test_name,
            status=SKIP,
            message="Skipped - Requires Raspberry Pi",
            duration=0.0
        )
    
    try:
        test_func()
        return TestResult(
            name=test_name,
            status=PASS,
            duration=time.time() - start_time
        )
    except ImportError as e:
        return TestResult(
            name=test_name,
            status=SKIP,
            message=f"Skipped - Missing dependency: {str(e).split()[-1]}",
            duration=time.time() - start_time
        )
    except Exception as e:
        return TestResult(
            name=test_name,
            status=FAIL,
            message=f"Error: {str(e)}",
            duration=time.time() - start_time
        )

def print_test_results(results: List[TestResult]):
    """Print test results in a formatted table."""
    print("\n" + "="*80)
    print("TEST RESULTS".center(80))
    print("="*80)
    
    max_name_length = max(len(result.name) for result in results) + 2
    
    print(f"{'TEST':<{max_name_length}} | STATUS  | TIME (s)  | MESSAGE")
    print("-" * 80)
    
    for result in results:
        print(f"{result.name:<{max_name_length}} | {result.status:^7} | {result.duration:7.3f}s | {result.message}")
    
    passed = sum(1 for r in results if r.status == PASS)
    failed = sum(1 for r in results if r.status == FAIL)
    skipped = sum(1 for r in results if r.status == SKIP)
    
    print("-" * 80)
    print(f"TOTAL: {len(results)} | PASSED: {passed} | FAILED: {failed} | SKIPPED: {skipped}")
    print("="*80 + "\n")

def test_component_initialization():
    """Test that all components can be initialized."""
    from component import Component, Input, Output
    from ultrasonic import Ultrasonic
    from motor import Motor, Motor_System
    from servo import Servo, ServoOutput
    from led_board import LED_Board
    from car import Tank
    
    # Test component initialization
    components = [
        ("Ultrasonic", Ultrasonic(echo_pin=17, trigger_pin=27)),
        ("Motor", Motor(pin1=1, pin2=2)),
        ("Motor_System", Motor_System(left_forward_pin=1, left_backward_pin=2, right_forward_pin=3, right_backward_pin=4)),
        ("Servo", Servo(channel=0)),
        ("LED_Board", LED_Board(led_pins=[17, 18, 22, 23])),
        ("Tank", Tank())
    ]
    
    for name, component in components:
        component.start()
        component.close()

def test_led_board():
    """Test LED board functionality."""
    from led_board import LED_Board
    
    leds = LED_Board(led_pins=[17, 18, 22, 23])
    leds.start()
    
    try:
        # Test individual LEDs
        for i in range(4):
            leds.set_led(i, True)
            time.sleep(0.2)
            leds.set_led(i, False)
        
        # Test all on/off
        leds.all_on()
        time.sleep(0.5)
        leds.all_off()
        
    finally:
        leds.close()

def test_motor_system():
    """Test motor system functionality."""
    from motor import Motor_System
    
    motors = Motor_System(
        left_forward_pin=24,
        left_backward_pin=23,
        right_forward_pin=5,
        right_backward_pin=6
    )
    
    try:
        # Test forward
        motors.setMotorModel(1000, 1000)
        time.sleep(1)
        # Test backward
        motors.setMotorModel(-1000, -1000)
        time.sleep(1)
        # Test turn
        motors.setMotorModel(-1000, 1000)
        time.sleep(1)
        # Stop
        motors.setMotorModel(0, 0)
        
    finally:
        motors.close()

def test_ultrasonic():
    """Test ultrasonic sensor."""
    from ultrasonic import Ultrasonic
    
    sonic = Ultrasonic(echo_pin=17, trigger_pin=27)
    try:
        for _ in range(3):
            distance = sonic.get_distance()
            print(f"Distance: {distance:.1f} cm")
            time.sleep(0.5)
    finally:
        sonic.close()

def test_servo():
    """Test servo movement."""
    from servo import Servo
    
    servo = Servo(channel=0)
    try:
        for angle in [0, 45, 90, 135, 180, 90]:
            servo.set_angle(angle)
            time.sleep(0.5)
    finally:
        servo.close()

def test_tank_integration():
    """Test the complete tank system."""
    from car import Tank
    
    tank = Tank()
    try:
        tank.start()
        
        # Test motors
        tank.setMotorModel(1000, 1000)  # Forward
        time.sleep(1)
        tank.setMotorModel(-1000, -1000)  # Backward
        time.sleep(1)
        tank.setMotorModel(0, 0)  # Stop
        
        # Test ultrasonic
        distance = tank.get_distance()
        print(f"Distance: {distance:.1f} cm")
        
        # Test LEDs
        tank.set_leds({0: True, 1: False, 2: True, 3: False})
        time.sleep(1)
        tank.set_leds({0: False, 1: True, 2: False, 3: True})
        time.sleep(1)
        
    finally:
        tank.close()

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description='Run tests for Freenove Tank Robot')
    parser.add_argument('--test', type=str, choices=['all', 'unit', 'integration'], 
                       default='all', help='Type of tests to run')
    
    args = parser.parse_args()
    
    # Define test groups
    unit_tests = [
        ("Component Initialization", test_component_initialization),
        ("LED Board", test_led_board),
        ("Motor System", test_motor_system),
        ("Ultrasonic Sensor", test_ultrasonic),
        ("Servo Control", test_servo),
    ]
    
    integration_tests = [
        ("Tank Integration", test_tank_integration),
    ]
    
    # Select tests to run
    tests_to_run = []
    if args.test in ['all', 'unit']:
        tests_to_run.extend(unit_tests)
    if args.test in ['all', 'integration']:
        tests_to_run.extend(integration_tests)
    
    # Run tests
    results = []
    for name, test_func in tests_to_run:
        print(f"\nRunning test: {name}...")
        # All hardware tests require Raspberry Pi
        requires_pi = name not in ["Component Initialization"]
        result = run_test(test_func, name, requires_pi=requires_pi)
        results.append(result)
    
    # Print results
    print_test_results(results)
    
    # Exit with appropriate status code
    if any(result.status == FAIL for result in results):
        sys.exit(1)

if __name__ == "__main__":
    main()
