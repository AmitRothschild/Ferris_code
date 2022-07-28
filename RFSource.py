import pyvisa
from scipy.signal import freqs


class RFSource:
    def __init__(self, address):
        self.address = address
        self.instance = self.create_client(address)

    def set_frequency(self, frequency):
        self.instance.write(':FREQ %s GHZ;' % str(frequency))
        print('setting the frequency to ', frequency, ' GHZ')

    def set_power(self, power):
        self.instance.write(':POW %s;' % str(power))
        print('setting output power to ', power, ' dBm')

    def get_frequency(self):
        return float(self.instance.query('FREQ?').strip('\n'))/10**9

    def get_power(self):
        return self.instance.query('POW?')

    def get_visa_address(self):
        return self.address

    def get_identity(self):
        return self.instance.query('*IDN?').strip('\n')

    def enable_output(self, on):
        if on:
            self.instance.write(':OUTP ON;')
            print('turning on the RF source')
        else:
            self.instance.write(':OUTP OFF;')
            print('turning off the RF source')

    def create_client(self, address):
        rm = pyvisa.ResourceManager()
        print('initialized device')
        return rm.open_resource(address)

    def close_client(self):
        self.instance.close()
