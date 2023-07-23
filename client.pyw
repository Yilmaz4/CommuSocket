from tkinter import *
from tkinter import Label as TkLabel
from tkinter.ttk import *
from tkinter import messagebox

from typing import *
from commusocket import Server, Address, Message
from requests import get

import socket, pickle, time

class ScrolledText(Text):
    def __init__(self, master: Tk | Frame | LabelFrame, *args, **kwargs):
        try:
            self._textvariable = kwargs.pop("textvariable")
        except KeyError:
            self._textvariable = None

        # Implement the scrollbar
        self.frame = Frame(master)
        self.vbar = Scrollbar(self.frame)
        self.vbar.pack(side=RIGHT, fill=Y)
        kwargs.update({'yscrollcommand': self.vbar.set})
        super().__init__(self.frame, *args, **kwargs)
        self.pack(side=LEFT, fill=BOTH, expand=YES)
        self.vbar['command'] = self.yview
        text_meths = vars(Text).keys()
        methods = vars(Pack).keys() | vars(Grid).keys() | vars(Place).keys()
        methods = methods.difference(text_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

        # Implement textvariable
        if self._textvariable is not None:
            self.insert("1.0", self._textvariable.get())
        self.tk.eval("""
        proc widget_proxy {widget widget_command args} {

            set result [uplevel [linsert $args 0 $widget_command]]

            if {([lindex $args 0] in {insert replace delete})} {
                event generate $widget <<Change>> -when tail
            }

            return $result
        }""")
        self.tk.eval('''
            rename {widget} _{widget}
            interp alias {{}} ::{widget} {{}} widget_proxy {widget} _{widget}
        '''.format(widget=str(Text.__str__(self))))
        self.bind("<<Change>>", self._on_widget_change)

        if self._textvariable is not None:
            self._textvariable.trace("wu", self._on_var_change)

    def replace(self, chars: str):
        """
        Method to replace the text in the widget entirely with the given string
        """
        old_val = self["state"]
        self.configure(state=NORMAL)
        self.delete("1.0", END)
        self.insert("1.0", chars)
        self.configure(state=old_val)

    def clear(self):
        """
        Method to clear all the text in the widget
        """
        old_val = self["state"]
        self.configure(state=NORMAL)
        self.delete("1.0", END)
        self.configure(state=old_val)

    def _on_var_change(self, *args):
        text_current = self.get("1.0", "end-1c")
        var_current = self._textvariable.get()
        if text_current != var_current:
            self.delete("1.0", "end")
            self.insert("1.0", var_current)

    def _on_widget_change(self, event=None):
        if self._textvariable is not None:
            self._textvariable.set(self.get("1.0", "end-1c"))

    def __str__(self):
        return str(self.frame)

class Interface(Tk):
    def __init__(self):
        super().__init__()

        self.wm_geometry("283x173")
        self.wm_minsize(width=283, height=173)
        self.wm_maxsize(width=283, height=173)
        self.wm_iconbitmap("icon.ico")
        self.wm_resizable(False, False)

        self.main_menu()

        self.mainloop()
    
    def wait_for_response(self):
        while True:
            try:
                data = self.socket.recv(10)
            except TimeoutError:
                continue
            except ConnectionResetError:
                return False
            if data and data.startswith(b"SUCCESS"):
                return True
            else:
                return None

    def main_menu(self):
        for child in self.winfo_children():
            child.destroy()
        self.wm_title("CommuSocket")
        self.wm_minsize(width=283, height=173)
        self.wm_maxsize(width=283, height=173)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        optionFrame = Frame(self)
        
        host_button = Button(optionFrame, text="Create", width=16, takefocus=0, command=self.create_server)
        conn_button = Button(optionFrame, text="Join", width=16, takefocus=0, command=self.join_server)
        sett_button = Button(optionFrame, text="Settings", width=16, takefocus=0)
        
        host_button.grid_configure(row=0, column=0, pady=2)
        conn_button.grid_configure(row=1, column=0, pady=2)
        sett_button.grid_configure(row=2, column=0, pady=2)
        
        optionFrame.place_configure(relx=0.5, rely=0.5, anchor=CENTER)
        title = Label(self, text="CommuSocket", font=("Lato-Thin", 14))
        title.pack(side=TOP, pady=13)
        copyright = Label(self, text="Copyright © 2017-2022 Yılmaz Alpaslan", font=("Segoe UI", 8), foreground="gray")
        copyright.pack(side=BOTTOM)

    def create_server(self):
        for child in self.winfo_children():
            child.destroy()
        self.wm_title("Create Server")
        self.wm_minsize(width=283, height=123)
        self.wm_maxsize(width=283, height=123)

        def name_callback(*args, **kwargs):
            create_button.configure(state=NORMAL if name_var.get() else DISABLED)

        def create():
            try:
                self.socket.connect(("94.54.96.223", 2422))
            except OSError:
                pass
            self.socket.send(b"CREATE_SERVER/" + pickle.dumps({
                "name": name_entry.get(),
                "capacity": capacity_entry.get(),
                "password": password_entry.get()
            }))
            if self.wait_for_response():
                messagebox.showinfo("Server creation successful", f"A server named {name_entry.get()} with a capacity of {capacity_entry.get()} has been successfully created!")
                self.main_menu()

        name_var = StringVar()
        capacity_var = DoubleVar(value=10)

        name_label = Label(self, text="Name:")
        name_entry = Entry(self, width=32, textvariable=name_var)
        password_label = Label(self, text="Password:")
        password_entry = Entry(self, width=32)
        capacity_label = Label(self, text="Capacity:")
        capacity_entry = Spinbox(self, from_=2, to=20, width=30, textvariable=capacity_var, state="readonly")

        create_button = Button(self, text="Create", width=24, takefocus=0, command=create, state=DISABLED)
        back_button = Button(self, text="Back", width=15, takefocus=0, command=self.main_menu)

        name_var.trace_variable("w", name_callback)

        name_label.place(x=9, y=10)
        name_entry.place(x=73, y=8)
        password_label.place(x=9, y=35)
        password_entry.place(x=73, y=33)
        capacity_label.place(x=9, y=60)
        capacity_entry.place(x=73, y=58)
        create_button.place(x=9, y=88)
        back_button.place(x=172, y=88)

    def join_server(self):
        self.servers = []
        for child in self.winfo_children():
            child.destroy()
        self.wm_title("Join Server")
        self.wm_minsize(width=504, height=258)
        self.wm_maxsize(width=504, height=258)

        tree = Treeview(self, columns=("name", "owner", "members", "capacity", "password"), show="headings")

        tree.heading('name', text='Name')
        tree.heading('owner', text='Owner')
        tree.heading('members', text="Members")
        tree.heading('capacity', text='Capacity')
        tree.heading('password', text='Password')

        minwidth = tree.column('name', option='minwidth')
        tree.column('name', width=minwidth)
        minwidth = tree.column('owner', option='minwidth')
        tree.column('owner', width=minwidth)
        minwidth = tree.column('members', option='minwidth')
        tree.column('members', width=minwidth)
        minwidth = tree.column('capacity', option='minwidth')
        tree.column('capacity', width=minwidth)
        minwidth = tree.column('password', option='minwidth')
        tree.column('password', width=minwidth)

        def on_select(event):
            connect_button.configure(state=NORMAL)

        tree.bind("<<TreeviewSelect>>", on_select)

        tree.place_configure(x=9, y=9, height=210, width=470)

        scrollbar = Scrollbar(self, orient=VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.place_configure(x=479, y=9, height=210)

        def refresh():
            try:
                self.socket.connect((get('https://api.ipify.org').content.decode('utf8'), 2422))
            except OSError:
                tree.delete(*tree.get_children())
                refresh_button.configure(state=DISABLED)
                try:
                    def set_refresh_button_state():
                        try:
                            refresh_button.configure(state=NORMAL)
                        except Exception:
                            pass
                    self.after(1000, set_refresh_button_state)
                except Exception:
                    pass
            self.socket.send(b"GET_MASTERLIST")
            while True:
                try:
                    data = self.socket.recv(1024)
                except TimeoutError:
                    continue
                except ConnectionResetError:
                    return
                self.servers: List[Server] = pickle.loads(data)
                break
            for server in self.servers:
                tree.insert('', END, values=(server.name, server.owner, len(server.users), server.capacity, "Present" if bool(server.password) else "None"))

        def connect():
            self.socket.send(b"JOIN_SERVER/" + pickle.dumps(self.servers[int(tree.selection()[0][1:])]))
            if self.wait_for_response():
                self.in_server()

        connect_button = Button(self, text="Join", width=17, takefocus=0, state=DISABLED, command=connect)
        refresh_button = Button(self, text="Refresh", width=14, takefocus=0, command=refresh)
        direct_button = Button(self, text="Direct Join", width=17, takefocus=0)
        back_button = Button(self, text="Back", width=15, takefocus=0, command=self.main_menu)

        refresh()

        connect_button.place(x=8, y=226)
        refresh_button.place(x=127, y=226)
        direct_button.place(x=228, y=226)
        back_button.place(x=396, y=226)

    def in_server(self):
        for child in self.winfo_children():
            child.destroy()
        self.wm_title("CommuSocket")

        self.height = 427
        self.width = 237
        self.wm_minsize(width=self.height, height=self.width)
        self.wm_maxsize(width=self.height, height=self.width)

        self.messageVar = StringVar()

        def entry_callback(*args, **kwargs):
            self.sendButton.configure(state=NORMAL if self.messageVar.get() else DISABLED)

        self.chatbox = ScrolledText(self, width=48, height=10, state=DISABLED, bg="white", relief=FLAT, takefocus=0, highlightbackground="#7a7a7a", highlightthickness=1, highlightcolor="#7a7a7a")
        self.chatbox.place(x=10, y=10)
        
        self.chatbox.tag_config("connection", foreground="gray")
        self.chatbox.tag_config("author", foreground="black")
        self.chatbox.tag_config("message", foreground="#3e3e3e")
        
        self.entry = Entry(self, width=50, state=DISABLED, textvariable=self.messageVar, takefocus=0)
        self.entry.place(x=9, y=185)
        
        self.messageVar.trace_variable("w", entry_callback)

        self.sendButton = Button(self, text="Send", state=DISABLED, width=14, takefocus=0, command=self.send_message)
        self.sendButton.place(x=323, y=183)
        
        self.statusBar = TkLabel(self, text="1 Member(s)", bd=1, relief=SUNKEN, anchor=W)
        self.statusBar.pack(side=BOTTOM, fill=X)

if __name__ == "__main__":
    Interface()