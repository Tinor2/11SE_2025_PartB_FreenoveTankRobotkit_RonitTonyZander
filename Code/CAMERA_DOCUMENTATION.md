# Freenove Tank Robot Camera Documentation

## Overview
The camera module provides functionality for capturing images and videos, as well as streaming video from the Raspberry Pi camera. It uses the `picamera2` library to interface with the Raspberry Pi camera module.

## Dependencies
- Python 3.x
- picamera2
- OpenCV (for some advanced image processing)
- numpy
- libcamera

## Camera Class

### Initialization
```python
def __init__(self, preview_size=(640, 480), hflip=False, vflip=False, stream_size=(400, 300)):
    """
    Initialize the camera with specified settings.
    
    Args:
        preview_size (tuple): Resolution for camera preview (width, height)
        hflip (bool): Flip image horizontally if True
        vflip (bool): Flip image vertically if True
        stream_size (tuple): Resolution for video streaming (width, height)
    """
```

### Key Methods

#### 1. Starting the Camera Preview
```python
def start_image(self):
    """Start the camera preview using QTGL backend."""
    self.camera.start_preview(Preview.QTGL)
    self.camera.start()
```

#### 2. Capturing Images
```python
def save_image(self, filename):
    """
    Capture and save an image.
    
    Args:
        filename (str): Path where to save the image
        
    Returns:
        dict: Metadata of the captured image
    """
    metadata = self.camera.capture_file(filename)
    return metadata
```

#### 3. Video Streaming
```python
def start_stream(self, filename=None):
    """
    Start video streaming or recording.
    
    Args:
        filename (str, optional): If provided, records video to this file.
                                 If None, enables live streaming.
    """
    # Implementation details...
```

#### 4. Getting Video Frames
```python
def get_frame(self):
    """
    Get the current frame from the video stream.
    
    Returns:
        bytes: JPEG-encoded frame data
    """
    with self.streaming_output.condition:
        self.streaming_output.condition.wait()
        return self.streaming_output.frame
```

#### 5. Recording Video
```python
def save_video(self, filename, duration=10):
    """
    Record a video for the specified duration.
    
    Args:
        filename (str): Path where to save the video
        duration (int): Duration of the video in seconds (default: 10)
    """
    self.start_stream(filename)
    time.sleep(duration)
    self.stop_stream()
```

#### 6. Stopping the Camera
```python
def close(self):
    """Stop all camera activities and release resources."""
    if self.streaming:
        self.stop_stream()
    self.camera.close()
```

## StreamingOutput Class
Helper class that handles the streaming output buffer.

```python
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        """Write buffer to frame and notify waiting threads."""
        with self.condition:
            self.frame = buf
            self.condition.notify_all()
```

## Usage Example

### Basic Usage
```python
# Create camera instance
camera = Camera()

# Start preview
camera.start_image()
time.sleep(2)  # Let camera adjust

# Capture image
camera.save_image("test_image.jpg")

# Record video
camera.save_video("test_video.h264", duration=5)

# Clean up
camera.close()
```

### Streaming Video
```python
camera = Camera()

# Start streaming
camera.start_stream()

try:
    while True:
        # Get and process frames
        frame = camera.get_frame()
        # Process frame here...
        
except KeyboardInterrupt:
    pass
finally:
    camera.close()
```

## Troubleshooting

1. **Camera Not Detected**
   - Ensure the camera is properly connected to the Raspberry Pi
   - Enable the camera in `raspi-config`
   - Check if the camera is detected with `libcamera-hello`

2. **Permission Issues**
   - Make sure the user has permission to access the camera
   - Run with `sudo` if necessary

3. **Streaming Issues**
   - Check network connection if streaming over network
   - Reduce resolution if experiencing lag
   - Ensure sufficient lighting for better image quality

## Notes
- The camera uses H.264 encoding for video recording
- JPEG encoding is used for streaming
- Default preview resolution is 640x480
- Default streaming resolution is 400x300
- The camera supports horizontal and vertical flipping of the image
