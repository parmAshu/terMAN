"""
This module contains utility functions for performing serial port related tasks
"""

__author__ = "ASHUTOSH SINGH PARMAR"

import serial
import serial.tools.list_ports
import time
from utility import utils

# Default baud rate for the application
default_baud='9600'

# List baud rates supported by the application
baud_list = ['600','1200', '1800', '2400', '4800', '9600', '19200', '38400', '57600', '115200']

# Default parity for the application
default_parity = 'None'

# List of parity type
parity_list = ['None', 'Odd', 'Even']

def getPorts():
    """
    This function returns the list of available serial ports

    PARAMETES
    ---------
    NONE

    RETURNS : list
    -------
    A list of available com  ports at the time of calling. If there are no com ports available then, a list with single item
    '-' is returned. This can be used to make decision at higher level.
    """
    ports_list=[]
    for i in list(serial.tools.list_ports.comports()):
        ports_list.append(i.device)
    if len(ports_list) == 0:
        ports_list.append('-')
    return ports_list

def SERIAL_PARITY(parity):
    """
    This function returns the serial.Serial class compatible parity code corresponding to the provided parity string - 'parity'

    PARAMETERS
    ----------
    parity : str
    The parity string

    RETURNS
    -------
    E : for even parity
    O : for odd parity
    N : for no parity
    """
    if parity == 'Even':
        return 'E'
    elif parity == 'Odd':
        return 'O'
    else:
        return 'N'

run_serial_thread = 0
def appThread1(app):
    """
    This function handles the communication with the selected serial device. It runs as a separate thread.

    PARAMETERS
    ----------
    app : App class object
    This object is used for interacting with the user interface

    RETURNS
    -------
    NOTHING
    """
    # creating an object of the serial.Serial class
    device = serial.Serial()

    try:
        device.port = app.getPortSelection()
        device.baudrate = int(app.getBaudSelection())
        device.stopbits = int(app.getStopBits())
        device.parity=SERIAL_PARITY(app.getParity())
        device.timeout=0
        device.open()

        app.send_buff.flush()
        app.receive_buff.flush()

        # signal the successful initialization to the user interface
        app.serialStartedCallback()

        while True:

            # If there is data in the uart send buffer then keep sending the bytes to the serial buffer
            if app.send_buff.filled:
                device.write(app.send_buff.dequeue(1))
            
            # If there is data in the uart receive buffer then pass it into the receive buffer
            if device.in_waiting:
                app.receive_buff.enqueue(device.read(device.in_waiting))
            
            if run_serial_thread == 0:
                raise SerialTermination("terminate thread")

    except Exception as e:
        # signal the termination to the user interface
        app.serialTerminateCallback(str(e.__class__.__name__))
        device.close()

run_serial_thread1 = 0
def appThread3(app, delay):
    """
    This function handles the communication with the selected serial device. It runs as a separate thread.
    This thread is run when a record file is to be played.

    PARAMETERS
    ----------
    app : App class object
    This object is used for interacting with the user interface

    delay : float
    Delay between sending two consecutive bytes

    RETURNS
    -------
    NOTHING
    """
    # creating an object of the serial.Serial class
    device = serial.Serial()

    try:
        device.port = app.getPortSelection()
        device.baudrate = int(app.getBaudSelection())
        device.stopbits = int(app.getStopBits())
        device.parity=SERIAL_PARITY(app.getParity())
        device.timeout=0
        device.open()

        # signal the successful initialization to the user interface
        app.serialStartedCallback_Play()

        # convert the delay to seconds
        delay=delay/1000

        while True:
            
            # If there is data in the uart send buffer then keep sending the bytes to the serial buffer
            if app.send_buff.filled:
                device.write(app.send_buff.dequeue(1))
            
            # If there is data in the uart receive buffer then pass it into the receive buffer
            if device.in_waiting:
                app.receive_buff.enqueue(device.read(device.in_waiting))
            
            if run_serial_thread1 == 0 or app.send_buff.filled ==0:
                raise SerialTermination("terminate thread")

            time.sleep(delay)

    except Exception as e:
        # signal the termination to the user interface
        app.serialTerminateCallback_Play(str(e.__class__.__name__))
        device.close()

# Custom Exception class
class SerialTermination(Exception):
    """
    This is a custom exception used in the serial thread
    """
    pass