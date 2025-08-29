"""
LED Board module for controlling multiple LEDs.
Implements the Output interface for unified control.
"""
from typing import List, Tuple, Optional
from component import Output

class LED_Board(Output):
    """
    A class to control multiple LEDs on a board.
    Implements the Output interface for unified control.
    """
    
    def __init__(self, 
                 led_pins: List[int] = None,
                 name: str = "led_board"):
        """
        Initialize the LED Board with the specified GPIO pins.
        
        Args:
            led_pins: List of GPIO pin numbers for the LEDs.
                     If None, uses an empty list (no LEDs).
            name: Name of the LED board (default: "led_board")
        """
        super().__init__(name, 0)  # Instance is 0 as this is a composite
        
        # Import here to allow the module to be imported on non-Raspberry Pi systems
        try:
            from gpiozero import LED
            self.LED = LED
        except ImportError:
            # Fallback for testing on non-Raspberry Pi
            class MockLED:
                def __init__(self, pin):
                    self.pin = pin
                    self.is_lit = False
                def on(self): self.is_lit = True
                def off(self): self.is_lit = False
                def toggle(self): self.is_lit = not self.is_lit
                def close(self): pass
            self.LED = MockLED
        
        self.leds = []
        self.states = []
        
        # Initialize all LEDs
        if led_pins is not None:
            for pin in led_pins:
                self.add_led(pin)
    
    def add_led(self, pin: int) -> int:
        """
        Add an LED to the board.
        
        Args:
            pin: GPIO pin number for the LED
            
        Returns:
            Index of the newly added LED
        """
        self.leds.append(self.LED(pin))
        self.states.append(False)  # Start with LED off
        return len(self.leds) - 1
    
    def start(self):
        """Initialize all LEDs (turns them off by default)."""
        for led in self.leds:
            led.off()
    
    def set_value(self, value: float):
        """
        Set all LEDs to the specified brightness.
        
        Args:
            value: Brightness value (0.0 to 1.0)
        """
        for i in range(len(self.leds)):
            self.set_led(i, value > 0.5)
    
    def set_led(self, index: int, state: bool):
        """
        Set the state of a specific LED.
        
        Args:
            index: Index of the LED to control
            state: True to turn on, False to turn off
        """
        if 0 <= index < len(self.leds):
            self.states[index] = state
            if state:
                self.leds[index].on()
            else:
                self.leds[index].off()
    
    def toggle_led(self, index: int):
        """
        Toggle the state of a specific LED.
        
        Args:
            index: Index of the LED to toggle
        """
        if 0 <= index < len(self.leds):
            self.set_led(index, not self.states[index])
    
    def get_led_state(self, index: int) -> Optional[bool]:
        """
        Get the current state of a specific LED.
        
        Args:
            index: Index of the LED
            
        Returns:
            Current state (True for on, False for off), or None if invalid index
        """
        if 0 <= index < len(self.states):
            return self.states[index]
        return None
    
    def get_states(self) -> List[bool]:
        """
        Get the current state of all LEDs.
        
        Returns:
            List of boolean states for all LEDs
        """
        return self.states.copy()
    
    def all_on(self):
        """Turn all LEDs on."""
        for i in range(len(self.leds)):
            self.set_led(i, True)
    
    def all_off(self):
        """Turn all LEDs off."""
        for i in range(len(self.leds)):
            self.set_led(i, False)
    
    def close(self):
        """Close all LEDs and release resources."""
        self.all_off()
        for led in self.leds:
            try:
                led.close()
            except:
                pass

# Example usage
if __name__ == "__main__":
    import time
    
    # Create an LED board with 4 LEDs on GPIO pins 17, 18, 22, and 23
    print("Initializing LED board...")
    leds = LED_Board(led_pins=[17, 18, 22, 23])
    
    try:
        print("Starting LED test sequence...")
        leds.start()
        
        # Turn on LEDs one by one
        for i in range(len(leds.leds)):
            print(f"Turning on LED {i}")
            leds.set_led(i, True)
            time.sleep(0.5)
        
        time.sleep(1)
        
        # Toggle all LEDs off
        print("Toggling all LEDs off")
        for i in range(len(leds.leds)):
            leds.toggle_led(i)
        
        time.sleep(1)
        
        # Use set_value to turn all LEDs on
        print("Turning all LEDs on")
        leds.set_value(1.0)
        
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        # Clean up
        leds.close()
        print("LED board test complete.")
