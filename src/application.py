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
import app_constants as appconst


def RECORD_THREAD(app):
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
    start_time = datetime.now()

    # All the thread4 logic goes in here
    while True:

        if app.receive_buff.filled:
            # Dequeue one byte at a time
            byt = app.receive_buff.dequeue(1)

            # If the binary record option is enabled
            if app.recordAsCSV():

                # If newline is detected then, append a tuple to the csv list option
                if byt == b'\x0a':
                    _data = app.csv_data_var
                    app.csv_data_var = b''
                    if not len(_data)==0:
                        try:
                            app.recorded_csv_list.append( (datetime.now(), _data.decode()) )
                        except:
                            pass

                # Otherwise append data to csv_data_var variable
                else:
                    app.csv_data_var = app.csv_data_var + byt

            app.recorded_data.enqueue(byt)


        now = datetime.now()
        if (now-start_time).total_seconds() >= appconst.update_interval:
            start_time = now

            # Update the list of available ports
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

        time.sleep(appconst.record_thread_interval)


class App:
    """
    This class creates the user interface and provides methods to interact with the elements of the user interface.
    """

#----------------------------------------------------------------------------------------------------------------------------
# CONSTRUCTOR AND OTHER METHODS
    def __init__(self):
        """
        Class constructor; it builds the user interface by invoking various private member methods.
        """

        #CREATE THE MAIN WINDOW FOR THE APPLICATION
        self.root=tk.Tk()
        self.root.title(appconst.application_title)
        self.root.configure()
        self.__extern_on_close_function = None
        self.root.protocol("WM_DELETE_WINDOW", self.__function_on_close)

        #CREATE THE WORKSPACE SEGMENT
        self.__createWorkspaceSegment()

        #CREATE THE PORT SEGMENT
        self.__createPortsSegment()

        #CREATE THE LEFT SEGMENT
        self.__createLeftSegment()

        #CREATE THE RIGHT SEGMENT
        self.__createRightSegment()

        # SERIAL UTILITY THREAD OBJECTS
        self.serial_thread0=None
        self.serial_thread1=None

        # CREATE BUFFERS AND OTHER VARIABLES
        self.receive_buff = utils.buffer(appconst.receive_buffer_size)
        self.send_buff = utils.buffer(appconst.send_buffer_size)
        self.recorded_data = utils.buffer(appconst.binary_record_buffer_size)
        self.recorded_csv_list = []
        self.csv_data_var = b''
        self.csv_index = 0

        #file name of the temporary record file
        self.record_file_name = ""
        self.csv_record_file_name = ""

        #LAUNCH THE THREADS
        self.record_thread=threading.Thread(target = RECORD_THREAD, args=(self,), daemon=True)
        self.record_thread.start()
        

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
#----------------------------------------------------------------------------------------------------------------------------





#---------------------------------------------------------------------------------------------------------------------------
# CALLBACK METHODS

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

    def serial0StoppedClbk(self, err):
        """
        This method is called by serial thread 0 when it is terminated.

        PARAMETERS
        ----------
        err : str
        The exception that caused the termination of serial thread

        RETURNS
        -------
        NOTHING
        """
        print('Error : ', err)
        self.serial_thread0 = None
        serial_utility.run_serial_thread0 = 0

        # when there is problem with opening the port
        if err == "SerialException":
            self.error('Port Unavailable')
        elif err == "SerialTerminate":
            pass
        elif err == "AttributeError":
            pass

        self.connect_button['state'] = "normal"
        self.connect_button.configure(text="connect")

    def serial0StartedClbk(self):
        """
        This method is called by serial thread 0 when it has started successfully.

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

    def serial1StoppedClbk(self, err):
        """
        This method is called by serial thread 1 when it is terminated.

        PARAMETERS
        ----------
        err : str
        The exception that caused the termination of the serial thread

        RETURNS
        -------
        NOTHING
        """
        print('Error : ', err)
        self.serial_thread1 = None
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

    def serial1StartedClbk(self):
        """
        This method is called by serial thread 1 when it has started successfully.

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
#---------------------------------------------------------------------------------------------------------------------------





#---------------------------------------------------------------------------------------------------------------------------
# POPUPS

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
#---------------------------------------------------------------------------------------------------------------------------





#----------------------------------------------------------------------------------------------------------------------------
# WORSPACE SEGMENT

    def __browseButtonHandler(self):
        """
        EVENT HANDLER
        This method is invoked when the browse button is clicked on.

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

    def __createWorkspaceSegment(self):
        """
        This private method creates the Workspace Segment in the application.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.workspace_segment = tk.LabelFrame(self.root, text="Workspace")
        self.workspace_segment.pack(expand=1, fill=tk.X, padx=5)
        
        self.workspace_label = tk.Label(self.workspace_segment, text=os_utility.getActiveWorkspace(), width=60, anchor='w')
        self.workspace_label.pack(expand=1, fill=tk.X, side=tk.LEFT, padx=5, pady=5)

        self.explorer_button=tk.Button(self.workspace_segment, text=" browse ", command=self.__browseButtonHandler)
        self.explorer_button.configure(width=appconst.explorer_button_width)
        self.explorer_button.pack(expand=1, padx=5, pady=5)

#----------------------------------------------------------------------------------------------------------------------------





#----------------------------------------------------------------------------------------------------------------------------
# PORTS SEGMENT

    def __createPortsSegment(self):
        """
        This private method creates the ports segment in the application window.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.ports_segment = tk.LabelFrame(self.root, text="Device")
        self.ports_segment.pack( expand=1, fill=tk.X, padx=5)

        self.ports_segment_frm0 = tk.Frame(self.ports_segment)
        self.ports_segment_frm1 = tk.Frame(self.ports_segment)
        self.ports_segment_frm0.pack(expand=1, fill=tk.X)
        self.ports_segment_frm1.pack(expand=1, fill=tk.X)

        self.__createPortsSegmentLabels()
        self.__createPortsMenu()
        self.__createBaudMenu(serial_utility.baud_list)
        self.__createStopBitsBox()
        self.__createParityMenu()
        self.__createConnectionButton()

    def __createPortsSegmentLabels(self):
        """
        This private method creates the labels for ports segment.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.ports_segment_lab0 = tk.Label(self.ports_segment_frm0, text="port :", width=appconst.port_menu_width)
        self.ports_segment_lab0.pack(expand=1, side=tk.LEFT)

        self.ports_segment_lab1 = tk.Label(self.ports_segment_frm0, text="baud rate :", width=appconst.baud_menu_width)
        self.ports_segment_lab1.pack(expand=1, side=tk.LEFT)

        self.ports_segment_lab2 = tk.Label(self.ports_segment_frm0, text="stop bits :", width=appconst.stop_bits_menu_width)
        self.ports_segment_lab2.pack(expand=1, side=tk.LEFT)

        self.ports_segment_lab3 = tk.Label(self.ports_segment_frm0, text="parity :", width=appconst.parity_menu_width)
        self.ports_segment_lab3.pack(expand=1, side=tk.LEFT)

        self.lab4 = tk.Label(self.ports_segment_frm0, text="-", width=appconst.connection_button_width)
        self.lab4.pack(expand=1, side=tk.LEFT)

    def __createPortsMenu(self):
        """
        This private method creates the ports segment menu.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.ports_list = serial_utility.getPorts()

        self.var_ports = tk.StringVar(self.ports_segment_frm1)
        self.var_ports.set(self.ports_list[0])
        
        self.port_menu = tk.OptionMenu(self.ports_segment_frm1, self.var_ports, *self.ports_list)
        self.port_menu.config(width=appconst.port_menu_width)
        self.port_menu.pack(expand=1, side=tk.LEFT, padx=5, pady=5)

    def __createBaudMenu(self, list_rates):
        """
        This private method creates the baud rate selection drop down menu.

        PARAMETERS
        ----------
        list_rates : list
        A list of baud rates supported by the tool

        RETURNS
        -------
        NOTHING
        """
        self.var_baud = tk.StringVar(self.ports_segment_frm1)
        self.var_baud.set(serial_utility.default_baud)

        self.baud_menu = tk.OptionMenu(self.ports_segment_frm1, self.var_baud, *list_rates)
        self.baud_menu.config(width=appconst.baud_menu_width)
        self.baud_menu.pack(expand=1, side=tk.LEFT, padx=5, pady=5)

    def __createStopBitsBox(self):
        """
        This private methos creates a menu for selecting number of stop bits.

        PARAMETERS
        ----------
        NONE

        Returns
        -------
        NOTHINGs
        """
        self.stp_bits_menu=tk.Spinbox(self.ports_segment_frm1, from_ = 1, to_ = 2)
        self.stp_bits_menu.config(width=appconst.stop_bits_menu_width)
        self.stp_bits_menu.pack(expand=1, side=tk.LEFT, padx=5, pady=5)

    def __createParityMenu(self):
        """
        This private method creates a drop down menu for selecting parity type.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.var_parity = tk.StringVar(self.ports_segment_frm1)
        self.var_parity.set(serial_utility.default_parity)

        self.parity_menu=tk.OptionMenu(self.ports_segment_frm1, self.var_parity, *serial_utility.parity_list)
        self.parity_menu.config(width=appconst.parity_menu_width)
        self.parity_menu.pack(expand=1, side=tk.LEFT, padx=5, pady=5)
    
    def __connectionHandler(self):
        """
        EVENT HANDLER
        This method is triggered whenever the connect button is clicked.
        
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
            serial_utility.run_serial_thread0 = 1
            self.serial_thread0 = threading.Thread(target = serial_utility.SERIAL_THREAD0, args=(self,), daemon=True)
            self.serial_thread0.start()
        else:
            serial_utility.run_serial_thread0 = 0

    def __createConnectionButton(self):
        """
        This private method creates the connect/disconnect button.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.connect_button = tk.Button(self.ports_segment_frm1, text="connect", command=self.__connectionHandler, width=appconst.connection_button_width)
        self.connect_button.pack(expand=1, side=tk.LEFT, padx=5, pady=5)

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
        This method returns the selected port.

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
        This method returns the selected baud rate.

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
        This method returns the selected number of stop bits.

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
        This method returns the selected parity.

        PARAMETERS
        ----------
        NONE

        RETURNS : str
        -------
        The selected parity type
        """
        return self.var_parity.get()

#----------------------------------------------------------------------------------------------------------------------------




#----------------------------------------------------------------------------------------------------------------------------
# METHODS TO CREATE AND INTERACT WITH LEFT PANEL OF THE APPLICATION INTERFACE

    def __createLeftSegment(self):
        """
        This private method creates the left side panel in the application window.
        
        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.left_segment = tk.Frame(self.root)
        self.left_segment.pack(expand=1, padx=5, pady=5, side=tk.LEFT)

        self.display_section = tk.LabelFrame(self.left_segment, text="Display")
        self.display_section.pack(expand=1, fill=tk.X, padx=5, pady=5)

        self.record_section = tk.LabelFrame(self.left_segment, text="Record")
        self.record_section.pack(expand=1, fill=tk.X, padx=5, pady=5)

        self.play_section = tk.LabelFrame(self.left_segment, text="Play")
        self.play_section.pack(expand=1, fill=tk.X, padx=5, pady=5)

        self.__createDisplayOptCheckBoxes()
        self.__createRecordOption()
        self.__createRecordAsCSVOption()
        self.__createSaveButton()
        self.__createPlayFileMenu()
        self.__createDelayBox()
        self.__createPlayButton()

    def __createDisplayOptCheckBoxes(self):
        """
        This method creates the radio buttons that are used to change display settings for data coming from serial port.

        PARAMTERS
        ---------
        NONE

        RETURNS
        -------
        NOTHING
        """

        self.var_disp = tk.IntVar()
        self.disp_cbox0 = tk.Radiobutton(self.display_section, text="ASCII", variable=self.var_disp, value=1, justify="left")
        self.disp_cbox1 = tk.Radiobutton(self.display_section, text="HEX ", variable=self.var_disp, value=2, justify="left")
        self.disp_cbox0.pack(expand=1, padx=5, pady=5)
        self.disp_cbox1.pack(expand=1, padx=5, pady=5)
        self.disp_cbox0.select()

    def __toggleRecordOption(self):
        """
        This method is invoked whenever the record option is toggled.

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
        This private method creates a checkbox that is used to enable recording the incoming data.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.do_record = tk.IntVar()
        self.record_option = tk.Checkbutton(self.record_section, text="Record incoming data", variable=self.do_record, command=self.__toggleRecordOption)
        self.record_option.pack(expand=1, padx=5, pady=5)

    def __toggleRecordAsCSV(self):
        """
        This private method is invoked when the record as csv checkbox is toggled.

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
        This private method creates a checkbox that will be used to enable recording the incoming data in csv format.

        PARAMETER
        ---------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.record_csv = tk.IntVar()
        self.record_csv_option = tk.Checkbutton(self.record_section, text="Record as CSV", variable=self.record_csv, command=self.__toggleRecordAsCSV)
        self.record_csv_option.pack(expand=1, padx=5, pady=5)

    def __saveButtonHandler(self):
        """
        EVENT HANDLER
        This method is invoked whenever the 'save as' button is pressed.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        # If there is unprocessed data then, ask the user to wait
        if self.receive_buff.filled or self.recorded_data.filled or len(self.recorded_csv_list):
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
        This private method creates the 'save' button.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.save_button = tk.Button(self.record_section, text="save", command=self.__saveButtonHandler, width=appconst.save_button_width)
        self.save_button.pack(expand=1, padx=5, pady=5)

    def doRecord(self):
        """
        This method returns the status of enable recording checkbox.

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
        """This method returns the status of record as CSV checkbox.

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
        This method returns the selected display option.

        PARAMETERS
        ----------
        NONE

        RETURNS : int
        -------
        0 : ASCII
        1 : HEX
        """
        return self.var_disp.get()

    def __createPlayFileMenu(self):
        """
        This private method creates the drop down menu for selecting the file to be played.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.var_play_file = tk.StringVar(self.play_section)
        files_list=os_utility.filesInWorkspace()
        
        if len(files_list)==0:
            self.var_play_file.set('-')
            self.play_file_menu = tk.OptionMenu(self.play_section, self.var_play_file, '-')
        else:
            self.var_play_file.set(files_list[0])
            self.play_file_menu = tk.OptionMenu(self.play_section, self.var_play_file, *files_list)

        self.play_file_menu.config(width=appconst.play_file_menu_width, padx=2)
        self.play_file_menu.pack(expand=1, padx=5, pady=5)
    
    def updatePlayFileMenu(self):
        """
        This method updates the drop down menu that is used for selecting to be played file.
        
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

    def getPlayFile(self):
        """
        This method returns the currently selected play file name.

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
        self.delay_lab = tk.Label(self.play_section, text="Delay (ms):")
        self.delay_box = tk.Entry(self.play_section)
        self.delay_box.config(bd=2)
        self.delay_lab.pack(expand=1, padx=5, pady=5)
        self.delay_box.pack(expand=1, padx=5, pady=5)

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
    
    def playButtonHandler(self):
        """
        EVENT HANDLER
        This method is invoked whenever the play button is clicked on.

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

            except:
                self.error("Could not read file")
                enableButtons(self)
                return

            serial_utility.run_serial_thread1 = 1
            self.serial_thread1 = threading.Thread(target = serial_utility.SERIAL_THREAD1, args=(self,delay), daemon=True)
            self.serial_thread1.start()
        else:
            serial_utility.run_serial_thread1 = 0


    def __createPlayButton(self):
        """
        This method creates the play button.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.play_button=tk.Button(self.play_section, text="play", width=appconst.play_button_width, command=self.playButtonHandler)
        self.play_button.pack(expand=1, padx=5, pady=5)

# END OF LEFT SEGMENT
#----------------------------------------------------------------------------------------------------------------------------





#---------------------------------------------------------------------------------------------------------------------------
# RIGHT SEGMENT

    def __createRightSegment(self):
        """
        This private method create the right side segment.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """

        self.right_segment = tk.LabelFrame(self.root, text="")
        self.right_segment.pack(fill=tk.X, expand=1, padx=5, pady=5)

        self.__createEntries()

        self.__createOptions_Button()

        self.__createDisplayBox()

    def __createEntries(self):
        """
        This private method creates the entry boxes for sending data.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.entry0_frm = tk.Frame(self.right_segment)
        self.entry1_frm = tk.Frame(self.right_segment)
        self.entry0_frm.pack(expand=1, fill=tk.X, padx=5, pady=5)
        self.entry1_frm.pack(expand=1, fill=tk.X, padx=5, pady=5)

        self.entry0_lab = tk.Label(self.entry0_frm, text="UTF-8:", padx=2)
        self.entry0_lab.pack(expand=1, side=tk.LEFT)

        self.entry1_lab = tk.Label(self.entry1_frm, text="RAW:", padx=2)
        self.entry1_lab.pack(expand=1, side=tk.LEFT)

        self.entry0 = tk.Entry(self.entry0_frm, width=appconst.entry_width)
        self.entry0.config(bd=2, bg=appconst.display_color)
        self.entry0.pack(expand=1, fill=tk.X)

        self.entry1 = tk.Entry(self.entry1_frm, width=appconst.entry_width)
        self.entry1.config(bd=2, bg=appconst.display_color)
        self.entry1.pack(expand=1, fill=tk.X)

    def sendButtonHandler(self):
        """
        This method is invoked whenever the send button is clicked on.

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

    def __createOptions_Button(self):
        """
        This private method creates various options below the entry boxes. It also creates the send button 
        """

        self.options_button_frm = tk.Frame(self.right_segment)
        self.options_button_frm.pack(expand=1, fill=tk.X, padx=5, pady=5)

        self.packetize = tk.IntVar()
        self.packetize_option = tk.Checkbutton(self.options_button_frm, text="Packet mode", variable=self.packetize)
        self.packetize_option.pack(expand=1, padx=2, side=tk.LEFT)

        self.send_newline = tk.IntVar()
        self.send_newline_option = tk.Checkbutton(self.options_button_frm, text="Newline", variable=self.send_newline)
        self.send_newline_option.pack(expand=1, padx=2, side=tk.LEFT)

        self.send_button=tk.Button(self.options_button_frm, text="send", width=appconst.send_button_width, command=self.sendButtonHandler)
        self.send_button.pack(expand=1, padx=2)

    def __createDisplayBox(self):
        """
        This method creates a text box where incoming data is displayed.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.display = tk.Text(self.right_segment, bg=appconst.display_color, fg=appconst.display_text_color, xscrollcommand=False, yscrollcommand=True, width=appconst.entry_width + 20)
        self.display.configure(font=(appconst.display_font, appconst.display_font_size))
        self.display.pack(expand=1, fill=tk.X, padx=5, pady=5)

        self.clear_display_button=tk.Button(self.right_segment, text="Clear",command=self.clearDisplayHandler, width=appconst.clear_button_width)
        self.clear_display_button.pack(expand=1)      

    def getTextEntry0(self):
        """
        This function returns the text in entry0 box.
        
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
        This method deletes all the characters from entry0 box.

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
        This method returns the text in entry1 box.

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
        This method deletes all the characters from entry1 box.

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
        This method returns whether packet mode is enabled or not.
        
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
        This method returns the state of send newline character option.

        PARAMETERS
        ----------
        NONE

        RETURNS : int
        -------
        0 : disabled
        1 : enabled
        """
        return self.send_newline.get()

    def scroll(self):
        self.display.see(tk.END)

    def clearDisplayHandler(self):
        """
        EVENT HANDLER
        This function is invoked when the clear display button is clicked.

        PARAMETERS
        ----------
        NONE

        RETURNS
        -------
        NOTHING
        """
        self.clearDisplay()

    def clearDisplay(self):
        """
        This method clears the display box.

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
        This function appends text to display box.

        PARAMETERS
        ----------
        text : str
        The text to be displayed in the display area

        RETURNS
        -------
        NOTHING
        """
        self.display.insert(tk.END, text)

# END OF RIGHT SEGMENT
#---------------------------------------------------------------------------------------------------------------------------