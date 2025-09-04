import os
import pygame
import time
import threading
from Command import COMMAND as cmd
from PyQt5.QtCore import QObject, pyqtSignal, QEvent, QCoreApplication
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt

class XboxController(QObject):
    movement_changed = pyqtSignal(bool, bool, bool, bool)
    button_pressed = pyqtSignal(int)
    
    # Button to key mapping
    BUTTON_MAPPING = {
        0: (Qt.Key_L, "Toggle LED Mode"),     # A - Toggle LED mode
        1: (Qt.Key_V, "Toggle Camera View"),  # B - Toggle camera view
        2: (Qt.Key_P, "Drop Object"),         # X - Drop object
        # Y button (3), Back button (6), and Start button (7) are intentionally left unmapped
    }
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.running = False
        
        # Simplified state tracking
        self.movement_state = {"forward": False, "backward": False, "left": False, "right": False}
        self.servo_position = {"horizontal": 90, "vertical": 140}  # Default positions
        self.deadzone = 0.2
    
    def start(self):
        """Start the controller input thread."""
        if not self.running:
            self.running = True
            threading.Thread(target=self._run, daemon=True).start()
    
    def stop(self):
        """Stop the controller input thread."""
        self.running = False
    
    def is_moving_forward(self):
        """Check if moving forward."""
        return self.movement_state["forward"]
    
    def is_moving_backward(self):
        """Check if moving backward."""
        return self.movement_state["backward"]
    
    def is_turning_left(self):
        """Check if turning left."""
        return self.movement_state["left"]
    
    def is_turning_right(self):
        """Check if turning right."""
        return self.movement_state["right"]
    
    def _update_movement(self, x, y):
        """Update movement based on stick position."""
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
    
    def _update_servo(self, x, y):
        """Update servo positions with bounds checking."""
        if abs(x) > self.deadzone:
            self.servo_position["horizontal"] = max(90, min(150, 
                self.servo_position["horizontal"] + int(x * 5)))
        
        if abs(y) > self.deadzone:
            self.servo_position["vertical"] = max(90, min(150, 
                self.servo_position["vertical"] - int(y * 5)))
            
        # Update UI and send commands
        try:
            self.main_window.HSlider_Servo1.setValue(self.servo_position["horizontal"])
            self.main_window.VSlider_Servo2.setValue(self.servo_position["vertical"])
            
            for servo_id, position in enumerate([self.servo_position["horizontal"], 
                                               self.servo_position["vertical"]]):
                cmd_str = (f"{cmd.CMD_SERVO}{self.main_window.intervalChar}"
                          f"{servo_id}{self.main_window.intervalChar}"
                          f"{position}{self.main_window.endChar}")
                self.main_window.TCP.sendData(cmd_str)
        except Exception as e:
            print(f"Servo update error: {e}")
    
    def _run(self):
        """Main controller loop."""
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        
        try:
            pygame.display.init()
            pygame.joystick.init()
            
            if pygame.joystick.get_count() == 0:
                print("No controllers found")
                return
                
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN and event.button in self.BUTTON_MAPPING:
                        key, _ = self.BUTTON_MAPPING[event.button]
                        QCoreApplication.postEvent(self.main_window, 
                            QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier))
                        self.button_pressed.emit(event.button)
                    elif event.type == pygame.JOYHATMOTION and any(event.value):
                        key = Qt.Key_L if event.value[1] else Qt.Key_Q
                        QCoreApplication.postEvent(self.main_window,
                            QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier))
                
                # Update movement and servos
                self._update_movement(joystick.get_axis(0), joystick.get_axis(1))
                self._update_servo(joystick.get_axis(2), joystick.get_axis(3))
                
                time.sleep(0.01)
                
        except Exception as e:
            print(f"Controller error: {e}")
        finally:
            if pygame.get_init():
                pygame.quit()