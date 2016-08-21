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

class RegisteredSessionsWidget(object):
    """
    A class that handles the registered-sessions GUI widget.
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
        self.log = logging.getLogger("RegisteredSessionsWidget")
        self.log.debug("Constructing the registered-sessions widget...")

        # Hold a reference to the parent in case it is needed later on.
        self.parent = parent

        # Open the icon used for the registered-session icon
        self.registered_session_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Office/png_32/Notebook-2.png")
        self.registered_session_icon = self.registered_session_icon.resize((16, 16), Image.BICUBIC)
        self.registered_session_icon = ImageTk.PhotoImage(self.registered_session_icon)

        # Open the icon used for the geometry information
        self.geometry_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Office/png_32/Square-Ruler.png")
        self.geometry_icon = self.geometry_icon.resize((16, 16), Image.BICUBIC)
        self.geometry_icon = ImageTk.PhotoImage(self.geometry_icon)

        # Open the icon used for the pixelformat information
        self.pixelformat_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Editing/png_32/Hue.png")
        self.pixelformat_icon = self.pixelformat_icon.resize((16, 16), Image.BICUBIC)
        self.pixelformat_icon = ImageTk.PhotoImage(self.pixelformat_icon)

        # Create a frame that can display a name, to wrap the TreeView component.
        self.registered_sessions_frame = ttk.LabelFrame(self.parent, text='Registered Sessions')
        self.registered_sessions_frame.columnconfigure((0, 1, 2, 3), weight=1)
        self.registered_sessions_frame.rowconfigure(0, weight=1)
        self.registered_sessions_frame.rowconfigure(1, weight=0)
        self.parent.add(self.registered_sessions_frame, weight=1)

        # Create the TreeView component that will display the list of registered sessions.
        self.registered_sessions_tv = ttk.Treeview(self.registered_sessions_frame)
        self.registered_sessions_tv.grid(column=0, columnspan=4, row=0, padx=4, pady=4, sticky=(N, S, E, W))
        self.registered_sessions_tv["selectmode"] = "browse"
        self.registered_sessions_tv["columns"] = ("Username", "Display #", "Display Name")
        self.registered_sessions_tv.column(column="#0", anchor="center", minwidth=40, stretch=False, width=40)
        self.registered_sessions_tv.heading(column="#0", text="")
        self.registered_sessions_tv.column(column="Username", anchor="e", minwidth=60, stretch=True, width=100)
        self.registered_sessions_tv.heading(column="Username", text="Username")
        self.registered_sessions_tv.column(column="Display #", anchor="e", minwidth=40, stretch=False, width=75)
        self.registered_sessions_tv.heading(column="Display #", text="Display #")
        self.registered_sessions_tv.column(column="Display Name", anchor="e", minwidth=40, stretch=True, width=100)
        self.registered_sessions_tv.heading(column="Display Name", text="Display Name")

        # Add the refresh registered-sessions button
        self.refresh_button_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Controls & Navigation/png_32/Refresh.png")
        self.refresh_button_icon = self.refresh_button_icon.resize((24, 24), Image.BICUBIC)
        self.refresh_button_icon = ImageTk.PhotoImage(self.refresh_button_icon)

        self.refresh_button = ttk.Button(self.registered_sessions_frame,
                                         text="Refresh",
                                         image=self.refresh_button_icon,
                                         compound='left')
        self.refresh_button.grid(column=0, row=2, sticky=(N, S, E, W))

        # Add the new registered-session button
        self.new_button_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Controls & Navigation/png_32/Plus.png")
        self.new_button_icon = self.new_button_icon.resize((24, 24), Image.BICUBIC)
        self.new_button_icon = ImageTk.PhotoImage(self.new_button_icon)

        self.new_button = ttk.Button(self.registered_sessions_frame,
                                     text="New",
                                     image=self.new_button_icon,
                                     compound='left')
        self.new_button.grid(column=1, row=2, sticky=(N, S, E, W))

        # Add the delete registered-session button
        self.delete_button_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Controls & Navigation/png_32/Remove.png")
        self.delete_button_icon = self.delete_button_icon.resize((24, 24), Image.BICUBIC)
        self.delete_button_icon = ImageTk.PhotoImage(self.delete_button_icon)

        self.delete_button = ttk.Button(self.registered_sessions_frame,
                                         text="Remove",
                                         image=self.delete_button_icon,
                                         compound='left')
        self.delete_button.grid(column=2, row=2, sticky=(N, S, E, W))

        # Add the start registered-session button
        self.start_button_icon = Image.open(self.SRC_DIR+"/icons/squid-ink/Controls & Navigation/png_32/Play.png")
        self.start_button_icon = self.start_button_icon.resize((24, 24), Image.BICUBIC)
        self.start_button_icon = ImageTk.PhotoImage(self.start_button_icon)

        self.start_button = ttk.Button(self.registered_sessions_frame,
                                      text="Start",
                                      image=self.start_button_icon,
                                      compound='left')
        self.start_button.grid(column=3, row=2, sticky=(N, S, E, W))


        # Treeview widgets don't give you a way to iterate over their items. You
        # must store references to the items, yourself. Which is stupid...but, oh well...
        self.items_in_tv = []

        # Create H and V scroll bars to allow changing the view point of the listbox.
        self.log_vscroll = ttk.Scrollbar(self.registered_sessions_frame, orient='vertical', command=self.registered_sessions_tv.yview)
        self.log_vscroll.grid(column=4, row=0, sticky=(N, S))
        self.registered_sessions_tv.configure(yscrollcommand=self.log_vscroll.set)

        self.log_hscroll = ttk.Scrollbar(self.registered_sessions_frame, orient='horizontal', command=self.registered_sessions_tv.xview)
        self.log_hscroll.grid(column=0, row=1, columnspan=4, sticky=(E, W))
        self.registered_sessions_tv.configure(xscrollcommand=self.log_hscroll.set)

        # Insert some dummy items into the TreeView while stubbing out the code.
        self.insert(-1, "mschinca", "300", "test", "1920x1020", "RGB888")
        self.insert(-1, "bklow", "55", "test313", "1280x720", "RGB565")





    def clear(self):
        """
        Clears the TreeView of all items.
        """
        self.log.debug("Clearing TreeView")
        for item in self.items_in_tv:
            self.registered_sessions_tv.delete(item)
        self.items_in_tv.clear()


    def insert(self, idx, username, display_number, display_name, geometry, pixelformat):
        """

        :param idx:
        :param username:
        :param display_number:
        :param display_name:
        :param geometry:
        :param pixelformat:
        :return:
        """
        index = 'end' if idx == -1 else idx
        new_item = self.registered_sessions_tv.insert('',
                                                  index=index,
                                                  text='',
                                                  image=self.registered_session_icon,
                                                  values=(username, display_number, display_name, geometry))
        self.items_in_tv.append(new_item)

        # Insert the less commonly used information as a child of the item
        # inserted above so that it is not shown by default (the user will have
        # to click the node to open it).
        self.registered_sessions_tv.insert(new_item,
                                           index='end',
                                           text='',
                                           values=(geometry),
                                           tags='geo_childitem')
        self.registered_sessions_tv.insert(new_item,
                                           index='end',
                                           text='',
                                           values=(pixelformat),
                                           tags='fmt_childitem')

        self.registered_sessions_tv.tag_configure('geo_childitem', image=self.geometry_icon)
        self.registered_sessions_tv.tag_bind('geo_childitem', sequence="<<TreeviewSelect>>", callback=self.adjust_selection_to_parent)
        self.registered_sessions_tv.tag_configure('fmt_childitem', image=self.pixelformat_icon)
        self.registered_sessions_tv.tag_bind('fmt_childitem', sequence="<<TreeviewSelect>>", callback=self.adjust_selection_to_parent)


    def adjust_selection_to_parent(self, e):
        selected_item = e.widget.selection()
        parent = e.widget.parent(selected_item)
        if parent != "":
            # Select the parent item instead of it's child
            self.registered_sessions_tv.selection_set(parent)
            # Ensure the parent is visible
            self.registered_sessions_tv.see(parent)
        else:
            pass