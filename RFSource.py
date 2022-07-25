import pyvisa


class RFSource(object):
    def __init__(self, address):
        self.address = address
        self.instance = self.create_client(address)

    def set_frequency(self):
        pass

    def set_power(self):
        pass

    def get_frequency(self):
        pass

    def get_power(self):
        pass

    def get_visa_address(self):
        return self.address

    def get_identity(self):
        return self.instance.query('*IDN?').strip('\n')

    def enable_output(self, on):
        if on:
            self.instance.write(':OUTP ON')
            print('turning on the RF source')
        else:
            self.instance.write(':OUTP OFF')
            print('turning off the RF source')

    def create_client(self, address):
        rm = pyvisa.ResourceManager()
        return rm.open_resource(address)

    def close_client(self):
        pass
