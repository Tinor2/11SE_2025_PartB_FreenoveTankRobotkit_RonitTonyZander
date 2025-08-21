# Freenove Tank Robot Kit - Comprehensive Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Hardware Overview](#hardware-overview)
3. [Software Architecture](#software-architecture)
4. [Getting Started](#getting-started)
5. [Using the Robot](#using-the-robot)
6. [Customization Guide](#customization-guide)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Features](#advanced-features)
9. [Contributing](#contributing)
10. [License and Support](#license-and-support)

## Introduction

The Freenove Tank Robot Kit is an open-source robotics platform designed for Raspberry Pi enthusiasts. This kit allows you to build and program a fully functional tank-style robot with various sensors and actuators. The robot can be controlled remotely and is perfect for learning robotics, computer vision, and IoT applications.

## Hardware Overview

### Main Components
- **Raspberry Pi** (Compatible with RPi 4 and 5, with some limitations)
- **Motor System**: Dual DC motors with H-bridge control
- **Sensors**:
  - Ultrasonic sensor for distance measurement
  - Infrared line-following sensors
  - Camera module for computer vision
- **Actuators**:
  - Servo motors for camera/arm control
  - RGB LED indicators
- **Power Management**: Battery system with charging circuit

### PCB Versions
There are two versions of the PCB with some differences:

| Feature | V1.0 | V2.0 |
|---------|------|------|
| Servo Pins | GPIO7, GPIO8 | GPIO12, GPIO13 |
| Infrared Pins | GPIO16, GPIO20, GPIO21 | GPIO16, GPIO26, GPIO21 |
| LED Control | GPIO18 | GPIO10 (SPI) |
| Motor Control | GPIO23, GPIO24, GPIO6, GPIO5 | Same as V1.0 |

## Software Architecture

The codebase is organized into several key components:

### Client-Server Architecture
1. **Server** (Runs on Raspberry Pi):
   - `main.py`: Main server application
   - `server.py`: Handles TCP communication
   - `camera.py`: Manages the camera module
   - `car.py`: Controls motors and sensors

2. **Client** (Runs on PC):
   - `Main.py`: Main GUI application
   - `Client_Ui.py`: User interface definition
   - `Command.py`: Command definitions
   - `Video.py`: Handles video streaming

## Getting Started

### Prerequisites
- Raspberry Pi 4 or 5 (recommended)
- Installed Raspberry Pi OS (32-bit)
- Python 3.x
- Required Python packages (install using `pip install -r requirements.txt`)

### Installation
1. Clone the repository:
   ```bash
   git clone --depth 1 https://github.com/Freenove/Freenove_Tank_Robot_Kit_for_Raspberry_Pi.git
   cd Freenove_Tank_Robot_Kit_for_Raspberry_Pi/Code
   ```

2. Install dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-dev python3-pyqt5
   pip3 install -r requirements.txt
   ```

3. For Raspberry Pi 5 users (PCB V2.0):
   ```bash
   cd Libs/rpi-ws281x-python/library
   sudo python3 setup.py install
   ```

## Using the Robot

### Starting the Server
On the Raspberry Pi:
```bash
cd Code/Server
python3 main.py
```

### Connecting the Client
On your PC:
1. Run `Main.py` from the Client directory
2. Enter the Raspberry Pi's IP address
3. Click "Connect"

### Basic Controls
- **Movement**: Use the arrow keys or on-screen buttons
- **Camera**: Tilt using the camera controls
- **Sensors**: View ultrasonic and IR sensor readings in real-time
- **LEDs**: Control the RGB LEDs using the interface

## Customization Guide

### Adding New Features
1. **New Commands**:
   - Add command definitions in `Command.py`
   - Implement handlers in both client and server

2. **New Sensors**:
   - Connect the sensor to available GPIO pins
   - Update the pin configuration in the server code
   - Add data processing and transmission logic

### Code Structure
```
Code/
├── Client/           # Client-side code
│   ├── Main.py      # Main application
│   ├── Command.py   # Command definitions
│   └── ...
├── Server/          # Server-side code
│   ├── main.py      # Main server
│   ├── car.py       # Motor and sensor control
│   └── ...
└── Libs/            # External libraries
```

## Troubleshooting

### Common Issues
1. **Motors not responding**:
   - Check power supply
   - Verify GPIO connections
   - Ensure server is running

2. **Video not streaming**:
   - Check camera connection
   - Verify network connectivity
   - Restart the server

3. **LEDs not working (RPi 5)**:
   - Ensure you're using PCB V2.0
   - Check SPI is enabled in raspi-config

## Advanced Features

### Autonomous Navigation
Implement line following or obstacle avoidance using the built-in sensors.

### Computer Vision
Use OpenCV with the camera module for object detection and tracking.

### Remote Control
Extend the client to work with game controllers or mobile apps.

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License and Support

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.

For support, contact:
- Email: support@freenove.com
- Website: [www.freenove.com](http://www.freenove.com)

---
*This guide was generated for the Freenove Tank Robot Kit. For the latest updates, please check the official repository.*
