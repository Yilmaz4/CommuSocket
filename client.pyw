import socket, threading, multipledispatch, functools, inspect, os, signal

from typing import final, Optional, Callable, Literal

from tkinter import *
from tkinter import Label as TkLabel
from tkinter.ttk import *
from tkinter import messagebox

class selfinjected(object):
    def __init__(self, name: str):
        self.name = name
    def __call__(self, function: Callable):
        function.__globals__[self.name] = function
        return function
    
@final
class Utilities(object):
    """
    Utilities class for some useful methods that may help me in the future
    """
    def __init__(self, root: Tk):
        self.root = root
        
    @selfinjected("self")
    def __init_subclass__(cls: type, *args, **kwargs):
        raise TypeError(f"Class \"{Utilities.get_master_class(self).__name__}\" cannot be subclassed.") # type: ignore

    @classmethod
    def get_master_class(utils, meth: Callable) -> type:
        """
        Returns the class of the given method
        """
        if isinstance(meth, functools.partial):
            return utils.get_master_class(meth.func)
        if inspect.ismethod(meth) or (inspect.isbuiltin(meth) and getattr(meth, '__self__', None) is not None and getattr(meth.__self__, '__class__', None)):
            for cls in inspect.getmro(meth.__self__.__class__):
                if meth.__name__ in cls.__dict__:
                    return cls
            meth: Callable = getattr(meth, '__func__', meth)
        if inspect.isfunction(meth):
            cls: type = getattr(inspect.getmodule(meth),
                        meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0],
                        None)
            if isinstance(cls, type):
                return cls
        return getattr(meth, '__objclass__', None)
    
    @classmethod
    def get_inner_classes(utils, cls: type) -> list[type]:
        """
        Returns a list of all inner classes of the given class
        """
        return [cls_attr for cls_attr in cls.__dict__.values() if inspect.isclass(cls_attr)]

@final
class ToolTip(object):
    """
    A class for creating tooltips that appear on hover
    """
    def __init__(self, widget: Widget, tooltip: str, interval: int = 1000, length: int = 400):
        self.widget = widget
        self.interval = interval
        self.wraplength = length
        self.text = tooltip
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

        self.speed = 10
    
    @selfinjected("self")
    def __init_subclass__(cls: type, *args, **kwargs):
        raise TypeError(f"Class \"{Utilities.get_master_class(self).__name__}\" cannot be subclassed.") # type: ignore

    def enter(self, event=None):
        self.schedule()
    def leave(self, event=None):
        self.unschedule()
        self.hidetip()
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.interval, self.showtip)
    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        # Get the mouse position and determine the screen coordinates to show the tooltip
        x = root.winfo_pointerx() + 12
        y = root.winfo_pointery() + 16

        # Create a Toplevel because we can't just show a label out of nowhere in the main window with fade-in & fade-away animations
        self.tw = Toplevel(self.widget)
        self.tw.attributes("-alpha", 0)

        # Configure the tooltip for visuality
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tw, text=self.text,
            justify='left', background="#ffffff",
            foreground="#6f6f6f", relief='solid',
            borderwidth=1, wraplength=self.wraplength)
        label.pack(ipadx=1)

        def fade_in():
            if not self.widget is root.winfo_containing(root.winfo_pointerx(), root.winfo_pointery()):
                # If mouse is no longer on the widget, destroy the tooltip and unschedule the fade_in
                self.tw.destroy()
                return
            alpha = self.tw.attributes("-alpha")
            if alpha != 1:
                # Increase the transparency by 0.1 until it is fully visible
                alpha += .1
                self.tw.attributes("-alpha", alpha)
                # Call this function again in 10 milliseconds (value of self.speed attribute)
                self.tw.after(self.speed, fade_in)
            else:
                return
        fade_in()

    def hidetip(self):
        if self.tw:
            # If the tooltip is still a thing (i.e. it has not been destroyed unexpectedly), start fading it away
            def fade_away():
                if self.widget is root.winfo_containing(root.winfo_pointerx(), root.winfo_pointery()):
                    self.tw.destroy()
                    return
                try:
                    alpha = self.tw.attributes("-alpha")
                except TclError:
                    return
                if alpha != 0:
                    # Decrease the transparency by 0.1 until it is fully invisible
                    alpha -= .1
                    self.tw.attributes("-alpha", alpha)
                    # Call this function again in 10 milliseconds (value of self.speed attribute)
                    self.tw.after(self.speed, fade_away)
                else:
                    self.tw.destroy()
            fade_away()

@final
class ScrolledText(Text):
    def __init__(self, master: Tk | Frame | LabelFrame, tooltip: Optional[str] = None, *args, **kwargs):
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

        # Create the tooltip object for the widget if a string for tooltip was specified (rather than None)
        if tooltip is not None:
            self.toolTip = ToolTip(widget=self, tooltip=tooltip)
            
    @selfinjected("self")
    def __init_subclass__(cls: type, *args, **kwargs):
        raise TypeError(f"Class \"{Utilities.get_master_class(self).__name__}\" cannot be subclassed.") # type: ignore

    @multipledispatch.dispatch(str)
    def replace(self, chars: str):
        """
        Method to replace the text in the widget entirely with the given string
        """
        old_val = self["state"]
        self.configure(state=NORMAL)
        self.delete("1.0", END)
        self.insert("1.0", chars)
        self.configure(state=old_val)

    @multipledispatch.dispatch(str, str, str)
    def replace(self, chars: str, start_index: str, end_index: str):
        """
        Text class' original replace method in case the user (me) wants to replace a range of text
        """
        self.tk.call(self._w, 'replace', start_index, end_index, chars)

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

@final
class Text(Text):
    def __init__(self, master: Tk | Frame | LabelFrame, tooltip: Optional[str] = None, *args, **kwargs):
        try:
            self._textvariable = kwargs.pop("textvariable")
        except KeyError:
            self._textvariable = None

        super().__init__(master, *args, **kwargs)

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
        '''.format(widget=str(self)))
        self.bind("<<Change>>", self._on_widget_change)

        if self._textvariable is not None:
            self._textvariable.trace("wu", self._on_var_change)
        
        # Create the tooltip object for the widget if a string for tooltip was specified (rather than None)
        if tooltip is not None:
            self.toolTip = ToolTip(widget=self, tooltip=tooltip)

    @selfinjected("self")
    def __init_subclass__(cls: type, *args, **kwargs):
        raise TypeError(f"Class \"{Utilities.get_master_class(self).__name__}\" cannot be subclassed.") # type: ignore

    @multipledispatch.dispatch(str)
    def replace(self, chars: str):
        """
        Method to replace the text in the widget entirely with the given string
        """
        old_val = self["state"]
        self.configure(state=NORMAL)
        self.delete("1.0", END)
        self.insert("1.0", chars)
        self.configure(state=old_val)

    @multipledispatch.dispatch(str, str, str)
    def replace(self, chars: str, start_index: str, end_index: str):
        """
        Text class' original replace method in case the user (me) wants to replace a range of text
        """
        self.tk.call(self._w, 'replace', start_index, end_index, chars)

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

class Notebook(Notebook):
    def __init__(self, master: Tk | Frame | LabelFrame, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.bind("<<NotebookTabChanged>>", lambda _: self.on_tab_change())
        self.__history: Optional[list] = list()

    @property
    def last_tab(self) -> Optional[int]:
        """
        Property to get the index of the last tab that was selected in case an
        error occures while switching to a tab that downloads data from web and
        the program must return to the last tab
        """
        try:
            # Try to get the lastly indexed element from the history
            return self.__history[-1]
        except IndexError:
            if len(self.__history):
                return self.__history[0]
            else:
                return None
            
class Widget(Widget):
    """
    Base-class for all the Tkinter widgets except Text and ScrolledText widgets in order to implement tooltips easily
    """
    def __init__(self, master: Tk | Frame | LabelFrame, tooltip: Optional[str] = None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        if tooltip is not None:
            self.toolTip = ToolTip(widget=self, tooltip=tooltip)

# Multiply inherit all the widgets from the Widget class and the original Tkinter widgets in order to add tooltips to them

@final
class Entry(Widget, Entry):
    @selfinjected("self")
    def __init_subclass__(cls: type, *args, **kwargs):
        raise TypeError(f"Class \"{Utilities.get_master_class(self).__name__}\" cannot be subclassed.") # type: ignore

    def replace(self, string: str):
        old_val = self["state"]
        self.configure(state=NORMAL)
        self.delete(0, END)
        self.insert(0, string)
        self.configure(state=old_val)

    def clear(self):
        old_val = self["state"]
        self.configure(state=NORMAL)
        self.delete(0, END)
        self.configure(state=old_val)

@final
class Button(Widget, Button): ...

@final
class Label(Widget, Label): ...

@final
class Radiobutton(Widget, Radiobutton): ...

@final
class Checkbutton(Widget, Checkbutton): ...

class Interface(Tk):
    def __init__(self, server: bool):
        super().__init__()
        self.server = server
        self.wm_withdraw()
        self.__initialize_protocols()
        self.__initialize_variables()
        
        self.__client = None
        
        self.wm_geometry("427x250")
        self.wm_minsize(width=427, height=250)
        self.wm_maxsize(width=427, height=250)
        self.wm_title("Server" if server else "Client")
        self.wm_resizable(False, False)
        
        self.chatbox = ScrolledText(self, width=48, height=10, state=DISABLED, bg="white", relief=FLAT, takefocus=0, highlightbackground="#7a7a7a", highlightthickness=1, highlightcolor="#7a7a7a")
        self.chatbox.place(x=10, y=10)
        
        self.chatbox.tag_config("connection", foreground="gray")
        self.chatbox.tag_config("author", foreground="black")
        self.chatbox.tag_config("message", foreground="#3e3e3e")
        
        self.entry = Entry(self, width=50, state=DISABLED, textvariable=self.messageVar, takefocus=0)
        self.entry.place(x=9, y=185)
        
        self.messageVar.trace_variable("w", self.entry_callback)

        self.sendButton = Button(self, text="Send", state=DISABLED, width=14, takefocus=0, command=self.send_message)
        self.sendButton.place(x=323, y=183)
        
        self.statusBar = TkLabel(self, text="Status: Not connected", bd=1, relief=SUNKEN, anchor=W)
        self.statusBar.pack(side=BOTTOM, fill=X)
        
        menubar = Menu(self, background='#ff8000', foreground='black', activebackground='white', activeforeground='black')
        file = Menu(menubar, tearoff=0)
        file.add_command(label="Close connection")
        file.add_separator()
        file.add_command(label="Change username", command=self.change_username)
        file.add_separator()
        file.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file)

        edit = Menu(menubar, tearoff=0)
        edit.add_command(label="Undo")
        edit.add_separator()
        edit.add_command(label="Cut")
        edit.add_command(label="Copy")
        edit.add_command(label="Paste")
        menubar.add_cascade(label="Preferences", menu=edit)

        help = Menu(menubar, tearoff=0)
        help.add_command(label="About")
        menubar.add_cascade(label="Help", menu=help)
            
        self.config(menu=menubar)

        self.bind("<Return>", lambda *args, **kwargs: self.send_message())
        
        
        
    @property
    def client(self) -> socket.socket:
        return self.__client
    
    @client.setter
    def client(self, value: socket.socket):
        self.sendButton.configure(state=NORMAL if not self.server else DISABLED)
        self.entry.configure(state=NORMAL if not self.server else DISABLED)
        self.__client = value
        
    def mainloop(self):
        self.wm_deiconify()
        super().mainloop()
        
    def entry_callback(self, *args, **kwargs):
        print("hi")
        if self.messageVar.get().startswith("!&registername|") or not self.messageVar.get():
            self.sendButton.configure(state=DISABLED)
        else:
            self.sendButton.configure(state=NORMAL)
        
    def send_message(self):
        self.client.send(self.entry.get().encode("utf-8"))
        self.chatbox.configure(state=NORMAL)
        self.chatbox.insert(END, f"{self.name if hasattr(self, 'name') and self.name else 'You'}: ", "author")
        self.chatbox.insert(END, f"{self.entry.get()}\n", "message")
        self.chatbox.configure(state=DISABLED)
        self.entry.delete(0, END)
        
    def change_username(self):
        root = Toplevel(self)
        root.wm_geometry("283x73")
        root.wm_minsize(width=283, height=73)
        root.wm_maxsize(width=283, height=73)
        
        name_label = Label(root, text="Nickname:")
        name_entry = Entry(root, width=18)
        
        connectButton = Button(root, text="Change", width=30, takefocus=0, command=lambda: self.client.send(b"!&registername|" + name_entry.get().encode("utf-8")))
        backButton = Button(root, text="Cancel", width=9, takefocus=0, command=self.menu)
        
        name_label.place(x=10, y=10)
        name_entry.place(x=75, y=8)
        
        connectButton.place(x=10, y=37)
        backButton.place(x=208, y=37)
        
    def __initialize_protocols(self):
        self.protocol("WM_DELETE_WINDOW", lambda: os.kill(os.getpid(), signal.SIGTERM))
    def __initialize_variables(self):
        self.messageVar = StringVar()

class Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.names: dict[str, str] = {}
        
        self.input = Tk()
        self.input.wm_geometry("283x113")
        self.input.wm_title("YCT")
        self.input.wm_resizable(False, False)
        self.input.wm_minsize(width=283, height=113)
        self.input.wm_maxsize(width=283, height=113)
        
        self.menu()
        
        self.input.protocol("WM_DELETE_WINDOW", lambda: exit(1))
        
        self.input.mainloop()
    
    def menu(self):
        for child in self.input.winfo_children():
            child.destroy()
        self.input.wm_geometry("283x113")
        self.input.wm_minsize(width=283, height=113)
        self.input.wm_maxsize(width=283, height=113)

        optionFrame = Frame(self.input)
        
        host_button = Button(optionFrame, text="Host", width=16, takefocus=0, command=self.host)
        conn_button = Button(optionFrame, text="Connect", width=16, takefocus=0, command=self.connect)
        
        host_button.grid(row=0, column=0, pady=2)
        conn_button.grid(row=1, column=0, pady=2)
        
        optionFrame.place(relx=0.5, rely=0.5, anchor=CENTER)

    def host(self):
        for child in self.input.winfo_children():
            child.destroy()
            
        self.input.wm_geometry("283x73")
        self.input.wm_minsize(width=283, height=73)
        self.input.wm_maxsize(width=283, height=73)
        
        name_label = Label(self.input, text="Nickname:")
        name_entry = Entry(self.input, width=18)
        
        port_label = Label(self.input, text="Port:")
        port_entry = Entry(self.input, width=5, font=("Consolas", 9))
        
        def host():
            try:
                self.port = int(port_entry.get())
            except:
                messagebox.showerror("Invalid port number", "A port number can only be a number from 0 to 65535.")
                return
            self.sock.bind(('192.168.0.100', self.port))
            self.root = Interface(server=True)
            self.root.server = self
            self.root.client = self.sock
            if name_entry.get():
                self.root.name = name_entry.get()
            self.input.destroy()
            threading.Thread(target = self.listen_server).start()
            self.root.mainloop()
        
        connectButton = Button(self.input, text="Host", width=30, takefocus=0, command=host)
        backButton = Button(self.input, text="Back", width=9, takefocus=0, command=self.menu)
        
        name_label.place(x=10, y=10)
        name_entry.place(x=75, y=8)
        
        port_label.place(x=196, y=10)
        port_entry.place(x=230, y=8)
        
        connectButton.place(x=10, y=37)
        backButton.place(x=208, y=37)

    def connect(self):
        for child in self.input.winfo_children():
            child.destroy()
        self.input.wm_geometry("283x113")
        self.input.wm_minsize(width=283, height=113)
        self.input.wm_maxsize(width=283, height=113)

        ip_label = Label(self.input, text="IP Address:")
        ip_entry = Entry(self.input, width=15, font=("Consolas", 9))
        port_label = Label(self.input, text="Port:")
        port_entry = Entry(self.input, width=5, font=("Consolas", 9))
        
        seperator = Separator(self.input, orient=HORIZONTAL)
        
        name_label = Label(self.input, text="Nickname:")
        name_entry = Entry(self.input, width=32)
        
        def connect(*args, **kwargs):
            if not all([
                block.isdigit() for block in ip_entry.get().split('.')
            ]) or len(ip_entry.get().split('.')) != 4 or any([
                int(block) > 255 for block in ip_entry.get().split('.')
            ]):
                messagebox.showerror("Invalid IP address", "An IP address must be in the format x.x.x.x where x is a number between 0 and 255.")
                return
            self.ip = ip_entry.get()
            try:
                self.port = int(port_entry.get())
            except:
                messagebox.showerror("Invalid port number", "A port number can only be a number from 0 to 65535.")
                return
            if name_entry.get():
                self.name = name_entry.get()
            try:
                self.sock.connect((self.ip, self.port))
            except ConnectionRefusedError:
                messagebox.showerror("Target unreachable", "The person you're trying to contact is currently unreachable. Either enter another IP address or port number, or try again later.")
            else:
                self.root = Interface(server=False)
                self.root.name = name_entry.get()
                self.root.server = self
                self.root.client = self.sock
                self.input.destroy()
                if hasattr(self, 'name') and self.name:
                    self.sock.send(b"!&registername|" + self.name.encode("utf-8"))
                threading.Thread(target = self.listen_client).start()
                self.root.mainloop()
        
        connectButton = Button(self.input, text="Connect", width=30, takefocus=0, command=connect)
        backButton = Button(self.input, text="Back", width=9, takefocus=0, command=self.menu)
        
        self.input.bind("<Return>", connect)
        
        ip_label.place(x=10, y=10)
        ip_entry.place(x=77, y=8)
        port_label.place(x=196, y=10)
        port_entry.place(x=230, y=8)
        seperator.place(x=12, y=37, width=259)
        name_label.place(x=10, y=49)
        name_entry.place(x=73, y=47)
        connectButton.place(x=10, y=77)
        backButton.place(x=208, y=77)

    def listen_client(self) -> Optional[bool]:
        self.root.entry.configure(state=NORMAL)
        self.root.sendButton.configure(state=NORMAL)
        self.root.statusBar.configure(text="Status: Connected to " + self.names.get(':'.join([self.ip, str(self.port)]), ':'.join([self.ip, str(self.port)])))
        self.root.chatbox.configure(state=NORMAL)
        self.root.chatbox.insert(END, f"Connected to {self.names.get(':'.join([self.ip, str(self.port)]), ':'.join([self.ip, str(self.port)]))}.\n", "connection")
        self.root.chatbox.configure(state=DISABLED)
        while True:
            try:
                data = self.sock.recv(1024)
            except ConnectionResetError:
                self.root.entry.configure(state=DISABLED)
                self.root.sendButton.configure(state=DISABLED)
                self.root.statusBar.configure(text="Status: Not connected")
                self.root.chatbox.configure(state=NORMAL)
                self.root.chatbox.insert(END, f"Connection to {self.names.get(':'.join([self.ip, str(self.port)]), ':'.join([self.ip, str(self.port)]))} has been lost.\n", "connection")
                self.root.chatbox.configure(state=DISABLED)
                return
            if data.startswith(b"!&registername|"):
                self.names[':'.join([self.ip, str(self.port)])] = data.split(b"|")[1].decode("utf-8")
                continue
            if data:
                self.root.chatbox.configure(state=NORMAL)
                self.root.chatbox.insert(END, f"{self.names[':'.join([self.ip, str(self.port)])] if ':'.join([self.ip, str(self.port)]) in self.names else ':'.join([self.ip, str(self.port)])}: ", "author")
                self.root.chatbox.insert(END, f"{data.decode('utf-8')}\n", "message")
                self.root.chatbox.configure(state=DISABLED)
            else:
                pass
            
    def listen_server(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            self.root.client = client
            client.settimeout(60)
            threading.Thread(target=self.listenToClient, args=(client, address)).start()

    def listenToClient(self, client: socket.socket, address: tuple[str, int]) -> Optional[bool]:
        self.root.entry.configure(state=NORMAL)
        self.root.sendButton.configure(state=NORMAL)
        self.root.statusBar.configure(text="Status: Connected to " + self.names.get(':'.join([address[0], str(address[1])]), ':'.join([address[0], str(address[1])])))
        self.root.chatbox.configure(state=NORMAL)
        self.root.chatbox.insert(END, f"Connected to {self.names.get(':'.join([address[0], str(address[1])]), ':'.join([address[0], str(address[1])]))}.\n", "connection")
        self.root.chatbox.configure(state=DISABLED)
        if hasattr(self.root, 'name') and self.root.name:
            client.send(b"!&registername|" + self.root.name.encode("utf-8"))
        while True:
            try:
                data = client.recv(1024)
            except TimeoutError:
                continue
            except ConnectionResetError:
                self.root.entry.configure(state=DISABLED)
                self.root.sendButton.configure(state=DISABLED)
                self.root.statusBar.configure(text="Status: Not connected")
                self.root.chatbox.configure(state=NORMAL)
                self.root.chatbox.insert(END, f"Connection to {self.names.get(':'.join([address[0], str(address[1])]), ':'.join([address[0], str(address[1])]))} has been lost.\n", "connection")
                self.root.chatbox.configure(state=DISABLED)
                return
            if data:
                if data.startswith(b"!&registername|"):
                    self.names[':'.join([address[0], str(address[1])])] = data.split(b"|")[1].decode("utf-8")
                    continue
                self.root.chatbox.configure(state=NORMAL)
                self.root.chatbox.insert(END, f"{self.names[':'.join([address[0], str(address[1])])] if ':'.join([address[0], str(address[1])]) in self.names else ':'.join([address[0], str(address[1])])}: ", "author")
                self.root.chatbox.insert(END, f"{data.decode('utf-8')}\n", "message")
                self.root.chatbox.configure(state=DISABLED)
            else:
                pass

if __name__ == "__main__":
    server = Server()