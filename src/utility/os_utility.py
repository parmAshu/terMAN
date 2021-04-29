"""
This module contains utility functions to perform file io and other os related tasks for the application
"""

__author__ = "ASHUTOSH SINGH PARMAR"

import os
import json

#data file name
data_file = 'saved_data.json'

#list of restricted files
restricted_files=['.DS_Store', '.localized']

try:
    #reading the data from data file
    with open(data_file) as fl:
        saved_data = json.loads(fl.read())
except:
    fl = open(data_file, 'w')
    fl.write('{"workspace": "none"}')
    fl.close()
    saved_data = json.loads( '{"workspace": "none"}' )


def getActiveWorkspace():
    """
    This function returns the active workspace directory; the data is read from the json object stored in the module scope

    PARAMETERS
    ----------
    NONE

    RETURNS : str
    -------
    Active workspace
    """
    global saved_data
    return saved_data["workspace"]

def filesInWorkspace():
    """
    This function returns a list of files in the active workspace directory; if the directory does not contain any FILES
    then, the function returns an empty list

    PARAMETERS
    ----------
    NONE

    RETURNS : list
    -------
    List of file names in active workspace directory
    """
    global saved_data, restricted_files
    files_list=[]
    workspace_dir = saved_data['workspace']
    if not workspace_dir == 'none':
        for fl in os.listdir( workspace_dir ):
            if os.path.isfile(os.path.join( workspace_dir, fl)) and fl.endswith('.bin'):
                files_list.append(fl)
    return files_list

def updateWorkspace(workspace_dir):
    """
    This function updates the active workspace directory; this function updates the global object and the file both

    PARAMETERS
    ----------
    workspace_dir : str
    The new workspace directory name

    RETURNS
    -------
    NOTHINGS
    """
    global saved_data, data_file
    saved_data['workspace'] = workspace_dir
    with open(data_file, 'w') as fl:
        fl.write( json.dumps(saved_data) )
            