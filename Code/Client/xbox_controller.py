import pygame
import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal, QEvent, Qt
from PyQt5.QtGui import QKeyEvent

class XboxController(QObject):
    # Define signals
    movement_changed = pyqtSignal(bool, bool, bool, bool)  # forward, backward, left, right
    button_pressed = pyqtSignal(int)  # button number
    """Xbox controller class for Freenove Tank Robot.
    
    Buttons:
    - A: Toggle Pinch Object (O key)
    - B: Toggle Drop Object (P key)
    - X: Toggle Video Feed (V key)
    - Y: Reset camera to home position (Home key)
    - D-Pad Up/Down: Cycle LED modes (L key)
    - D-Pad Left/Right: Cycle operation modes (Q key)
    - Start: Connect to robot (C key)
    - Back: Toggle Ultrasonic sensor
    - Left Stick: Movement (WASD keys)
    """
    
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
        
        # Movement states
        self.moving_forward = False
        self.moving_backward = False
        self.turning_left = False
        self.turning_right = False
        
        # Button states (to track button down/up)
        self.buttons = {
            0: False,  # A
            1: False,  # B
            2: False,  # X
            3: False,  # Y
            4: False,  # LB
            5: False,  # RB
            6: False,  # Back
            7: False,  # Start
            8: False,  # Left stick press
            9: False   # Right stick press
        }
        
        # Deadzone for analog sticks (to ignore small movements)
        self.deadzone = 0.1
        
        # Movement states
        self.moving_forward = False
        self.moving_backward = False
        self.turning_left = False
        self.turning_right = False
    
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
        new_forward = left_y < -deadzone
        new_backward = left_y > deadzone
        new_left = left_x < -deadzone
        new_right = left_x > deadzone
        
        # Only update if there's a change to prevent unnecessary signals
        if (new_forward != self.moving_forward or 
            new_backward != self.moving_backward or
            new_left != self.turning_left or 
            new_right != self.turning_right):
            
            self.moving_forward = new_forward
            self.moving_backward = new_backward
            self.turning_left = new_left
            self.turning_right = new_right

    def _run(self):
        """Main controller input loop."""
        # Set environment variable to use dummy video driver (no window)
        import os
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        
        try:
            # Initialize pygame without display
            pygame.display.init()
            pygame.joystick.init()
            
            # Check for controllers
            joystick_count = pygame.joystick.get_count()
            if joystick_count == 0:
                print("No controllers found. Please connect your controller and try again.")
                return
                
            # Initialize the first joystick
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            
            print(f"Xbox Controller connected: {joystick.get_name()}")
            
            # Main loop
            clock = pygame.time.Clock()
            while self.running:
                try:
                    # Process events
                    for event in pygame.event.get():
                        if event.type == pygame.JOYBUTTONDOWN:
                            self._handle_button_press(event.button)
                        elif event.type == pygame.JOYBUTTONUP:
                            self._handle_button_release(event.button)
                        elif event.type == pygame.JOYAXISMOTION:
                            self._handle_axis_event(event)
                        elif event.type == pygame.JOYHATMOTION:
                            self._handle_hat_motion(event.value)
                            
                    # Update movement states based on current stick positions
                    if hasattr(joystick, 'get_axis'):
                        # Get left stick position
                        left_x = joystick.get_axis(0)  # Axis 0: left stick horizontal
                        left_y = -joystick.get_axis(1)  # Axis 1: left stick vertical (inverted)
                        
                        # Update movement states
                        self._update_movement_states(left_x, left_y)
                        
                except Exception as e:
                    print(f"Error in controller thread: {e}")
                    time.sleep(1)
                    break
                
                time.sleep(0.01)  # Small delay to prevent high CPU usage
                
        except Exception as e:
            print(f"Fatal error in controller thread: {e}")
        finally:
            if pygame.get_init():
                pygame.quit()
                print("Controller disconnected")
    
    def _handle_axis_event(self, event):
        """Handle joystick axis movement events."""
        # Left stick X axis (horizontal)
        if event.axis == 0:
            self.left_x = event.value if abs(event.value) > self.deadzone else 0
        # Left stick Y axis (vertical, inverted)
        elif event.axis == 1:
            self.left_y = -event.value if abs(event.value) > self.deadzone else 0
        # Right stick X axis (horizontal)
        elif event.axis == 2:
            self.right_x = event.value if abs(event.value) > self.deadzone else 0
        # Right stick Y axis (vertical, inverted)
        elif event.axis == 3:
            self.right_y = -event.value if abs(event.value) > self.deadzone else 0
    
    def _handle_button_press(self, button):
        """Handle button press events."""
        if button in self.buttons:
            self.buttons[button] = True
            self._on_button_pressed(button)
    
    def _handle_button_release(self, button):
        """Handle button release events."""
        if button in self.buttons:
            self.buttons[button] = False
    
    def _on_button_pressed(self, button):
        """Handle button press actions."""
        # Emit signal for button press
        self.button_pressed.emit(button)
        
        # Map buttons to keyboard keys
        if button == 0:  # A button
            self.main_window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_O, Qt.NoModifier))
        elif button == 1:  # B button
            self.main_window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_P, Qt.NoModifier))
        elif button == 2:  # X button
            self.main_window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_V, Qt.NoModifier))
        elif button == 3:  # Y button
            self.main_window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Home, Qt.NoModifier))
        elif button == 6:  # Back button
            self.main_window.on_btn_Ultrasonic()
        elif button == 7:  # Start button
            self.main_window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_C, Qt.NoModifier))
    
    def _handle_hat_motion(self, value):
        """Handle D-pad movement."""
        # D-pad up/down (cycle LED modes)
        if value[1] == 1:  # Up
            self.main_window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_L, Qt.NoModifier))
        elif value[1] == -1:  # Down
            self.main_window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_L, Qt.NoModifier))
        # D-pad left/right (cycle operation modes)
        if value[0] == -1:  # Left
            self.main_window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Q, Qt.NoModifier))
        elif value[0] == 1:  # Right
            self.main_window.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Q, Qt.NoModifier))
    
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
    
    @staticmethod
    def _create_key_event(key):
        """Create a QKeyEvent for simulating key presses."""
        from PyQt5.QtCore import Qt, QEvent
        from PyQt5.QtGui import QKeyEvent
        return QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)

def print_controller_inputs():
    """Test controller and print movement status in a user-friendly way."""
    # Initialize pygame and joystick module
    pygame.init()
    pygame.joystick.init()
    
    # Set up the display (required for some joystick backends)
    pygame.display.set_mode((1, 1))  # Minimal window
    
    try:
        # Check for controllers
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            print("No controllers found. Please connect your controller and try again.")
            return
            
        # Initialize the first joystick
        try:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
        except pygame.error as e:
            print(f"Error initializing joystick: {e}")
            return
            
        print(f"\nTesting controller: {joystick.get_name()}")
        print("Left Stick: Move | A: Toggle Pinch | B: Toggle Drop | X: Toggle Video | Y: Reset Camera")
        print("Start: Connect | Back: Toggle Ultrasonic | D-Pad: Cycle Modes")
        print("-" * 50)
        print("Press CTRL+C to return to menu\n")
        
        # Movement states
        moving_forward = False
        moving_backward = False
        turning_left = False
        turning_right = False
        
        # Button states
        button_states = {
            0: False,  # A
            1: False,  # B
            2: False,  # X
            3: False,  # Y
            4: False,  # LB
            5: False,  # RB
            6: False,  # Back
            7: False,  # Start
            8: False,  # Left stick press
            9: False   # Right stick press
        }
        
        # Deadzone for analog sticks
        deadzone = 0.2
        
        # Last status to avoid printing duplicates
        last_status = ""
        
        # Set up the clock for a decent frame rate
        clock = pygame.time.Clock()
        
        # Main loop
        running = True
        while running:
            try:
                status = []
                
                # Process events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    
                    # Handle button presses
                    elif event.type == pygame.JOYBUTTONDOWN:
                        if event.button in button_states:
                            button_states[event.button] = True
                            
                            # Map buttons to actions
                            if event.button == 0:  # A
                                status.append("ACTION: Toggle Pinch Object")
                            elif event.button == 1:  # B
                                status.append("ACTION: Toggle Drop Object")
                            elif event.button == 2:  # X
                                status.append("ACTION: Toggle Video Feed")
                            elif event.button == 3:  # Y
                                status.append("ACTION: Reset Camera")
                            elif event.button == 6:  # Back
                                status.append("ACTION: Toggle Ultrasonic")
                            elif event.button == 7:  # Start
                                status.append("ACTION: Connect to Robot")
                    
                    # Handle button releases
                    elif event.type == pygame.JOYBUTTONUP:
                        if event.button in button_states:
                            button_states[event.button] = False
                    
                    # Handle D-pad
                    elif event.type == pygame.JOYHATMOTION:
                        if event.value != (0, 0):
                            x, y = event.value
                            if y > 0:
                                status.append("D-Pad: Up - Cycle LED Modes")
                            elif y < 0:
                                status.append("D-Pad: Down - Cycle LED Modes")
                            if x < 0:
                                status.append("D-Pad: Left - Cycle Operation Modes")
                            elif x > 0:
                                status.append("D-Pad: Right - Cycle Operation Modes")
                
                # Check left stick for movement
                left_x = joystick.get_axis(0)
                left_y = joystick.get_axis(1)
                
                # Reset movement states
                new_moving_forward = False
                new_moving_backward = False
                new_turning_left = False
                new_turning_right = False
                
                # Check stick positions
                if abs(left_y) > deadzone:
                    if left_y < -deadzone:
                        new_moving_forward = True
                        status.append("MOVING: Forward")
                    elif left_y > deadzone:
                        new_moving_backward = True
                        status.append("MOVING: Backward")
                
                if abs(left_x) > deadzone:
                    if left_x < -deadzone:
                        new_turning_left = True
                        status.append("TURNING: Left")
                    elif left_x > deadzone:
                        new_turning_right = True
                        status.append("TURNING: Right")
                
                # Check for no movement
                if not any([new_moving_forward, new_moving_backward, new_turning_left, new_turning_right]):
                    status.append("STATUS: Stopped")
                
                # Update states
                moving_forward = new_moving_forward
                moving_backward = new_moving_backward
                turning_left = new_turning_left
                turning_right = new_turning_right
                
                # Print status if it changed
                current_status = " | ".join(status) if status else "STATUS: No input"
                if current_status != last_status:
                    print("\r" + " " * 80, end="")  # Clear line
                    print(f"\r{current_status}", end="", flush=True)
                    last_status = current_status
                
                # Cap the frame rate and handle events
                clock.tick(30)
                pygame.event.pump()  # Process event queue
                
            except KeyboardInterrupt:
                print("\nExiting...")
                running = False
            except Exception as e:
                print(f"\nError: {e}")
                running = False
                
    except Exception as e:
        print(f"\nError: {e}")
    
    finally:
        # Clean up
        pygame.joystick.quit()
        pygame.quit()
        print("\nController test ended.")
        # Small delay to ensure clean exit
        time.sleep(0.5)

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
                print_controller_inputs()
                # After returning from test, show menu again
                print("\n" + "="*50)
                print("Xbox Controller Utility")
                print("1. Test controller movement")
                print("2. List connected controllers")
                print("3. Integration help")
                print("4. Exit")
            elif choice == '2':
                list_controllers()
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
