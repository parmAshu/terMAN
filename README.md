# TerMAN
**TerMAN** is a minimal yet powerful serial terminal for embedded systems developement.

![application window](/images/app.png)

### **Features**
* Users can provide *'to be sent'* data as:
    * UTF-8 string
    * list of HEX values
* Display recieved bytes as :
    * ASCII decoded string
    * HEX values
* *Packet Mode* : packets can be constructed and sent repeatedly to the connected port
* Incoming data can be recorded in :
    * raw form : Recieved data bytes are saved in a '.bin' file
    * csv form
* *Play Mode* is used to send data bytes from a '.bin' file to the connected device.

### **Supported Baud Rates (bps)**
* 600
* 1200
* 1800
* 2400
* 4800
* 9600
* 19200
* 38400
* 57600
* 115200

### **Supported Byte Sizes**
* 8 bits

### **Supported Number of Stop Bits**
* 1
* 2
