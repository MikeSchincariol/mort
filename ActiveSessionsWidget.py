import threading
import logging
import logging.handlers
import LogFilter
import queue
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image

class ActiveSessionsWidget(object):
    """
    A class that handles the active-sessions GUI widget.
    The "View" in the MVC pattern.
    """

    def __init__(self, parent):
        """
        Constructs the GUI widget.

        :param parent: A Tk widget that acts as the parent to this widget.
        """
        # Configure logging
        self.log = logging.getLogger("ActiveSessionsWidget")
        self.log.debug("Constructing the active-sessions widget...")

        # Hold a reference to the parent in case it is needed later on.
        self.parent = parent

        # Open the icon used for the server icon
        self.session_icon = Image.open("./icons/squid-ink/User Interface/png_32/Application-Modal.png")
        self.session_icon = self.session_icon.resize((16, 16), Image.BICUBIC)
        self.session_icon = ImageTk.PhotoImage(self.session_icon)

        # Create a frame that can display a name, to wrap the TreeView component.
        self.active_sessions_frame = ttk.LabelFrame(self.parent,
                                                    text='Active Sessions',
                                                    width=200,
                                                    height=100)

        self.active_sessions_frame.columnconfigure((0, 1, 2), weight=1)
        self.active_sessions_frame.rowconfigure(0, weight=1)
        self.active_sessions_frame.rowconfigure(1, weight=0)
        self.parent.add(self.active_sessions_frame, weight=1)

        # Create the TreeView component that will display the list of active sessions.
        self.active_sessions_tv = ttk.Treeview(self.active_sessions_frame)
        self.active_sessions_tv.grid(column=0, columnspan=3, row=0, padx=4, pady=4, sticky=(N, S, E, W))
        self.active_sessions_tv["selectmode"] = "browse"
        self.active_sessions_tv["columns"] = ("Username", "Display #", "Display Name", "Geometry", "PID")
        self.active_sessions_tv.column(column="#0", anchor="center", minwidth=40, stretch=False, width=40)
        self.active_sessions_tv.heading(column="#0", text="")
        self.active_sessions_tv.column(column="Username", anchor="e", minwidth=60, stretch=True, width=80)
        self.active_sessions_tv.heading(column="Username", text="Username")
        self.active_sessions_tv.column(column="Display #", anchor="e", minwidth=40, stretch=False, width=80)
        self.active_sessions_tv.heading(column="Display #", text="Display #")
        self.active_sessions_tv.column(column="Display Name", anchor="e", minwidth=40, stretch=True, width=120)
        self.active_sessions_tv.heading(column="Display Name", text="Display Name")
        self.active_sessions_tv.column(column="Geometry", anchor="e", minwidth=60, stretch=False, width=100)
        self.active_sessions_tv.heading(column="Geometry", text="Geometry")
        self.active_sessions_tv.column(column="PID", anchor="e", minwidth=50, stretch=False, width=50)
        self.active_sessions_tv.heading(column="PID", text="PID")

        # Add the active-sessions refresh button
        self.refresh_button_icon = Image.open("./icons/squid-ink/Controls & Navigation/png_32/Refresh.png")
        self.refresh_button_icon = self.refresh_button_icon.resize((24, 24), Image.BICUBIC)
        self.refresh_button_icon = ImageTk.PhotoImage(self.refresh_button_icon)

        self.refresh_button = ttk.Button(self.active_sessions_frame,
                                         text="Refresh",
                                         image=self.refresh_button_icon,
                                         compound='left')
        self.refresh_button.grid(column=0, row=1, sticky=(N, S, E, W))

        # Add the active-session connect button
        self.connect_button_icon = Image.open("./icons/squid-ink/Controls & Navigation/png_32/Expand.png")
        self.connect_button_icon = self.connect_button_icon.resize((24, 24), Image.BICUBIC)
        self.connect_button_icon = ImageTk.PhotoImage(self.connect_button_icon)

        self.connect_button = ttk.Button(self.active_sessions_frame,
                                         text="Connect",
                                         image=self.connect_button_icon,
                                         compound='left')
        self.connect_button.grid(column=1, row=1, sticky=(N, S, E, W))

        # Add the active-session kill button
        self.kill_button_icon = Image.open("./icons/squid-ink/Controls & Navigation/png_32/Remove.png")
        self.kill_button_icon = self.kill_button_icon.resize((24, 24), Image.BICUBIC)
        self.kill_button_icon = ImageTk.PhotoImage(self.kill_button_icon)

        self.kill_button = ttk.Button(self.active_sessions_frame,
                                      text="Kill",
                                      image=self.kill_button_icon,
                                      compound='left')
        self.kill_button.grid(column=2, row=1, sticky=(N, S, E, W))


        # Treeview widgets don't give you a way to iterate over their items. You
        # must store references to the items, yourself. Which is stupid...but, oh well...
        self.items_in_tv = []

        # Insert some dummy items into the TreeView while stubbing out the code.
        self.insert(-1, "mschinca", "300", "test", "1920x1020", 14270)
        self.insert(-1, "bklow", "55", "test313", "1280x720", 2709)





    def clear(self):
        """
        Clears the TreeView of all items.
        """
        self.log.debug("Clearing TreeView")
        for item in self.items_in_tv:
            self.active_sessions_tv.delete(item)
        self.items_in_tv.clear()


    def insert(self, idx, username, display_number, display_name, geometry, pid):
        """

        :param idx:
        :param username:
        :param display_number:
        :param display_name:
        :param geometry:
        :param pid:
        :return:
        """
        index = 'end' if idx == -1 else idx
        new_item = self.active_sessions_tv.insert('',
                                                  index=index,
                                                  text='',
                                                  image=self.session_icon,
                                                  values=(username, display_number, display_name, geometry, pid))
        self.items_in_tv.append(new_item)



