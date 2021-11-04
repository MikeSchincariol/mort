*University of Washintong - Profressional and Continuing Education*  
Certificate in Python Programming  
Capstone Project  


# **Mort - The VNC Session Helper**

In Linux it is possible to start multiple additional desktop sessions, accessible remotely via TCP/IP, using a program called VNC. While running programs remotely is also possible using SSH, the advantage of VNC is that the session and programs continue even if the client disconnects. With SSH, any running processes started in the SSH session are terminated when the SSH session ends.  

However, VNC has a few rough edges, among them:
+ It requires the user to select a display number to use, when starting the server. The display number must not be in use by any other VNC process. Available display numbers are difficult to determine.
+ It requires the user to first login to the server they want to use to start the VNC service for their desktop session.
+ If the server running their VNC session dies or is restarted, the user must manually restart the VNC service.

Mort attempts to solve these issues by:
+ Identifying which servers on a network are available for running VNC sessions
+ Identifying which VNC desktops are already running on a given server, and their display numbers, so that picking a non-conflicting display number is simple
+ Freeing the user from needing to log into the server to start their VNC session by starting the VNC server processes on behalf of the user
+ Keeping track of VNC desktops that should be automatically restarted, and restarts them for the user if the server the VNC desktop is running on gets rebooted

The app is written in Python using Tk for the GUI.
Testing was done on a setup in an AWS VPC.

Download and review the slide presentation located [here](./final_proj_presentation/mort.odp) for more details.

# Installation and Configuration

Mort Servers - The servers that will host the VNC servers:
  + Must have user accounts for all users that will start desktop sessions there:
    sudo useradd -m *username*
    sudo passwd *username*)
  + Must have a vnc server installed 
    Consult your distributions package manager and package list to determine the package to install and how to install it
  + Must have the vnc password set for each user (ideally, make it the same as their user account, but, this is not mandatory)
      su *username*
      vncpassword
    Must have the firewall configured to allow Mort and VNC related inbound connections
      TCP 5900-6900
      TCP 42124-59000
      UDB 42124-59000
      
      Or disable the firewall
          sudo systemctl stop firewalld.service
          sudo systemctl disable firewalld.service
          
  + Clone the Mort git repo to each server
  + Configure the server.ini file inside the Mort git repo
    Configure whether broadcast and/or unicast announce should be used (most cloud providers do not support broadcast messages)
    If using unicast announce, change the "unicast_announce_to_hosts" list and add the hosts that will run the Mort launcher.
    
          
Mort Launcher - this is the user's machine
  + Clone the Mort git repo to the machine
  + Install additional dependencies
      Python Tk library (usually via distrobution specific package manager)
      Python Pillow library (usually via pip3)
 
       
# Running

+ Server - run the server process as root
  sudo ./mort_session_server.py
          
+ Launcher - run the launcher process as the user
  ./mort_session_launcher.py
  
  
  
          
      
    
  
