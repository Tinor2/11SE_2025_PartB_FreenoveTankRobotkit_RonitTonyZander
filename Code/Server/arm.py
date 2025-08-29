"""
Arm module for controlling a robotic arm with multiple servos.
Implements the Output interface for unified control.
"""
from typing import Dict, Optional, Tuple
from component import Output
from servo import Servo

class Arm(Output):
    """
    A composite class that manages multiple servos for a robotic arm.
    Implements the Output interface for unified control.
    """
    
    def __init__(self, 
                 servo_pins: Dict[str, Tuple[int, int]] = None,
                 name: str = "arm"):
        """
        Initialize the Arm with the specified servo configurations.
        
        Args:
            servo_pins: Dictionary mapping servo names to (channel, default_angle) tuples.
                       If None, uses default configuration for a 3-servo arm.
            name: Name of the arm (default: "arm")
        """
        super().__init__(name, 0)  # Instance is 0 as this is a composite
        
        # Default configuration if none provided
        if servo_pins is None:
            servo_pins = {
                'base': (0, 90),    # Channel 0, default 90 degrees
                'shoulder': (1, 90), # Channel 1, default 90 degrees
                'elbow': (2, 90)     # Channel 2, default 90 degrees
            }
            
        self.servos: Dict[str, Servo] = {}
        self.angles: Dict[str, float] = {}
        
        # Initialize all servos
        for servo_name, (channel, default_angle) in servo_pins.items():
            self.servos[servo_name] = Servo(channel=channel, instance=0)
            self.angles[servo_name] = default_angle
    
    def start(self):
        """Initialize all servos in the arm."""
        for servo in self.servos.values():
            servo.start()
    
    def set_value(self, value: float):
        """
        Set all servos to the specified angle.
        
        Args:
            value: Angle in degrees (0-180) to set all servos to
        """
        for servo_name in self.servos:
            self.set_servo_angle(servo_name, value)
    
    def set_servo_angle(self, servo_name: str, angle: float):
        """
        Set a specific servo to the specified angle.
        
        Args:
            servo_name: Name of the servo to control
            angle: Angle in degrees (0-180)
        """
        if servo_name in self.servos:
            angle = max(0.0, min(180.0, angle))  # Clamp angle
            self.angles[servo_name] = angle
            self.servos[servo_name].set_angle(angle)
    
    def get_servo_angle(self, servo_name: str) -> Optional[float]:
        """
        Get the current angle of a specific servo.
        
        Args:
            servo_name: Name of the servo
            
        Returns:
            Current angle in degrees, or None if servo not found
        """
        return self.angles.get(servo_name)
    
    def get_angles(self) -> Dict[str, float]:
        """
        Get the current angles of all servos.
        
        Returns:
            Dictionary mapping servo names to their current angles
        """
        return self.angles.copy()
    
    def move_to_position(self, position: Dict[str, float]):
        """
        Move multiple servos to specified angles in one operation.
        
        Args:
            position: Dictionary mapping servo names to target angles
        """
        for servo_name, angle in position.items():
            if servo_name in self.servos:
                self.set_servo_angle(servo_name, angle)
    
    def stop(self):
        """Stop all servos in the arm."""
        for servo in self.servos.values():
            servo.stop()
    
    def close(self):
        """Close all servos and release resources."""
        for servo in self.servos.values():
            try:
                servo.close()
            except:
                pass

# Example usage
if __name__ == "__main__":
    import time
    
    # Create an arm with default configuration
    arm = Arm()
    
    try:
        print("Moving arm to home position...")
        arm.start()
        
        # Move to home position
        arm.move_to_position({
            'base': 90,
            'shoulder': 90,
            'elbow': 90
        })
        
        # Simple movement sequence
        print("Starting movement sequence...")
        for angle in range(30, 150, 10):
            arm.set_servo_angle('base', angle)
            time.sleep(0.1)
            
        time.sleep(1)
        
        # Move all servos to 0 degrees
        arm.set_value(0)
        
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Clean up
        arm.close()
        print("Arm controller stopped.")
