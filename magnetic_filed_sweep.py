from pylablib.devices import Thorlabs
import matplotlib.pyplot as plt
import time
from MultiMeter import MultiMeter
import numpy as np


MM_TO_STEPS_RATIO = 34304
speed = 0.025
meas_lst = []
location_lst = []
STOP_STAGE = 22
multimeter = MultiMeter('GPIB2::22::INSTR')


time.sleep(2)
with Thorlabs.KinesisMotor("27004822") as stage:
    stage.setup_velocity(None, None, MM_TO_STEPS_RATIO)
    print('stage is moving to ', 24)
    stage.move_to(24 * MM_TO_STEPS_RATIO)
    while stage.is_moving():
        print('stage is moving...')
        time.sleep(0.5)
    print('stage arrived at final location ', stage.get_position() / MM_TO_STEPS_RATIO)



speed_in_steps_per_sec = speed * MM_TO_STEPS_RATIO
with Thorlabs.KinesisMotor("27004822") as stage:
    stage.setup_velocity(None, None, speed_in_steps_per_sec)
    print('started the stage sweep move')
    stage.move_to(STOP_STAGE * MM_TO_STEPS_RATIO)

with Thorlabs.KinesisMotor("27004822") as stage:
    while stage.get_position() / MM_TO_STEPS_RATIO > STOP_STAGE:
        meas_lst.append(multimeter.get_voltage())
        location_lst.append(stage.get_position() / MM_TO_STEPS_RATIO)
        # time.sleep(0.05)

print('done')

plt.plot(location_lst, meas_lst)
plt.savefig('sweep.png', format="png")
data = np.column_stack([location_lst, meas_lst])
np.savetxt('sweep data.txt', data, fmt=['%.8f', '%.8f'])



