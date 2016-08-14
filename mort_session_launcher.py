import sys
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
    root.title("Mort VNC Session Launcher")
    root.grid()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    v_panes = ttk.PanedWindow(root, orient='vertical')
    v_panes.grid(column=0, row=0, sticky=(N, S, E, W))
    v_panes.columnconfigure(0, weight=1)
    v_panes.rowconfigure(0, weight=1)

    # :WARN: PanedWindow's are also geometry managers, so, don't
    #        grid any panes that are added to the PanedWindow
    #        instance (even if the newly added pane is itself a
    #        PaneWindow instance).

    h_panes0 = ttk.PanedWindow(v_panes, orient='horizontal')
    v_panes.add(h_panes0, weight=1)
    h_panes0.columnconfigure(0, weight=1)
    h_panes0.rowconfigure(0, weight=1)

    # Create the session-servers widget as a child of the first horizontal PanedWindow widget
    session_servers_widget = SessionServersWidget.SessionServersWidget(h_panes0)

    # Create the active-sessions widget as a child of the first horizontal PanedWindow widget
    active_sessions_widget = ActiveSessionsWidget.ActiveSessionsWidget(h_panes0)

    # Create the registered-sessions widget as a child of the first horizontal PanedWindow widget
    registered_sessions_pane = ttk.LabelFrame(h_panes0,
                                              text='Registered Sessions',
                                              width=200,
                                              height=100)
    registered_sessions_pane.columnconfigure(0, weight=1)
    registered_sessions_pane.rowconfigure(0, weight=1)
    h_panes0.add(registered_sessions_pane, weight=1)

    registered_sessions_tv = ttk.Treeview(registered_sessions_pane)
    registered_sessions_tv.grid(column=0, row=0, padx=4, pady=4, sticky=(N, S, E, W))
    registered_sessions_tv.insert('', 'end', "item0", text='First Item')

    # Create the log-box widget as a child of the first vertical PanedWindow widget
    log_box_widget = LogBoxWidget.LogBoxWidget(v_panes, log_queue)

    #
    exit_button_icon = Image.open("./icons/man_exit.png")
    exit_button_icon = exit_button_icon.resize((12, 15), Image.BICUBIC)
    exit_button_icon = ImageTk.PhotoImage(exit_button_icon)
    exit_button = ttk.Button(v_panes,
                             text="Exit",
                             image=exit_button_icon,
                             compound='left',
                             command=sys.exit)
    v_panes.add(exit_button)

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

if __name__ == "__main__":
    main()
