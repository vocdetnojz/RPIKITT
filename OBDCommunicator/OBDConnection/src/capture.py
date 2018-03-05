#!/usr/bin/env python

from OBDCommunicator.OBDConnection import obd_io
from OBDCommunicator.OBDConnection import obd_sensors
import serial
# import platform
# import obd_sensors
from datetime import datetime
import time


# TODO: this file has to be refactored really hard!!!


def scan_serial():
    """scan for available ports. return a list of serial names"""
    available = []
    # Enable Bluetooth connection
    for i in range(10):
        try:
            s = serial.Serial("/dev/rfcomm" + str(i))
            available.append((str(s.port)))
            s.close()  # explicit close 'cause of delayed GC in java
        except serial.SerialException:
            pass
            # Enable USB connection
    for i in range(256):
        try:
            s = serial.Serial("/dev/ttyUSB" + str(i))
            available.append(s.portstr)
            s.close()  # explicit close 'cause of delayed GC in java
        except serial.SerialException:
            pass
            # Enable obdsim
            # for i in range(256):
            # try: #scan Simulator
            # s = serial.Serial("/dev/pts/"+str(i))
            # available.append(s.portstr)
            # s.close()   # explicit close 'cause of delayed GC in java
            # except serial.SerialException:
            # pass

    return available


class ObdCapture(object):

    def __init__(self):
        self._supportedSensorList = []
        self._port = None
        localtime = time.localtime(time.time())

    def connect(self):
        portnames = scan_serial()
        print(portnames)
        for port in portnames:
            self._port = obd_io.OBDPort(port, None, 2, 2)
            if self._port.State == 0:
                self._port.close()
                self._port = None
            else:
                break

        if self._port:
            print("Connected to " + self._port.port.name)

    def is_connected(self):
        return self._port

    def get_supported_sensor_list(self):
        return self._supportedSensorList

    def capture_data(self):
        text = ""
        # Find supported sensors - by getting PIDs from OBD
        # its a string of binary 01010101010101
        # 1 means the sensor is supported
        supp = self._port.sensor(0)[1]
        self._supportedSensorList = []
        unsupported_sensor_list = []

        # loop through PIDs binary
        for i in range(0, len(supp)):
            if supp[i] == "1":
                # store index of sensor and sensor object
                self._supportedSensorList.append([i + 1, obd_sensors.SENSORS[i + 1]])
            else:
                unsupported_sensor_list.append([i + 1, obd_sensors.SENSORS[i + 1]])

        for supportedSensor in self._supportedSensorList:
            text += "supported sensor index = " + str(supportedSensor[0]) + " " + str(supportedSensor[1].shortname) + "\n"

        time.sleep(3)

        if self._port is None:
            return None

        # Loop until Ctrl C is pressed
        localtime = datetime.now()
        current_time = str(localtime.hour) + ":" + str(localtime.minute) + ":" + str(localtime.second) + "." + str(localtime.microsecond)
        # log_string = current_time + "\n"
        text = current_time + "\n"
        results = {}
        for supportedSensor in self._supportedSensorList:
            sensor_index = supportedSensor[0]
            (name, value, unit) = self._port.sensor(sensor_index)
            text += name + " = " + str(value) + " " + str(unit) + "\n"

        return text


if __name__ == "__main__":

    o = ObdCapture()
    o.connect()
    time.sleep(3)
    # if not o.is_connected():
    #     print("Not connected")
    # else:
    #     o.capture_data()
    while not o.is_connected():
        print("Not connected, retrying...")
        o.connect()
        time.sleep(3)
    o.capture_data()
