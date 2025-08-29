"""
Tank Server - A high-level server for controlling the Freenove Tank Robot.
This server provides a clean API for the TankClient to interact with the robot.
"""
import json
import socket
import threading
from typing import Dict, Any, Optional, Tuple

from car import Tank

class TankServer:
    """Server for handling tank control commands."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5003):
        """Initialize the TankServer.
        
        Args:
            host: Host address to bind to (default: '0.0.0.0')
            port: Port to listen on (default: 5003)
        """
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.clients = {}
        self.tank = Tank()
        self.command_handlers = {
            'MOVE_FORWARD': self._handle_move_forward,
            'MOVE_BACKWARD': self._handle_move_backward,
            'TURN_LEFT': self._handle_turn_left,
            'TURN_RIGHT': self._handle_turn_right,
            'STOP': self._handle_stop,
            'SET_SERVO': self._handle_set_servo,
            'SET_LED': self._handle_set_led,
            'SET_LED_COLOR': self._handle_set_led_color,
            'GET_DISTANCE': self._handle_get_distance,
            'SET_ARM_POSITION': self._handle_set_arm_position,
            'SET_CAMERA_TILT': self._handle_set_camera_tilt,
        }
    
    def start(self) -> None:
        """Start the tank server."""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Tank server started on {self.host}:{self.port}")
        
        # Start accepting connections in a separate thread
        accept_thread = threading.Thread(target=self._accept_connections)
        accept_thread.daemon = True
        accept_thread.start()
    
    def stop(self) -> None:
        """Stop the tank server and clean up resources."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        # Close all client connections
        for client_socket in list(self.clients.keys()):
            self._remove_client(client_socket)
        
        # Clean up tank resources
        if hasattr(self.tank, 'close'):
            self.tank.close()
    
    def _accept_connections(self) -> None:
        """Accept incoming client connections."""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address}")
                
                # Start a new thread to handle the client
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
                # Store the client socket and thread
                self.clients[client_socket] = client_thread
                
            except (OSError, socket.error) as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client_address: tuple) -> None:
        """Handle communication with a connected client."""
        buffer = ""
        
        try:
            while self.running:
                # Receive data from client
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    buffer += data.decode('utf-8')
                    
                    # Process complete commands (ending with newline)
                    while '\n' in buffer:
                        command, _, buffer = buffer.partition('\n')
                        if command.strip():
                            response = self._process_command(command.strip())
                            if response is not None:
                                client_socket.sendall((json.dumps(response) + '\n').encode('utf-8'))
                
                except (socket.timeout, socket.error) as e:
                    if isinstance(e, socket.timeout):
                        continue
                    print(f"Error receiving data from {client_address}: {e}")
                    break
                    
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
            
        finally:
            print(f"Client {client_address} disconnected")
            self._remove_client(client_socket)
    
    def _remove_client(self, client_socket: socket.socket) -> None:
        """Remove a client and close its connection."""
        if client_socket in self.clients:
            try:
                client_socket.close()
            except:
                pass
            del self.clients[client_socket]
    
    def _process_command(self, command_str: str) -> Dict[str, Any]:
        """Process a command string and return a response."""
        parts = command_str.split('#')
        if not parts:
            return {"status": "error", "message": "Empty command"}
        
        command = parts[0]
        args = parts[1:]
        
        handler = self.command_handlers.get(command)
        if not handler:
            return {"status": "error", "message": f"Unknown command: {command}"}
        
        try:
            return handler(*args)
        except Exception as e:
            return {"status": "error", "message": f"Error executing {command}: {str(e)}"}
    
    # Command handlers
    def _handle_move_forward(self, speed_str: str) -> Dict[str, Any]:
        """Handle MOVE_FORWARD command."""
        try:
            speed = int(speed_str)
            # Convert 0-100 speed to -1000-1000 range used by the motor
            motor_speed = int((speed / 100.0) * 1000)
            self.tank.motor_system.setMotorModel(motor_speed, motor_speed)
            return {"status": "success", "message": f"Moving forward at {speed}%"}
        except (ValueError, TypeError) as e:
            return {"status": "error", "message": f"Invalid speed: {speed_str}"}
    
    def _handle_move_backward(self, speed_str: str) -> Dict[str, Any]:
        """Handle MOVE_BACKWARD command."""
        try:
            speed = int(speed_str)
            # Convert 0-100 speed to -1000-1000 range (negative for backward)
            motor_speed = -int((speed / 100.0) * 1000)
            self.tank.motor_system.setMotorModel(motor_speed, motor_speed)
            return {"status": "success", "message": f"Moving backward at {speed}%"}
        except (ValueError, TypeError) as e:
            return {"status": "error", "message": f"Invalid speed: {speed_str}"}
    
    def _handle_turn_left(self, speed_str: str) -> Dict[str, Any]:
        """Handle TURN_LEFT command."""
        try:
            speed = int(speed_str)
            motor_speed = int((speed / 100.0) * 1000)
            self.tank.motor_system.setMotorModel(-motor_speed, motor_speed)
            return {"status": "success", "message": f"Turning left at {speed}%"}
        except (ValueError, TypeError) as e:
            return {"status": "error", "message": f"Invalid speed: {speed_str}"}
    
    def _handle_turn_right(self, speed_str: str) -> Dict[str, Any]:
        """Handle TURN_RIGHT command."""
        try:
            speed = int(speed_str)
            motor_speed = int((speed / 100.0) * 1000)
            self.tank.motor_system.setMotorModel(motor_speed, -motor_speed)
            return {"status": "success", "message": f"Turning right at {speed}%"}
        except (ValueError, TypeError) as e:
            return {"status": "error", "message": f"Invalid speed: {speed_str}"}
    
    def _handle_stop(self) -> Dict[str, Any]:
        """Handle STOP command."""
        self.tank.motor_system.setMotorModel(0, 0)
        return {"status": "success", "message": "Stopped"}
    
    def _handle_set_servo(self, channel_str: str, angle_str: str) -> Dict[str, Any]:
        """Handle SET_SERVO command."""
        try:
            channel = int(channel_str)
            angle = int(angle_str)
            # Ensure angle is within valid range
            angle = max(0, min(180, angle))
            self.tank.set_servo_angle(str(channel), angle)
            return {"status": "success", "message": f"Set servo {channel} to {angle}°"}
        except (ValueError, TypeError) as e:
            return {"status": "error", "message": f"Invalid servo parameters: {channel_str}, {angle_str}"}
    
    def _handle_set_led(self, led_id_str: str, state_str: str) -> Dict[str, Any]:
        """Handle SET_LED command."""
        try:
            led_id = int(led_id_str)
            state = int(state_str) != 0  # Convert to boolean
            # Assuming the LED board is available as led_board in the tank
            if hasattr(self.tank, 'led_board'):
                self.tank.led_board.set_led(led_id, state)
                return {"status": "success", "message": f"Set LED {led_id} to {'on' if state else 'off'}"}
            else:
                return {"status": "error", "message": "LED board not available"}
        except (ValueError, TypeError, AttributeError) as e:
            return {"status": "error", "message": f"Invalid LED parameters: {led_id_str}, {state_str}"}
    
    def _handle_set_led_color(self, led_id_str: str, r_str: str, g_str: str, b_str: str) -> Dict[str, Any]:
        """Handle SET_LED_COLOR command."""
        try:
            led_id = int(led_id_str)
            r = int(r_str)
            g = int(g_str)
            b = int(b_str)
            
            # Clamp values to 0-255
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            # Assuming the LED board supports RGB and is available as led_board in the tank
            if hasattr(self.tank, 'led_board') and hasattr(self.tank.led_board, 'set_led_color'):
                self.tank.led_board.set_led_color(led_id, r, g, b)
                return {"status": "success", "message": f"Set LED {led_id} to RGB({r}, {g}, {b})"}
            else:
                return {"status": "error", "message": "RGB LED control not available"}
        except (ValueError, TypeError, AttributeError) as e:
            return {"status": "error", "message": f"Invalid LED color parameters: {led_id_str}, {r_str}, {g_str}, {b_str}"}
    
    def _handle_get_distance(self) -> Dict[str, Any]:
        """Handle GET_DISTANCE command."""
        try:
            if hasattr(self.tank, 'ultrasonic'):
                distance = self.tank.ultrasonic.get_distance()
                return {"status": "success", "data": distance}
            else:
                return {"status": "error", "message": "Ultrasonic sensor not available"}
        except Exception as e:
            return {"status": "error", "message": f"Error reading distance: {str(e)}"}
    
    def _handle_set_arm_position(self, joint: str, angle_str: str) -> Dict[str, Any]:
        """Handle SET_ARM_POSITION command."""
        try:
            angle = int(angle_str)
            angle = max(0, min(180, angle))  # Clamp angle
            
            if hasattr(self.tank, 'arm'):
                # Create a position dictionary for the arm
                position = {joint: angle}
                self.tank.arm.set_position(position)
                return {"status": "success", "message": f"Set {joint} to {angle}°"}
            else:
                return {"status": "error", "message": "Arm not available"}
        except (ValueError, TypeError, AttributeError) as e:
            return {"status": "error", "message": f"Invalid arm position parameters: {joint}, {angle_str}"}
    
    def _handle_set_camera_tilt(self, angle_str: str) -> Dict[str, Any]:
        """Handle SET_CAMERA_TILT command."""
        try:
            angle = int(angle_str)
            angle = max(0, min(180, angle))  # Clamp angle
            
            # Assuming the camera tilt is controlled by a servo on channel 3
            # Adjust the channel number as needed for your setup
            self.tank.set_servo_angle('3', angle)
            return {"status": "success", "message": f"Set camera tilt to {angle}°"}
        except (ValueError, TypeError, AttributeError) as e:
            return {"status": "error", "message": f"Invalid camera tilt angle: {angle_str}"}


def main():
    """Main function to run the tank server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tank Robot Server')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host address to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5003,
                       help='Port to listen on (default: 5003)')
    
    args = parser.parse_args()
    
    server = TankServer(host=args.host, port=args.port)
    
    try:
        print(f"Starting tank server on {args.host}:{args.port}")
        print("Press Ctrl+C to stop")
        server.start()
        
        # Keep the main thread alive
        while True:
            try:
                # Just sleep and check for keyboard interrupt
                import time
                time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.stop()
        print("Server stopped")


if __name__ == "__main__":
    main()
