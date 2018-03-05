import socket
import tkinter as tk
import RPi.GPIO
from time import sleep


def run_gui():
    """
    Mock func
    
    :return: 
    """
    print("{}: HELLO MOTHAFUCKAS! ".format(str(socket.gethostname())))

    root = tk.Tk()
    app = Application(root)

    app.mainloop()

    print("Quiting...")
    sleep(1)

    pass


class Application(tk.Frame):

    def __init__(self, master=None):
        """
        Overload constructor
        
        :param master: 
        """
        super().__init__(master)
        self._master = master
        self.pack()

        # window
        self._window = tk.Toplevel(self)
        pad = 3
        g = "{0}x{1}+0+0".format(master.winfo_screenwidth()-pad, master.winfo_screenheight()-pad)
        self._window.geometry(g)
        self._window.overrideredirect(1)

        # buttons
        self._hi_button = None
        self._quit = None

        # creators
        self.create_widgets()
        pass

    def create_widgets(self):
        """
        Creates the widgets
        
        :return: 
        """

        self._hi_button = tk.Button(self._window)
        self._hi_button["text"] = "Hello World\n(click me)"
        self._hi_button["command"] = self.say_hi
        self._hi_button.pack(side="top")

        self._quit = tk.Button(self._window, text="QUIT", fg="red", command=self._master.destroy)
        self._quit.pack(side="bottom")

        pass

    def say_hi(self):
        """
        Method to execute on button pressed.
        
        :return: 
        """

        print("hi there, everyone!")
        pass

    pass


class GPIOHandler(object):

    def __init__(self):
        pass

    pass
