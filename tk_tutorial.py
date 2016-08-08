from tkinter import *
from tkinter import ttk


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

root.mainloop()
