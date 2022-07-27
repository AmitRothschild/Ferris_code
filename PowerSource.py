# import easy_scpi as scpi
import pyvisa
import visa
from pymeasure import instruments


def parse_channel(channel):
    dict_channels = {1: 'OUT1', 2: 'OUT2', 3: 'OUT3'}
    return dict_channels[channel]


class PowerSource:
    def __init__(self, num_of_channels, address):
        self.num_of_channels = num_of_channels
        self.address = address
        self.instance = self.create_client(address)

    def create_client(self, address):
        rm = pyvisa.ResourceManager()
        return rm.open_resource(address)

    def set_voltage(self, channel_number, voltage_value):
        if channel_number == 0 or channel_number > self.get_num_of_channels():
            print('invalid channel')
            return
        print('Setting the voltage of channel ', channel_number, ' to ', voltage_value)
        channel = parse_channel(channel_number)
        self.instance.write('INST:SEL ', channel)
        self.instance.write('VOLT ', str(voltage_value))

    def set_current(self, channel_number, current_value):
        if channel_number == 0 or channel_number > self.get_num_of_channels():
            print('invalid channel')
            return
        print('Setting the current of channel ', channel_number, ' to ', current_value)
        channel = parse_channel(channel_number)
        self.instance.write('INST:SEL ', channel)
        self.instance.write('CURR ', str(current_value))

    def get_num_of_channels(self):
        return self.num_of_channels

    def get_visa_address(self):
        return self.address

    def get_identity(self):
        return self.instance.query('*IDN?').strip('\n')

    # def enable_output(self, channel, on):
    #     ch = parse_channel(channel)
    #     if on:
    #         self.instance.write(':OUTP ' + ch + ',ON')
    #         print('turning on the power source')
    #     else:
    #         self.instance.write(':OUTP ' + ch + ',OFF')
    #         print('turning off the power source')

    def enable_output(self, on):
        if on:
            self.instance.write(':OUTP ON')
            print('turning on the power source')
        else:
            self.instance.write(':OUTP OFF')
            print('turning off the power source')

    def close_client(self):
        pass
