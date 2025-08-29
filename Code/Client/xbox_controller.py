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
    """Defines safe operating limits for servos. 
    This lines up with the limits set in other parts of the codebase
    These angles ensure the code does not send commands that would damage the servos
    """
    min_angle: int = 90
    max_angle: int = 150
    default_horizontal: int = 90
    default_vertical: int = 140

class XboxController(QObject): 
    """Handles Xbox controller input and mapping to tank robot controls.
    Inherits from an existing python module. 
    Note that I am using this, in order to keep this script consistent with the rest of the code base. 
    A future improvement could be to switch this out for a more modern applicaiton
    """
    
    # Signal definitions
    movement_changed = pyqtSignal(bool, bool, bool, bool)
    button_pressed = pyqtSignal(int)
    controller_status = pyqtSignal(str)  # New signal for status updates
    
    #Set up a global dictionary, that maps the button number for an xbox, to the keyboard hotkey that has been linked to the UI 
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
        
        # State tracking. Allows for easy tracking for which direction robot intends to move 
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
        # deadzone: float to define the range from -1 to 1 in which no movement is reported
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
    # Next 4 functions interact with the attribute of the Xbox controller class, which is updated depending on which directions movement is occuring      
    def is_moving_forward(self) -> bool:
        """Check if moving forward."""
        return self.movement_state.get("forward", False) 
        
    def is_moving_backward(self) -> bool:
        """Check if moving backward."""
        return self.movement_state.get("backward", False)
        
    def is_turning_left(self) -> bool:
        """Check if turning left."""
        return self.movement_state.get("left", False)
        
    def is_turning_right(self) -> bool:
        """Check if turning right."""
        return self.movement_state.get("right", False)
    
    def _initialize_pygame(self) -> None:
        """Initialize pygame and controller with error handling."""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        try:
            pygame.display.init() #initialize basic modules (input and display)
            pygame.joystick.init()
            
            if pygame.joystick.get_count() == 0:
                raise NoControllersFoundError("No controllers found") # Stop code early if connection issue arises
                
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.initialized = True 
        except NoControllersFoundError as e:
            self.initialized = False
            raise
        except pygame.error as e:
            self.initialized = False
            raise JoystickInitializationError(f"Failed to initialize joystick: {e}")
        except pygame.error:
            self.initialized = False
            raise PygameInitializationError("Failed to initialize pygame")
    
    def _cleanup_resources(self) -> None:
        """Safely cleanup pygame resources."""
        try:
            if self.joystick:
                self.joystick.quit()
            if pygame.get_init():
                pygame.quit()
        except Exception as e:
            print(f"Error during cleanup: {e}") # generic error if anythig goes wrong
        finally:
            self.initialized = False # reset flag if everything works fine, priming the script to re-intilize later if needed
    
    def _update_movement(self, x: float, y: float) -> None:
        """
        Update movement based on stick position with input validation.
        Args:
            x: X-axis position (-1 to 1)
            y: Y-axis position (-1 to 1)
        """
        try:
            # These values are out of bounds; if these come up, there must be a big problem somewhere, in between the program and the xbox controller. 
            # Because of this, just raise an error if they come up. 
            if not (-1 <= x <= 1) or not (-1 <= y <= 1): 
                raise ValueError("Invalid joystick values")
            
            # Update the boolean states, if joysticks are outside of the deadzones
            new_state = {
                "forward": y < -self.deadzone,
                "backward": y > self.deadzone,
                "left": x < -self.deadzone,
                "right": x > self.deadzone
            }
            
            # Emit the movement changed signal if the states have changed
            if new_state != self.movement_state:
                self.movement_state = new_state
                self.movement_changed.emit(
                    new_state["forward"],
                    new_state["backward"],
                    new_state["left"],
                    new_state["right"]
                )
        except Exception as e:
            self.controller_status.emit(f"Movement update error: {e}") # Generic error if something goes wrong
    
    def _update_servo(self, x: float, y: float) -> None:
        """
        Update servo positions with safety bounds and error handling.
        Args:
            x: X-axis position for horizontal servo
            y: Y-axis position for vertical servo
        """
        try:
            # Check if the stick is outside of the deadzone
            if abs(x) > self.deadzone:
                # Calculate the new position for the horizontal servo
                new_horizontal = self.servo_position["horizontal"] + int(x * 5)
                # Update the position with safety bounds
                self.servo_position["horizontal"] = max(
                    self.servo_limits.min_angle,
                    min(self.servo_limits.max_angle, new_horizontal)
                )
            
            if abs(y) > self.deadzone:
                # Calculate the new position for the vertical servo
                new_vertical = self.servo_position["vertical"] - int(y * 5)
                # Update the position with safety bounds
                self.servo_position["vertical"] = max(
                    self.servo_limits.min_angle,
                    min(self.servo_limits.max_angle, new_vertical)
                )
            
            # Send the updated commands to the hardware
            self._send_servo_commands()
        except Exception as e:
            # Handle any errors that occur during the update
            self.controller_status.emit(f"Servo update error: {e}")
    
    def _send_servo_commands(self) -> None:
        """
        Send validated servo commands to hardware.
        """
        try:
            # Update the UI sliders
            self.main_window.HSlider_Servo1.setValue(self.servo_position["horizontal"])
            self.main_window.VSlider_Servo2.setValue(self.servo_position["vertical"])
            
            # Send commands to the hardware
            for servo_id, position in enumerate([
                self.servo_position["horizontal"],
                self.servo_position["vertical"]
            ]):
                # Construct the command string
                cmd_str = (f"{cmd.CMD_SERVO}{self.main_window.intervalChar}"
                          f"{servo_id}{self.main_window.intervalChar}"
                          f"{position}{self.main_window.endChar}")
                # Send the command to the hardware
                self.main_window.TCP.sendData(cmd_str)
        except Exception as e:
            # Handle any errors that occur during the send process
            self.controller_status.emit(f"Failed to send servo commands: {e}")
    
    def _run(self) -> None:
        """
        Main controller loop with comprehensive error handling.
        """
        if not self.initialized:
            # Handle the case when the controller is not properly initialized
            self.controller_status.emit("Controller not properly initialized")
            return
            
        try:
            while self.running:
                # Handle all events in the event queue
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
            # Handle any errors that occur during the main loop
            self.controller_status.emit(f"Controller error: {e}")
        finally:
            # Clean up any resources when the loop finishes
            self._cleanup_resources()
    
    def _handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle pygame events with type checking.
        """
        try:
            # Check if the event is a button press
            if event.type == pygame.JOYBUTTONDOWN and event.button in self.BUTTON_MAPPING:
                # Get the key and modifier for the button press
                key, _ = self.BUTTON_MAPPING[event.button]
                # Post a key press event to the main window
                QCoreApplication.postEvent(
                    self.main_window,
                    QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
                )
                # Emit the button pressed signal
                self.button_pressed.emit(event.button)
            # Check if the event is a hat motion
            elif event.type == pygame.JOYHATMOTION and any(event.value):
                # Get the key for the hat motion
                key = Qt.Key_L if event.value[1] else Qt.Key_Q
                # Post a key press event to the main window
                QCoreApplication.postEvent(
                    self.main_window,
                    QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
                )
        except Exception as e:
            # Handle any errors that occur during event handling
            self.controller_status.emit(f"Event handling error: {e}")