from gpiozero import Motor
from component import Output

class Motor(Output):
    """
    A class to control a single motor, implementing the Output interface.
    This is a wrapper around gpiozero.Motor with additional functionality.
    """
    def __init__(self, forward_pin: int, backward_pin: int, instance: int = 0, name: str = "motor"):
        """
        Initialize a motor with the specified GPIO pins.
        
        Args:
            forward_pin: GPIO pin number for forward movement
            backward_pin: GPIO pin number for backward movement
            instance: Instance number for multiple motors
            name: Name of the motor (default: "motor")
        """
        super().__init__(name, instance)
        self.forward_pin = forward_pin
        self.backward_pin = backward_pin
        self.motor = Motor(forward_pin, backward_pin)
    
    def start(self):
        """Initialize the motor. No special initialization needed for gpiozero."""
        pass
        
    def set_value(self, speed: float):
        """
        Set the motor speed.
        
        Args:
            speed: Speed value between -1.0 (full reverse) and 1.0 (full forward)
            
        Raises:
            ValueError: If speed is outside the valid range (-1.0 to 1.0)
            RuntimeError: If there's an error controlling the motor
        """
        try:
            if not -1.0 <= speed <= 1.0:
                raise ValueError(f"Speed {speed} is outside valid range [-1.0, 1.0]")
                
            if speed > 0:
                self.motor.forward(speed)
            elif speed < 0:
                self.motor.backward(-speed)
            else:
                self.motor.stop()
                
        except Exception as e:
            self.stop()  # Ensure motor is stopped on error
            raise RuntimeError(f"Failed to set motor speed: {str(e)}") from e
    
    def stop(self):
        """
        Stop the motor.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            self.motor.stop()
            return True
        except Exception as e:
            print(f"Error stopping motor: {e}")
            return False
    
    def close(self):
        """
        Close the motor to release resources.
        
        Returns:
            bool: True if closed successfully, False otherwise
        """
        try:
            self.stop()  # Ensure motor is stopped before closing
            self.motor.close()
            return True
        except Exception as e:
            print(f"Error closing motor: {e}")
            return False

class Motor_System(Output):
    """
    A composite class that manages two motors for tank-style movement.
    Implements the Output interface for unified control.
    """
    def __init__(self, 
                 left_forward_pin: int = 24, 
                 left_backward_pin: int = 23,
                 right_forward_pin: int = 5,
                 right_backward_pin: int = 6,
                 name: str = "motor_system"):
        """
        Initialize the motor system with the specified GPIO pins.
        
        Args:
            left_forward_pin: GPIO pin for left motor forward
            left_backward_pin: GPIO pin for left motor backward
            right_forward_pin: GPIO pin for right motor forward
            right_backward_pin: GPIO pin for right motor backward
            name: Name of the motor system (default: "motor_system")
        """
        super().__init__(name, 0)  # Instance is 0 as this is a composite
        
        # Initialize left and right motors
        self.left_motor = Motor(
            forward_pin=left_forward_pin,
            backward_pin=left_backward_pin,
            instance=0,
            name=f"{name}_left"
        )
        
        self.right_motor = Motor(
            forward_pin=right_forward_pin,
            backward_pin=right_backward_pin,
            instance=1,
            name=f"{name}_right"
        )
        
        self._left_speed = 0.0
        self._right_speed = 0.0
    
    def start(self):
        """Initialize both motors."""
        self.left_motor.start()
        self.right_motor.start()
    
    def set_value(self, value: float):
        """
        Set the speed for both motors.
        
        Args:
            value: Speed value between -1.0 (full reverse) and 1.0 (full forward)
            
        Raises:
            RuntimeError: If there's an error setting motor speeds
        """
        self.set_speeds(value, value)
    
    def set_speeds(self, left_speed: float, right_speed: float):
        """
        Set different speeds for left and right motors.
        
        Args:
            left_speed: Speed for left motor (-1.0 to 1.0)
            right_speed: Speed for right motor (-1.0 to 1.0)
            
        Raises:
            RuntimeError: If there's an error setting motor speeds
        """
        try:
            self._left_speed = max(-1.0, min(1.0, left_speed))
            self._right_speed = max(-1.0, min(1.0, right_speed))
            
            self.left_motor.set_value(self._left_speed)
            self.right_motor.set_value(self._right_speed)
        except Exception as e:
            self.stop()
            raise RuntimeError(f"Failed to set motor speeds: {str(e)}") from e
    
    def stop(self):
        """
        Stop both motors and reset speed tracking.
        
        Returns:
            bool: True if both motors stopped successfully, False otherwise
        """
        success = True
        try:
            if not self.left_motor.stop():
                print("Warning: Failed to stop left motor")
                success = False
            if not self.right_motor.stop():
                print("Warning: Failed to stop right motor")
                success = False
            self._left_speed = 0.0
            self._right_speed = 0.0
            return success
        except Exception as e:
            print(f"Error stopping motors: {e}")
            return False
    
    def close(self):
        """Close both motors and release resources."""
        self.stop()
        self.left_motor.close()
        self.right_motor.close()
    
    def get_speeds(self) -> tuple[float, float]:
        """
        Get the current speeds of both motors.
        
        Returns:
            Tuple of (left_speed, right_speed) where each is between -1.0 and 1.0
        """
        return self._left_speed, self._right_speed
    
    # Legacy compatibility methods
    def duty_range(self, duty1: int, duty2: int) -> tuple[int, int]:
        """
        Ensure the duty cycle values are within the valid range (-4095 to 4095).
        
        Args:
            duty1: First duty cycle value
            duty2: Second duty cycle value
            
        Returns:
            Tuple of clamped duty cycle values
        """
        duty1 = max(-4095, min(4095, duty1))
        duty2 = max(-4095, min(4095, duty2))
        return duty1, duty2
    
    def left_Wheel(self, duty: int):
        """
        Control the left wheel based on the duty cycle value.
        
        Args:
            duty: Duty cycle value between -4095 and 4095
            
        Raises:
            RuntimeError: If there's an error controlling the left wheel
        """
        try:
            speed = max(-1.0, min(1.0, duty / 4095.0))
            self._left_speed = speed
            self.left_motor.set_value(speed)
        except Exception as e:
            self.stop()
            raise RuntimeError(f"Failed to control left wheel: {str(e)}") from e
    
    def right_Wheel(self, duty: int):
        """
        Control the right wheel based on the duty cycle value.
        
        Args:
            duty: Duty cycle value between -4095 and 4095
            
        Raises:
            RuntimeError: If there's an error controlling the right wheel
        """
        try:
            speed = max(-1.0, min(1.0, duty / 4095.0))
            self._right_speed = speed
            self.right_motor.set_value(speed)
        except Exception as e:
            self.stop()
            raise RuntimeError(f"Failed to control right wheel: {str(e)}") from e
    
    def setMotorModel(self, duty1: int, duty2: int):
        """
        Set the duty cycle for both motors (legacy method).
        
        Args:
            duty1: Duty cycle for left motor (-4095 to 4095)
            duty2: Duty cycle for right motor (-4095 to 4095)
            
        Raises:
            RuntimeError: If there's an error setting motor model
        """
        try:
            duty1, duty2 = self.duty_range(duty1, duty2)
            self.left_Wheel(duty1)
            self.right_Wheel(duty2)
        except Exception as e:
            self.stop()
            raise RuntimeError(f"Failed to set motor model: {str(e)}") from e


# For backward compatibility
class tankMotor(Motor_System):
    """
    Legacy class for backward compatibility. 
    This is now a thin wrapper around Motor_System with the original pin configuration.
    """
    def __init__(self):
        super().__init__(
            left_forward_pin=24,
            left_backward_pin=23,
            right_forward_pin=5,
            right_backward_pin=6,
            name="tank_motor"
        )

    def duty_range(self, duty1, duty2):
        """Ensure the duty cycle values are within the valid range (-4095 to 4095)."""
        if duty1 > 4095:
            duty1 = 4095     # Cap the value at 4095 if it exceeds the maximum
        elif duty1 < -4095:
            duty1 = -4095    # Cap the value at -4095 if it falls below the minimum
        
        if duty2 > 4095:
            duty2 = 4095     # Cap the value at 4095 if it exceeds the maximum
        elif duty2 < -4095:
            duty2 = -4095    # Cap the value at -4095 if it falls below the minimum
        
        return duty1, duty2  # Return the clamped duty cycle values

    def left_Wheel(self, duty):
        """Control the left wheel based on the duty cycle value."""
        # Convert duty cycle (-4095 to 4095) to speed (-1.0 to 1.0)
        speed = max(-1.0, min(1.0, duty / 4095.0))
        self.left_motor.set_value(speed)

    def right_Wheel(self, duty):
        """Control the right wheel based on the duty cycle value."""
        # Convert duty cycle (-4095 to 4095) to speed (-1.0 to 1.0)
        speed = max(-1.0, min(1.0, duty / 4095.0))
        self.right_motor.set_value(speed)

    def setMotorModel(self, duty1, duty2):
        """Set the duty cycle for both motors and ensure they are within the valid range."""
        duty1, duty2 = self.duty_range(duty1, duty2)  # Clamp the duty cycle values
        self.left_Wheel(duty1)   # Control the left wheel
        self.right_Wheel(duty2)  # Control the right wheel
    
    def close(self):
        """
        Close the motors to release resources.
        
        Returns:
            bool: True if both motors closed successfully, False otherwise
        """
        success = True
        try:
            self.stop()  # Ensure motors are stopped before closing
            if not self.left_motor.close():
                print("Warning: Failed to close left motor")
                success = False
            if not self.right_motor.close():
                print("Warning: Failed to close right motor")
                success = False
            return success
        except Exception as e:
            print(f"Error closing motor system: {e}")
            return False

# Main program logic follows:
if __name__ == '__main__':
    import time  # Import the time module for sleep functionality
    print('Program is starting ... \n')  # Print a start message
    pwm_motor = tankMotor()              # Create an instance of the tankMotor class

    try:
        pwm_motor.setMotorModel(2000, 2000)    # Set both motors to move forward
        time.sleep(1)                          # Wait for 1 second
        pwm_motor.setMotorModel(-2000, -2000)  # Set both motors to move backward
        time.sleep(1)                          # Wait for 1 second
        pwm_motor.setMotorModel(2000, -2000)   # Turn right(left motor forward, right motor backward)
        time.sleep(1)                          # Wait for 1 second
        pwm_motor.setMotorModel(-2000, 2000)   # Turn left(left motor backward, right motor forward)
        time.sleep(1)                          # Wait for 1 second
        pwm_motor.setMotorModel(0, 0)          # Stop both motors
        time.sleep(1)                          # Wait for 1 second
    except KeyboardInterrupt:                  # Handle a keyboard interrupt (Ctrl+C)
        pwm_motor.setMotorModel(0, 0)          # Stop both motors
        pwm_motor.close()                      # Close the motors to release resources