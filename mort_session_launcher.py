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
    session_server_tv["columns"] = ("Hostname", "IP Address", "Port")
    session_server_tv.column(column="#0", anchor="center", minwidth=40, stretch=False, width=36)
    session_server_tv.heading(column="#0", text="")
    session_server_tv.column(column="Hostname", anchor="e", minwidth=64, stretch=True, width=160)
    session_server_tv.heading(column="Hostname", text="Hostname")
    session_server_tv.column(column="IP Address", anchor="e", minwidth=64, stretch=False, width=90)
    session_server_tv.heading(column="IP Address", text="IP Address")
    session_server_tv.column(column="Port", anchor="e", minwidth=64, stretch=False, width=48)
    session_server_tv.heading(column="Port", text="Port")


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
    known_servers = SessionServerList.SessionServerList()
    known_servers_cv = threading.Condition()

    # Start a thread to handle announce messages from the session-servers
    announce_task = LauncherAnnounceTask.LauncherAnnounceTask(known_servers, known_servers_cv)
    announce_task.start()

    # Start a thread to periodically clean the list of session-servers to
    # remove those that haven't been heard from in a while.
    purge_task = ServerPurgeTask.ServerPurgeTask(known_servers, known_servers_cv)
    purge_task.start()

    known_servers_treeview_update_task = threading.Thread(target=update_known_servers_treeview_task,
                                                          name="update_known_servers_treeview_task",
                                                          args=(session_server_tv, known_servers, known_servers_cv))
    known_servers_treeview_update_task.start()

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
    # Configure logging
    log = logging.getLogger("update_logbox_task")
    log.info("Mort update_logbox_task starting up...")

    # Watch the queue for messages that should be displayed in
    # the logbox widget.
    while True:
        item = log_queue.get()
        logbox_widget.insert('end', item.msg+"\n")


def update_known_servers_treeview_task(session_server_tv, known_servers, known_servers_cv):
    """

    :param known_servers_cv:
    :return:
    """
    # Configure logging
    log = logging.getLogger("update_known_servers_treeview_task")
    log.info("Mort update_known_servers_treeview_task starting up...")

    # Open the icon used for the server icon
    server_icon = Image.open("./icons/squid-ink/Devices & Network/png_32/Server.png")
    server_icon = server_icon.resize((16, 16), Image.BICUBIC)
    server_icon = ImageTk.PhotoImage(server_icon)


    # Treeview widgets don't give you a way to iterate over their
    # items. You must store references to the items, yourself.
    # Which is stupid...but, oh well...
    items_in_tv = []
    with known_servers_cv:
        while True:
            # Clear treeview of all entries present
            for item in items_in_tv:
                session_server_tv.delete(item)
            items_in_tv.clear()
            # Insert entries from known_servers list
            for idx, server in enumerate(known_servers):
                new_item = session_server_tv.insert('',
                                                    'end',
                                                    "item{}".format(idx),
                                                    text='',
                                                    image=server_icon,
                                                    values=(server.hostname, server.ip_address, server.port))
                items_in_tv.append(new_item)
            # Wait for updates to happen to the underlying list
            # :NOTE: After wait() resumes, it re-aquires the lock.
            known_servers_cv.wait()

if __name__ == "__main__":
    main()
