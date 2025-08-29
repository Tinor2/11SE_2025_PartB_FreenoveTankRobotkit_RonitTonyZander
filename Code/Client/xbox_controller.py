import pygame
import time
import threading
import os
from typing import Dict, Tuple
from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal, QEvent, QCoreApplication
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt

@dataclass
class ServoLimits:
    """Defines safe operating limits for servos."""
    min_angle: int = 90
    max_angle: int = 150
    default_horizontal: int = 90
    default_vertical: int = 140

class XboxController(QObject):
    """Handles Xbox controller input and mapping to tank robot controls."""
    
    # Signal definitions
    movement_changed = pyqtSignal(bool, bool, bool, bool)
    button_pressed = pyqtSignal(int)
    controller_status = pyqtSignal(str)  # New signal for status updates
    
    BUTTON_MAPPING: Dict[int, Tuple[int, str]] = {
        0: (Qt.Key_O, "Pinch Object"),    # A
        1: (Qt.Key_P, "Drop Object"),     # B
        2: (Qt.Key_V, "Toggle Video"),    # X
        3: (Qt.Key_Home, "Reset Camera"), # Y
        6: (Qt.Key_U, "Ultrasonic"),      # Back
        7: (Qt.Key_C, "Connect")          # Start
    }
    
    def __init__(self, main_window) -> None:
        """Initialize controller with safety parameters and state tracking."""
        super().__init__()
        self.main_window = main_window
        self.running = False
        self.initialized = False
        
        # State tracking
        self.movement_state = {
            "forward": False, 
            "backward": False, 
            "left": False, 
            "right": False
        }
        
        # Hardware safety parameters
        self.servo_limits = ServoLimits()
        self.servo_position = {
            "horizontal": self.servo_limits.default_horizontal,
            "vertical": self.servo_limits.default_vertical
        }
        self.deadzone = 0.2
        
        # Resource management
        self.joystick = None
    
    def start(self) -> None:
        """
        Start the controller input thread with initialization checks.
        Emits status updates for debugging.
        """
        if not self.running:
            try:
                self._initialize_pygame()
                self.running = True
                threading.Thread(target=self._run, daemon=True).start()
                self.controller_status.emit("Controller started successfully")
            except Exception as e:
                self.controller_status.emit(f"Failed to start controller: {e}")
                self.running = False
    
    def stop(self) -> None:
        """Safely stop the controller and clean up resources."""
        try:
            self.running = False
            if self.initialized:
                self._cleanup_resources()
            self.controller_status.emit("Controller stopped")
        except Exception as e:
            self.controller_status.emit(f"Error stopping controller: {e}")
    
    def _initialize_pygame(self) -> None:
        """Initialize pygame and controller with error handling."""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        try:
            pygame.display.init()
            pygame.joystick.init()
            
            if pygame.joystick.get_count() == 0:
                raise RuntimeError("No controllers found")
                
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.initialized = True
        except Exception as e:
            self.initialized = False
            raise RuntimeError(f"Failed to initialize controller: {e}")
    
    def _cleanup_resources(self) -> None:
        """Safely cleanup pygame resources."""
        try:
            if self.joystick:
                self.joystick.quit()
            if pygame.get_init():
                pygame.quit()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.initialized = False
    
    def _update_movement(self, x: float, y: float) -> None:
        """
        Update movement based on stick position with input validation.
        Args:
            x: X-axis position (-1 to 1)
            y: Y-axis position (-1 to 1)
        """
        try:
            if not (-1 <= x <= 1) or not (-1 <= y <= 1):
                raise ValueError("Invalid joystick values")
                
            new_state = {
                "forward": y < -self.deadzone,
                "backward": y > self.deadzone,
                "left": x < -self.deadzone,
                "right": x > self.deadzone
            }
            
            if new_state != self.movement_state:
                self.movement_state = new_state
                self.movement_changed.emit(
                    new_state["forward"],
                    new_state["backward"],
                    new_state["left"],
                    new_state["right"]
                )
        except Exception as e:
            self.controller_status.emit(f"Movement update error: {e}")
    
    def _update_servo(self, x: float, y: float) -> None:
        """
        Update servo positions with safety bounds and error handling.
        Args:
            x: X-axis position for horizontal servo
            y: Y-axis position for vertical servo
        """
        try:
            if abs(x) > self.deadzone:
                new_horizontal = self.servo_position["horizontal"] + int(x * 5)
                self.servo_position["horizontal"] = max(
                    self.servo_limits.min_angle,
                    min(self.servo_limits.max_angle, new_horizontal)
                )
            
            if abs(y) > self.deadzone:
                new_vertical = self.servo_position["vertical"] - int(y * 5)
                self.servo_position["vertical"] = max(
                    self.servo_limits.min_angle,
                    min(self.servo_limits.max_angle, new_vertical)
                )
            
            self._send_servo_commands()
        except Exception as e:
            self.controller_status.emit(f"Servo update error: {e}")
    
    def _send_servo_commands(self) -> None:
        """Send validated servo commands to hardware."""
        try:
            # Update UI
            self.main_window.HSlider_Servo1.setValue(self.servo_position["horizontal"])
            self.main_window.VSlider_Servo2.setValue(self.servo_position["vertical"])
            
            # Send commands
            for servo_id, position in enumerate([
                self.servo_position["horizontal"],
                self.servo_position["vertical"]
            ]):
                cmd_str = (f"{cmd.CMD_SERVO}{self.main_window.intervalChar}"
                          f"{servo_id}{self.main_window.intervalChar}"
                          f"{position}{self.main_window.endChar}")
                self.main_window.TCP.sendData(cmd_str)
        except Exception as e:
            self.controller_status.emit(f"Failed to send servo commands: {e}")
    
    def _run(self) -> None:
        """Main controller loop with comprehensive error handling."""
        if not self.initialized:
            self.controller_status.emit("Controller not properly initialized")
            return
            
        try:
            while self.running:
                for event in pygame.event.get():
                    self._handle_event(event)
                
                # Update movement and servos
                self._update_movement(
                    self.joystick.get_axis(0),
                    self.joystick.get_axis(1)
                )
                self._update_servo(
                    self.joystick.get_axis(2),
                    self.joystick.get_axis(3)
                )
                
                time.sleep(0.01)
                
        except Exception as e:
            self.controller_status.emit(f"Controller error: {e}")
        finally:
            self._cleanup_resources()
    
    def _handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events with type checking."""
        try:
            if event.type == pygame.JOYBUTTONDOWN and event.button in self.BUTTON_MAPPING:
                key, _ = self.BUTTON_MAPPING[event.button]
                QCoreApplication.postEvent(
                    self.main_window,
                    QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
                )
                self.button_pressed.emit(event.button)
            elif event.type == pygame.JOYHATMOTION and any(event.value):
                key = Qt.Key_L if event.value[1] else Qt.Key_Q
                QCoreApplication.postEvent(
                    self.main_window,
                    QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
                )
        except Exception as e:
            self.controller_status.emit(f"Event handling error: {e}")