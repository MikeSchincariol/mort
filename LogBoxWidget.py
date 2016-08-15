import threading
import logging
import logging.handlers
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image

class LogBoxWidget(object):
    """
    A class that handles the log box GUI widget.
    The "View" in the MVC pattern.
    """

    def __init__(self, parent, log_queue):
        """
        Constructs the GUI widget.

        :param parent: A Tk widget that acts as the parent to this widget.
        :param queue: A queue.Queue that the widget will watch for logging.LogRecord
                      items to display in the log box.
        """
        # Configure logging
        self.log = logging.getLogger("LogBoxWidget")
        self.log.debug("Constructing the log-box widget...")

        # Hold a reference to the parent in case it is needed later on.
        self.parent = parent

        # Hold a reference to the queue to watch for log items to display.
        self.log_queue = log_queue

        # Create a dictionary of icons to use for the various message types.
        self.msg_icons = {}

        icon = Image.open("./icons/squid-ink/Files & Folders/png_32/File-Settings.png")
        icon = icon.resize((12, 15), Image.BICUBIC)
        icon = ImageTk.PhotoImage(icon)
        self.msg_icons['DEBUG'] = icon

        icon = Image.open("./icons/squid-ink/Files & Folders/png_32/File-Checked-3.png")
        icon = icon.resize((12, 15), Image.BICUBIC)
        icon = ImageTk.PhotoImage(icon)
        self.msg_icons['INFO'] = icon

        icon = Image.open("./icons/squid-ink/Files & Folders/png_32/File-Favorite.png")
        icon = icon.resize((12, 15), Image.BICUBIC)
        icon = ImageTk.PhotoImage(icon)
        self.msg_icons['WARNING'] = icon

        icon = Image.open("./icons/squid-ink/Files & Folders/png_32/File-Error.png")
        icon = icon.resize((12, 15), Image.BICUBIC)
        icon = ImageTk.PhotoImage(icon)
        self.msg_icons['ERROR'] = icon

        icon = Image.open("./icons/squid-ink/Files & Folders/png_32/File-Heart.png")
        icon = icon.resize((16, 16), Image.BICUBIC)
        icon = ImageTk.PhotoImage(icon)
        self.msg_icons['CRITICAL'] = icon

        # Create a frame that can display a name, to wrap the Text component.
        self.logbox_pane = ttk.LabelFrame(self.parent, text='Log Box')
        self.logbox_pane.columnconfigure(0, weight=1)
        self.logbox_pane.columnconfigure(1, weight=0)
        self.logbox_pane.rowconfigure(0, weight=1)
        self.logbox_pane.rowconfigure(1, weight=0)
        self.parent.add(self.logbox_pane, weight=1)

        # Create the Text component that will display the log messages.
        self.logbox = Text(self.logbox_pane)
        self.logbox.grid(column=0, row=0, padx=4, pady=4, sticky=(N, E, S, W))
        self.logbox.configure(wrap="none")
        self.logbox.configure(font="TkFixedFont")

        # Create H and V scroll bars to allow changing the view point of the log box.
        self.log_vscroll = ttk.Scrollbar(self.logbox_pane, orient='vertical', command=self.logbox.yview)
        self.log_vscroll.grid(column=1, row=0, sticky=(N, S))
        self.logbox.configure(yscrollcommand=self.log_vscroll.set)

        self.log_hscroll = ttk.Scrollbar(self.logbox_pane, orient='horizontal', command=self.logbox.xview)
        self.log_hscroll.grid(column=0, row=1, sticky=(E, W))
        self.logbox.configure(xscrollcommand=self.log_hscroll.set)

        # Kick off a thread that will watch the queue and update the Text widget
        # with the info in the LogRecords from the queue.
        self.logbox_update_task = threading.Thread(target=self.update_task,
                                                   name="LogBoxWidgetUpdateTask",
                                                   args=(),
                                                   daemon=True)

        self.logbox_update_task.start()


    def update_task(self):
        """
        A method that runs as a seperate thread to watch the log_queue
        and display the contents of any LogRecords found there.
        """
        # Configure logging
        log = logging.getLogger("LogBoxWidgetUpdateTask")
        log.debug("Starting up...")

        # Watch the queue for messages that should be displayed in
        # the logbox widget.
        while True:
            item = self.log_queue.get()
            self.logbox.image_create('end',
                                     image=self.msg_icons[item.levelname],
                                     align='center',
                                     padx=1,
                                     pady=1)
            self.logbox.insert('end', ":{0.levelname:10}: {0.name} - {0.msg}\n".format(item))
            self.logbox.see('end')