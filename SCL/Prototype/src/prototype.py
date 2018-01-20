import os


def print_hello_world():
    print("{}: HELLO MOTHAFUCKAS! ".format(str(os.environ.get("COMPUTERNAME"))))
    pass
