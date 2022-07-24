# import zope.interface
import numpy as np
import pyvisa


class PowerSourceInterface:
    def __init__(self, num_of_channels, address):
        self.num_of_channels = num_of_channels
        self.address = address

    def create_client(self):
        pass

    def set_voltage(self, channel_number, voltage_value):
        if channel_number == 0 or channel_number > self.get_num_of_channels():
            print('invalid channel')
            return
        print('Setting the voltage to ' + voltage_value)


    def set_current(self, channel_number, current_value):
        if channel_number == 0 or channel_number > self.get_num_of_channels():
            print('invalid channel')
            return
        print('Setting the voltage to ' + current_value)


    def get_num_of_channels(self):
        return self.num_of_channels

    def get_visa_address(self):
        return self.address
