from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
import logging


class NewVNCSessionForm(object):
    """
    A class to display a form that allows the user to enter the
    configuration of a new VNC server.
    """


    def __init__(self):
        """
        Constructs form

        :param parent: A Tk widget that acts as the parent to this widget.
        """
        # Configure logging
        self.log = logging.getLogger("ActiveSessionsWidget")
        self.log.debug("Constructing the active-sessions widget...")

        # Create a new toplevel window
        self.toplevel = Toplevel()
        self.toplevel.resizable(width=False, height=False)
        self.toplevel.rowconfigure((0, 1, 2, 3, 4), weight=0)
        self.toplevel.columnconfigure((1, 2,), weight=1)

        # The display number label and entry box
        self.display_number_label = ttk.Label(self.toplevel, text="Display Number")
        self.display_number_label.grid(column=0, row=0, padx=4, pady=4, sticky=(N, S, E, W))
        self.display_number = StringVar()
        self.display_number_entry = ttk.Entry(self.toplevel, textvariable=self.display_number, width=4)
        self.display_number_entry.grid(column=1, row=0, padx=4, pady=4, sticky=(N, S, E, W))

        # The display name label and entry box
        self.display_name_label = ttk.Label(self.toplevel, text="Display Name")
        self.display_name_label.grid(column=0, row=1, padx=4, pady=4, sticky=(N, S, E, W))
        self.display_name = StringVar()
        self.display_name_entry = ttk.Entry(self.toplevel, textvariable=self.display_name, width=4)
        self.display_name_entry.grid(column=1, columnspan=2, row=1, padx=4, pady=4, sticky=(N, S, E, W))

        # The session geometry label and boxes for width and height.
        self.width_label = ttk.Label(self.toplevel, text="Width", width=4)
        self.width_label.grid(column=1, row=2, padx=4, pady=4, sticky=(N, S, E, W))
        self.height_label = ttk.Label(self.toplevel, text="Height", width=4)
        self.height_label.grid(column=2, row=2, padx=4, pady=4, sticky=(N, S, E, W))
        self.geometry_label = ttk.Label(self.toplevel, text="Geometry")
        self.geometry_label.grid(column=0, row=3, padx=4, pady=4, sticky=(N, S, E, W))
        self.width = StringVar()
        self.width_entry = ttk.Entry(self.toplevel, textvariable=self.width, width=8)
        self.width_entry.grid(column=1, row=3, padx=4, pady=4, sticky=(N, S, E, W))
        self.height = StringVar()
        self.height_entry = ttk.Entry(self.toplevel, textvariable=self.height, width=8)
        self.height_entry.grid(column=2, row=3, padx=4, pady=4, sticky=(N, S, E, W))

        self.pxielformat_label = ttk.Label(self.toplevel, text="Pixelformat")
        self.pxielformat_label.grid(column=0, row=4, padx=4, pady=4, sticky=(E, W))
        self.pixelformat_list = ["RGB233", "BGR233", "RGB565", "BGR565", "RGB888", "BGR888"]
        self.pixelformat = StringVar()
        self.pixelformat_combobox = ttk.Combobox(self.toplevel,
                                                 textvariable=self.pixelformat,
                                                 values=self.pixelformat_list,
                                                 width=6)
        self.pixelformat_combobox.grid(column=1, row=4, padx=4, pady=4, sticky=(N, S, E, W))

        # Create a frame to visually offset the buttons from the rest of the form
        self.frame = ttk.Frame(self.toplevel)
        self.frame.grid(column=0, columnspan=4, row=5, padx=4, pady=4, sticky=(N, S, E, W))
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure((0,2,3), weight=1)


        self.ok_button_icon = Image.open("./icons/squid-ink/Controls & Navigation/png_32/Ok.png")
        self.ok_button_icon = self.ok_button_icon.resize((24, 24), Image.BICUBIC)
        self.ok_button_icon = ImageTk.PhotoImage(self.ok_button_icon)
        self.ok_button = ttk.Button(self.frame,
                                    text="OK",
                                    image=self.ok_button_icon,
                                    compound='left',
                                    command=self._on_ok_clicked)
        self.ok_button.grid(column=0, columnspan=2, row=0, padx=4, pady=4, sticky=(N, S, E, W))

        self.cancel_button_icon = Image.open("./icons/squid-ink/Controls & Navigation/png_32/Block.png")
        self.cancel_button_icon = self.cancel_button_icon.resize((24, 24), Image.BICUBIC)
        self.cancel_button_icon = ImageTk.PhotoImage(self.cancel_button_icon)
        self.cancel_button = ttk.Button(self.frame,
                                        text="Cancel",
                                        image=self.cancel_button_icon,
                                        compound='left',
                                        command=self._on_cancel_clicked)
        self.cancel_button.grid(column=2, columnspan=2, row=0, padx=4, pady=4, sticky=(N, S, E, W))


        # Setup default values
        self.display_number.set("999")
        self.display_name.set("Default")
        self.width.set("640")
        self.height.set("512")
        self.pixelformat.set("RGB565")

        # Keep track of how the form was exited
        self.ok_was_clicked = False
        self.cancel_was_clicked = False


    def _on_ok_clicked(self):
        self.ok_was_clicked = True
        self.toplevel.destroy()


    def _on_cancel_clicked(self):
        self.cancel_was_clicked = True
        self.toplevel.destroy()


    def show(self):
        # Put the dialogue in the center of the screen
        screen_width = self.toplevel.winfo_screenwidth()
        screen_height = self.toplevel.winfo_screenheight()
        window_width = 270
        window_height = 180
        x_offset = int(screen_width/2 - window_width/2)
        y_offset = int(screen_height/2 - window_height/2)
        self.toplevel.geometry("{0}x{1}+{2}+{3}".format(window_width,
                                                        window_height,
                                                        x_offset,
                                                        y_offset))
        self.toplevel.focus_set()
        self.toplevel.grab_set()
        #self.toplevel.transient()
        self.toplevel.wait_window()


    def get_info(self):
        info = {"display_number": self.display_number.get(),
                "display_name": self.display_name.get(),
                "geometry": "{}x{}".format(self.width.get(), self.height.get()),
                "pixelformat": "{}".format(self.pixelformat.get())}
        return info

if __name__ == "__main__":
    inst = NewVNCSessionForm()
    inst.show()