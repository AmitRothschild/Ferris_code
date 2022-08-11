import pyvisa


class MultiMeter:
    def __init__(self, address):
        self.address = address
        self.instance = self.create_client(address)

    def create_client(self, address):
        rm = pyvisa.ResourceManager()
        print('initialized device')
        # inst = rm.open_resource(address)
        # inst.write('SYSTem:REMote')
        return rm.open_resource(address)

    def get_identity(self):
        return self.instance.query('*IDN?').strip('\n')

    def get_voltage(self):
        return float(self.instance.query('MEAS:VOLT:DC? 0.5,0.001').strip('\n'))

    def close_client(self):
        self.instance.close()
