import threading
import logging
import logging.handlers
import LogFilter
import queue
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image


class SessionServersWidget(object):
    """
    A class that handles the session-servers GUI widget.
    The "View" in the MVC pattern.
    """

    def __init__(self, parent):
        """
        Constructs the GUI widget.

        :param parent: A Tk widget that acts as the parent to this widget.
        """
        # Configure logging
        self.log = logging.getLogger("SessionServersWidget")
        self.log.debug("Constructing the session-servers widget...")

        # Hold a reference to the parent in case it is needed later on.
        self.parent = parent

        # Open the icon used for the server icon
        self.server_icon = Image.open("./icons/squid-ink/Devices & Network/png_32/Server.png")
        self.server_icon = self.server_icon.resize((16, 16), Image.BICUBIC)
        self.server_icon = ImageTk.PhotoImage(self.server_icon)

        # Create a frame that can display a name, to wrap the TreeView component.
        self.session_servers_frame = ttk.LabelFrame(self.parent,
                                                    text='Session Servers',
                                                    width=200,
                                                    height=100)

        self.session_servers_frame.columnconfigure(0, weight=1)
        self.session_servers_frame.rowconfigure(0, weight=1)
        self.parent.add(self.session_servers_frame, weight=1)

        # Create the TreeView component that will display the list of session-servers.
        self.session_server_tv = ttk.Treeview(self.session_servers_frame)
        self.session_server_tv.grid(column=0, row=0, padx=4, pady=4, sticky=(N, S, E, W))
        self.session_server_tv["selectmode"] = "browse"
        self.session_server_tv["columns"] = ("Hostname", "IP Address", "Port")
        self.session_server_tv.column(column="#0", anchor="center", minwidth=40, stretch=False, width=36)
        self.session_server_tv.heading(column="#0", text="")
        self.session_server_tv.column(column="Hostname", anchor="e", minwidth=64, stretch=True, width=200)
        self.session_server_tv.heading(column="Hostname", text="Hostname")
        self.session_server_tv.column(column="IP Address", anchor="e", minwidth=64, stretch=False, width=90)
        self.session_server_tv.heading(column="IP Address", text="IP Address")
        self.session_server_tv.column(column="Port", anchor="e", minwidth=64, stretch=False, width=48)
        self.session_server_tv.heading(column="Port", text="Port")

        # Treeview widgets don't give you a way to iterate over their items. You
        # must store references to the items, yourself. Which is stupid...but, oh well...
        self.items_in_tv = []


    def clear(self):
        """
        Clears the TreeView of all items.
        """
        self.log.debug("Clearing TreeView")
        for item in self.items_in_tv:
            self.session_server_tv.delete(item)
        self.items_in_tv.clear()


    def insert(self, idx, hostname, ip_address, port):
        """

        :param idx:
        :param hostname:
        :param ip_address:
        :param port:
        :return:
        """
        index = 'end' if idx == -1 else idx
        self.log.debug("Inserting item: {0}:{1}:{2}@{3}".format(hostname,
                                                                ip_address,
                                                                port,
                                                                index))
        new_item = self.session_server_tv.insert('',
                                                 index=index,
                                                 text='',
                                                 image=self.server_icon,
                                                 values=(hostname, ip_address, port))
        self.items_in_tv.append(new_item)

