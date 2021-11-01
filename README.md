*University of Washintong - Profressional and Continuing Education*  
Certificate in Python Programming  
Capstone Project  


# _Mort - The VNC Session Helper_

In Linux it is possible to start multiple additional desktop sessions, accessible remotely via TCP/IP, using a program called VNC. While running programs remotely is also possible using SSH, the advantage of VNC is that the session and programs continue even if the client disconnectxs. With SSH, any running processes started in the SSH session are terminated when the SSH session ends.  

However, VNC has a few rough edges, among them:
+ It requires the user to select a display number to use, when starting the server. The display number must not be in use by any other VNC process. Available display numbers are difficult to determine.
+ It requires the user to first login to the server they want to use to start the VNC service for their desktop session.
+ If the server running their VNC session dies or is restarted, nothing restarts the VNC service.

Mort attempts to solve these issues by:
+ Identifying which servers on a network are available for running VNC sessions
+ Identifying which VNC desktops are already running on a given server, and their display numbers, so that picking a non-conflicting display number is simple
+ Freeing the user from needing to log into the server to start their VNC session by starting the VNC server processes on behalf of the user
+ Keeps track of VNC desktops that are "registered" with Mort, and restarts them if the server the VNC desktop is running on gets rebooted

The app is written in Python using Tk for the GUI.
Testing was done on an setup in an AWS VPC.

Download and review the slide presentation located [here](./final_proj_presentation/mort.odp) for more details.
