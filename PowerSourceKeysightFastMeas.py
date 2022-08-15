import PowerSource
import pyvisa


class PowerSourceFastMeas(PowerSource.PowerSource):

    def __init__(self, num_of_channels, address):
        super(PowerSourceFastMeas, self).__init__(num_of_channels, address)
        self.operation = ''

    def set_voltage(self, voltage_value):
        print('setting the voltage limit to ', str(voltage_value), ' Volts')
        if self.get_operation_mode() == 'voltage':
            self.instance.write('VOLT ', str(voltage_value))
        else:
            self.instance.write(':sens:volt:prot ', str(voltage_value))

    def set_current(self, current_value):
        print('setting the current limit to ', str(current_value), 'Amps')
        if self.get_operation_mode() == 'current':
            self.instance.write('CURR ', str(current_value))
        else:
            self.instance.write(':sens:curr:prot ', str(current_value))

    def get_voltage(self):
        return float(self.instance.query('MEAS:VOLT?').strip('\n'))

    def get_current(self):
        return float(self.instance.query('MEAS:CURR?').strip('\n'))

    def set_operation_mode(self, operation):
        if operation == 1:
            print('setting the power source as a current source')
            self.instance.write('FUNC:MODE curr')
            self.operation = 'current'
        else:
            print('setting the power source as a voltage source')
            self.instance.write('FUNC:MODE volt')
            self.operation = 'voltage'

    def get_operation_mode(self):
        return self.operation






