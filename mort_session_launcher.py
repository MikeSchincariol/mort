#!/usr/bin/env python3

import sys
import os.path
import subprocess
import socket
import threading
import logging
import logging.handlers
import LogFilter
import queue
import json
import time
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import ImageTk, Image

import SessionServerList
import LauncherAnnounceTask
import ServerPurgeTask

import SessionServersWidget
import ActiveSessionsWidget
import RegisteredSessionsWidget
import LogBoxWidget
import NewVNCSessionForm

def main():
    """

    :return:
    """

    # Determine where the source code is to be found
    # :NOTE: Refer to documentation of sys.path for why this works.
    SRC_DIR = os.path.abspath(sys.path[0])

    # Configure a log filter to dissallow messages from the PIL module
    pil_log_filter = LogFilter.Filter("PIL")

    # Configure a log file, to write log messages into, that auto-rotates when
    # it reaches a certain size.
    rotating_log_handler = logging.handlers.RotatingFileHandler(filename='mort_session_launcher.log',
                                                                mode='a',
                                                                maxBytes=1E6,
                                                                backupCount=3)
    rotating_log_handler.setLevel(logging.DEBUG)
    rotating_log_handler.addFilter(pil_log_filter)

    # Configure a stdout log handler to print all messages
    stdout_log_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_log_handler.setLevel(logging.DEBUG)
    stdout_log_handler.addFilter(pil_log_filter)

    # Configure a stderr log handler to print only ERROR messages and above
    stderr_log_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_log_handler.setLevel(logging.ERROR)
    stderr_log_handler.addFilter(pil_log_filter)

    # Configure a queue log handler to print all messages to the GUI log box
    log_queue = queue.Queue()
    queue_log_handler = logging.handlers.QueueHandler(log_queue)
    queue_log_handler.setLevel(logging.DEBUG)
    queue_log_handler.addFilter(pil_log_filter)

    logging.basicConfig(format="{asctime:11} :{levelname:10}: {name:22}({lineno:4}) - {message}",
                        style="{",
                        level=logging.DEBUG,
                        handlers=[stdout_log_handler,
                                  stderr_log_handler,
                                  rotating_log_handler,
                                  queue_log_handler])

    # Get a new logger to use
    log = logging.getLogger("mort_session_launcher")

    # Print a startup banner to mark the beginning of logging
    log.info("")
    log.info("--------------------------------------------------------------------------------")
    log.info("Mort session-launcher starting up...")

    # Create the GUI widgets
    root = Tk()
    root.geometry("900x768")
    root.title("Mort VNC Session Launcher", )
    root.grid()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    v_panes0 = ttk.PanedWindow(root, orient='vertical')
    v_panes0.grid(column=0, row=0, sticky=(N, S, E, W))
    v_panes0.columnconfigure(0, weight=1)
    v_panes0.rowconfigure(0, weight=1)

    # :WARN: PanedWindow's are also geometry managers, so, don't
    #        grid any panes that are added to the PanedWindow
    #        instance (even if the newly added pane is itself a
    #        PanedWindow instance).

    h_panes0 = ttk.PanedWindow(v_panes0, orient='horizontal')
    v_panes0.add(h_panes0, weight=1)
    h_panes0.columnconfigure(0, weight=1)
    h_panes0.rowconfigure(0, weight=1)

    # Create the session-servers widget as a child of the first horizontal PanedWindow widget
    session_servers_widget = SessionServersWidget.SessionServersWidget(h_panes0)

    v_panes1 = ttk.PanedWindow(h_panes0, orient='vertical')
    h_panes0.add(v_panes1, weight=1)

    # Create the active-sessions widget as a child of the second vertical PanedWindow widget
    active_sessions_widget = ActiveSessionsWidget.ActiveSessionsWidget(v_panes1)

    # Create the registered-sessions widget as a child of the second vertical PanedWindow widget
    registered_sessions_widget = RegisteredSessionsWidget.RegisteredSessionsWidget(v_panes1)

    # Create the log-box widget as a child of the first vertical PanedWindow widget
    log_box_widget = LogBoxWidget.LogBoxWidget(v_panes0, log_queue)

    #
    exit_button_icon = Image.open(SRC_DIR+"/icons/user_exit.png")
    exit_button_icon = exit_button_icon.resize((12, 15), Image.BICUBIC)
    exit_button_icon = ImageTk.PhotoImage(exit_button_icon)
    exit_button = ttk.Button(v_panes0,
                             text="Exit",
                             image=exit_button_icon,
                             compound='left',
                             command=sys.exit)
    v_panes0.add(exit_button)

    # Register call backs to happen when the various GUI items are interacted with
    session_servers_widget.add_selection_event_handler(fetch_active_sessions,
                                                       session_servers_widget,
                                                       active_sessions_widget)

    active_sessions_widget.add_refresh_button_clicked_event_handler(fetch_active_sessions,
                                                                    session_servers_widget,
                                                                    active_sessions_widget)

    active_sessions_widget.add_new_button_clicked_event_handler(new_active_session,
                                                                active_sessions_widget)
    active_sessions_widget.add_new_button_clicked_event_handler(fetch_active_sessions,
                                                                session_servers_widget,
                                                                active_sessions_widget)

    active_sessions_widget.add_kill_button_clicked_event_handler(kill_active_session,
                                                                 active_sessions_widget)
    active_sessions_widget.add_kill_button_clicked_event_handler(fetch_active_sessions,
                                                                 session_servers_widget,
                                                                 active_sessions_widget)

    active_sessions_widget.add_connect_button_clicked_event_handler(connect_to_active_session,
                                                                 active_sessions_widget)

    # A list of session-servers already seen and a lock to use
    # to arbitrate access from different threads
    known_servers = SessionServerList.SessionServerList()
    known_servers_cv = threading.Condition()

    # Start a thread to handle announce messages from the session-servers
    announce_task = LauncherAnnounceTask.LauncherAnnounceTask(known_servers, known_servers_cv)
    announce_task.start()

    # Start a thread to periodically clean the list of session-servers to
    # remove those that haven't been heard from in a while.
    purge_task = ServerPurgeTask.ServerPurgeTask(known_servers, known_servers_cv)
    purge_task.start()

    session_servers_update_task = threading.Thread(target=update_session_servers_task,
                                                   name="update_session_servers_task",
                                                   args=(session_servers_widget, known_servers, known_servers_cv),
                                                   daemon=True)
    session_servers_update_task.start()

    # Start Tk's mainloop to wait for GUI events
    root.mainloop()


def update_session_servers_task(session_servers_widget, known_servers, known_servers_cv):
    """

    :param known_servers_cv:
    :return:
    """
    # Configure logging
    log = logging.getLogger("update_session_servers_task")
    log.debug("Starting up...")

    with known_servers_cv:
        while True:
            # Clear treeview of all entries present
            session_servers_widget.clear()
            # Insert entries from known_servers list
            for server in known_servers:
                new_item = session_servers_widget.insert(-1,
                                                         server.hostname,
                                                         server.ip_address,
                                                         server.port)
            # Wait for updates to happen to the underlying list
            # :NOTE: After wait() resumes, it re-aquires the lock.
            known_servers_cv.wait()


def fetch_active_sessions(session_servers_widget, active_sessions_widget):
    """
    :param info: A dictionary of key:value pairs representing the name
                 and value of the columns of the selected item.

    :param active_sessions_widget:
    :return:
    """
    # Configure logging
    log = logging.getLogger("fetch_active_sessions")

    # Get the server info
    # :NOTE: If no item is selected, "None" will be returned, in which case,
    #        don't proceed any further.
    server_info = session_servers_widget.get_selected_item_info()
    if server_info is None:
        log.debug("No server info returned from session_servers_widget. Nothing selected?")
        log.debug("Nothing to do. Returning early to caller.")
        return

    # Construct the request message
    msg = ("msg_type:get_active_sessions\n")

    # Construct a TCP socket to communicate with the server
    try:
        log.debug("Creating socket...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except OSError as ex:
        msg = ("Unable to create TCP socket."
               " Error No: {0}"
               " Error Msg: {1}".format(ex.errno, ex.strerror))
        log.critical(msg)
        raise

    # Connect to the remote server
    try:
        log.debug("Connecting to server {0}:{1}...".format(server_info["IP Address"], server_info["Port"]))
        sock.connect((server_info["IP Address"], server_info["Port"]))
    except OSError as ex:
        msg = ("Unable to connect to remote host."
               " IP Address: {0}"
               " Port: {1}"
               " Error No: {2}"
               " Error Msg: {3}".format(server_info["IP Address"],
                                        server_info["Port"],
                                        ex.errno,
                                        ex.strerror))
        log.critical(msg)
        raise

    # Send the request
    try:
        log.debug("Sending list_active_sessions request...")
        sock.sendall(msg.encode('utf8'))
    except OSError as ex:
        msg = ("Unable to send message to TCP socket."
               " IP Address: {0}"
               " Port: {1}"
               " Error No: {2}"
               " Error Msg: {3}".format(server_info["IP Address"],
                                        server_info["Port"],
                                        ex.errno,
                                        ex.strerror))
        log.critical(msg)
        raise

    # Wait for the response then close the socket
    log.debug("Waiting for response...")
    resp = sock.recv(16384)
    log.debug("Received {0} bytes".format(len(resp)))
    resp = resp.decode('utf8')
    log.debug("Closing socket")
    sock.close()

    # Break the response down into its key/value pairs
    log.debug("Parsing message...")
    resp_lines = resp.splitlines()
    resp_fields = {}
    for resp_line in resp_lines:
        resp_field = resp_line.split(':', 1)
        resp_fields[resp_field[0]] = resp_field[1]

    # Check for the correct message type. If this isn't a active_sessions_list
    # message then discard it and move on.
    if "msg_type" in resp_fields.keys():
        if resp_fields["msg_type"] == "active_sessions_list":
            # Clear the current listing of all entries present
            active_sessions_widget.clear()
            # Display the results in the active-sessions Treeview
            if "active_sessions" in resp_fields.keys():
                active_sessions_json = resp_fields["active_sessions"]
                sessions = json.loads(active_sessions_json)
                log.debug("Message is good. Contains {} entries.".format(len(sessions)))
                for session in sessions:
                    active_sessions_widget.insert(-1, **session)
                # Update the server info to identify where the entries came from
                active_sessions_widget.set_server_info(server_info["Hostname"],
                                                       server_info["IP Address"],
                                                       server_info["Port"])

            else:
                # Discard message; not active-sessions listing.
                msg = ("Invalid active sessions list message from {0}:{1}."
                       " Invalid active-sessions listing."
                       " Discarding".format(server_info["IP Address"],
                                            server_info["Port"]))
                log.warning(msg)

        else:
            # Discard message; not a "active_sessions_list" message
            msg = ("Invalid active sessions list message from {0}:{1}."
                   " Invalid msg_type value."
                   " Discarding".format(server_info["IP Address"],
                                        server_info["Port"]))
            log.warning(msg)
    else:
        # Discard message; no msg_type field found.
        msg = ("Invalid active sessions list message from {0}:{1}."
               " Invalid msg_type value."
               " Discarding".format(server_info["IP Address"],
                                    server_info["Port"]))
        log.warning(msg)
    log.debug("Done updating active-sessions widget.")



def new_active_session(active_sessions_widget):
    """

    :param active_sessions_widget:
    :return:
    """
    # Configure logging
    log = logging.getLogger("new_active_session")
    # Get the server info
    # :NOTE: If no item is selected, "None" will be returned, in which case,
    #        don't proceed any further.
    server_info = active_sessions_widget.get_server_info()
    if (server_info["Hostname"] is None or
        server_info["IP Address"] is None or
        server_info["Port"] is None):
        log.debug("No server info returned from active_sessions_widget.")
        log.debug("Nothing to do. Returning early to caller.")
        return

    # Get the parameters of the new server to create
    form = NewVNCSessionForm.NewVNCSessionForm()
    form.show()
    form_info = form.get_info()

    # Check if the user wants to abort
    if not form.ok_was_clicked:
        log.debug("User didn't click OK.")
        return

    # Construct the request message
    username = os.environ["USER"]
    msg = ("msg_type:start_active_session\n"
           "username:{0}\n"
           "display_number:{1[display_number]}\n"
           "display_name:{1[display_name]}\n"
           "geometry:{1[geometry]}\n"
           "pixelformat:{1[pixelformat]}\n").format(username, form_info)

    # Construct a TCP socket to communicate with the server
    try:
        log.debug("Creating socket...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except OSError as ex:
        msg = ("Unable to create TCP socket."
               " Error No: {0}"
               " Error Msg: {1}".format(ex.errno, ex.strerror))
        log.critical(msg)
        raise

    # Connect to the remote server
    try:
        log.debug("Connecting to server {0}:{1}...".format(server_info["IP Address"], server_info["Port"]))
        sock.connect((server_info["IP Address"], server_info["Port"]))
    except OSError as ex:
        msg = ("Unable to connect to remote host."
               " IP Address: {0}"
               " Port: {1}"
               " Error No: {2}"
               " Error Msg: {3}".format(server_info["IP Address"],
                                        server_info["Port"],
                                        ex.errno,
                                        ex.strerror))
        log.critical(msg)
        raise

    # Send the request
    try:
        log.debug("Sending start_active_session request...")
        sock.sendall(msg.encode('utf8'))
    except OSError as ex:
        msg = ("Unable to send message to TCP socket."
               " IP Address: {0}"
               " Port: {1}"
               " Error No: {2}"
               " Error Msg: {3}".format(server_info["IP Address"],
                                        server_info["Port"],
                                        ex.errno,
                                        ex.strerror))
        log.critical(msg)
        raise

    # Wait for the response then close the socket
    log.debug("Waiting for response...")
    resp = sock.recv(16384)
    log.debug("Received {0} bytes".format(len(resp)))
    resp = resp.decode('utf8')
    log.debug("Closing socket")
    sock.close()

    # Break the response down into its key/value pairs
    log.debug("Parsing message...")
    resp_lines = resp.splitlines()
    resp_fields = {}
    for resp_line in resp_lines:
        resp_field = resp_line.split(':', 1)
        resp_fields[resp_field[0]] = resp_field[1]

   # Check for the correct message type. If this isn't a strart_active_session_response
    # message then discard it and move on.
    if "msg_type" in resp_fields.keys():
        if resp_fields["msg_type"] == "start_active_session_response":
            if "outcome" in resp_fields.keys():
                if resp_fields["outcome"].lower() == "success":
                    log.info("Session started.")
                    messagebox.showinfo(title="Start New Session Feedback",
                                        message="Success - New session created on {}, display {}".format(server_info["IP Address"],
                                                                                                         form_info["display_number"]),
                                        icon="info",
                                        default="ok")
                elif resp_fields["outcome"].lower() == "display in use":
                    log.warning("The display number selected is already in use.")
                    messagebox.showinfo(title="Start New Session Feedback",
                                        message="The display number chosen is alread in use",
                                        icon="warning",
                                        default="ok")
                else:
                    log.warning("Unexpected server reply: {}".format(resp_fields["outcome"]))
                    messagebox.showinfo(title="Start New Session Feedback",
                                        message="Unexpected reply from server",
                                        icon="warning",
                                        default="ok")
            else:
                # Discard message; missing outcome field
                msg = ("Invalid start active session response message from {0}:{1}."
                       " Missing outcome field"
                       " Discarding".format(server_info["IP Address"],
                                            server_info["Port"]))
                log.warning(msg)
        else:
            # Discard message; not a "start_active_session_response" message
            msg = ("Invalid start active session response message from {0}:{1}."
                   " Invalid msg_type value."
                   " Discarding".format(server_info["IP Address"],
                                        server_info["Port"]))
            log.warning(msg)
    else:
        # Discard message; no msg_type field found.
        msg = ("Invalid start active session response message from {0}:{1}."
               " Invalid msg_type value."
               " Discarding".format(server_info["IP Address"],
                                    server_info["Port"]))
        log.warning(msg)
    # :TODO: Fix this hack! It's gross. I'm personally offended by it :)
    # Wait a few seconds for the server process to startup before leaving this
    # method so that the widget update will see the new process.
    # :NOTE: This is a HACK!!!! There has to be a better way.
    time.sleep(2)
    log.debug("Done.")


def kill_active_session(active_sessions_widget):
    """

    :param active_sessions_widget:
    :return:
    """
    # Configure logging
    log = logging.getLogger("kill_active_session")
    # Get the server info
    # :NOTE: If no item is selected, "None" will be returned, in which case,
    #        don't proceed any further.
    server_info = active_sessions_widget.get_server_info()
    if (server_info["Hostname"] is None or
        server_info["IP Address"] is None or
        server_info["Port"] is None):
        log.debug("No server info returned from active_sessions_widget.")
        log.debug("Nothing to do. Returning early to caller.")
        return

    # Get the active session info
    # :NOTE: If no item is selected, "None" will be returned, in which case,
    #        don't proceed any further.
    session_info = active_sessions_widget.get_selected_item_info()
    if session_info is None:
        log.debug("No session info returned from active_sessions_widget. Nothing selected?")
        log.debug("Nothing to do. Returning early to caller.")
        return

    # Construct the request message
    msg = ("msg_type:kill_active_session\n"
           "pid:{}".format(session_info["PID"]))


    # Construct a TCP socket to communicate with the server
    try:
        log.debug("Creating socket...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except OSError as ex:
        msg = ("Unable to create TCP socket."
               " Error No: {0}"
               " Error Msg: {1}".format(ex.errno, ex.strerror))
        log.critical(msg)
        raise

    # Connect to the remote server
    try:
        log.debug("Connecting to server {0}:{1}...".format(server_info["IP Address"], server_info["Port"]))
        sock.connect((server_info["IP Address"], server_info["Port"]))
    except OSError as ex:
        msg = ("Unable to connect to remote host."
               " IP Address: {0}"
               " Port: {1}"
               " Error No: {2}"
               " Error Msg: {3}".format(server_info["IP Address"],
                                        server_info["Port"],
                                        ex.errno,
                                        ex.strerror))
        log.critical(msg)
        raise

    # Send the request
    try:
        log.debug("Sending list_active_sessions request...")
        sock.sendall(msg.encode('utf8'))
    except OSError as ex:
        msg = ("Unable to send message to TCP socket."
               " IP Address: {0}"
               " Port: {1}"
               " Error No: {2}"
               " Error Msg: {3}".format(server_info["IP Address"],
                                        server_info["Port"],
                                        ex.errno,
                                        ex.strerror))
        log.critical(msg)
        raise

    # Wait for the response then close the socket
    log.debug("Waiting for response...")
    resp = sock.recv(16384)
    log.debug("Received {0} bytes".format(len(resp)))
    resp = resp.decode('utf8')
    log.debug("Closing socket")
    sock.close()

    # Break the response down into its key/value pairs
    log.debug("Parsing message...")
    resp_lines = resp.splitlines()
    resp_fields = {}
    for resp_line in resp_lines:
        resp_field = resp_line.split(':', 1)
        resp_fields[resp_field[0]] = resp_field[1]

    # Check for the correct message type. If this isn't a kill_active_session_response
    # message then discard it and move on.
    if "msg_type" in resp_fields.keys():
        if resp_fields["msg_type"] == "kill_active_session_response":
            if "outcome" in resp_fields.keys():
                if resp_fields["outcome"].lower() == "killed":
                    log.info("Session killed.")
                    messagebox.showinfo(title="Kill Seession Feedback",
                                        message="Success - session terminated!",
                                        icon="info",
                                        default="ok")
                elif resp_fields["outcome"].lower() == "process not found":
                    log.warning("Xvnc session process was not found. Was it killed already?")
                    messagebox.showinfo(title="Kill Session Feedback",
                                        message="Xvnc session process was not found. Was it killed already?",
                                        icon="warning",
                                        default="ok")
                else:
                    log.warning("Unexpected server reply: {}".format(resp_fields["outcome"]))
                    log.warning("Unexpected server reply: {}".format(resp_fields["outcome"]))
                    messagebox.showinfo(title="Start New Session Feedback",
                                        message="Unexpected reply from server",
                                        icon="warning",
                                        default="ok")
            else:
                # Discard message; missing outcome field
                msg = ("Invalid kill active session response message from {0}:{1}."
                       " Missing outcome field"
                       " Discarding".format(server_info["IP Address"],
                                            server_info["Port"]))
                log.warning(msg)
        else:
            # Discard message; not a "kill_active_session_response" message
            msg = ("Invalid kill active session response message from {0}:{1}."
                   " Invalid msg_type value."
                   " Discarding".format(server_info["IP Address"],
                                        server_info["Port"]))
            log.warning(msg)
    else:
        # Discard message; no msg_type field found.
        msg = ("Invalid kill active session response message from {0}:{1}."
               " Invalid msg_type value."
               " Discarding".format(server_info["IP Address"],
                                    server_info["Port"]))
        log.warning(msg)
    log.debug("Done.")


def connect_to_active_session(active_sessions_widget):
    """

    :param active_sessions_widget:
    :return:
    """
    # Configure logging
    log = logging.getLogger("connect_to_active_session")
    # Get the server info
    # :NOTE: If no item is selected, "None" will be returned, in which case,
    #        don't proceed any further.
    server_info = active_sessions_widget.get_server_info()
    if (server_info["Hostname"] is None or
        server_info["IP Address"] is None or
        server_info["Port"] is None):
        log.debug("No server info returned from active_sessions_widget.")
        log.debug("Nothing to do. Returning early to caller.")
        return

    # Get the active session info
    # :NOTE: If no item is selected, "None" will be returned, in which case,
    #        don't proceed any further.
    session_info = active_sessions_widget.get_selected_item_info()
    if session_info is None:
        log.debug("No session info returned from active_sessions_widget. Nothing selected?")
        log.debug("Nothing to do. Returning early to caller.")
        return

    vnc_port = 5900+int(session_info["Display #"])
    subprocess.call(["vncviewer", "{}:{}".format(server_info["IP Address"],
                                                 vnc_port)])



if __name__ == "__main__":
    main()
