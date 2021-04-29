"""
This module contains utility functions that are used by application
"""

__author__ = "ASHUTOSH SINGH PARMAR"

import time
from datetime import datetime, timedelta

tz = -time.timezone
if tz < 0:
    tz=tz*-1
    utc_off = "-" + str( timedelta(seconds=tz) )[0:-3]
else:
    utc_off = "+" + str( timedelta(seconds=tz) )[0:-3]


def convertToByteString(inputStr):
    """
    This utility function accepts a string of hex values and returns a sequence of bytes corresponding to it.
    The function raises an exception if the input string is not in the corect format

    PARAMETERS
    ----------
    inputStr : str
    The input string containing hex values separated by whitespace

    RETURNS : byte string
    -------
    The byte sequence corresponding to the input string
    """
    if len(inputStr)==0:
        return b''
    else:
        valueList = inputStr.split(' ')
        bytstr = b''
        for val in valueList:
            bytstr = bytstr + bytearray.fromhex(val)
        return bytstr

def convertToHexString(inputByts):
    """
    This utililty function accepts a squence of bytes (a byte array) and returns a string containing HEX values
    corresponding to the input sequence of bytes

    PARAMETERS
    ---------
    iputByts : byte array
    Input byte array

    RETURNS : str
    ------- 
    A string containing HEX values corresponding to the input bytes
    """
    st = ""
    for byt in inputByts:
        st = st + hex(byt) + " "
    return st

def convertToCSV(app, data):
    """
    This functions accepts a list of tuples ( datetime object, data ) and returns a string in csv file format

    PARAMETERS
    ----------
    data : list
    A list of tuples of the form ( datetime obj, data string )

    RETURNS
    -------
    NOTHING
    """

    csv_str = ""
    index = app.csv_index
    for item in data :
        csv_str = csv_str + str(index) + ';' + item[0].strftime("%Y-%m-%dT%H:%M:%S") + utc_off + ";" + item[1] +'\n'
        index = index + 1
    app.csv_index = index

    return csv_str 


class buffer:
    """
    This class is used to implement buffers

    Attributes
    ----------
    maxSize : int
    The maximum number of bytes allowed in the buffer

    filled : int
    The number of data bytes in buffer

    data : byte array
    The actual data as byte array

    Methods
    -------

    enqueue()
    This method enqueues data into the buffer

    dequeue()
    This method dequeues data from the buffer

    flush()
    This method flushes the buffer
    
    """

    def __init__(self, size):
        """
        The class constructor

        PARAMETERS
        ----------
        size : int
        Maximum size of the buffer

        RETURNS
        -------
        NOTHING
        """
        self.maxSize = size
        self.inPos = 0
        self.outPos = 0
        self.filled = 0
        self.data = b''

    def enqueue(self, bytSeq):
        """
        This method is used to push bytes into the buffer

        PARAMETERS
        ----------
        bytSeq : byte array
        The byte sequence to push into the buffer

        RETURNS : bool
        -------
        True : data is enqueued successfully
        False : not sufficient space in the buffer to hold the passed number of data bytes
        """

        # Proceed only if there is sufficient space in the buffer to accomodate the byte sequence
        lt = len(bytSeq)
        if self.filled + lt <= self.maxSize:
            self.data = self.data + bytSeq
            self.filled = self.filled + lt
            return True
        # If there is not sufficient space in the buffer to accomonate the passed number of data bytes, return False
        else:
            return False
    
    def dequeue(self, req):
        """
        This method is used to pop data byte from the buffer

        PARAMETERS
        ----------
        req : int
        The number of data bytes to be dequeued

        RETURNS : byte array
        -------
        The dequeued byte string
        """
        
        if req == 0:
            return b''
        # If the passed number data bytes are not avaialable in the buffer then raise an exception
        elif self.filled >= req:
            st = self.data[0:req]
            self.data = self.data[req:]
            self.filled = self.filled - req
            return st
        # If data is not available to return then, raise an exception
        else:
            raise bufferException("Data unavailable")
    
    def flush(self):
        """
        This method is used to flush the buffer

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.data=b''
        self.filled=0


class bufferException(Exception):
    """
    This is a child class of the Exception class. It is a custom exception class.
    """
    pass