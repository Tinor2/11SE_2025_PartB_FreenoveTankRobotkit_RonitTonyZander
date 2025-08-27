# Xbox Controller Integration for Freenove Tank Robot

## Current Situation

We've successfully integrated an Xbox controller with the Freenove Tank Robot, allowing for wireless control of the robot's movement, camera, and various functions. The controller provides a more intuitive and responsive interface compared to keyboard controls.

## Xbox Controller Implementation (`xbox_controller.py`)

### Key Components

1. **XboxController Class**
   - Inherits from `QObject` for Qt signal/slot support
   - Runs in a separate thread to prevent UI blocking
   - Manages controller state and button mappings

2. **Controller Initialization**
   ```python
   def __init__(self, main_window):
       super().__init__()
       self.main_window = main_window
       self.running = False
       self.thread = None
       # Initialize controller state and button mappings
   ```

3. **Button Mappings**
   - **A Button (0)**: Toggle Pinch Object (O key)
   - **B Button (1)**: Toggle Drop Object (P key)
   - **X Button (2)**: Toggle Video Feed (V key)
   - **Y Button (3)**: Reset camera (Home key)
   - **Back Button (6)**: Toggle Ultrasonic sensor
   - **Start Button (7)**: Connect to robot (C key)
   - **D-pad**: Cycle modes (Q/L keys)
   - **Left Stick**: Robot movement

4. **Main Control Loop**
   ```python
   def _run(self):
       while self.running:
           # Process controller events
           for event in pygame.event.get():
               if event.type == pygame.JOYBUTTONDOWN:
                   self._handle_button_press(event.button)
               elif event.type == pygame.JOYAXISMOTION:
                   self._handle_axis_event(event)
               # ... other event types
   ```

5. **Movement Handling**
   - Uses left stick for directional control
   - Implements deadzone to prevent drift
   - Maps stick positions to movement commands

## Main Application Integration (`Main.py`)

### Key Components

1. **Controller Initialization**
   ```python
   # In mywindow.__init__()
   try:
       self.xbox_controller = XboxController(self)
       self.xbox_controller.start()
   except Exception as e:
       print(f"Failed to initialize Xbox controller: {e}")
   ```

2. **Key Press Integration**
   The controller simulates key presses that are handled by the existing `keyPressEvent` method:
   ```python
   def keyPressEvent(self, event):
       # ... existing key handling ...
       if event.key() == Qt.Key_W or \
          (hasattr(self, 'xbox_controller') and self.xbox_controller and 
           self.xbox_controller.is_moving_forward()):
           self.on_btn_ForWard()
       # ... other key mappings ...
   ```

3. **Cleanup**
   ```python
   def closeEvent(self, event):
       if hasattr(self, 'xbox_controller') and self.xbox_controller:
           self.xbox_controller.stop()
       # ... other cleanup ...
   ```

## Integration Guide

### Prerequisites
- Pygame installed (`pip install pygame`)
- Xbox controller connected and recognized by the system

### Setup Steps
1. Ensure the controller is properly connected to your computer
2. The controller will be automatically initialized when the application starts
3. Use the controller as follows:
   - Left stick: Move robot
   - A/B/X/Y: Various actions
   - D-pad: Cycle modes
   - Start/Back: Connect/Toggle sensors

### Troubleshooting
1. **Controller Not Detected**
   - Check USB/Bluetooth connection
   - Verify pygame detects the controller:
     ```python
     import pygame
     pygame.init()
     pygame.joystick.init()
     print(f"Number of joysticks: {pygame.joystick.get_count()}")
     ```

2. **Buttons Not Working**
   - Verify button mappings in `_on_button_pressed`
   - Check for error messages in console

3. **Stick Drift**
   - Adjust the deadzone value in `_update_movement_states`
   - Current deadzone is set to 0.2 (20%)

## Implementation Notes

1. **Threading**
   - Controller runs in a separate thread to prevent UI freezing
   - Uses a dummy video driver to avoid GUI window creation

2. **Event Handling**
   - Maps controller inputs to existing keyboard commands
   - Maintains button state for movement controls

3. **Error Handling**
   - Gracefully handles controller disconnections
   - Provides feedback for debugging

4. **Performance**
   - Uses efficient event polling
   - Minimal CPU usage when idle

## Future Improvements
1. Add configuration file for button mappings
2. Implement custom calibration
3. Add haptic feedback support
4. Create a controller configuration UI
5. Support multiple controller profiles
    
    pygame.init()
    pygame.joystick.init()
    
    try:
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            print("No controllers found. Please connect your controller and try again.")
            return
            
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        
        print(f"Controller detected: {joystick.get_name()}")
        print(f"Number of axes: {joystick.get_numaxes()}")
        print(f"Number of buttons: {joystick.get_numbuttons()}")
        print("-" * 50)
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.JOYAXISMOTION:
                    if abs(event.value) > 0.1:  # Only show significant movements
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] Axis {event.axis}: {event.value:.3f}")
                
                elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    state = "pressed" if event.type == pygame.JOYBUTTONDOWN else "released"
                    print(f"[{timestamp}] Button {event.button} {state}")
                
                elif event.type == pygame.JOYHATMOTION:
                    if event.value != (0, 0):  # Only show when not centered
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] Hat {event.hat}: {event.value}")
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nTest mode ended by user.")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        pygame.quit()
        print("Controller test complete.")

def main():
    print("Xbox Controller Test Utility (pygame)")
    print("1. Test controller inputs (print all events)")
    print("2. List connected controllers")
    print("3. Exit")
    
    try:
        choice = input("Select an option (1-3): ")
        
        if choice == "1":
            print_controller_inputs()
        elif choice == "2":
            pygame.init()
            pygame.joystick.init()
            count = pygame.joystick.get_count()
            print(f"\nFound {count} controller(s):")
            for i in range(count):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                print(f"  {i}: {joystick.get_name()}")
            pygame.quit()
        else:
            print("Goodbye!")
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
```

### 2. Using `inputs` Library (Alternative)

If you prefer using the `inputs` library, create `xbox_test.py` in the `Client` directory:

```python
import inputs
import time
from datetime import datetime

def print_controller_inputs():
    """Print all controller inputs to the terminal for testing."""
    print("Xbox Controller Test Mode")
    print("Press Ctrl+C to exit")
    print("Move sticks and press buttons to see the input data")
    print("=" * 50)
    
    try:
        while True:
            events = inputs.get_gamepad()
            for event in events:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] {event.ev_type}: {event.code} = {event.state}")
                
    except KeyboardInterrupt:
        print("\nTest mode ended.")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("Controller test complete.")

def main():
    print("Xbox Controller Test Utility")
    print("1. Test controller inputs (print all events)")
    print("2. Exit")
    
    try:
        choice = input("Select an option (1-2): ")
        
        if choice == "1":
            print_controller_inputs()
        else:
            print("Goodbye!")
    except EOFError:
        print("\nInput not available. Running in test mode...")
        print_controller_inputs()

if __name__ == "__main__":
    main()
```

### How to Use the Test Scripts

1. **Using pygame (Recommended for macOS)**:
   ```bash
   python3 Client/xbox_test_pygame.py
   ```
   - Select option 1 to start testing
   - Select option 2 to list connected controllers
   - Move sticks and press buttons to see the input data
   - Press Ctrl+C to exit

2. **Using inputs library**:
   ```bash
   python3 Client/xbox_test.py
   ```
   - Select option 1 to start testing
   - Move sticks and press buttons to see the input data
   - Press Ctrl+C to exit

## Implementation Files

### 1. `xbox_controller.py`

Create this new file in the `Client` directory:

```python
import inputs
import time
from Main import mywindow  # Import the main window class

class XboxController:
    def __init__(self, tank_controller):
        self.tank = tank_controller
        self.running = True
        
        # Controller state
        self.left_stick_x = 0
        self.left_stick_y = 0
        self.right_stick_x = 0
        self.right_stick_y = 0
        
        # Button states
        self.a_button = 0
        self.b_button = 0
        self.x_button = 0
        self.y_button = 0
        self.start_button = 0
        self.back_button = 0
        
    def process_events(self):
        """Process controller events and update tank controls."""
        events = inputs.get_gamepad()
        for event in events:
            self._handle_event(event)
        self._update_controls()
    
    def _handle_event(self, event):
        """Handle individual controller events."""
        if event.ev_type == 'Absolute':
            if event.code == 'ABS_X':
                self.left_stick_x = event.state / 32768.0  # Normalize to [-1, 1]
            elif event.code == 'ABS_Y':
                self.left_stick_y = event.state / 32768.0  # Normalize to [-1, 1]
            elif event.code == 'ABS_RX':
                self.right_stick_x = event.state / 32768.0  # Normalize to [-1, 1]
            elif event.code == 'ABS_RY':
                self.right_stick_y = event.state / 32768.0  # Normalize to [-1, 1]
        
        elif event.ev_type == 'Key':
            if event.code == 'BTN_SOUTH':  # A button
                self.a_button = event.state
            elif event.code == 'BTN_EAST':  # B button
                self.b_button = event.state
            elif event.code == 'BTN_NORTH':  # Y button
                self.y_button = event.state
            elif event.code == 'BTN_WEST':  # X button
                self.x_button = event.state
            elif event.code == 'BTN_START':  # Start button
                self.start_button = event.state
                if event.state == 1:  # Toggle on press
                    self.running = not self.running
            elif event.code == 'BTN_SELECT':  # Back button
                self.back_button = event.state
    
    def _update_controls(self):
        """Update tank controls based on controller state."""
        if not self.running:
            self.tank.on_btn_Stop()
            return
        
        # Left stick controls movement
        deadzone = 0.1
        
        # Forward/Backward movement
        if abs(self.left_stick_y) > deadzone:
            speed = int(2000 * self.left_stick_y)  # Scale to motor speed
            if speed > 0:
                self.tank.TCP.sendData("CMD_MOTOR#" + str(speed) + "#" + str(speed) + "\n")
            else:
                self.tank.TCP.sendData("CMD_MOTOR#" + str(speed) + "#" + str(speed) + "\n")
        # Left/Right turning
        elif abs(self.left_stick_x) > deadzone:
            turn_speed = int(2000 * abs(self.left_stick_x))
            if self.left_stick_x > 0:  # Right turn
                self.tank.TCP.sendData("CMD_MOTOR#" + str(turn_speed) + "#" + str(-turn_speed) + "\n")
            else:  # Left turn
                self.tank.TCP.sendData("CMD_MOTOR#" + str(-turn_speed) + "#" + str(turn_speed) + "\n")
        else:
            self.tank.on_btn_Stop()
        
        # Right stick controls camera
        if abs(self.right_stick_x) > deadzone:
            # Update servo1 (horizontal) based on right stick X
            self.tank.servo1 = max(0, min(180, self.tank.servo1 + int(5 * self.right_stick_x)))
            self.tank.HSlider_Servo1.setValue(self.tank.servo1)
            self.tank.TCP.sendData("CMD_SERVO#0#" + str(self.tank.servo1) + "\n")
        
        if abs(self.right_stick_y) > deadzone:
            # Update servo2 (vertical) based on right stick Y (inverted)
            self.tank.servo2 = max(0, min(180, self.tank.servo2 - int(5 * self.right_stick_y)))
            self.tank.VSlider_Servo2.setValue(self.tank.servo2)
            self.tank.TCP.sendData("CMD_SERVO#1#" + str(self.tank.servo2) + "\n")

def main():
    # Initialize the tank controller
    tank = mywindow()
    
    # Initialize Xbox controller
    try:
        controller = XboxController(tank)
        print("Xbox controller connected. Press Start to enable/disable controls.")
        print("Press Ctrl+C to exit.")
        
        while True:
            controller.process_events()
            time.sleep(0.01)  # Small delay to prevent high CPU usage
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        tank.on_btn_Stop()  # Stop the tank when exiting

if __name__ == "__main__":
    main()
```

## How It Works

### Controller Mapping

- **Left Stick**: Controls movement
  - Up/Down: Move forward/backward
  - Left/Right: Turn left/right
  
- **Right Stick**: Controls camera/servo
  - Left/Right: Pan camera left/right
  - Up/Down: Tilt camera up/down

- **Start Button**: Toggle controller input (enable/disable)

### Integration with Existing Code

The `XboxController` class works alongside the existing `Main.py` by:
1. Using the same TCP connection to send commands to the tank
2. Updating the same servo position variables used by the GUI
3. Sending the same command strings that the tank expects

### Running the Controller

1. First, make sure the main tank client is running and connected to the robot
2. Run the controller script:
   ```bash
   python3 Client/xbox_controller.py
   ```
3. Use the controller as described above
4. Press Start to enable/disable controller input
5. Press Ctrl+C to exit

## Troubleshooting

1. **Controller Not Detected**:
   - Make sure the controller is properly connected to your Mac
   - Check if it appears in System Information > USB
   
2. **Permission Issues**:
   - On macOS, you might need to grant input monitoring permissions
   - Go to System Preferences > Security & Privacy > Privacy > Input Monitoring
   - Add your terminal app to the list

3. **Button Mappings**:
   - If buttons don't match your controller, you may need to adjust the button codes in `_handle_event()`
   - You can print event codes to find the correct mappings for your controller

## Customization

You can customize the controls by modifying the `_update_controls()` method in the `XboxController` class. For example:

- Adjust the `deadzone` value to change sensitivity
- Modify the speed scaling factors for finer control
- Add more button mappings for additional features

## Controller Test Utility

Before integrating the controller with the tank, you can test that it's working correctly using the `xbox_test.py` script:

```python
import inputs
import time
from datetime import datetime

def print_controller_inputs():
    """Print all controller inputs to the terminal for testing."""
    print("Xbox Controller Test Mode")
    print("Press Ctrl+C to exit")
    print("Move sticks and press buttons to see the input data")
    print("=" * 50)
    
    try:
        while True:
            events = inputs.get_gamepad()
            for event in inputs.get_gamepad():
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] {event.ev_type}: {event.code} = {event.state}")
                
    except KeyboardInterrupt:
        print("\nTest mode ended.")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("Controller test complete.")

def main():
    print("Xbox Controller Test Utility")
    print("1. Test controller inputs (print all events)")
    print("2. Exit")
    
    choice = input("Select an option (1-2): ")
    
    if choice == "1":
        print_controller_inputs()
    else:
        print("Goodbye!")

if __name__ == "__main__":
    main()
```

### How to Use the Test Utility

1. Save the script as `xbox_test.py` in your project directory
2. Run it with: `python3 xbox_test.py`
3. Select option 1 to start the test
4. Move the sticks and press buttons on your controller
5. You'll see real-time output showing all controller events
6. Press Ctrl+C to exit

### What the Test Shows

- Timestamp of each event
- Event type (Absolute for sticks/triggers, Key for buttons)
- Button/axis code (e.g., 'BTN_SOUTH' for A button)
- Current state/value of the input

This is particularly useful for:
- Verifying your controller is being detected
- Seeing the exact button/axis codes
- Understanding the range of values for each input
- Debugging any connection issues

## Notes

- The controller runs in a separate thread from the main GUI
- Controller input is disabled by default (press Start to enable)
- The script includes error handling for disconnections
- All movements respect the same limits as the GUI controls
