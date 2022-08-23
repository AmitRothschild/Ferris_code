import time
from pylablib.devices import Thorlabs
from PowerSourceKeysightFastMeas import PowerSourceFastMeas
from PowerSourceKeithley import PowerSourceKeithley
from RFSource import RFSource
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import math

matplotlib.use('Agg')



MM_TO_STEPS_RATIO = 34304
INIT_LOCATION = 20
END_LOCATION = 5
SPEED = 0.05

def location_to_magnetic_field(stage_location):
    """
    converts the stage location to magnetic field
    the fit is two exponents: a*exp(b*x) + c*exp(d*x)
    a = 3672, b = -0.4017, c = 1645, d = -0.1618
    :param stage_location: stage location in mm
    :return: magnetic field in Oe
    """
    a = 3672
    b = -0.4017
    c = 1645
    d = -0.1618
    return a * math.exp(b * stage_location) + c * math.exp(d * stage_location)

# rf_source = RFSource('USB0::0x03EB::0xAFFF::181-4396D0000-1246::0::INSTR')
# rf_source.enable_output(False)
# power_source = PowerSourceKeithley(3, 'GPIB2::1::INSTR')
# power_source.enable_output(False)
current_source = PowerSourceFastMeas(1, 'GPIB2::23::INSTR')
current_source.enable_output(False)
current_source.set_operation_mode(1)
current_source.set_voltage(6)
# time.sleep(15)
# print('started homing')
# with Thorlabs.KinesisMotor("27004822") as stage:
#     stage.home(force=True)
#     stage.wait_for_home()
#     print('homing complete')



time.sleep(2)
with Thorlabs.KinesisMotor("27004822") as stage:
    stage.setup_velocity(None, None, MM_TO_STEPS_RATIO)
    print('stage is moving to ', INIT_LOCATION)
    stage.move_to(INIT_LOCATION * MM_TO_STEPS_RATIO)
    while stage.is_moving():
        print('stage is moving...')
        time.sleep(0.5)
    print('stage arrived at final location ', stage.get_position() / MM_TO_STEPS_RATIO)

meas_lst = []
field = []




current_source.set_current(0.01)
current_source.enable_output(True)

speed_in_steps_per_sec = SPEED * MM_TO_STEPS_RATIO
with Thorlabs.KinesisMotor("27004822") as stage:
    stage.setup_velocity(None, None, speed_in_steps_per_sec)
    print('started the stage sweep move')
    stage.move_to(END_LOCATION * MM_TO_STEPS_RATIO)

with Thorlabs.KinesisMotor("27004822") as stage:
    while stage.get_position() / MM_TO_STEPS_RATIO > END_LOCATION:
        meas_lst.append(current_source.get_voltage()/current_source.get_current())
        field.append(location_to_magnetic_field(stage.get_position() / MM_TO_STEPS_RATIO))
        time.sleep(0.2)

current_source.enable_output(False)

plt.plot(field, meas_lst)
plt.savefig('try.png', format="png")
data = np.column_stack([field, meas_lst])
np.savetxt('data_list.txt', data, fmt=['%.8f', '%.8f'])



