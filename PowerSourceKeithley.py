import pyvisa
import PowerSource


def parse_channel(channel):
    dict_channels = {1: 'OUT1', 2: 'OUT2', 3: 'OUT3'}
    return dict_channels[channel]


class PowerSourceKeithley(PowerSource):

    def __init__(self, num_of_channels, address):
        super(PowerSourceKeithley, self).__init__(num_of_channels, address)


    # overide those functions
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
