import threading
import logging
import logging.handlers
import queue
from tkinter import *
from tkinter import ttk

import LauncherAnnounceTask
import ServerPurgeTask


def main():
    """

    :return:
    """

    # Configure a log file, to write log messages into, that auto-rotates when
    # it reaches a certain size.
    rotating_log_handler = logging.handlers.RotatingFileHandler(filename='mort_session_launcher.log',
                                                                mode='a',
                                                                maxBytes=1E6,
                                                                backupCount=3)  # Configure a stdout log handler to print all messages
    stdout_log_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_log_handler.setLevel(logging.DEBUG)

    # Configure a stderr log handler to print only ERROR messages and above
    stderr_log_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_log_handler.setLevel(logging.ERROR)

    # Configure a queue log handler to print all messages to the GUI log box
    log_queue = queue.Queue()
    queue_log_handler = logging.handlers.QueueHandler(log_queue)
    queue_log_handler.setLevel(logging.DEBUG)

    logging.basicConfig(format="{asctime:11} :{levelname:10}: {name:22}({lineno:4}) - {message}",
                        style="{",
                        level=logging.DEBUG,
                        handlers=[stdout_log_handler,
                                  stderr_log_handler,
                                  rotating_log_handler,
                                  queue_log_handler])

    # Get a new logger to use
    log = logging.getLogger("mort_session_launcher")


    # Create the GUI widgets
    root = Tk()
    root.title("Mort VNC Session Launcher")
    root.grid()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    size_grip = ttk.Sizegrip(root)
    size_grip.grid(column=999, row=999, sticky=(S, W))

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

    session_servers_pane = ttk.LabelFrame(h_panes0,
                                          text='Session Servers',
                                          width=200,
                                          height=100)
    session_servers_pane.columnconfigure(0, weight=1)
    session_servers_pane.rowconfigure(0, weight=1)
    h_panes0.add(session_servers_pane, weight=1)

    active_sessions_pane = ttk.LabelFrame(h_panes0,
                                          text='Active Sessions',
                                          width=200,
                                          height=100)
    active_sessions_pane.columnconfigure(0, weight=1)
    active_sessions_pane.rowconfigure(0, weight=1)

    h_panes0.add(active_sessions_pane, weight=1)

    registered_sessions_pane = ttk.LabelFrame(h_panes0,
                                              text='Registered Sessions',
                                              width=200,
                                              height=100)
    registered_sessions_pane.columnconfigure(0, weight=1)
    registered_sessions_pane.rowconfigure(0, weight=1)
    h_panes0.add(registered_sessions_pane, weight=1)

    session_server_tv = ttk.Treeview(session_servers_pane)
    session_server_tv.grid(column=0, row=0, sticky=(N, S, E, W))
    session_server_tv.insert('', 'end', "item0", text='First Item')

    active_sessions_tv = ttk.Treeview(active_sessions_pane)
    active_sessions_tv.grid(column=0, row=0, sticky=(N, S, E, W))
    active_sessions_tv.insert('', 'end', "item0", text='First Item')

    registered_sessions_tv = ttk.Treeview(registered_sessions_pane)
    registered_sessions_tv.grid(column=0, row=0, sticky=(N, S, E, W))
    registered_sessions_tv.insert('', 'end', "item0", text='First Item')

    logbox_pane = ttk.LabelFrame(v_panes,
                                 text='Log Box',
                                 width=600,
                                 height=100)
    logbox_pane.columnconfigure(0, weight=1)
    logbox_pane.rowconfigure(0, weight=1)
    v_panes.add(logbox_pane, weight=1)
    logbox = Text(logbox_pane)
    logbox.grid(column=0, row=0, sticky=(N, E, S, W))
    logbox.configure(wrap="none")

    log_vscroll = ttk.Scrollbar(logbox_pane, orient='vertical', command=logbox.yview)
    log_vscroll.grid(column=1, row=0, sticky=(N, S))
    logbox.configure(yscrollcommand=log_vscroll.set)

    log_hscroll = ttk.Scrollbar(logbox_pane, orient='horizontal', command=logbox.xview)
    log_hscroll.grid(column=0, row=1, sticky=(E, W))
    logbox.configure(xscrollcommand=log_hscroll.set)



    # Print a startup banner to mark the beginning of logging
    log.info("")
    log.info("--------------------------------------------------------------------------------")
    log.info("Mort session-launcher starting up...")

    # A list of session-servers already seen and a lock to use
    # to arbitrate access from different threads
    known_servers = []
    known_servers_lock = threading.Lock()

    # Start a thread to handle announce messages from the session-servers
    announce_task = LauncherAnnounceTask.LauncherAnnounceTask(known_servers, known_servers_lock)
    announce_task.start()

    # Start a thread to periodically clean the list of session-servers to
    # remove those that haven't been heard from in a while.
    purge_task = ServerPurgeTask.ServerPurgeTask(known_servers, known_servers_lock)
    purge_task.start()

    # Start a thread to update the GUI logbox when new messages are sent to it's
    # queue
    logbox_update_task = threading.Thread(target=update_logbox_task,
                                          name="logbox_update_task",
                                          args=(log_queue, logbox))
    logbox_update_task.start()


    # Start Tk's mainloop to wait for GUI events
    root.mainloop()

def update_logbox_task(log_queue, logbox_widget):
    """

    :param log_queue:
    :param logbox_widget:
    :return:
    """
    while True:
        item = log_queue.get()
        logbox_widget.insert('end', item.msg+"\n")


if __name__ == "__main__":
    main()
