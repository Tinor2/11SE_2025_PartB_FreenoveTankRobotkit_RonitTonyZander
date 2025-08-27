from abc import ABC, abstractmethod

class Component(ABC):
    """
    Abstract base class for all components in the system.
    Implements common functionality and interface for all components.
    """
    def __init__(self, name: str, instance: int = 0, is_input: bool = False):
        """
        Initialize a new component.
        
        Args:
            name: The name of the component (e.g., 'ultrasonic', 'motor')
            instance: Instance number for components of the same type
            is_input: Whether this is an input component (True) or output component (False)
        """
        self.name = name
        self.instance = instance
        self.IO = is_input
    
    @abstractmethod
    def start(self):
        """Initialize the component and any required resources."""
        pass
    
    @abstractmethod
    def close(self):
        """Clean up resources used by the component."""
        pass


class Input(Component):
    """
    Abstract base class for all input components.
    Input components read data from sensors or other input devices.
    """
    def __init__(self, name: str, instance: int = 0):
        super().__init__(name, instance, is_input=True)
    
    @abstractmethod
    def get_data(self):
        """
        Read data from the input component.
        
        Returns:
            The data read from the component, type depends on the specific component.
        """
        pass


class Output(Component):
    """
    Abstract base class for all output components.
    Output components control actuators or other output devices.
    """
    def __init__(self, name: str, instance: int = 0):
        super().__init__(name, instance, is_input=False)
    
    @abstractmethod
    def set_value(self, *args, **kwargs):
        """
        Set the value of the output component.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        pass
