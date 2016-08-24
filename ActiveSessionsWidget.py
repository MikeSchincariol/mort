import sys
import os.path
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
        # Determine where the source code is to be found
        # :NOTE: Refer to documentation of sys.path for why this works.
        self.SRC_DIR = os.path.abspath(sys.path[0])

        # Configure logging
        self.log = logging.getLogger("ActiveSessionsWidget")
        self.log.debug("Constructing the active-sessions widget...")

        # Hold a reference to the parent in case it is needed later on.
        self.parent = parent

        # Open the icon used for the session icon
        self.session_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/User Interface/png_32/Application-Modal.png")
        self.session_icon = self.session_icon.resize((16, 16), Image.BICUBIC)
        self.session_icon = ImageTk.PhotoImage(self.session_icon)

        # Open the icon used for the geometry information
        self.geometry_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Office/png_32/Square-Ruler.png")
        self.geometry_icon = self.geometry_icon.resize((16, 16), Image.BICUBIC)
        self.geometry_icon = ImageTk.PhotoImage(self.geometry_icon)

        # Open the icon used for the pixelformat information
        self.pixelformat_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Editing/png_32/Hue.png")
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
        self.refresh_button_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Controls & Navigation/png_32/Refresh.png")
        self.refresh_button_icon = self.refresh_button_icon.resize((24, 24), Image.BICUBIC)
        self.refresh_button_icon = ImageTk.PhotoImage(self.refresh_button_icon)

        self.refresh_button = ttk.Button(self.active_sessions_frame,
                                         text="Refresh",
                                         image=self.refresh_button_icon,
                                         compound='left',
                                         command=self.handle_refresh_button_clicked)
        self.refresh_button.grid(column=0, row=2, sticky=(N, S, E, W))

        # Add the new session button
        self.new_button_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Controls & Navigation/png_32/Plus.png")
        self.new_button_icon = self.new_button_icon.resize((24, 24), Image.BICUBIC)
        self.new_button_icon = ImageTk.PhotoImage(self.new_button_icon)

        self.new_button = ttk.Button(self.active_sessions_frame,
                                     text="New",
                                     image=self.new_button_icon,
                                     compound='left',
                                     command=self.handle_new_button_clicked)
        self.new_button.grid(column=1, row=2, sticky=(N, S, E, W))

        # Add the kill active-session button
        self.kill_button_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Controls & Navigation/png_32/Remove.png")
        self.kill_button_icon = self.kill_button_icon.resize((24, 24), Image.BICUBIC)
        self.kill_button_icon = ImageTk.PhotoImage(self.kill_button_icon)

        self.kill_button = ttk.Button(self.active_sessions_frame,
                                      text="Kill",
                                      image=self.kill_button_icon,
                                      compound='left',
                                      command=self.handle_kill_button_clicked)
        self.kill_button.grid(column=2, row=2, sticky=(N, S, E, W))

        # Add the connect to active-session button
        self.connect_button_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Controls & Navigation/png_32/Expand.png")
        self.connect_button_icon = self.connect_button_icon.resize((24, 24), Image.BICUBIC)
        self.connect_button_icon = ImageTk.PhotoImage(self.connect_button_icon)

        self.connect_button = ttk.Button(self.active_sessions_frame,
                                         text="Connect",
                                         image=self.connect_button_icon,
                                         compound='left',
                                         command=self.handle_connect_button_clicked)
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

        # Server identification information to relate the entries in the Treeview
        # to the server they came from.
        # :NOTE: The Treeview is only expected to ever hold entries from one server
        #        at a time.
        self.server_hostname = None
        self.server_ip_address = None
        self.server_port = None

        # A list of method references to call when the refresh button is clicked.
        self.refresh_button_clicked_handlers = []

        # A list of method references to call when the new button is clicked.
        self.new_button_clicked_handlers = []

        # A list of method references to call when the kill button is clicked.
        self.kill_button_clicked_handlers = []

        # A list of method references to call when the connect button is clicked.
        self.connect_button_clicked_handlers = []

        # Insert some dummy items into the TreeView while stubbing out the code.
        # self.insert(-1, "mschinca", "300", "test", 14720, "1920x1020", "RGB888")
        # self.insert(-1, "bklow", "55", "test313", 2709, "1280x720", "RGB565")

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

    def get_display_numbers_in_use(self):
        """
        Returns a list of display numbers already in use by items in the
        list of active-sessions.
        :return:
        """
        self.log.debug("Retrieving list of display numbers in use...")
        # A list to return to the caller
        display_list = []
        # Get the column names (note that Tk returns this as item 4
        # in a weird 5-tuple structure)
        cols = self.active_sessions_tv.configure("columns")[4]
        # Determine which column index is holds the display number
        display_number_idx = None
        for idx, col in enumerate(cols):
            if col.lower() == "display #":
                display_number_idx = idx
                break
        # Iterate over all the items in the TreeView
        for item in self.items_in_tv:
            # Get the value of each column of the item
            item_vals = self.active_sessions_tv.item(item)["values"]
            # Extract the display number and add it to the list of display numbers
            display_list.append(item_vals[display_number_idx])
        return display_list


    def get_selected_item_info(self):
        """
        Returns a dictionary of the columns names and their associated
        values for the selected item.
        """
        self.log.debug("Retrieving selected item info...")
        # Get the column names (note that Tk returns this as item 4
        # in a weird 5-tuple structure)
        keys = self.active_sessions_tv.configure("columns")[4]

        # Get the item in the tree that is selected
        selected_item = self.active_sessions_tv.selection()

        # Get the value of each column of the selected item. If no item
        # is selected, return None.
        selected_vals = self.active_sessions_tv.item(selected_item)["values"]
        if selected_vals == "":
            return None

        # Construct the dictionary of key:value pairs to give the registered handlers.
        vals = {}
        for idx, key in enumerate(keys):
            vals[key] = selected_vals[idx]
        return vals


    def set_server_info(self, hostname, ip_address, port):
        """
        Allows the caller to associate server related information with the
        entries in the Treeview.
        :param hostname: The hostname of the server that provided the entries.
        :param ip_address: The IP address of the server that provided the entries.
        :param port: The port to communicate with the server on
        """
        self.log.debug("Setting related server to: {0}({1}:{2})".format(hostname,
                                                                        ip_address,
                                                                        port))
        self.server_hostname = hostname
        self.server_ip_address = ip_address
        self.server_port = port


    def get_server_info(self):
        """
        Retrieves the server information associated with the entries in
        the Treeview.

        :return: A dictionary with keys for "Hostname", "IP Address" and "Port".
        """
        self.log.debug("Returning related server of: {0}({1}:{2})".format(self.server_hostname,
                                                                          self.server_ip_address,
                                                                          self.server_port))
        server_info = {"Hostname": self.server_hostname,
                       "IP Address": self.server_ip_address,
                       "Port": self.server_port}
        return server_info



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


    def add_new_button_clicked_event_handler(self, callback, *args):
        """
        Registers the callback to be called when the new button is clicked.

        :param callback: A method that will be passed *args when called.
        """
        self.log.debug("Adding new button clicked event handler: {}".format(callback))
        self.new_button_clicked_handlers.append([callback, args])


    def handle_new_button_clicked(self):
        """
        :param e: A TK event object
        :return:
        """
        self.log.debug("New button clicked...")

        # Call each registered handler in turn
        for handler, args in self.new_button_clicked_handlers:
            self.log.debug("Calling handler {}".format(handler))
            handler(*args)


    def add_kill_button_clicked_event_handler(self, callback, *args):
        """
        Registers the callback to be called when the kill button is clicked.

        :param callback: A method that will be passed *args when called.
        """
        self.log.debug("Adding kill button clicked event handler: {}".format(callback))
        self.kill_button_clicked_handlers.append([callback, args])


    def handle_kill_button_clicked(self):
        """
        :param e: A TK event object
        :return:
        """
        self.log.debug("Kill button clicked...")

        # Call each registered handler in turn
        for handler, args in self.kill_button_clicked_handlers:
            self.log.debug("Calling handler {}".format(handler))
            handler(*args)


    def add_connect_button_clicked_event_handler(self, callback, *args):
        """
        Registers the callback to be called when the connect button is clicked.

        :param callback: A method that will be passed *args when called.
        """
        self.log.debug("Adding connect button clicked event handler: {}".format(callback))
        self.connect_button_clicked_handlers.append([callback, args])


    def handle_connect_button_clicked(self):
        """
        :param e: A TK event object
        :return:
        """
        self.log.debug("Connect button clicked...")

        # Call each registered handler in turn
        for handler, args in self.connect_button_clicked_handlers:
            self.log.debug("Calling handler {}".format(handler))
            handler(*args)
