import pigpio
from component import Output

class ServoOutput(Output):
    """
    A class to control a servo motor, implementing the Output interface.
    This is an abstract base class that defines the interface for servo control.
    """
    def __init__(self, name: str = "servo"):
        """
        Initialize the servo output.
        
        Args:
            name: Name of the servo (default: "servo")
        """
        super().__init__(name, 0)  # Instance is 0 for single servo
    
    @abstractmethod
    def set_angle(self, angle: float):
        """
        Set the servo angle.
        
        Args:
            angle: Angle in degrees (0-180)
        """
        pass
    
    def set_value(self, value: float):
        """
        Set the servo angle using a normalized value (0.0 to 1.0).
        
        Args:
            value: Normalized value (0.0 to 1.0)
        """
        angle = max(0.0, min(180.0, value * 180.0))
        self.set_angle(angle)
    
    def start(self):
        """Initialize the servo. No special initialization needed by default."""
        pass
    
    def close(self):
        """Clean up resources used by the servo."""
        pass


class PigpioServo(ServoOutput):
    def __init__(self, channel: int, instance: int = 0):
        """
        Initialize the PigpioServo instance for a specific channel.
        
        Args:
            channel: GPIO pin number for this servo
            instance: Instance number for multiple servos (default: 0)
        """
        super().__init__(f"servo_{channel}")
        self.channel = channel
        self.instance = instance
        self.pwm = pigpio.pi()  # Initialize the pigpio library
        self.pwm.set_mode(self.channel, pigpio.OUTPUT)
        self.pwm.set_PWM_frequency(self.channel, 50)  # 50 Hz for servos
        self.pwm.set_PWM_range(self.channel, 4000)    # Standard range for servos
        
    def set_angle(self, angle: float):
        """
        Set the servo angle in degrees (0-180).
        
        Args:
            angle: Angle in degrees (0-180)
            
        Raises:
            ValueError: If angle is outside valid range (0-180)
            RuntimeError: If there's an error setting the servo angle
        """
        if not 0 <= angle <= 180:
            raise ValueError(f"Angle {angle}° is outside valid range (0-180)")
            
        try:
            # Convert angle to duty cycle (80-480 corresponds to 0-180 degrees)
            duty_cycle = 80 + (400 / 180) * angle
            self.pwm.set_PWM_dutycycle(self.channel, duty_cycle)
        except Exception as e:
            raise RuntimeError(f"Failed to set servo angle: {str(e)}") from e
        
    def close(self):
        """
        Clean up resources.
        
        Returns:
            bool: True if closed successfully, False otherwise
        """
        success = True
        try:
            # Turn off PWM
            self.pwm.set_PWM_dutycycle(self.channel, 0)
            self.pwm.stop()
            return True
        except Exception as e:
            print(f"Error closing servo: {e}")
            return False
        finally:
            # Ensure PWM is stopped even if an error occurs
            try:
                self.pwm.stop()
            except:
                pass

    # For backward compatibility
    def setServoPwm(self, channel, angle):
        """Legacy method for backward compatibility."""
        if str(self.channel) == str(channel):
            self.set_angle(angle)

from gpiozero import AngularServo

class GpiozeroServo(ServoOutput):
    def __init__(self, channel: int, instance: int = 0):
        """
        Initialize the GpiozeroServo instance for a specific channel.
        
        Args:
            channel: GPIO pin number for this servo
            instance: Instance number for multiple servos (default: 0)
        """
        super().__init__(f"servo_{channel}")
        self.channel = channel
        self.instance = instance
        self.myCorrection = 0.0  # Correction value for pulse width
        self.maxPW = (2.5 + self.myCorrection) / 1000  # Maximum pulse width (2.5ms)
        self.minPW = (0.5 - self.myCorrection) / 1000  # Minimum pulse width (0.5ms)
        
        # Initialize the servo
        self.servo = AngularServo(
            self.channel,
            initial_angle=90,  # Start at 90 degrees (center)
            min_angle=0,
            max_angle=180,
            min_pulse_width=self.minPW,
            max_pulse_width=self.maxPW
        )

    def set_angle(self, angle: float):
        """
        Set the servo angle in degrees (0-180).
        
        Args:
            angle: Angle in degrees (0-180)
            
        Raises:
            ValueError: If angle is outside valid range (0-180)
            RuntimeError: If there's an error setting the servo angle
        """
        if not 0 <= angle <= 180:
            raise ValueError(f"Angle {angle}° is outside valid range (0-180)")
            
        try:
            self.servo.angle = angle
        except Exception as e:
            raise RuntimeError(f"Failed to set servo angle: {str(e)}") from e

    # For backward compatibility
    def setServoPwm(self, channel, angle):
        """Legacy method for backward compatibility."""
        if str(self.channel) == str(channel):
            self.set_angle(angle)

from rpi_hardware_pwm import HardwarePWM

class HardwareServo(ServoOutput):
    def __init__(self, channel: int, pcb_version: int, instance: int = 0):
        """
        Initialize the HardwareServo instance for a specific channel.
        
        Args:
            channel: GPIO pin number (must be 12 or 13 for hardware PWM)
            pcb_version: PCB version (1 or 2)
            instance: Instance number for multiple servos (default: 0)
        """
        super().__init__(f"hw_servo_{channel}")
        self.channel = channel
        self.pcb_version = pcb_version
        self.instance = instance
        self.pwm = None
        
        # Hardware PWM only works on specific GPIO pins (12, 13, etc.)
        if channel == 12:
            pwm_channel = 0
        elif channel == 13:
            pwm_channel = 1
        else:
            raise ValueError(f"Hardware PWM not supported on GPIO {channel}. Use GPIO 12 or 13.")
        
        # Initialize the appropriate PWM channel based on PCB version
        chip = 0  # Default chip for PCB version 1
        if pcb_version == 2:
            chip = 2  # Different chip for PCB version 2
            
        self.pwm = HardwarePWM(pwm_channel=pwm_channel, hz=50, chip=chip)
        self.pwm.start(0)  # Start with 0% duty cycle

    def set_angle(self, angle: float):
        """
        Set the servo angle in degrees (0-180).
        
        Args:
            angle: Angle in degrees (0-180)
            
        Raises:
            ValueError: If angle is outside valid range (0-180)
            RuntimeError: If there's an error setting the servo angle
        """
        if not 0 <= angle <= 180:
            raise ValueError(f"Angle {angle}° is outside valid range (0-180)")
            
        try:
            # Map angle to duty cycle (0-100%)
            duty_cycle = self._map(angle, 0, 180, 2.5, 12.5)
            self.pwm.start(duty_cycle)
        except Exception as e:
            raise RuntimeError(f"Failed to set servo angle: {str(e)}") from e
    
    def _map(self, x, in_min, in_max, out_min, out_max):
        """Helper method to map a value from one range to another."""
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
    def start(self):
        """Initialize the hardware PWM."""
        if self.pwm is not None:
            self.pwm.start(0)  # Start with 0% duty cycle
    
    def close(self):
        """
        Clean up hardware PWM resources.
        
        Returns:
            bool: True if closed successfully, False otherwise
        """
        success = True
        try:
            if self.pwm is not None:
                self.pwm.stop()
                self.pwm = None
            return True
        except Exception as e:
            print(f"Error closing hardware servo: {e}")
            return False
        finally:
            # Ensure PWM is stopped even if an error occurs
            try:
                if self.pwm is not None:
                    self.pwm.stop()
            except:
                pass

    # For backward compatibility
    def setServoPwm(self, channel, angle):
        """Legacy method for backward compatibility."""
        if str(self.channel) == str(channel):
            self.set_angle(angle)

    def setServoDuty(self, channel, duty):
        """Legacy method to set duty cycle directly."""
        if self.pwm is not None and str(self.channel) == str(channel):
            self.pwm.change_duty_cycle(duty)
    
    def setServoFrequency(self, channel, freq):
        """Legacy method to set PWM frequency."""
        if self.pwm is not None and str(self.channel) == str(channel):
            self.pwm.freq = freq

from abc import abstractmethod
from parameter import ParameterManager

class Servo(Output):
    def __init__(self, channel: int, instance: int = 0):
        """
        Initialize the Servo instance for a specific channel.
        
        Args:
            channel: GPIO pin number for this servo
            instance: Instance number for multiple servos (default: 0)
        """
        super().__init__(f"servo_{channel}", instance)
        self.channel = channel
        self.param = ParameterManager()
        self.pcb_version = self.param.get_pcb_version()
        self.pi_version = self.param.get_raspberry_pi_version()
        
        # Initialize the appropriate servo implementation based on hardware
        if self.pcb_version == 1 and self.pi_version == 1:
            self.servo = PigpioServo(channel, instance)
        elif self.pcb_version == 1 and self.pi_version == 2:
            self.servo = GpiozeroServo(channel, instance)
        elif self.pcb_version == 2:
            # For hardware PWM, we only support specific channels (12, 13, etc.)
            hw_pwm_chip = 0 if self.pi_version == 1 else 2
            self.servo = HardwareServo(channel, hw_pwm_chip, instance)
        else:
            # Default to GpiozeroServo if version is unknown
            self.servo = GpiozeroServo(channel, instance)
        
        # Initialize the servo
        self.servo.start()
    
    def set_angle(self, angle: float):
        """
        Set the servo angle in degrees (0-180).
        
        Args:
            angle: Angle in degrees (0-180)
            
        Raises:
            ValueError: If angle is outside valid range (0-180)
            RuntimeError: If there's an error setting the servo angle
        """
        if not 0 <= angle <= 180:
            raise ValueError(f"Angle {angle}° is outside valid range (0-180)")
            
        try:
            self.servo.set_angle(angle)
        except Exception as e:
            raise RuntimeError(f"Failed to set servo angle: {str(e)}") from e
    
    def set_value(self, value: float):
        """
        Set the servo angle using a normalized value (0.0 to 1.0).
        
        Args:
            value: Normalized value (0.0 to 1.0)
        """
        self.servo.set_value(value)
    
    def start(self):
        """Initialize the servo."""
        self.servo.start()
    
    def close(self):
        """
        Clean up resources.
        
        Returns:
            bool: True if closed successfully, False otherwise
        """
        try:
            self.servo.close()
            return True
        except Exception as e:
            print(f"Error closing servo: {e}")
            return False
    
    # Legacy methods for backward compatibility
    def setServoAngle(self, channel, angle):
        """Legacy method for setting servo angle."""
        if str(self.channel) == str(channel):
            self.set_angle(angle)
    
    def setServoStop(self):
        """Legacy method to stop the servo."""
        self.close()

# Main program logic follows:
if __name__ == '__main__':
    import time
    
    # Example usage of the new Servo class
    try:
        # Create two servo instances (one for each channel)
        print('Initializing servos...')
        servo1 = Servo(channel=12)  # First servo on GPIO 12
        servo2 = Servo(channel=13)  # Second servo on GPIO 13
        
        print('PWM Servo test program...')
        print('Press Ctrl+C to exit')
        
        while True:
            try:
                # Sweep both servos from 0 to 180 degrees
                for angle in range(0, 181, 5):
                    servo1.set_angle(angle)
                    servo2.set_angle(180 - angle)  # Move in opposite direction
                    print(f'Servo 1: {angle}°, Servo 2: {180-angle}°')
                    time.sleep(0.05)
                
                # Sweep back from 180 to 0 degrees
                for angle in range(180, -1, -5):
                    servo1.set_angle(angle)
                    servo2.set_angle(180 - angle)  # Move in opposite direction
                    print(f'Servo 1: {angle}°, Servo 2: {180-angle}°')
                    time.sleep(0.05)
                    
            except KeyboardInterrupt:
                print('\nTest interrupted by user')
                break
                
    except Exception as e:
        print(f'Error: {e}')
    
    finally:
        # Clean up
        print('Cleaning up...')
        try:
            servo1.close()
            servo2.close()
        except:
            pass
        print('Done!')
