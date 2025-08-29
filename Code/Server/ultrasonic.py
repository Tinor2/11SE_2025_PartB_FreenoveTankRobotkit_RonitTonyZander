from gpiozero import DistanceSensor, PWMSoftwareFallback
import warnings
from component import Input

class Ultrasonic(Input):
    def __init__(self, instance: int = 0):
        """
        Initialize the Ultrasonic sensor component.
        
        Args:
            instance: Instance number for multiple ultrasonic sensors
        """
        super().__init__("ultrasonic", instance)
        warnings.filterwarnings("ignore", category=PWMSoftwareFallback)
        self.trigger_pin = 27
        self.echo_pin = 22
        self.sensor = DistanceSensor(echo=self.echo_pin, trigger=self.trigger_pin, max_distance=3)

    def start(self):
        """Initialize the sensor. No special initialization needed for gpiozero."""
        pass

    def get_data(self):
        """
        Get the distance measurement from the ultrasonic sensor.
        
        Returns:
            float: Distance in centimeters, rounded to one decimal place
        """
        distance_cm = self.sensor.distance * 100  # Convert meters to centimeters
        return round(float(distance_cm), 1)
        
    # Alias for backward compatibility
    def get_distance(self):
        """Alias for get_data() for backward compatibility."""
        return self.get_data()

    def close(self):
        # Close the distance sensor.
        self.sensor.close()        # Close the sensor to release resources

if __name__ == '__main__':
    import time  # Import the time module for sleep functionality
    ultrasonic = Ultrasonic()      # Initialize the Ultrasonic instance
    try:
        while True:
            print("Ultrasonic distance: {}cm".format(ultrasonic.get_distance()))  # Print the distance measurement
            time.sleep(0.5)        # Wait for 0.5 seconds
    except KeyboardInterrupt:      # Handle keyboard interrupt (Ctrl+C)
        ultrasonic.close()         # Close the sensor
        print("\nEnd of program")  # Print an end message