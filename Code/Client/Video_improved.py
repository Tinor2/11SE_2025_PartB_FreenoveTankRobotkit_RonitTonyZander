#!/usr/bin/python 
# -*- coding: utf-8 -*-
import numpy as np
import cv2
import socket
import io
import sys
import struct
import time
import logging
from PIL import Image
from threading import Lock, Thread
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VideoStreaming')

class VideoStreaming:
    def __init__(self):
        """Initialize the VideoStreaming class with default values and thread safety."""
        self.video_Flag = True
        self.connect_Flag = False
        self.face_x = 0
        self.face_y = 0
        self.client_socket = None
        self.client_socket1 = None
        self.connection = None
        self._lock = Lock()  # For thread safety
        self._running = False
        self._reconnect_attempts = 3
        self._reconnect_delay = 2  # seconds
        self.image = None

    def _create_socket(self) -> socket.socket:
        """Create and configure a new socket with timeout settings."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)  # 5 second timeout for operations
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
            return sock
        except socket.error as e:
            logger.error(f"Failed to create socket: {e}")
            raise

    def StartTcpClient1(self, ip: str, port: int = 8002) -> bool:
        """
        Initialize the command TCP client socket.
        
        Args:
            ip: Server IP address
            port: Server port (default: 8002 for commands)
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            with self._lock:
                if self.client_socket1:
                    self.StopTcpcClient1()
                
                self.client_socket1 = self._create_socket()
                self.client_socket1.connect((ip, port))
                self.connect_Flag = True
                logger.info(f"Connected to command server at {ip}:{port}")
                return True
                
        except (socket.error, socket.timeout) as e:
            logger.error(f"Failed to connect to command server: {e}")
            self.connect_Flag = False
            return False

    def StartTcpClient(self, ip: str, port: int = 8003) -> bool:
        """
        Initialize the video streaming TCP client socket.
        
        Args:
            ip: Server IP address
            port: Server port (default: 8003 for video)
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            with self._lock:
                if self.client_socket:
                    self.StopTcpcClient()
                
                self.client_socket = self._create_socket()
                self.client_socket.connect((ip, port))
                self.connection = self.client_socket.makefile('rb')
                logger.info(f"Connected to video server at {ip}:{port}")
                return True
                
        except (socket.error, socket.timeout) as e:
            logger.error(f"Failed to connect to video server: {e}")
            return False

    def StopTcpcClient(self) -> None:
        """Safely close the video streaming client connection."""
        with self._lock:
            try:
                if hasattr(self, 'connection') and self.connection:
                    self.connection.close()
            except Exception as e:
                logger.warning(f"Error closing video connection: {e}")
            
            try:
                if hasattr(self, 'client_socket') and self.client_socket:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                    self.client_socket.close()
            except Exception as e:
                logger.warning(f"Error closing video socket: {e}")
            finally:
                self.client_socket = None
                self.connection = None

    def StopTcpcClient1(self) -> None:
        """Safely close the command client connection."""
        with self._lock:
            try:
                if hasattr(self, 'client_socket1') and self.client_socket1:
                    self.client_socket1.shutdown(socket.SHUT_RDWR)
                    self.client_socket1.close()
            except Exception as e:
                logger.warning(f"Error closing command socket: {e}")
            finally:
                self.client_socket1 = None
                self.connect_Flag = False

    def IsValidImage4Bytes(self, buf: bytes) -> bool:
        """
        Validate if the provided buffer contains a valid JPEG image.
        
        Args:
            buf: Binary data to validate
            
        Returns:
            bool: True if the buffer contains a valid image, False otherwise
        """
        if not buf or len(buf) < 10:  # Minimum size for a valid JPEG
            return False
            
        try:
            # Check for JPEG magic numbers
            if buf[0] == 0xFF and buf[1] == 0xD8:  # JPEG start marker
                if buf[-2] == 0xFF and buf[-1] == 0xD9:  # JPEG end marker
                    return True
                    
                # Some JPEGs might have padding before the end marker
                if buf.rstrip(b'\0\r\n').endswith(b'\xFF\xD9'):
                    return True
                    
            # Check for EXIF/JPEG headers
            if len(buf) > 20 and buf[6:10] in (b'JFIF', b'Exif'):
                return buf.rstrip(b'\0\r\n').endswith(b'\xFF\xD9')
                
            # Try PIL verification as a last resort
            try:
                Image.open(io.BytesIO(buf)).verify()
                return True
            except Exception:
                pass
                
        except Exception as e:
            logger.debug(f"Image validation error: {e}")
            
        return False


    def face_detect(self,img):
        if sys.platform.startswith('win') or sys.platform.startswith('darwin'):
            video = img
            #gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            gray = img
            faces = self.face_cascade.detectMultiScale(gray,1.2,3)
            if len(faces)>0 :
                for (x,y,w,h) in faces:
                    self.face_x=float(x+w/2.0)
                    self.face_y=float(y+h/2.0)
                    video = cv2.flip(video, -1)
                    img= cv2.rectangle(img, (x-10,y-10), (w+h+10,y+h+10), (0, 255, 0), 2)
            else:
                self.face_x=0
                self.face_y=0

    def streaming(self, ip: str, port: int = 8003) -> None:
        """
        Handle the video streaming from the server with reconnection logic.
        
        Args:
            ip: Server IP address
            port: Server port (default: 8003 for video)
        """
        self._running = True
        reconnect_attempts = 0
        
        while self._running:
            try:
                # (Re)connect if needed
                if not self.client_socket or not self.connection:
                    if not self.StartTcpClient(ip, port):
                        if reconnect_attempts < self._reconnect_attempts:
                            reconnect_attempts += 1
                            time.sleep(self._reconnect_delay * reconnect_attempts)
                            continue
                        else:
                            logger.error("Max reconnection attempts reached")
                            self._running = False
                            break
                
                # Reset reconnect attempts on successful connection
                reconnect_attempts = 0
                
                # Read frame length (4 bytes)
                stream_bytes = self.connection.read(4)
                if not stream_bytes or len(stream_bytes) != 4:
                    raise ConnectionError("Invalid frame header received")
                
                # Unpack frame length
                try:
                    frame_length = struct.unpack('<L', stream_bytes)[0]
                except struct.error as e:
                    logger.error(f"Invalid frame length: {e}")
                    continue
                
                # Read frame data
                frame_data = bytearray()
                remaining = frame_length
                
                while remaining > 0:
                    chunk = self.connection.read(min(remaining, 4096))
                    if not chunk:
                        raise ConnectionError("Incomplete frame data received")
                    frame_data.extend(chunk)
                    remaining -= len(chunk)
                
                # Process frame if valid
                if self.IsValidImage4Bytes(frame_data):
                    try:
                        # Convert to numpy array and decode
                        nparr = np.frombuffer(frame_data, dtype=np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if frame is not None and frame.size > 0:
                            with self._lock:
                                self.image = frame
                                self.video_Flag = False
                    except Exception as e:
                        logger.error(f"Error processing frame: {e}")
                
            except (ConnectionError, socket.error, IOError) as e:
                logger.error(f"Streaming error: {e}")
                self.StopTcpcClient()
                time.sleep(1)  # Prevent tight loop on connection errors
                
            except Exception as e:
                logger.error(f"Unexpected error in streaming: {e}")
                self.StopTcpcClient()
                time.sleep(1)
        
        # Cleanup on exit
        self.StopTcpcClient()
        logger.info("Video streaming stopped")

    def sendData(self, data: str, max_retries: int = 2) -> bool:
        """
        Send data to the command server with retry logic.
        
        Args:
            data: String data to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: True if data was sent successfully, False otherwise
        """
        if not data or not self.connect_Flag or not self.client_socket1:
            return False
            
        for attempt in range(max_retries + 1):
            try:
                if not self.connect_Flag or not self.client_socket1:
                    logger.warning("Not connected to command server")
                    return False
                
                # Ensure data ends with newline if not already
                if not data.endswith('\n'):
                    data = data.strip() + '\n'
                self.client_socket1.sendall(data.encode('utf-8'))
                return True
                
            except (socket.error, ConnectionError) as e:
                if attempt == max_retries:
                    logger.error(f"Failed to send data after {max_retries} attempts: {e}")
                    self.connect_Flag = False
                    return False
                
                logger.warning(f"Send attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                
                # Try to reconnect if connection was lost
                if attempt == 0 and not self.connect_Flag:
                    try:
                        self.client_socket1 = self._create_socket()
                        # Note: Need to store the IP/port to reconnect properly
                        # This is a limitation of the current design
                        logger.warning("Reconnection not fully implemented - need original IP/port")
                    except Exception as reconnect_error:
                        logger.error(f"Reconnection failed: {reconnect_error}")
                        return False
        
        return False

    def recvData(self, timeout: float = 1.0) -> str:
        """
        Receive data from the command server with timeout.
        
        Args:
            timeout: Maximum time to wait for data in seconds
            
        Returns:
            str: Received data as string, or empty string on error
        """
        if not self.connect_Flag or not self.client_socket1:
            return ""
            
        try:
            # Set socket timeout
            self.client_socket1.settimeout(timeout)
            
            # Receive data
            data = self.client_socket1.recv(4096)  # Increased buffer size
            if not data:
                logger.warning("Connection closed by server")
                self.connect_Flag = False
                return ""
                
            return data.decode('utf-8').strip()
            
        except socket.timeout:
            return ""  # No data available, normal condition
            
        except (ConnectionError, socket.error) as e:
            logger.error(f"Receive error: {e}")
            self.connect_Flag = False
            return ""
            
        except Exception as e:
            logger.error(f"Unexpected error in recvData: {e}")
            return ""
        finally:
            # Reset to blocking mode
            try:
                self.client_socket1.settimeout(None)
            except:
                pass
            pass
        return data

    def socket1_connect(self, ip):
        """
        Connect to the command server.
        
        Args:
            ip: Server IP address
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            if not self.client_socket1:
                self.client_socket1 = self._create_socket()
            
            self.client_socket1.connect((ip, 5003))
            self.connect_Flag = True
            logger.info("Connection to command server successful")
            return True
            
        except (socket.error, socket.timeout) as e:
            logger.error(f"Failed to connect to command server: {e}")
            self.connect_Flag = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error in socket1_connect: {e}")
            self.connect_Flag = False
            return False
            
    def close_all(self):
        """
        Safely close all connections and clean up resources.
        
        This should be called when the application is shutting down or when
        connections need to be reset.
        """
        logger.info("Closing all connections and cleaning up...")
        self._running = False  # Signal streaming thread to stop
        
        # Stop and close video connection
        self.StopTcpcClient()
        
        # Stop and close command connection
        self.StopTcpcClient1()
        
        # Reset state
        self.connect_Flag = False
        self.video_Flag = True
        
        logger.info("All connections closed and resources cleaned up")

if __name__ == '__main__':
    pass

