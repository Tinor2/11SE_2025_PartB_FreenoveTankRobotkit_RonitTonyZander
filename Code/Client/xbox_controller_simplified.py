import pygame
import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal, QEvent, Qt
from PyQt5.QtGui import QKeyEvent

class XboxController(QObject):
    """Simplified Xbox controller class for Freenove Tank Robot.
    
    Features:
    - Left stick: Robot movement (WASD)
    - A/B/X/Y: Various actions (O/P/V/Home keys)
    - D-Pad: Cycle modes (Q/L keys)
    - Start/Back: Connect/Toggle Ultrasonic
    """
    
    # Signals for movement state changes
    movement_changed = pyqtSignal(bool, bool, bool, bool)  # forward, backward, left, right
    button_pressed = pyqtSignal(int)  # button number
    
    # Button mappings (button_number: (qt_key, method_name))
    BUTTON_MAP = {
        0: (Qt.Key_O, None),          # A: Toggle Pinch Object
        1: (Qt.Key_P, None),          # B: Toggle Drop Object
        2: (Qt.Key_V, None),          # X: Toggle Video Feed
        3: (Qt.Key_Home, None),       # Y: Reset camera
        6: (None, 'on_btn_Ultrasonic'), # Back: Toggle Ultrasonic
        7: (Qt.Key_C, None)           # Start: Connect to robot
    }
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.running = False
        self.thread = None
        
        # Controller state
        self.left_x = 0
        self.left_y = 0
        self.deadzone = 0.1  # Ignore small stick movements
        
        # Movement states
        self.moving_forward = False
        self.moving_backward = False
        self.turning_left = False
        self.turning_right = False
        
        # Set up pygame in headless mode
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        
    def start(self):
        """Start the controller input thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the controller input thread."""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _run(self):
        """Main controller input loop."""
        try:
            pygame.init()
            pygame.joystick.init()
            
            if pygame.joystick.get_count() == 0:
                print("No controllers found. Connect a controller and try again.")
                return
                
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            print(f"Xbox Controller connected: {joystick.get_name()}")
            
            while self.running:
                self._process_events(joystick)
                self._update_movement(joystick)
                time.sleep(0.01)
                
        except Exception as e:
            print(f"Controller error: {e}")
        finally:
            if pygame.get_init():
                pygame.quit()
    
    def _process_events(self, joystick):
        """Process all pending pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                self._handle_button(event.button)
            elif event.type == pygame.JOYHATMOTION:
                self._handle_hat(event.value)
    
    def _handle_button(self, button):
        """Handle button press events."""
        self.button_pressed.emit(button)
        
        if button not in self.BUTTON_MAP:
            return
            
        key, method = self.BUTTON_MAP[button]
        if key is not None:
            self._send_key_event(key)
        elif method and hasattr(self.main_window, method):
            getattr(self.main_window, method)()
    
    def _handle_hat(self, value):
        """Handle D-pad movement."""
        x, y = value
        # D-pad up/down: Cycle LED modes (L key)
        if y != 0:
            self._send_key_event(Qt.Key_L)
        # D-pad left/right: Cycle operation modes (Q key)
        if x != 0:
            self._send_key_event(Qt.Key_Q)
    
    def _update_movement(self, joystick):
        """Update movement based on left stick position."""
        # Get stick positions with deadzone
        self.left_x = joystick.get_axis(0)
        self.left_y = -joystick.get_axis(1)  # Invert Y axis
        
        # Apply deadzone
        if abs(self.left_x) < self.deadzone:
            self.left_x = 0
        if abs(self.left_y) < self.deadzone:
            self.left_y = 0
        
        # Update movement states
        new_forward = self.left_y > 0.5
        new_backward = self.left_y < -0.5
        new_left = self.left_x < -0.5
        new_right = self.left_x > 0.5
        
        # Only update if there's a change
        if (new_forward != self.moving_forward or 
            new_backward != self.moving_backward or
            new_left != self.turning_left or 
            new_right != self.turning_right):
            
            self.moving_forward = new_forward
            self.moving_backward = new_backward
            self.turning_left = new_left
            self.turning_right = new_right
            
            # Emit movement changed signal
            self.movement_changed.emit(
                self.moving_forward,
                self.moving_backward,
                self.turning_left,
                self.turning_right
            )
    
    def _send_key_event(self, key):
        """Send a key press event to the main window."""
        event = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier)
        self.main_window.keyPressEvent(event)
    
    # Movement state getters
    def is_moving_forward(self):
        return self.moving_forward
        
    def is_moving_backward(self):
        return self.moving_backward
        
    def is_turning_left(self):
        return self.turning_left
        
    def is_turning_right(self):
        return self.turning_right
