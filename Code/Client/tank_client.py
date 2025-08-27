"""
Tank Client - A high-level client for controlling the Freenove Tank Robot.
This client communicates with the server's car.py class to control the robot.
"""
import socket
import json
from typing import Optional, Dict, Any, List, Tuple

class TankClient:
    """A client for controlling the Freenove Tank Robot."""
    
    def __init__(self, host: str, command_port: int = 5003):
        """Initialize the TankClient.
        
        Args:
            host: The IP address of the server
            command_port: The port for command communication (default: 5003)
        """
        self.host = host
        self.command_port = command_port
        self.socket = None
        self.connected = False
        self.buffer_size = 4096
        
    def connect(self) -> bool:
        """Connect to the tank server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.command_port))
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to {self.host}:{self.command_port}: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the tank server."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connected = False
    
    def _send_command(self, command: str, *args) -> Optional[Dict[str, Any]]:
        """Send a command to the server and wait for a response."""
        if not self.connected and not self.connect():
            return None
            
        try:
            # Format: COMMAND#arg1#arg2#...\n
            # Build the command string
            cmd_parts = [command] + [str(arg) for arg in args]
            cmd_str = "#".join(cmd_parts) + "\n"
            
            # Send the command
            self.socket.sendall(cmd_str.encode('utf-8'))
            
            # Wait for response (non-blocking with timeout)
            self.socket.settimeout(1.0)  # 1 second timeout
            response = self.socket.recv(self.buffer_size).decode('utf-8').strip()
            
            # Try to parse as JSON, return raw response if not JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"status": "success", "data": response}
                
        except socket.timeout:
            print("Command timed out")
            return {"status": "error", "message": "Command timed out"}
        except Exception as e:
            print(f"Error sending command: {e}")
            self.connected = False
            return {"status": "error", "message": str(e)}
    
    # High-level movement commands
    def move_forward(self, speed: int = 50) -> Optional[Dict[str, Any]]:
        """Move the tank forward at the specified speed (0-100)."""
        return self._send_command("MOVE_FORWARD", max(0, min(100, speed)))
    
    def move_backward(self, speed: int = 50) -> Optional[Dict[str, Any]]:
        """Move the tank backward at the specified speed (0-100)."""
        return self._send_command("MOVE_BACKWARD", max(0, min(100, speed)))
    
    def turn_left(self, speed: int = 50) -> Optional[Dict[str, Any]]:
        """Turn the tank left at the specified speed (0-100)."""
        return self._send_command("TURN_LEFT", max(0, min(100, speed)))
    
    def turn_right(self, speed: int = 50) -> Optional[Dict[str, Any]]:
        """Turn the tank right at the specified speed (0-100)."""
        return self._send_command("TURN_RIGHT", max(0, min(100, speed)))
    
    def stop(self) -> Optional[Dict[str, Any]]:
        """Stop all movement."""
        return self._send_command("STOP")
    
    # Servo control
    def set_servo_angle(self, channel: int, angle: int) -> Optional[Dict[str, Any]]:
        """Set the angle of a servo.
        
        Args:
            channel: The servo channel (0 for pan, 1 for tilt)
            angle: The angle to set (0-180)
        """
        return self._send_command("SET_SERVO", channel, max(0, min(180, angle)))
    
    # LED control
    def set_led(self, led_id: int, state: bool) -> Optional[Dict[str, Any]]:
        """Turn an LED on or off.
        
        Args:
            led_id: The ID of the LED to control
            state: True to turn on, False to turn off
        """
        return self._send_command("SET_LED", led_id, 1 if state else 0)
    
    def set_led_color(self, led_id: int, r: int, g: int, b: int) -> Optional[Dict[str, Any]]:
        """Set the color of an RGB LED.
        
        Args:
            led_id: The ID of the LED to control
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        return self._send_command("SET_LED_COLOR", led_id, 
                               max(0, min(255, r)),
                               max(0, min(255, g)),
                               max(0, min(255, b)))
    
    # Sensor reading
    def get_distance(self) -> Optional[float]:
        """Get the distance from the ultrasonic sensor in cm."""
        response = self._send_command("GET_DISTANCE")
        if response and response.get("status") == "success":
            try:
                return float(response.get("data", 0))
            except (ValueError, TypeError):
                pass
        return None
    
    # Arm control
    def set_arm_position(self, joint: str, angle: int) -> Optional[Dict[str, Any]]:
        """Set the position of a robot arm joint.
        
        Args:
            joint: The joint to move (e.g., 'base', 'shoulder', 'elbow', 'wrist', 'gripper')
            angle: The angle to set (0-180)
        """
        return self._send_command("SET_ARM_POSITION", joint, max(0, min(180, angle)))
    
    # Camera control
    def set_camera_tilt(self, angle: int) -> Optional[Dict[str, Any]]:
        """Set the camera tilt angle."""
        return self._send_command("SET_CAMERA_TILT", max(0, min(180, angle)))
    
    def __del__(self):
        """Clean up resources."""
        self.disconnect()

# Example usage
if __name__ == "__main__":
    # Example usage
    tank = TankClient("192.168.1.100")  # Replace with your server's IP
    
    if tank.connect():
        print("Connected to tank!")
        
        # Example commands
        tank.move_forward(50)  # Move forward at 50% speed
        tank.turn_right(30)    # Turn right at 30% speed
        tank.set_servo_angle(0, 90)  # Set pan servo to 90 degrees
        tank.set_led(0, True)  # Turn on LED 0
        tank.set_led_color(1, 255, 0, 0)  # Set LED 1 to red
        
        # Get sensor data
        distance = tank.get_distance()
        if distance is not None:
            print(f"Distance: {distance} cm")
        
        tank.stop()  # Stop all movement
        tank.disconnect()
