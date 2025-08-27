"""
Tank module implementing a component-based architecture for the robot.
This module provides the main Tank class that composes various hardware components.
"""
from typing import Optional, Dict, Any
import time
from component import Component
from ultrasonic import Ultrasonic
from motor import Motor_System
from servo import Servo
from infrared import Infrared
from arm import Arm
from led_board import LED_Board

class Tank(Component):
    """
    Main tank class that composes various hardware components.
    Implements the Component interface for unified control.
    """
    
    def __init__(self, 
                 config: Optional[Dict[str, Any]] = None,
                 name: str = "tank"):
        """
        Initialize the Tank with the specified configuration.
        
        Args:
            config: Configuration dictionary for hardware components.
                   If None, uses default configuration.
            name: Name of the tank (default: "tank")
        """
        super().__init__(name, 0)  # Instance is 0 as this is the main component
        
        # Default configuration
        self.config = config or {
            'ultrasonic': {'echo_pin': 17, 'trigger_pin': 27},
            'motor_system': {
                'left_forward_pin': 24,
                'left_backward_pin': 23,
                'right_forward_pin': 5,
                'right_backward_pin': 6
            },
            'servo': {},
            'infrared': {},
            'arm': {
                'servo_pins': {
                    'base': (0, 90),    # Channel 0, default 90 degrees
                    'shoulder': (1, 90), # Channel 1, default 90 degrees
                    'elbow': (2, 90)     # Channel 2, default 90 degrees
                }
            },
            'led_board': {
                'led_pins': [17, 18, 22, 23]  # Example LED pins
            }
        }
        
        # Initialize components
        self.components: Dict[str, Component] = {}
        self._initialize_components()
        
        # State variables
        self.clamp_mode = 0
        self.infrared_run_stop = False

    def _initialize_components(self):
        """Initialize all hardware components based on configuration."""
        # Initialize motor system
        motor_config = self.config.get('motor_system', {})
        self.components['motor_system'] = Motor_System(**motor_config)
        
        # Initialize ultrasonic sensor
        sonic_config = self.config.get('ultrasonic', {})
        self.components['ultrasonic'] = Ultrasonic(**sonic_config)
        
        # Initialize servo
        servo_config = self.config.get('servo', {})
        self.components['servo'] = Servo(**servo_config)
        
        # Initialize infrared sensor
        ir_config = self.config.get('infrared', {})
        self.components['infrared'] = Infrared(**ir_config)
        
        # Initialize arm
        arm_config = self.config.get('arm', {})
        self.components['arm'] = Arm(**arm_config)
        
        # Initialize LED board
        led_config = self.config.get('led_board', {})
        self.components['led_board'] = LED_Board(**led_config)
        
        # Create direct references for backward compatibility
        self.motor = self.components['motor_system']
        self.sonic = self.components['ultrasonic']
        self.servo = self.components['servo']
        self.infrared = self.components['infrared']
        self.leds = self.components['led_board']
        self.arm = self.components['arm']

    def start(self):
        """Start all components."""
        for component in self.components.values():
            component.start()

    def close(self):
        """Close all components and release resources."""
        self._cleanup_components()
        super().close()

    def _cleanup_components(self):
        """Safely close all components."""
        for component in reversed(list(self.components.values())):
            try:
                if hasattr(component, 'close'):
                    component.close()
            except Exception as e:
                print(f"Error closing component {component}: {e}")

    def setMotorModel(self, left_speed: int, right_speed: int):
        """
        Set motor speeds using the legacy interface.
        
        Args:
            left_speed: Speed for left motor (-4095 to 4095)
            right_speed: Speed for right motor (-4095 to 4095)
        """
        if 'motor_system' in self.components:
            self.motor.setMotorModel(left_speed, right_speed)

    def get_distance(self):
        """
        Get distance from ultrasonic sensor.
        
        Returns:
            Distance in centimeters
        """
        if 'ultrasonic' in self.components:
            return self.sonic.get_distance()
        return 0.0

    def set_servo_angle(self, channel: str, angle: float):
        """
        Set servo angle.
        
        Args:
            channel: Servo channel
            angle: Angle in degrees (0-180)
        """
        if 'servo' in self.components:
            self.servo.set_angle(channel, angle)

    def set_arm_position(self, position: Dict[str, float]):
        """
        Move arm to specified position.
        
        Args:
            position: Dictionary mapping joint names to angles
        """
        if 'arm' in self.components:
            self.arm.set_position(position)

    def set_leds(self, states: Dict[int, bool]):
        """
        Set LED states.
        
        Args:
            states: Dictionary mapping LED indices to states (True/False)
        """
        if 'led_board' in self.components:
            for index, state in states.items():
                self.leds.set_led(index, state)

# For backward compatibility
Car = Tank

def test_tank():
    """Test function for the Tank class."""
    tank = Tank()
    try:
        tank.start()
        
        # Test motors
        print("Testing motors...")
        tank.setMotorModel(1000, 1000)  # Forward
        time.sleep(1)
        tank.setMotorModel(-1000, -1000)  # Backward
        time.sleep(1)
        tank.setMotorModel(0, 0)  # Stop
        
        # Test ultrasonic
        print("Testing ultrasonic...")
        distance = tank.get_distance()
        print(f"Distance: {distance:.1f} cm")
        
        # Test LEDs
        print("Testing LEDs...")
        tank.set_leds({0: True, 1: False, 2: True, 3: False})
        time.sleep(1)
        tank.set_leds({0: False, 1: True, 2: False, 3: True})
        time.sleep(1)
        tank.set_leds({i: False for i in range(4)})
        
    finally:
        tank.close()

def test_infrared():
    """Test function for the infrared sensor."""
    tank = Tank()
    try:
        tank.start()
        print("Testing infrared sensor...")
        for _ in range(5):
            print(f"IR Left: {tank.infrared.left_value}, Right: {tank.infrared.right_value}")
            time.sleep(1)
    finally:
        tank.close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Tank Robot Components')
    parser.add_argument('--test', type=str, choices=['tank', 'infrared'], 
                       default='tank', help='Test to run')
    
    args = parser.parse_args()
    
    if args.test == 'tank':
        test_tank()
    elif args.test == 'infrared':
        test_infrared()
