import pygame
import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal, QEvent, QCoreApplication
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt

class XboxController(QObject):
    # Define signals
    movement_changed = pyqtSignal(bool, bool, bool, bool)  # forward, backward, left, right
    button_pressed = pyqtSignal(int)  # button number
    
    def __init__(self, main_window):
        """Initialize the Xbox controller.
        
        Args:
            main_window: Reference to the main window instance
        """
        super().__init__()
        self.main_window = main_window
        self.running = False
        self.thread = None
        
        # Controller state
        self.left_x = 0
        self.left_y = 0
        self.right_x = 0
        self.right_y = 0
        
        # Movement states (duplicate states removed)
        self.moving_forward = False
        self.moving_backward = False
        self.turning_left = False
        self.turning_right = False
        
        # Servo control
        self.last_servo1 = 90  # Default center position for servo1 (horizontal)
        self.last_servo2 = 140  # Default center position for servo2 (vertical)
        self.last_servo_update = 0  # For rate limiting
        
        # Button states (simplified to only track necessary buttons)
        self.buttons = {
            0: False,  # A
            1: False,  # B
            2: False,  # X
            3: False,  # Y
            6: False,  # Back
            7: False,  # Start
        }
        
        # Deadzone for analog sticks
        self.deadzone = 0.1
    
    def start(self):
        """Start the controller input thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the controller input thread."""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def is_moving_forward(self):
        """Check if moving forward."""
        return self.moving_forward
        
    def is_moving_backward(self):
        """Check if moving backward."""
        return self.moving_backward
        
    def is_turning_left(self):
        """Check if turning left."""
        return self.turning_left
        
    def is_turning_right(self):
        """Check if turning right."""
        return self.turning_right
        
    def _update_movement_states(self, left_x, left_y):
        """Update movement states based on left stick position."""
        deadzone = 0.2
        
        # Update movement states based on stick position
        # Note: Y-axis is already inverted by pygame (up is negative, down is positive)
        new_forward = left_y < -deadzone  # Up on stick = forward
        new_backward = left_y > deadzone  # Down on stick = backward
        new_left = left_x < -deadzone     # Left on stick = turn left
        new_right = left_x > deadzone     # Right on stick = turn right
        
        # Only update if there's a change to prevent unnecessary signals
        if (new_forward != self.moving_forward or 
            new_backward != self.moving_backward or
            new_left != self.turning_left or 
            new_right != self.turning_right):
            
            self.moving_forward = new_forward
            self.moving_backward = new_backward
            self.turning_left = new_left
            self.turning_right = new_right
            
            # Emit the movement changed signal
            self.movement_changed.emit(
                self.moving_forward,
                self.moving_backward,
                self.turning_left,
                self.turning_right
            )

    def _run(self):
        """Main controller input loop."""
        # Set environment variable to use dummy video driver (no window)
        import os
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        
        try:
            # Initialize pygame without display
            pygame.display.init()
            pygame.joystick.init()
            
            if pygame.joystick.get_count() == 0:
                print("No controllers found. Please connect your controller and try again.")
                return
                
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            print(f"Xbox Controller connected: {joystick.get_name()}")
            
            # Main loop
            while self.running:
                try:
                    for event in pygame.event.get():
                        if event.type == pygame.JOYBUTTONDOWN:
                            self._handle_button_press(event.button)
                        elif event.type == pygame.JOYBUTTONUP:
                            self._handle_button_release(event.button)
                        elif event.type == pygame.JOYAXISMOTION:
                            self._handle_axis_event(event)
                        elif event.type == pygame.JOYHATMOTION:
                            self._handle_hat_motion(event.value)
                    
                    # Update movement based on left stick
                    left_x = joystick.get_axis(0)  # Axis 0: left stick horizontal
                    left_y = joystick.get_axis(1)  # Axis 1: left stick vertical
                    self._update_movement_states(left_x, left_y)
                    
                    # Get right stick values for servo control
                    right_x = joystick.get_axis(2)  # Axis 2: right stick horizontal
                    right_y = joystick.get_axis(3)  # Axis 3: right stick vertical (inverted)
                    self._update_servos(right_x, right_y)
                    
                    time.sleep(0.01)  # Prevent high CPU usage
                    
                except Exception as e:
                    print(f"Controller error: {e}")
                    break
                    
        except Exception as e:
            print(f"Controller initialization failed: {e}")
        finally:
            if pygame.get_init():
                pygame.quit()
                print("Controller disconnected")
    
    def _map_joystick_to_servo(self, value, servo_min=90, servo_max=150):
        """Map joystick value (-1 to 1) to servo angle (servo_min to servo_max)."""
        # Scale from [-1, 1] to [servo_min, servo_max]
        return int((value + 1) * (servo_max - servo_min) / 2 + servo_min)
    
    def _update_servos(self, right_x, right_y):
        """Update servo positions based on right joystick position."""
        # Apply deadzone
        if abs(right_x) < self.deadzone:
            right_x = 0
        if abs(right_y) < self.deadzone:
            right_y = 0
        
        # Store current values to detect changes
        old_servo1 = self.last_servo1
        old_servo2 = self.last_servo2
        
        # Update servo1 (horizontal) based on right stick X
        if right_x != 0:
            self.last_servo1 = max(90, min(150, self.last_servo1 + int(right_x * 5)))
            
        # Update servo2 (vertical) based on right stick Y (inverted)
        if right_y != 0:
            self.last_servo2 = max(90, min(150, self.last_servo2 - int(right_y * 5)))
        
        # Only update if there's a change
        if self.last_servo1 != old_servo1 or self.last_servo2 != old_servo2:
            print(f"[Servo] Moving to: H={self.last_servo1}°, V={self.last_servo2}°")
            
            # Update UI sliders
            self.main_window.HSlider_Servo1.setValue(self.last_servo1)
            self.main_window.VSlider_Servo2.setValue(self.last_servo2)
            
            # Send commands to the robot
            try:
                # Update horizontal servo (servo1)
                self.main_window.TCP.sendData(
                    cmd.CMD_SERVO + 
                    self.main_window.intervalChar + '0' + 
                    self.main_window.intervalChar + str(self.last_servo1) + 
                    self.main_window.endChar
                )
                
                # Update vertical servo (servo2)
                self.main_window.TCP.sendData(
                    cmd.CMD_SERVO + 
                    self.main_window.intervalChar + '1' + 
                    self.main_window.intervalChar + str(self.last_servo2) + 
                    self.main_window.endChar
                )
            except Exception as e:
                print(f"[Servo] Error sending servo command: {e}")
    
    def _handle_axis_event(self, event):
        """Handle joystick axis movement events."""
        # Left stick (movement)
        if event.axis == 0:  # Left stick X
            self.left_x = event.value if abs(event.value) > self.deadzone else 0
        elif event.axis == 1:  # Left stick Y (inverted)
            self.left_y = -event.value if abs(event.value) > 0.2 else 0
            
        # Right stick (camera/servo control)
        elif event.axis == 2:  # Right stick X
            self.right_x = event.value if abs(event.value) > self.deadzone else 0
        elif event.axis == 3:  # Right stick Y (inverted)
            self.right_y = -event.value if abs(event.value) > self.deadzone else 0
            
        # Update servos if right stick is being used
        if event.axis in [2, 3]:
            self._update_servos(self.right_x, self.right_y)
    
    def _handle_button_press(self, button):
        """Handle button press events."""
        if button in self.buttons:
            self.buttons[button] = True
            self.button_pressed.emit(button)
            
            # Map buttons to keyboard events
            key_mapping = {
                0: Qt.Key_O,    # A -> O (Pinch Object)
                1: Qt.Key_P,    # B -> P (Drop Object)
                2: Qt.Key_V,    # X -> V (Toggle Video)
                3: Qt.Key_Home, # Y -> Home (Reset Camera)
                6: Qt.Key_U,    # Back -> U (Ultrasonic)
                7: Qt.Key_C,    # Start -> C (Connect)
            }
            
            if button in key_mapping:
                key_event = QKeyEvent(QEvent.KeyPress, key_mapping[button], Qt.NoModifier)
                QCoreApplication.postEvent(self.main_window, key_event)
    
    def _handle_button_release(self, button):
        """Handle button release events."""
        if button in self.buttons:
            self.buttons[button] = False
    
    def _handle_hat_motion(self, value):
        """Handle D-pad movement."""
        if value[1] != 0:  # D-pad up/down
            key = Qt.Key_L  # LED mode toggle
        elif value[0] != 0:  # D-pad left/right
            key = Qt.Key_Q  # Operation mode toggle
        else:
            return
            
        key_event = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
        QCoreApplication.postEvent(self.main_window, key_event)
    
    def _handle_movement(self):
        """Handle continuous movement from analog sticks."""
        # Left stick: Movement (WASD keys)
        if self.left_y > 0.5:  # Forward (W)
            self.main_window.on_btn_ForWard()
        elif self.left_y < -0.5:  # Backward (S)
            self.main_window.on_btn_BackWard()
        elif self.left_x < -0.5:  # Left (A)
            self.main_window.on_btn_Turn_Left()
        elif self.left_x > 0.5:  # Right (D)
            self.main_window.on_btn_Turn_Right()
        else:
            self.main_window.on_btn_Stop()

def main():
    print("Xbox Controller Utility")
    print("1. Test controller movement")
    print("2. List connected controllers")
    print("3. Integration help")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nSelect an option (1-4): ").strip()
            if choice == '1':
                print("\nStarting controller test...")
                print("Move the left stick to control movement")
                print("Press buttons to see their actions")
                print("Press CTRL+C to return to menu\n")
                print("\n=== Controller Input Debug ===")
                print("Controller inputs will be displayed here as you use them.")
                print("Right Joystick Controls:")
                print("  - Left/Right: Control horizontal servo (90-150°)")
                print("  - Up/Down:    Control vertical servo (90-150°)")
                print("\nNo robot connection is needed to see the inputs.\n")
                # After returning from test, show menu again
                print("\n" + "="*50)
                print("Xbox Controller Utility")
                print("1. Test controller movement")
                print("2. List connected controllers")
                print("3. Integration help")
                print("4. Exit")
            elif choice == '2':
                print("Not implemented")
            elif choice == '3':
                print("\nTo use the controller in your application:")
                print("1. Import the controller: from xbox_controller import XboxController")
                print("2. In your main window's __init__ method, add:")
                print("   self.controller = XboxController(self)  # self is the main window")
                print("   self.controller.start()  # Start the controller thread")
                print("\nThe controller will automatically map to these actions:")
                print("- Left Stick: Move robot")
                print("- A/B/X/Y: Various actions (see test mode)")
                print("- D-Pad: Cycle modes")
                print("- Start/Back: Connect/Toggle sensors")
                input("\nPress Enter to return to menu...")
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please select a number between 1 and 4.")
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
