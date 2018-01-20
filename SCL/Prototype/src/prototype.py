import socket
import RPi.GPIO


def print_hello_world():
    """
    Mock func
    
    :return: 
    """
    print("{}: HELLO MOTHAFUCKAS! ".format(str(socket.gethostname())))
    pass


class GPIO_Handler(object):

    def __init__(self):
        pass

    pass
