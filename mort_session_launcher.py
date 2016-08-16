import sys
import socket
import threading
import logging
import logging.handlers
import LogFilter
import queue
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image

import SessionServerList
import LauncherAnnounceTask
import ServerPurgeTask

import SessionServersWidget
import ActiveSessionsWidget
import RegisteredSessionsWidget
import LogBoxWidget

def main():
    """

    :return:
    """

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
    root.geometry("900x640")
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
    session_servers_widget.add_selection_event_handler(fetch_active_sessions)

    v_panes1 = ttk.PanedWindow(h_panes0, orient='vertical')
    h_panes0.add(v_panes1, weight=1)

    # Create the active-sessions widget as a child of the second vertical PanedWindow widget
    active_sessions_widget = ActiveSessionsWidget.ActiveSessionsWidget(v_panes1)

    # Create the registered-sessions widget as a child of the second vertical PanedWindow widget
    registered_sessions_widget = RegisteredSessionsWidget.RegisteredSessionsWidget(v_panes1)

    # Create the log-box widget as a child of the first vertical PanedWindow widget
    log_box_widget = LogBoxWidget.LogBoxWidget(v_panes0, log_queue)

    #
    exit_button_icon = Image.open("./icons/man_exit.png")
    exit_button_icon = exit_button_icon.resize((12, 15), Image.BICUBIC)
    exit_button_icon = ImageTk.PhotoImage(exit_button_icon)
    exit_button = ttk.Button(v_panes0,
                             text="Exit",
                             image=exit_button_icon,
                             compound='left',
                             command=sys.exit)
    v_panes0.add(exit_button)

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


def fetch_active_sessions(info):
    """

    :param self:
    :param info: A dictionary of key:value pairs representing the name
                 and value of the columns of the selected item.
    :return:
    """
    # Configure logging
    log = logging.getLogger("fetch_active_sessions")

    # Construct the request message
    msg = ("msg_type:get_active_sessions\n")

    # Construct a TCP socket to communicate with the server
    try:
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
        sock.connect((info["IP Address"], info["Port"]))
    except OSError as ex:
        msg = ("Unable to connect to remote host."
               " IP Address: {0}"
               " Port: {1}"
               " Error No: {2}"
               " Error Msg: {3}".format(info["IP Address"],
                                        info["Port"],
                                        ex.errno,
                                        ex.strerror))
        log.critical(msg)
        raise

    # Send the request
    try:
        sock.sendall(msg.encode('utf8'))
    except OSError as ex:
        msg = ("Unable to send message to TCP socket."
               " IP Address: {0}"
               " Port: {1}"
               " Error No: {2}"
               " Error Msg: {3}".format(info["IP Address"],
                                        info["Port"],
                                        ex.errno,
                                        ex.strerror))
        log.critical(msg)
        raise

    # Wait for the response


    # Close the socket


    # Validate the response

    # Display the results in the active-sessions Treeview




if __name__ == "__main__":
    main()
