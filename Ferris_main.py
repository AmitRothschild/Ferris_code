# Ferris FMR main
import sys
from threading import Thread
import logging
import time
import pandas as pd
import numpy as np
from pylablib.devices import Thorlabs
from pymeasure import instruments
from PowerSource import PowerSource
from RFSource import RFSource

MM_TO_STEPS_RATIO = 34304


# init all relevant devices by constructing the classes and setting the clients
def pre_test():
    # force home
    lock_in = instruments.srs.SR830('GPIB2::8::INSTR')
    power_source = PowerSource(2, 'GPIB2::10::INSTR')
    power_source.enable_output(False)
    RF_source = RFSource('USB0::0x03EB::0xAFFF::181-4396D0000-1246::0::INSTR')
    return lock_in, power_source, RF_source
    pass


# closing all clients
def post_test():
    pass


def power_meter_measurement():
    pass


# move the stage to a certain location
def move_stage(location):
    """
    move the stage to a desired location
    :param location: desired location in mm
    """
    with Thorlabs.KinesisMotor("27004822") as stage:
        stage.setup_velocity(None, None, MM_TO_STEPS_RATIO)
        print('stage is moving to ', location)
        stage.move_to(location * MM_TO_STEPS_RATIO)
        stage.wait_move()


def set_ferris_power_source():
    pass


def set_rf_source():
    pass


def init_basic_test_conditions(stage_location, power_source):
    move_stage(stage_location)
    power_source.set_voltage(2, 14.5)
    power_source.set_current(2, 0.55)
    power_source.enable_output(True)


def lock_in_and_stage_data_thread(end_location, lock_in):
    measurement_df = pd.DataFrame(columns=['location', 'R', 'X', 'Y', 'Theta'])  # , 'H', 'R', 'X', 'Y', 'Theta'])
    with Thorlabs.KinesisMotor("27004822") as stage:
        while stage.get_position() / MM_TO_STEPS_RATIO > end_location:
            print('stage current location is ', stage.get_position() / MM_TO_STEPS_RATIO, " mm")
            lock_in_measurement = lock_in.snap('R', 'X', 'Y', 'Theta')
            measurement_df.loc[measurement_df.shape[0]] = [stage.get_position() / MM_TO_STEPS_RATIO,
                                                           lock_in_measurement[0], lock_in_measurement[1],
                                                           lock_in_measurement[2], lock_in_measurement[3]]
            time.sleep(0.25)
    print('sweep is done')
    print(measurement_df)


def stage_sweep_move(speed, end_location):
    """
    Generate a sweep move with give speed and an end location
    :param speed: sweep speed in mm per second
    :param end_location: end location at mm
    """
    speed_in_steps_per_sec = speed * MM_TO_STEPS_RATIO
    with Thorlabs.KinesisMotor("27004822") as stage:
        stage.setup_velocity(None, None, speed_in_steps_per_sec)
        print('started the stage sweep move')
        stage.move_to(end_location * MM_TO_STEPS_RATIO)


def organize_run_parameters(run_parameters):
    """
    split the input parameters into the relevant values
    :param run_parameters: list of input parameters
    :return: organized input parameters
    """
    pass


def location_to_magnetic_field(stage_location):
    """
    converts the stage location to magnetic field
    :param stage_location: stage location in mm
    :return: magnetic field in Oe
    """
    pass


def main():
    organize_run_parameters(sys.argv[1:])
    lock_in, power_source = pre_test()
    lock_in_and_magnetic_field_thread = Thread(target=lock_in_and_stage_data_thread, args=[5, lock_in])
    init_basic_test_conditions(24, power_source)
    time.sleep(5)
    stage_sweep_move(0.5, 5)
    lock_in_and_magnetic_field_thread.start()

    # todo create full run blocks with the relevant loops


if __name__ == '__main__':
    main()
