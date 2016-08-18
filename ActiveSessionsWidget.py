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

        # Open the icon used for the session icon
        self.session_icon = Image.open("./icons/squid-ink/User Interface/png_32/Application-Modal.png")
        self.session_icon = self.session_icon.resize((16, 16), Image.BICUBIC)
        self.session_icon = ImageTk.PhotoImage(self.session_icon)

        # Open the icon used for the geometry information
        self.geometry_icon = Image.open("./icons/squid-ink/Office/png_32/Square-Ruler.png")
        self.geometry_icon = self.geometry_icon.resize((16, 16), Image.BICUBIC)
        self.geometry_icon = ImageTk.PhotoImage(self.geometry_icon)

        # Open the icon used for the pixelformat information
        self.pixelformat_icon = Image.open("./icons/squid-ink/Editing/png_32/Hue.png")
        self.pixelformat_icon = self.pixelformat_icon.resize((16, 16), Image.BICUBIC)
        self.pixelformat_icon = ImageTk.PhotoImage(self.pixelformat_icon)

        # Create a frame that can display a name, to wrap the TreeView component.
        self.active_sessions_frame = ttk.LabelFrame(self.parent, text='Active Sessions')
        self.active_sessions_frame.columnconfigure((0, 1, 2, 3), weight=1)
        self.active_sessions_frame.rowconfigure(0, weight=1)
        self.active_sessions_frame.rowconfigure(1, weight=0)
        self.parent.add(self.active_sessions_frame, weight=1)

        # Create the TreeView component that will display the list of active sessions.
        self.active_sessions_tv = ttk.Treeview(self.active_sessions_frame)
        self.active_sessions_tv.grid(column=0, columnspan=4, row=0, padx=4, pady=4, sticky=(N, S, E, W))
        self.active_sessions_tv["selectmode"] = "browse"
        self.active_sessions_tv["columns"] = ("Username", "Display #", "Display Name", "PID")
        self.active_sessions_tv.column(column="#0", anchor="center", minwidth=40, stretch=False, width=40)
        self.active_sessions_tv.heading(column="#0", text="")
        self.active_sessions_tv.column(column="Username", anchor="e", minwidth=60, stretch=True, width=100)
        self.active_sessions_tv.heading(column="Username", text="Username")
        self.active_sessions_tv.column(column="Display #", anchor="e", minwidth=40, stretch=False, width=75)
        self.active_sessions_tv.heading(column="Display #", text="Display #")
        self.active_sessions_tv.column(column="Display Name", anchor="e", minwidth=40, stretch=True, width=100)
        self.active_sessions_tv.heading(column="Display Name", text="Display Name")
        self.active_sessions_tv.column(column="PID", anchor="e", minwidth=50, stretch=False, width=50)
        self.active_sessions_tv.heading(column="PID", text="PID")

        # Add the refresh active-sessions button
        self.refresh_button_icon = Image.open("./icons/squid-ink/Controls & Navigation/png_32/Refresh.png")
        self.refresh_button_icon = self.refresh_button_icon.resize((24, 24), Image.BICUBIC)
        self.refresh_button_icon = ImageTk.PhotoImage(self.refresh_button_icon)

        self.refresh_button = ttk.Button(self.active_sessions_frame,
                                         text="Refresh",
                                         image=self.refresh_button_icon,
                                         compound='left',
                                         command=self.handle_refresh_button_clicked)
        self.refresh_button.grid(column=0, row=2, sticky=(N, S, E, W))

        # Add the new session button
        self.new_button_icon = Image.open("./icons/squid-ink/Controls & Navigation/png_32/Plus.png")
        self.new_button_icon = self.new_button_icon.resize((24, 24), Image.BICUBIC)
        self.new_button_icon = ImageTk.PhotoImage(self.new_button_icon)

        self.new_button = ttk.Button(self.active_sessions_frame,
                                     text="New",
                                     image=self.new_button_icon,
                                     compound='left')
        self.new_button.grid(column=1, row=2, sticky=(N, S, E, W))

        # Add the kill active-session button
        self.kill_button_icon = Image.open("./icons/squid-ink/Controls & Navigation/png_32/Remove.png")
        self.kill_button_icon = self.kill_button_icon.resize((24, 24), Image.BICUBIC)
        self.kill_button_icon = ImageTk.PhotoImage(self.kill_button_icon)

        self.kill_button = ttk.Button(self.active_sessions_frame,
                                      text="Kill",
                                      image=self.kill_button_icon,
                                      compound='left')
        self.kill_button.grid(column=2, row=2, sticky=(N, S, E, W))

        # Add the connect to active-session button
        self.connect_button_icon = Image.open("./icons/squid-ink/Controls & Navigation/png_32/Expand.png")
        self.connect_button_icon = self.connect_button_icon.resize((24, 24), Image.BICUBIC)
        self.connect_button_icon = ImageTk.PhotoImage(self.connect_button_icon)

        self.connect_button = ttk.Button(self.active_sessions_frame,
                                         text="Connect",
                                         image=self.connect_button_icon,
                                         compound='left')
        self.connect_button.grid(column=3, row=2, sticky=(N, S, E, W))

        # Treeview widgets don't give you a way to iterate over their items. You
        # must store references to the items, yourself. Which is stupid...but, oh well...
        self.items_in_tv = []

        # Create H and V scroll bars to allow changing the view point of the listbox.
        self.log_vscroll = ttk.Scrollbar(self.active_sessions_frame, orient='vertical', command=self.active_sessions_tv.yview)
        self.log_vscroll.grid(column=4, row=0, sticky=(N, S))
        self.active_sessions_tv.configure(yscrollcommand=self.log_vscroll.set)

        self.log_hscroll = ttk.Scrollbar(self.active_sessions_frame, orient='horizontal', command=self.active_sessions_tv.xview)
        self.log_hscroll.grid(column=0, row=1, columnspan=4, sticky=(E, W))
        self.active_sessions_tv.configure(xscrollcommand=self.log_hscroll.set)

        # Insert some dummy items into the TreeView while stubbing out the code.
        self.insert(-1, "mschinca", "300", "test", 14720, "1920x1020", "RGB888")
        self.insert(-1, "bklow", "55", "test313", 2709, "1280x720", "RGB565")

        # A list of method references to call when the refresh button is clicked.
        self.refresh_button_clicked_handlers = []


    def clear(self):
        """
        Clears the TreeView of all items.
        """
        self.log.debug("Clearing TreeView")
        for item in self.items_in_tv:
            self.active_sessions_tv.delete(item)
        self.items_in_tv.clear()


    def insert(self, idx, username, display_number, display_name, pid, geometry, pixelformat):
        """

        :param idx:
        :param username:
        :param display_number:
        :param display_name:
        :param pid:
        :param geometry:
        :param pixelformat
        :return:
        """
        index = 'end' if idx == -1 else idx
        self.log.debug("Inserting item: {0}:{1}({2}-{3}):{4}@{5}".format(username,
                                                                         display_number,
                                                                         geometry,
                                                                         pixelformat,
                                                                         display_name,
                                                                         index))
        # Insert the commonly used information as a child of the root
        new_item = self.active_sessions_tv.insert('',
                                                  index=index,
                                                  text='',
                                                  image=self.session_icon,
                                                  values=(username, display_number, display_name, pid))
        self.items_in_tv.append(new_item)

        # Insert the less commonly used information as a child of the item
        # inserted above so that it is not shown by default (the user will have
        # to click the node to open it).
        self.active_sessions_tv.insert(new_item,
                                       index='end',
                                       text='',
                                       values=(geometry),
                                       tags='geo_childitem')
        self.active_sessions_tv.insert(new_item,
                                       index='end',
                                       text='',
                                       values=(pixelformat),
                                       tags='fmt_childitem')

        self.active_sessions_tv.tag_configure('geo_childitem', image=self.geometry_icon)
        self.active_sessions_tv.tag_bind('geo_childitem', sequence="<<TreeviewSelect>>", callback=self.adjust_selection_to_parent)
        self.active_sessions_tv.tag_configure('fmt_childitem', image=self.pixelformat_icon)
        self.active_sessions_tv.tag_bind('fmt_childitem', sequence="<<TreeviewSelect>>", callback=self.adjust_selection_to_parent)


    def adjust_selection_to_parent(self, e):
        selected_item = e.widget.selection()
        parent = e.widget.parent(selected_item)
        if parent != "":
            # Select the parent item instead of it's child
            self.active_sessions_tv.selection_set(parent)
            # Ensure the parent is visible
            self.active_sessions_tv.see(parent)
        else:
            pass


    def add_refresh_button_clicked_event_handler(self, callback, *args):
        """
        Registers the callback to be called when the refresh button is clicked.

        :param callback: A method that will be passed *args when called.
        """
        self.log.debug("Adding refresh button clicked event handler: {}".format(callback))
        self.refresh_button_clicked_handlers.append([callback, args])


    def handle_refresh_button_clicked(self):
        """
        :param e: A TK event object
        :return:
        """
        self.log.debug("Refresh button clicked...")

        # Call each registered handler in turn
        for handler, args in self.refresh_button_clicked_handlers:
            self.log.debug("Calling handler {}".format(handler))
            handler(*args)