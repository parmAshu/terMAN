"""
This module contains the App class which is used to create the user interface for the application
"""

__author__ = "ASHUTOSH SINGH PARMAR"

import os
import time
from datetime import datetime
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from utility import serial_utility, os_utility, utils
import ui_constants as uic

def appThread0(app):
    """
    This function is a part of the application logic. It runs as a separate thread.
    The tasks performed by this thread are :
    1. displaying recieved data in the format choosen by the user
    2. storing incoming binary data in a record buffer provided the record option is enabled

    PARAMETERS
    ----------
    app : App class object
    The user interface object for the application

    RETURNS
    -------
    NOTHING
    """
    # the time at which the thread was started
    start_time = datetime.now()

    # All the thread0 logic goes in here
    while True:

        rxWaiting = app.receive_buff.filled
        if rxWaiting:
            try:
                # Dequeue one byte at a time
                byts = app.receive_buff.dequeue(rxWaiting)

                app.pass_buff.enqueue(byts)

                if app.getDisplayOption() == 2:
                    app.putOnDisplay( utils.convertToHexString(byts) )
                else:
                    app.putOnDisplay( byts.decode() )

            except Exception as err:
                pass

        time.sleep(uic.thread0_interval)

def appThread2(app):
    """
    This function is a part of application logic and runs as a separate thread.
    The tasks performed by this thread are :
    1. update the ports menu
    2. update the play file menu
    3. transfer the binary recorded data from buffer into the record file

    PARAMETERS
    ----------
    app : tkinter object

    RETURNS
    -------
    NOTHING
    """
    while True:
        
        # Update the list of available ports every 5 seconds
        app.updatePortsMenu()

        # Update the play file menu
        app.updatePlayFileMenu()

        # See if there is any recording data in the record buffer. If there is some then transfer it to the record file.
        avl = app.recorded_data.filled
        if avl:
            if not app.record_file_name == "":
                with open(app.record_file_name, 'ab') as fl:
                    fl.write( app.recorded_data.dequeue(avl) )

        # See if there is any recording data in the csv record buffer. If there is some then transfer it to the record file.
        avl = len(app.recorded_csv_list)
        if avl:
            if not app.csv_record_file_name=="":
                lst = app.recorded_csv_list[ 0 : avl ]
                del app.recorded_csv_list[ 0 : avl]
                csv_str=utils.convertToCSV(app, lst)
                with open( app.csv_record_file_name, 'a') as fl:
                    fl.write(csv_str)

        time.sleep(uic.thread2_interval)


def appThread4(app):
    """
    This function is a part of application logic and runs as a separate thread.
    The tasks performed by this thread are :

    PARAMETERS
    ----------
    app : tkinter object

    RETURNS
    -------
    NOTHING
    """

    # All the thread4 logic goes in here
    while True:

        if app.pass_buff.filled:
            try:
                # Dequeue one byte at a time
                byt = app.pass_buff.dequeue(1)

                # Record the incoming data if the record option is enabled
                if app.doRecord():

                    # If the binary record option is enabled
                    if app.recordAsCSV():

                        # If newline is detected then, append a tuple to the csv list option
                        if byt == b'\x0a':
                            print('newline - hit')
                            _data = app.csv_data_var
                            app.csv_data_var = b''
                            if not len(_data)==0:
                                app.recorded_csv_list.append( (datetime.now(), _data.decode()) )

                        # Otherwise append data to csv_data_var variable
                        else:
                            #print('character - hit')
                            app.csv_data_var = app.csv_data_var + byt

                    app.recorded_data.enqueue(byt)

            except Exception as err:
                pass

        time.sleep(uic.thread4_interval)
    pass


class App:
    """
    This class creates the user interface and provides methods to interact with the elements of the user interface.
    
    Attributes
    ----------

    root : tkinter object
    The main window object of the application

    __extern_on_close_function : function
    This holds the reference to external function that must be invoked when the user explicity closes the appliction window,
    it is optional to set this using the method onWindowClose()

    lab0 : tkinter Label object
    Says 'PORTS'

    lab1 : tkinter Label object
    Says 'Baud Rate'

    lab2 : tkinter Label object
    Says 'Stop bits'

    lab3 : tkinter Label object
    Says 'Parity'

    lab4 : tkinter Label object
    Says '-'

    var_ports : tkinter StringVar object
    It holds the selected port

    ports_menu : tkinter OptionMenu object
    Drop down menu for selecting ports

    var_baud : tkinter StringVar object
    It holds the selected baud rate

    baud_menu : tkinter OptionMenu object
    Drop down menu for selecting the baud rate

    lab5 : tkinter label object
    Says 'Display incoming data as'

    var_disp : tkinter IntVar()
    This variable holds the display selection; 0 - display as ASCII , 1 - display as HEX

    disp_cbox0 : tkinter RadioButton object
    This is the radiobutton used to select the 'display as ASCII' option
    
    disp_cbox1 : tkinter RadioButton object
    This is the radiobutton used to select the 'display as HEX' option

    Methods
    -------

    launch()
    This member method is used to lauch the appliction

    __function_on_close()
    This member methos is invoked when the main application window is explicity closed by the user

    __createLabel0()
    Private member method that creates lab0

    __createLabel1()
    Private member method that creates lab1

    __createLabel2()
    Private member method that creates lab2

    __createLabel3()
    Private member method that creates lab3

    __createLabel4()
    Private member method that creates lab4

    __createPortsMenu()
    Private member method that creates the dropdown menu for ports selection

    __createBaudMenu()
    Private member method that creates the dropdown menu for baud rate selection

    __createStopBitsBox()
    Private member method that creates stop bits selection menu

    __createParityMenu()
    Private member method that creates a dropdown menu for selecting parity type

    __createConnectionButton()
    Private member method that creates the connect/disconnect button in the SETTINGS MENU BAR in the application window

    __createLabel5()
    Private member method that creates lab5

    __createDisplayOptCheckboxes()
    Private member method that creates the display options radio-buttons in the LEFT PANEL in the application window

    __toggleRecordOption()
    EVENT HANDLER for toggle record option event

    __createRecordOption()
    Private member method that creates the recording enable checkbox

    __toggleRecordAsCSV()
    EVENT HANDLER for toggle record as csv option event

    __createRecordAsCSVOption()
    Private member method that creates the record as csv checkbox

    __saveButtonHandler()
    Private member method that is invoked when save as button is clicked

    __createSaveAsButton()
    Private member method that creates the save as button in the application window

    doRecord()
    This method returns the state of recording enable option

    recordCSV()
    This method returns the state of the enable recording as CSV option

    getDisplayOption()
    This method returns the display option selection

    __createLabel6()
    This method creates lab6

    __createLabel7()
    This method creates lab7

    __createEntry0()
    This method creates the entry text box 0

    __createEntry1()
    This method creates the entry text box 1

    __createPacketizeOption()
    This method creates the packetize option checkbox

    __createNewlineOption()
    This method creates the send newline option checkbox

    getTextEntry0()
    This method returns the text in text box 0

    deleteTextEntry0()
    This method clears the text box 0

    getTextEntry1()
    This method returns the text in text box 1

    deleteTextEntry1()
    This method clears the text box 1

    isPacketMode()
    This method returns the is packet mode is selected

    sendNewline()
    This method returns if the send newline option is enabled or another

    __createPlayFileMenu()
    This method creates the play file select drop down menu

    __createPlayButton()
    This method creates the play button

    __createSendButton()
    This method creates the send button

    __createExplorerButton()
    This method creates the explorer button

    __createWorkspaceLabel()
    This method creates the workspace display label

    __createLabel8()
    This method creates a blank label

    __createDisplayBox()
    This method creates the data display box

    clearDisplayHandler()
    EVENT HANDLER for click on clear display button

    __createClearDisplayButton()
    This method creates the clear display box

    putOnDisplay()
    This method appends the input text to text in the data display box
    """

#----------------------------------------------------------------------------------------------------------------------------
# CONSTRUCTOR AND OTHER APPLICATION METHODS
    def __init__(self):
        """
        Class constructor; it builds the user interface by invoking various private member methods.
        """


        #CREATE THE MAIN WINDOW FOR THE APPLICATION
        self.root=tk.Tk()
        self.root.title(uic.application_title)
        self.root.configure()
        #self.root.resizable(0,0)
        self.__extern_on_close_function = None
        self.root.protocol("WM_DELETE_WINDOW", self.__function_on_close)


        #CREATE THE SETTINGS MENU BAR ON THE TOP OF THE APPLICATION WINDOW
        self.__createLabel0()
        self.__createLabel1()
        self.__createLabel2()
        self.__createLabel3()
        self.__createLabel4()
        self.__createPortsMenu()
        self.__createBaudMenu(serial_utility.baud_list)
        self.__createStopBitsBox()
        self.__createParityMenu()
        self.__createConnectionButton()


        #CREATE THE LEFT PANEL IN THE APPLICATION WINDOW
        self.__createLabel5()
        self.__createDisplayOptCheckBoxes()
        self.__createSaveButton()
        self.__createRecordOption()
        self.__createRecordAsCSVOption()



        #CREATE THE DATA SENDING PANEL
        self.__createLabel6()
        self.__createLabel7()
        self.__createEntry0()
        self.__createEntry1()
        self.__createPacketizeOption()
        self.__createNewlineOption()


        #CREATE THE RIGHT SIDE PANEL
        self.__createPlayFileMenu()
        self.__createPlayButton()
        self.__createSendButton()
        self.__createExplorerButton()
        self.__createWorkspaceLabel()
        self.__createLabel8()
        self.__createDelayBox()


        #CREATE THE DATA DISPLAY SEGMENT
        self.__createDisplayBox()
        self.__createClearDisplayButton()

        #FOR HOLDING SERIAL UTILITY THREAD OBJECTS
        self.app_thread1=None
        self.app_thread3=None

        # CREATE THE SEND AND RECIEVE BUFFERS
        self.receive_buff = utils.buffer(1000)
        self.send_buff = utils.buffer(1000)
        self.pass_buff = utils.buffer(1000)

        #FOR HOLDING THE DATA WHEN RECORDING OPTION IS ENABLED
        self.recorded_data = utils.buffer(uic.binary_record_buffer_size)
        self.recorded_csv_list = []
        # variable used for storing items as csv
        self.csv_data_var = b''

        self.csv_index = 0

        #file name of the temporary record file
        self.record_file_name = ""
        self.csv_record_file_name = ""

        #LAUNCH THE BACKEND THREAD 0
        self.app_thread0=threading.Thread(target = appThread0, args=(self,), daemon=True)
        self.app_thread2=threading.Thread(target = appThread2, args=(self,), daemon=True)
        self.app_thread4=threading.Thread(target = appThread4, args=(self,), daemon=True)
        self.app_thread0.start()
        self.app_thread2.start()
        self.app_thread4.start()
        

    def launch(self):
        """
        This function will launch the user interface when invoked. Internally this function invokes the mainloop()
        function on the application main window object

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.root.mainloop()

    def __function_on_close(self):
        """
        This private method is invoked whenever the tkinter window is closed.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        if not self.record_file_name == "":
            os.remove(self.record_file_name)

        if not self.csv_record_file_name == "":
            os.remove(self.csv_record_file_name)
        
        if not self.__extern_on_close_function == None:
            self.__extern_on_close_function()
        self.root.destroy()

    def onWindowClose(self, closing_function):
        """
        This method associates a function with the WM_DELETE_WINDOW event. This is the event when the user explicity closes
        the application using the window manager.

        PARAMETERS
        ----------
        closing_function : function 
        This is the function that has to be associated with the window closing event

        RETURNS
        -------
        NOTHING
        """
        self.__extern_on_close_function = closing_function

    def warning(self, text):
        """
        This method makes a warning message appear on the application window

        PARAMETERS
        ----------
        text : str
        The warning message

        RETURNS
        -------
        NOTHING
        """
        messagebox.showwarning("warning", text)

    def information(self, text):
        """
        This method shows an information message box on the application window

        PARAMETERS
        ----------
        text : str
        The information text

        RETURNS
        -------
        NOTHING
        """
        messagebox.showinfo("message", text)

    def yesno(self, text):
        """
        This method makes a dialog box appear on the window and requires the user to select either YES or NO

        PARAMETERS
        ----------
        text : str
        The message text

        RETURNS
        -------
        NOTHING
        """
        return messagebox.askyesno("message", text)

    def okcancel(self, text):
        """
        This method makes a dialog box pop appear on the window and requires the user to select either CANCEK or OK

        PARAMETERS
        ----------
        text : str
        The message text

        RETURNS
        -------
        NOTHING
        """
        return messagebox.askyesnocancel("message", text)

    def error(self, text):
        """
        This method shows an error dialog box on the window

        PARAMETERS
        ----------
        text : str
        The error message

        RETURNS 
        -------
        NOTHING
        """
        messagebox.showerror('error', text)

    def serialTerminateCallback(self, err):
        """
        This method is called by serial utility thread when it is terminated

        PARAMETERS
        ----------
        err : str
        The exception that caused the termination of serial thread

        RETURNS
        -------
        NOTHING
        """
        print('Error : ', err)
        self.app_thread1 = None
        serial_utility.run_serial_thread = 0

        # when there is problem with opening the port
        if err == "SerialException":
            self.error('Port Unavailable')
        elif err == "SerialTerminate":
            pass
        elif err == "AttributeError":
            pass

        self.connect_button['state'] = "normal"
        self.connect_button.configure(text="connect")

    def serialStartedCallback(self):
        """
        This method is called serial utility thread when it has started successfully

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        # clear the recorded data upon a new connection
        self.recorded_data.flush()
        self.recorded_csv_list=[]
        self.csv_data_var=b''
        self.csv_index = 0

        # if there exits a record file when a connection is made then, delete it
        if not self.record_file_name == "":
            os.remove(self.record_file_name)
            self.record_file_name=""

        # if there exits a record file when a connection is made then, delete it
        if not self.csv_record_file_name == "":
            os.remove(self.csv_record_file_name)
            self.csv_record_file_name=""

        # Create a record file only when a workspace has been selected. This mechanism is fail proof because, recording
        # can be enabled only when there is valid workspace selected and similarly record file can be created only
        # when a valid workspace is selected. Moreover, there is data in the record buffer only when record option is enabled.
        # So, indirectly, there is data in the record buffer only when there is a valid workspace and hence a valid record file.
        wrksp = os_utility.getActiveWorkspace()
        if not wrksp == "none":
            flnm = os.path.join(wrksp, self.createFileName()+'.bin')
            with open( flnm , 'ab') as fl:
                fl.write(b'')
            self.record_file_name = flnm

            flnm = os.path.join(wrksp, self.createFileName()+'.csv')
            with open( flnm , 'w') as fl:
                fl.write('')
            self.csv_record_file_name = flnm

        self.connect_button['state'] = "normal"
        self.connect_button.configure(text="disconnect")

    def createFileName(self):
        """
        This private method creates a unique file name when invoked.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        now = datetime.now()
        file_name = now.strftime("temp_%d_%m_%Y_%H_%M_%S")
        return file_name

    def serialTerminateCallback_Play(self, err):
        """
        This method is called by serial utility thread when it is terminated

        PARAMETERS
        ----------
        err : str
        The exception that caused the termination of the serial thread

        RETURNS
        -------
        NOTHING
        """
        print('Error : ', err)
        self.app_thread3 = None
        serial_utility.run_serial_thread1 = 0

        # when there is problem with opening the port
        if err == "SerialException":
            self.error('Port Unavailable')
        elif err == "SerialTerminate":
            pass
        elif err == "AttributeError":
            pass

        self.connect_button['state'] = "normal"
        self.send_button['state']="normal"
        self.play_button['state']="normal"
        self.play_button['text']="play"

    def serialStartedCallback_Play(self):
        """
        This method is called serial utility thread when it has started successfully

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        # clear the recorded data upon a new connection
        self.recorded_data.flush()
        self.recorded_csv_list=[]
        self.csv_data_var=b''
        self.csv_index = 0

        # if there exits a record file when a connection is made then, delete it
        if not self.record_file_name == "":
            os.remove(self.record_file_name)
            self.record_file_name=""

        # if there exits a record file when a connection is made then, delete it
        if not self.csv_record_file_name == "":
            os.remove(self.csv_record_file_name)
            self.csv_record_file_name=""

        # Create a record file only when a workspace has been selected. This mechanism is fail proof because, recording
        # can be enabled only when there is valid workspace selected and similarly record file can be created only
        # when a valid workspace is selected. Moreover, there is data in the record buffer only when record option is enabled.
        # So, indirectly, there is data in the record buffer only when there is a valid workspace and hence a valid record file.
        wrksp = os_utility.getActiveWorkspace()
        if not wrksp == "none":
            flnm = os.path.join(wrksp, self.createFileName() + '.bin')
            with open( flnm , 'ab') as fl:
                fl.write(b'')
            self.record_file_name = flnm

            flnm = os.path.join(wrksp, self.createFileName()+'.csv')
            with open( flnm , 'w') as fl:
                fl.write('')
            self.csv_record_file_name = flnm

        self.play_button['state']='normal'
        self.play_button['text']='stop'


# END OF APPLICATION RELATED METHODS
#----------------------------------------------------------------------------------------------------------------------------





#----------------------------------------------------------------------------------------------------------------------------
# METHODS TO CREATE AND INTERACT WITH SETTINGS MENU ON THE TOP OF THE APPLICATION WINDOW
    def __createLabel0(self):
        """
        This private method creates the label that says 'PORT'

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.lab0 = tk.Label(self.root, text="PORT :")
        self.lab0.grid(row=0, column=0)
    
    def __createLabel1(self):
        """
        This private method creates the label that says 'BAUD RATE'

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.lab1 = tk.Label(self.root, text="BAUD RATE :")
        self.lab1.grid(row=0, column=1)
    
    def __createLabel2(self):
        """
        This private method creates the label that says 'STOP BITS'

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.lab2 = tk.Label(self.root, text="STOP BITS :")
        self.lab2.grid(row=0, column=2)

    def __createLabel3(self):
        """
        This private method creates the label that says 'PARITY'

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.lab3 = tk.Label(self.root, text="PARITY :")
        self.lab3.grid(row=0, column=3)

    def __createLabel4(self):
        """
        This private method creates a label that says '-'

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.lab4 = tk.Label(self.root, text="-")
        self.lab4.grid(row=0, column=4)

    def __createPortsMenu(self):
        """
        This private method creates the ports selection drop down menu

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.ports_list = serial_utility.getPorts()
        self.var_ports = tk.StringVar(self.root)
        self.var_ports.set(self.ports_list[0])
        self.port_menu = tk.OptionMenu(self.root, self.var_ports, *self.ports_list)
        self.port_menu.config(width=uic.port_menu_width)
        self.port_menu.grid(row=1, column=0)

    def __createBaudMenu(self, list_rates):
        """
        This private method creates the baud rate selection drop down menu

        PARAMETERS
        ----------
        list_rates : list
        A list of baud rates supported by the tool

        RETURNS
        -------
        NOTHING
        """
        self.var_baud = tk.StringVar(self.root)
        self.var_baud.set(serial_utility.default_baud)
        self.baud_menu = tk.OptionMenu(self.root, self.var_baud, *list_rates)
        self.baud_menu.config(width=uic.baud_menu_width)
        self.baud_menu.grid(row=1, column=1)

    def __createStopBitsBox(self):
        """
        This private methos creates a menu for selecting number of stop bits

        PARAMETERS
        ----------
        NONE

        Returns
        -------
        NOTHINGs
        """
        self.stp_bits_menu=tk.Spinbox(self.root, from_ = 1, to_ = 2)
        self.stp_bits_menu.config(width=uic.stop_bits_menu_width)
        self.stp_bits_menu.grid(row=1,column=2)

    def __createParityMenu(self):
        """
        This private method creates a drop down menu for selecting parity type

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.var_parity = tk.StringVar(self.root)
        self.var_parity.set(serial_utility.default_parity)
        self.parity_menu=tk.OptionMenu(self.root, self.var_parity, *serial_utility.parity_list)
        self.parity_menu.config(width=uic.parity_menu_width)
        self.parity_menu.grid(row=1,column=3)
    
    def __connectButtonHandler(self):
        """
        EVENT HANDLER
        This function is triggered whenever the connect button is clicked
        
        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        # DISABLING THE BUTTON
        self.connect_button['state']="disabled"

        if self.connect_button['text'] == 'connect':
            serial_utility.run_serial_thread = 1
            self.app_thread1 = threading.Thread(target = serial_utility.appThread1, args=(self,), daemon=True)
            self.app_thread1.start()
        else:
            serial_utility.run_serial_thread = 0

    def __createConnectionButton(self):
        """
        This private method creates the connect/disconnect button

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.connect_button = tk.Button(self.root, text="connect", command=self.__connectButtonHandler, width=uic.connection_button_width)
        self.connect_button.grid(row=1,column=4)

    def updatePortsMenu(self):
        """
        This method is used to update the ports menu in the SETTINGS MENU of the application.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        
        current_port_selection = self.getPortSelection()

        self.port_menu.children["menu"].delete(0, "end")
        self.ports_list=serial_utility.getPorts()
        
        for i in self.ports_list:
            self.port_menu.children["menu"].add_command(label=i, command=lambda value=i: self.var_ports.set(value))
        
        if current_port_selection in self.ports_list:
            self.var_ports.set(current_port_selection)
        else:
            self.var_ports.set(self.ports_list[0])

    def getPortSelection(self):
        """
        This method returns the selected port

        PARAMETERS
        ----------
        NONE

        RETURNS : str
        -------
        The name of the selected port
        """
        return self.var_ports.get()

    def getBaudSelection(self):
        """
        This method returns the selected baud rate

        PARAMETERS
        ----------
        NONE

        RETURNS : 
        -------
        The selected baud rate
        """
        return self.var_baud.get()

    def getStopBits(self):
        """
        This method returns the selected number of stop bits

        PARMETERS
        ---------
        NONE

        RETURNS :
        -------
        The selected number of stop bits
        """
        return self.stp_bits_menu.get()
    
    def getParity(self):
        """
        This method returns the selected parity

        PARAMETERS
        ----------
        NONE

        RETURNS : str
        -------
        The selected parity type
        """
        return self.var_parity.get()

# END OF SETTINGS MENU RELATED METHODS
#----------------------------------------------------------------------------------------------------------------------------





#----------------------------------------------------------------------------------------------------------------------------
# METHODS TO CREATE AND INTERACT WITH LEFT PANEL OF THE APPLICATION INTERFACE

    def __createLabel5(self):
        """
        This private method creates the label that says 'Display incoming data as'

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.lab5 = tk.Label(self.root, text="Display incoming data as:", pady=5)
        self.lab5.grid(row=2,column=0, sticky='W', padx=uic.left_border_padding)

    def __createDisplayOptCheckBoxes(self):
        """
        This method creates the radio buttons that are used to change display settings for data coming from serial port

        PARAMTERS
        ---------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.var_disp = tk.IntVar()
        self.disp_cbox0 = tk.Radiobutton(self.root, text="ASCII", variable=self.var_disp, value=1, justify="left")
        self.disp_cbox1 = tk.Radiobutton(self.root, text="HEX ", variable=self.var_disp, value=2, justify="left")
        self.disp_cbox0.grid(row=3,column=0, sticky='W', padx=uic.left_border_padding)
        self.disp_cbox1.grid(row=4,column=0, sticky='W', padx=uic.left_border_padding)
        self.disp_cbox0.select()

    def __toggleRecordOption(self):
        """
        This private method is invoked whenever the record option is toggled

        PARMETERS
        ---------
        NONE

        RETURNS
        -------
        NOTHING
        """
        if self.doRecord():
            # if the record option is enabled then, make sure that a workspace has been selected
            if os_utility.getActiveWorkspace() == "none":
                self.information("Please select a workspace before enabling the record option")
                self.record_option.deselect()
                self.record_csv_option.deselect()
        else:
            #if the record option has been deselected then deselect the record as csv option as well
            self.record_csv_option.deselect()

    def __createRecordOption(self):
        """
        This private method creates a checkbox that is used to enable recording the incoming data

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.do_record = tk.IntVar()
        self.record_option = tk.Checkbutton(self.root, text="Record incoming data", variable=self.do_record, command=self.__toggleRecordOption)
        self.record_option.grid(row=6, column=0, sticky='W', padx=uic.left_border_padding)

    def __toggleRecordAsCSV(self):
        """
        This private method is invoked when the record as csv checkbox is toggled

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        if not self.doRecord():
            self.record_csv_option.deselect()

    def __createRecordAsCSVOption(self):
        """
        This private method creates a checkbox that will be used to enable recording the incoming data in csv format

        PARAMETER
        ---------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.record_csv = tk.IntVar()
        self.record_csv_option = tk.Checkbutton(self.root, text="Record as CSV", variable=self.record_csv, command=self.__toggleRecordAsCSV)
        self.record_csv_option.grid(row=7, column=0, sticky='W', padx=uic.left_border_padding)

    def __saveButtonHandler(self):
        """
        EVENT HANDLER
        This method is invoked whenever the 'save as' button is pressed

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        # If there is unprocessed data then, ask the user to wait
        if self.receive_buff.filled or self.pass_buff.filled or self.recorded_data.filled or len(self.recorded_csv_list):
            self.information("Processing, kindly wait ")
            return

        if self.record_file_name == "" or self.csv_record_file_name == "":
            self.information("No recorded data !")
            return

        with open(self.record_file_name, 'rb') as fl:
            data_byts = fl.read()

        with open(self.csv_record_file_name) as fl:
            csv_data = fl.read()

        if len(data_byts) == 0 and len(csv_data) == 0:
            self.information("No recorded data")
            return

        file_name = filedialog.asksaveasfilename()

        if len(data_byts):
            with open( file_name + '.bin' , 'wb' ) as fl:
                fl.write(data_byts)
        
        if len(csv_data):
            with open( file_name + '.csv', 'w') as fl:
                fl.write(csv_data)
    
    def __createSaveButton(self):
        """
        This private method creates the 'save as' button

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.save_button = tk.Button(self.root, text="save", command=self.__saveButtonHandler, width=uic.save_button_width, bg="#0000ff")
        self.save_button.grid(row=8, column=0, stick='N', pady=5)

    def doRecord(self):
        """
        This method returns the status of enable recording checkbox

        PARAMETERS
        ----------
        NONE

        RETURNS : int
        -------
        0 : recording disabled
        1 : recoding enabled
        """
        return self.do_record.get()

    def recordAsCSV(self):
        """This method returns the status of record as CSV checkbox

        PARAMETERS
        ----------
        NONE

        RETURNS : int
        -------
        0 : disabled
        1 : enabled
        """
        return self.record_csv.get()

    def getDisplayOption(self):
        """
        This method returns the selected display option

        PARAMETERS
        ----------
        NONE

        RETURNS : int
        -------
        0 : ASCII
        1 : HEX
        """
        return self.var_disp.get()

# END OF LEFT PANEL RELATED METHODS
#----------------------------------------------------------------------------------------------------------------------------





#----------------------------------------------------------------------------------------------------------------------------
# METHODS TO CREATE AND INTERACT WITH THE DATA SENDING PANEL LOCATED IN THE CENTER AND TOWARDS THE TOP OF THE APPLICATION WINDOW

    def __createWorkspaceLabel(self):
        """
        This private method creates a label that is used to display the active workspace

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.workspace_label = tk.Label(self.root, text=os_utility.getActiveWorkspace(), width=uic.workspace_label_width, anchor="w")
        self.workspace_label.grid(row=2, column=1, columnspan=2)

    def __createLabel6(self):
        """
        This private method creates the label that says 'UTF-8:'

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.lab6 = tk.Label(self.root, text="UTF-8:", padx=2)
        self.lab6.grid(row=3,column=1,sticky='W')

    def __createLabel7(self):
        """
        This priavte method creates the label that says 'RAW:'

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.lab7 = tk.Label(self.root, text="RAW:", padx=2)
        self.lab7.grid(row=4,column=1,sticky='W')

    def __createEntry0(self):
        """
        This private method creates a text box where user types in the data to send over serial port;
        data from this text box is sent as it is

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.entry0 = tk.Entry(self.root)
        self.entry0.config(width=uic.entry_width, bd=2, bg=uic.display_color)
        self.entry0.grid(row=3, column=2, columnspan=2, stick='W')

    def __createEntry1(self):
        """
        This private method creates a text box where user types in the data to send over serial port;
        user must type data in HEX form in this text box

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.entry1 = tk.Entry(self.root)
        self.entry1.config(width=uic.entry_width, bd=2, bg=uic.display_color)
        self.entry1.grid(row=4, column=2, columnspan=2, stick='W')

    def __createPacketizeOption(self):
        """
        This private method creates a checkbox that is used to prevent clearing the entry boxes when clicking send button.
        This is called the packetize option
        
        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.packetize = tk.IntVar()
        self.packetize_option = tk.Checkbutton(self.root, text="Packet mode", variable=self.packetize)
        self.packetize_option.grid(row=6, column=1, sticky='W')

    def __createNewlineOption(self):
        """
        This private method creates a checkbox that will make the application automatically append newline character 
        when clicking the send button.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.send_newline = tk.IntVar()
        self.send_newline_option = tk.Checkbutton(self.root, text="Newline", variable=self.send_newline)
        self.send_newline_option.grid(row=6, column=2, sticky='W')

    def getTextEntry0(self):
        """
        This function returns the text in entry0 box
        
        PARAMETERS
        ----------
        NONE

        RETURNS : str
        -------
        Text in the text box 0
        """
        return self.entry0.get()

    def deleteTextEntry0(self):
        """
        This method deletes all the characters from entry0 box

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.entry0.delete(0, 'end')

    def getTextEntry1(self):
        """
        This method returns the text in entry1 box

        PARAMETERS
        ----------
        NONE

        RETURNS : str
        -------
        Text in the text box 1
        """
        return self.entry1.get()

    def deleteTextEntry1(self):
        """
        This method deletes all the characters from entry1 box

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.entry1.delete(0, 'end')

    def isPacketMode(self):
        """
        This method returns whether packet mode is enabled or not
        
        PARAMETERS
        ----------
        NONE

        RETURNS : int
        -------
        0 : disabled
        1 : enabled
        """
        return self.packetize.get()
    
    def sendNewline(self):
        """
        This method returns the state of send newline character option

        PARAMETERS
        ----------
        NONE

        RETURNS : int
        -------
        0 : disabled
        1 : enabled
        """
        return self.send_newline.get()

# END OF CENTER DATA SENDING PANEL RELATED MTEHODS
#----------------------------------------------------------------------------------------------------------------------------





#---------------------------------------------------------------------------------------------------------------------------
# METHODS TO CREATE AND INTERACT WITH RIGHT SIDE PANEL OF THE APPLICATION WINDOW

    def __createPlayFileMenu(self):
        """
        This private method creates the drop down menu for selecting the file to be played

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.var_play_file = tk.StringVar(self.root)
        files_list=os_utility.filesInWorkspace()
        
        if len(files_list)==0:
            self.var_play_file.set('-')
            self.play_file_menu = tk.OptionMenu(self.root, self.var_play_file, '-')
        else:
            self.var_play_file.set(files_list[0])
            self.play_file_menu = tk.OptionMenu(self.root, self.var_play_file, *files_list)

        self.play_file_menu.config(width=uic.play_file_menu_width, padx=2)
        self.play_file_menu.grid(row=5, column=4, padx=10)
    
    def updatePlayFileMenu(self):
        """
        This method updates the drop down menu that is used for selecting to be played file
        
        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.play_file_menu.children["menu"].delete(0, "end")
        files_list = os_utility.filesInWorkspace()
        for i in files_list:
            self.play_file_menu.children["menu"].add_command(label=i, command=lambda value=i: self.var_play_file.set(value))
        if len(files_list)==0:
            self.var_play_file.set('-')
        else:
            self.var_play_file.set(files_list[0])

    def sendButtonHandler(self):
        """
        This method is invoked whenever the send button is clicked on

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        try:
            byt_str = self.getTextEntry0().encode()
            byt_str = byt_str + utils.convertToByteString(self.getTextEntry1())

            if self.sendNewline():
                byt_str = byt_str + b'\n'

            if self.send_buff.enqueue(byt_str) == False:
                self.error("Insufficient space in send buffer")

            if not self.isPacketMode():
                self.deleteTextEntry0()
                self.deleteTextEntry1()
        except Exception as e:
            self.error('Invalid Data Packet' + str(e))
            self.deleteTextEntry0()
            self.deleteTextEntry1()

    def __createSendButton(self):
        """
        This method creates the send button

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.send_button=tk.Button(self.root, text="send", width=uic.send_button_width, command=self.sendButtonHandler)
        self.send_button.grid(row=3, column=4)

    def playButtonHandler(self):
        """
        EVENT HANDLER
        This method is invoked whenever the play button is clicked on

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        def disableButtons(app):
            app.connect_button['state']="disabled"
            app.play_button['state']="disabled"
            app.send_button['state']="disabled"

        def enableButtons(app):
            app.connect_button['state']="normal"
            app.play_button['state']="normal"
            app.send_button['state']="normal"

        disableButtons(self)

        if self.play_button['text'] == 'play':

            # if a port is already connected then, cancel any further operations
            if self.connect_button['text'] == 'disconnect':
                self.information("Disconnect before playing !!")
                enableButtons(self)
                return

            # if no valid play file is selected then, cancel any futher operations
            if self.getPlayFile() == '-':
                self.error("No play file selected")
                enableButtons(self)
                return
        
            delay = self.getDelay()
            if delay < 0:
                self.information("Invalid delay")
                enableButtons(self)
                return
            
            try:
                with open( os.path.join(os_utility.getActiveWorkspace(), self.getPlayFile()), 'rb') as fl:
                    byts = fl.read()
                
                self.send_buff.enqueue( byts )
                print('bytes in buffer : ', self.send_buff.filled)

            except:
                self.error("Could not read file")
                enableButtons(self)
                return

            serial_utility.run_serial_thread1 = 1
            self.app_thread3 = threading.Thread(target = serial_utility.appThread3, args=(self,delay), daemon=True)
            self.app_thread3.start()
        else:
            serial_utility.run_serial_thread1 = 0
            print(serial_utility.run_serial_thread1)


    def __createPlayButton(self):
        """
        This method creates the play button

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.play_button=tk.Button(self.root, text="play", width=uic.play_button_width, command=self.playButtonHandler)
        self.play_button.grid(row=9, column=4, sticky="N")

    def explorerButtonHandler(self):
        """
        EVENT HANDLER
        This method is invoked when the explorer button is clicked on

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        if self.connect_button['text'] == 'disconnect':
            self.information("Disconnect port before changing workspace")
            return

        dir_name = filedialog.askdirectory()
        if not dir_name == '':
            os_utility.updateWorkspace(dir_name)
            self.workspace_label.configure(text=os_utility.getActiveWorkspace())
            self.updatePlayFileMenu()

    def __createExplorerButton(self):
        """This function creates a button that will be used to lauch the file explorer"""
        self.explorer_button=tk.Button(self.root, text="workspace", command=self.explorerButtonHandler)
        self.explorer_button.grid(row=2,column=4)

    def __createLabel8(self):
        """
        This method creates a blank label
        
        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.lab8 = tk.Label(self.root, text="")
        self.lab8.grid(row=4, column=4)
    
    def getPlayFile(self):
        """
        This method returns the currently selected play file name

        PARAMETERS
        ----------
        NONE

        RETURNS : str
        -------
        Selected play file name
        """
        return self.var_play_file.get()

    def __createDelayBox(self):
        """
        This method creates an entry box where user can specify the required delay between sending two consecutive bytes
        when a file is being played!

        PARAMETERS
        ----------
        NONE
        
        RETURNS
        -------
        NOTHING
        """
        self.delay_lab = tk.Label(self.root, text="Delay (ms):")
        self.delay_box = tk.Entry(self.root)
        self.delay_box.config(bd=2)
        self.delay_lab.grid(row=7, column=4)
        self.delay_box.grid(row=8, column=4, sticky="N")

    def getDelay(self):
        """
        This method returns the delay time as specified in the delay box.

        PARAMETERS
        ----------
        NONE

        RETURNS : float
        -------
        The delay in millisseconds
        OR
        -1.0 - If the either no value was provided in the entry box or value provided is not valid
        """

        val = self.delay_box.get()

        if val == "":
            return -1.0
        else:
            try:
                delay = float(val)
                return delay
            except:
                return -1.0


# END OF RIGHT SIDE PANEL RELATED METHODS
#---------------------------------------------------------------------------------------------------------------------------


    

    
#---------------------------------------------------------------------------------------------------------------------------
# METHODS TO CREATE AND INTERACT WITH THE DISPLAY SEGMENT
    def __createDisplayBox(self):
        """
        This method creates a text box where incoming data is displayed

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.display = tk.Text(self.root, width=uic.display_width, bg=uic.display_color, fg=uic.display_text_color, xscrollcommand=False, yscrollcommand=True)
        self.display.configure(font=(uic.display_font, uic.display_font_size))
        self.display.grid(row=8, column=1, columnspan=3, rowspan=3, pady=10)

    def clearDisplayHandler(self):
        """
        EVENT HANDLER
        This function is invoked when the clear display button is clicked

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.clearDisplay()

    def __createClearDisplayButton(self):
        """
        This method creates a button that can be used to clear the display

        PARMETERS
        ---------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.clear_display_button=tk.Button(self.root, text="Clear", width=uic.clear_button_width, command=self.clearDisplayHandler)
        self.clear_display_button.grid(row=12, column=3, sticky='E', pady=10)
    

    def clearDisplay(self):
        """
        This method clears the display box

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.display.delete( '1.0', 'end')

    def putOnDisplay(self, text):
        """
        This function appends text to display box

        PARAMETERS
        ----------
        text : str
        The text to be displayed in the display area

        RETURNS
        -------
        NOTHING
        """
        self.display.insert(tk.END, text)
#---------------------------------------------------------------------------------------------------------------------------





#---------------------------------------------------------------------------------------------------------------------------
# CREATING THE BOTTUM INDICATORS BAR
#---------------------------------------------------------------------------------------------------------------------------