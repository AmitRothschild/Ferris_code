import PowerSource


def parse_channel(channel):
    dict_channels = {1: '1', 2: '2', 3: '3'}
    return dict_channels[channel]


def check_if_valid_channel(channel_number, num_of_channels):
    if channel_number == 0 or channel_number >= num_of_channels:
        print('invalid channel')
        return False
    return True


class PowerSourceKeithley(PowerSource.PowerSource):

    def __init__(self, num_of_channels, address):
        super(PowerSourceKeithley, self).__init__(num_of_channels, address)

    def set_voltage(self, channel_number, voltage_value):
        if not check_if_valid_channel(channel_number, self.get_num_of_channels()):
            return
        print('Setting the voltage of channel ', channel_number, ' to ', voltage_value)
        channel = parse_channel(channel_number)
        self.instance.write('INST:NSEL ', channel)
        self.instance.write('VOLT ', str(voltage_value))

    def set_current(self, channel_number, current_value):
        if channel_number == 0 or channel_number > self.get_num_of_channels():
            print('invalid channel')
            return
        print('Setting the current of channel ', channel_number, ' to ', current_value)
        channel = parse_channel(channel_number)
        self.instance.write('INST:NSEL ', channel)
        self.instance.write('CURR ', str(current_value))

    def get_voltage(self, channel_number):
        if not check_if_valid_channel(channel_number, self.get_num_of_channels()):
            return
        channel = parse_channel(channel_number)
        self.instance.write('INST:NSEL ', channel)
        voltage = self.instance.query(':MEAS:VOLT?')
        print('measured voltage is ', voltage.strip('\n'))
        return float(voltage.strip('\n'))

    def get_current(self, channel_number):
        if not check_if_valid_channel(channel_number, self.get_num_of_channels()):
            return
        channel = parse_channel(channel_number)
        self.instance.write('INST:NSEL ', channel)
        current = self.instance.query(':MEAS:CURR?')
        print('measured voltage is ', current.strip('\n'))
        return float(current.strip('\n'))

    def enable_single_channel(self, channel_number, on):
        if not check_if_valid_channel(channel_number, self.get_num_of_channels()):
            return
        channel = parse_channel(channel_number)
        self.instance.write('INST:NSEL ', channel)
        if on:
            self.instance.write('CHAN:OUTP ON')
            print('turning on channel ', channel_number)
        else:
            self.instance.write('CHAN:OUTP OFF')
            print('turning off channel ', channel_number)
