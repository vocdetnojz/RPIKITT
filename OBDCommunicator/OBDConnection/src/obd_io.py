#!/usr/bin/env python

###########################################################################
# odb_io.py
#
# Copyright 2004 Donour Sizemore (donour@uchicago.edu)
# Copyright 2009 Secons Ltd. (www.obdtester.com)
#
# This file is part of pyOBD.
#
# pyOBD is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# pyOBD is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyOBD; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
###########################################################################

import serial
import time
from OBDCommunicator.OBDConnection import obd_sensors

GET_DTC_COMMAND = "03"
CLEAR_DTC_COMMAND = "04"
GET_FREEZE_DTC_COMMAND = "07"


# TODO: this file has to be refactored really hard!!!


def decrypt_dtc_code(code):
    """Returns the 5-digit DTC code from hex encoding"""
    dtc = []
    current = code
    for i in range(0, 3):
        if len(current) < 4:
            raise "Tried to decode bad DTC: %s" % code
        tc = obd_sensors.hex_to_int(current[0])  # type code
        tc = tc >> 2
        if tc == 0:
            t = "P"
        elif tc == 1:
            t = "C"
        elif tc == 2:
            t = "B"
        elif tc == 3:
            t = "U"
        else:
            raise tc
        dig1 = str(obd_sensors.hex_to_int(current[0]) & 3)
        dig2 = str(obd_sensors.hex_to_int(current[1]))
        dig3 = str(obd_sensors.hex_to_int(current[2]))
        dig4 = str(obd_sensors.hex_to_int(current[3]))
        dtc.append(t+dig1+dig2+dig3+dig4)
        current = current[4:]
    return dtc


class OBDPort:
    """
        OBDPort abstracts all communication with OBD-II device.
    """

    def __init__(self, port_num, _notify_window, ser_timeout, reconnect_attempts):
        """
        Initializes port by resetting device and gettings supported PIDs. 
        
        :param port_num: 
        :param _notify_window: 
        :param ser_timeout: 
        :param reconnect_attempts: 
        """

        # These should really be set by the user.
        baud = 38400
        databits = 8
        par = serial.PARITY_NONE  # parity
        sb = 1  # stop bits
        to = ser_timeout
        self._elm_ver = "Unknown"
        self._state = 1  # state SERIAL is 1 connected, 0 disconnected (connection failed)
        self._port = ""
        
        self._notify_window = _notify_window
        print("Opening interface (serial port)")

        try:
            self._port = serial.Serial(port_num, baud, parity=par, stopbits=sb, bytesize=databits, timeout=to)
            
        except serial.SerialException as e:
            print(e)
            self._state = 0

        print("Interface successfully " + self._port.portstr + " opened")
        print("Connecting to ECU...")
        
        try:
            self.send_command("atz")   # initialize
            time.sleep(1)
        except serial.SerialException:
            self._state = 0

        self._elm_ver = self.get_result()
        if not self._elm_ver:
            self._state = 0

        print("atz response:" + self._elm_ver)
        self.send_command("ate0")  # echo off
        print("ate0 response:" + self.get_result())
        self.send_command("0100")
        ready = self.get_result()
        
        if ready is None:
            self._state = 0

        print("0100 response:" + ready)

    def close(self):
        """
        Resets device and closes all associated filehandles
        
        :return: 
        """
        
        if self._port is not None and self._state == 1:
            self.send_command("atz")
            self._port.close()
        
        self._port = None
        self._elm_ver = "Unknown"

    def send_command(self, cmd):
        """
        Internal use only: not a public interface
        
        :param cmd: 
        :return: 
        """
        if self._port:
            self._port.flushOutput()
            self._port.flushInput()
            for c in cmd:
                self._port.write(c)
            self._port.write("\r\n")
            print("Send command:" + cmd)

    @staticmethod
    def interpret_result(code):
        """
        Internal use only: not a public interface
        
        :param code: 
        :return: 
        """
        # Code will be the string returned from the device.
        # It should look something like this:
        # '41 11 0 0\r\r'
        
        # 9 seems to be the length of the shortest valid response
        if len(code) < 7:
            # raise Exception("BogusCode")
            print("boguscode?" + code)
        
        # get the first thing returned, echo should be off
        code = code.split("\r")
        code = code[0]
        
        # remove whitespace
        code = code.replace(" ", "")
        
        # cables can behave differently
        if code[:6] == "NODATA":  # there is no such sensor
            return "NODATA"
            
        # first 4 characters are code from ELM
        code = code[4:]
        return code
    
    def get_result(self):
        """
        Internal use only: not a public interface
        
        :return: 
        """
        # time.sleep(0.01)
        repeat_count = 0
        if self._port is not None:
            buffer = ""
            while 1:
                c = self._port.read(1)
                if len(c) == 0:
                    if repeat_count == 5:
                        break
                    print("Got nothing\n")
                    repeat_count = repeat_count + 1
                    continue
                    
                if c == '\r':
                    continue
                    
                if c == ">":
                    break
                    
                if buffer != "" or c != ">":  # if something is in buffer, add everything
                    buffer = buffer + c
                    
            print("Get result:" + buffer)
            if buffer == "":
                return None
            return buffer
        else:
            print("NO self.port!")
        return None

    # get sensor value from command
    def get_sensor_value(self, sensor):
        """
        Internal use only: not a public interface
        
        :param sensor: 
        :return: 
        """
        cmd = sensor.cmd
        self.send_command(cmd)
        data = self.get_result()
        
        if data:
            data = self.interpret_result(data)
            if data != "NODATA":
                data = sensor.value(data)
        else:
            return "NORESPONSE"
            
        return data

    # return string of sensor name and value from sensor index
    def sensor(self , sensor_index):
        """
        Returns 3-tuple of given sensors. 3-tuple consists of
        (Sensor Name (string), Sensor Value (string), Sensor Unit (string) ) 
        
        :param sensor_index: 
        :return: 
        """
        sensor = obd_sensors.SENSORS[sensor_index]
        r = self.get_sensor_value(sensor)
        return sensor.name, r, sensor.unit

    @staticmethod
    def sensor_names():
        """Internal use only: not a public interface"""
        names = []
        for s in obd_sensors.SENSORS:
            names.append(s.name)
        return names
        
    def get_tests_mil(self):
        status_text = ["Unsupported", "Supported - Completed", "Unsupported", "Supported - Incompleted"]
        
        status_res = self.sensor(1)[1]  # GET values
        status_trans = list()  # translate values to text
        
        status_trans.append(str(status_res[0]))  # DTCs
        
        if status_res[1] == 0:  # MIL
            status_trans.append("Off")
        else:
            status_trans.append("On")
            
        for i in range(2, len(status_res)):  # Tests
            status_trans.append(status_text[status_res[i]])

        return status_trans
        
    # fixme: j1979 specifies that the program should poll until the number
    # of returned DTCs matches the number indicated by a call to PID 01
    def get_dtc(self):
        """Returns a list of all pending DTC codes. Each element consists of
        a 2-tuple: (DTC code (string), Code description (string) )"""
        dtc_letters = ["P", "C", "B", "U"]
        r = self.sensor(1)[1]  # data
        dtc_number = r[0]
        mil = r[1]
        d_t_c_codes = []
        
        print("Number of stored DTC:" + str(dtc_number) + " MIL: " + str(mil))
        # get all DTC, 3 per message response
        for i in range(0, int((int(dtc_number)+2)/3)):
            self.send_command(GET_DTC_COMMAND)
            res = self.get_result()
            print("DTC result:" + res)
            for j in range(0, 3):
                val1 = obd_sensors.hex_to_int(res[3+j*6:5+j*6])
                val2 = obd_sensors.hex_to_int(res[6+j*6:8+j*6])  # get DTC codes from response (3 DTC each 2 bytes)
                val = (val1 << 8) + val2  # DTC val as int
                
                if val == 0:  # skip fill of last packet
                    break
                   
                d_t_c_str = dtc_letters[(val & 0xC000) > 14]
                d_t_c_str += str((val & 0x3000) >> 12)
                d_t_c_str += str((val & 0x0f00) >> 8)
                d_t_c_str += str((val & 0x00f0) >> 4)
                d_t_c_str += str(val & 0x000f)

                d_t_c_codes.append(["Active", d_t_c_str])
        
        # read mode 7
        self.send_command(GET_FREEZE_DTC_COMMAND)
        res = self.get_result()
        
        if res[:7] == "NODATA":  # no freeze frame
            return d_t_c_codes
        
        print("DTC freeze result:" + res)
        for i in range(0, 3):
            val1 = obd_sensors.hex_to_int(res[3+i*6:5+i*6])
            val2 = obd_sensors.hex_to_int(res[6+i*6:8+i*6])  # get DTC codes from response (3 DTC each 2 bytes)
            val = (val1 << 8) + val2  # DTC val as int
                
            if val == 0:  # skip fill of last packet
                break
                   
            d_t_c_str = dtc_letters[(val & 0xC000) > 14]
            d_t_c_str += str((val & 0x3000) >> 12)
            d_t_c_str += str((val & 0x0f00) >> 8)
            d_t_c_str += str((val & 0x00f0) >> 4)
            d_t_c_str += str(val & 0x000f)
            d_t_c_codes.append(["Passive", d_t_c_str])
            
        return d_t_c_codes
            
    def clear_dtc(self):
        """Clears all DTCs and freeze frame data"""
        self.send_command(CLEAR_DTC_COMMAND)     
        r = self.get_result()
        return r
    
    def log(self, sensor_index, filename): 
        file = open(filename, "w")
        start_time = time.time() 
        if file:
            data = self.sensor(sensor_index)
            file.write("%s     \t%s(%s)\n" % ("Time", data[0].strip(), data[2]))
            while 1:
                now = time.time()
                data = self.sensor(sensor_index)
                line = "%.6f,\t%s\n" % (now - start_time, data[1])
                file.write(line)
                file.flush()
