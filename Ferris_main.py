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
from PowerSourceKeithley import PowerSourceKeithley

import math

MM_TO_STEPS_RATIO = 34304


# init all relevant devices by constructing the classes and setting the clients
def pre_test():
    """
    initialize all devices and home the stage
    :return: devices as objects
    """
    with Thorlabs.KinesisMotor("27004822") as stage:
        stage.home(force=True)
        print('started homing')
        stage.wait_for_home()
        print('homing complete')
    lock_in = instruments.srs.SR830('GPIB2::8::INSTR')
    print('initialized lock in amp')
    power_source_motor = PowerSource(2, 'GPIB2::10::INSTR')
    power_source_motor.enable_output(False)
    RF_source = RFSource('USB0::0x03EB::0xAFFF::181-4396D0000-1246::0::INSTR')
    power_source_cur_amp = PowerSourceKeithley(3, 'GPIB2::1::INSTR')
    power_source_cur_amp.enable_output(False)
    return lock_in, power_source_motor, RF_source, power_source_cur_amp


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


def init_basic_test_conditions(stage_location, power_source, RF_source, power_source_rf_amp, RF_power, RF_init_freq):
    """
    create all clients and make sure that test conditions are correct
    :param stage_location: initial stage location
    :param power_source:  2 channel power source for the motor object
    :param RF_source: rf source object
    :param power_source_rf_amp: 3 channel power source for rf amp and current driven tests
    :param RF_power: rf power in dBm
    :param RF_init_freq: initial rf frequency for th run
    :return: none
    """
    move_stage(stage_location)
    power_source.set_voltage(2, 14.5)
    power_source.set_current(2, 0.55)
    power_source.enable_output(True)
    power_source_rf_amp.set_voltage(1, 12)
    power_source_rf_amp.set_current(1, 0.7)
    power_source_rf_amp.enable_single_channel(1)
    time.sleep(3)
    RF_source.set_frequency(RF_init_freq)
    RF_source.set_power(RF_power)
    RF_source.enable_output(True)


def lock_in_and_stage_data_thread(end_location, lock_in):
    measurement_df = pd.DataFrame(columns=['location', 'R', 'X', 'Y', 'Theta'])  # , 'H', 'R', 'X', 'Y', 'Theta'])
    with Thorlabs.KinesisMotor("27004822") as stage:
        while stage.get_position() / MM_TO_STEPS_RATIO > end_location:
            print('stage current location is ', stage.get_position() / MM_TO_STEPS_RATIO, " mm")
            lock_in_measurement = lock_in.snap('R', 'X', 'Y', 'Theta')
            measurement_df.loc[measurement_df.shape[0]] = [stage.get_position() / MM_TO_STEPS_RATIO,
                                                           lock_in_measurement[0], lock_in_measurement[1],
                                                           lock_in_measurement[2], lock_in_measurement[3]]
            time.sleep(0.05)
    print('sweep is done')
    print(measurement_df)
    return measurement_df


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
    file_location = run_parameters[0]
    RF_power = float(run_parameters[1])
    init_freq = float(run_parameters[2])
    freq_limit = float(run_parameters[3])
    freq_step = float(run_parameters[4])
    speed = float(run_parameters[5])
    stage_limit = float(run_parameters[6])
    return file_location, RF_power, init_freq, freq_limit, freq_step, speed, stage_limit


def location_to_magnetic_field(stage_location):
    """
    converts the stage location to magnetic field
    the fit is two exponents: a*exp(b*x) + c*exp(d*x)
    a = 411.9, b = -0.3221, c = 63.88, d = -0.09755
    :param stage_location: stage location in mm
    :return: magnetic field in Oe
    """
    a = 4119
    b = -0.3221
    c = 6388
    d = -0.09755
    return a * math.exp(b * stage_location) + c * math.exp(c * d)


def post_run(file_save_location, file_name, measured_v_vs_h, measured_graph):
    file_save_location + '\\' + file_name + 'txt'
    np.savetxt(file_save_location + '\\' + file_name + 'txt', measured_v_vs_h, fmt='%d')
    # with open(file_save_location, 'a') as f:
    #     data_as_str = measured_v_vs_h.to_string(header=True, index=False)
    #     f.write(data_as_str)


def prepare_for_next_run():
    pass


def switch_polarity(power_source, pos):
    if pos:
        power_source.set_voltage(2, 5)
    else:
        power_source.set_voltage(2, 0)


def increment_current(power_source, cur_val, step):
    power_source.set_current(3, cur_val + step)


def create_file_name(cur_freq, app_cur, pos):
    pass


def main():
    file_save_location, RF_power, init_freq, freq_limit, freq_step, stage_speed, stage_limit = organize_run_parameters(
        sys.argv[1:])
    lock_in, power_source_motor, RF_source, power_source_current_amp = pre_test()
    lock_in_and_magnetic_field_thread = Thread(target=lock_in_and_stage_data_thread, args=[5, lock_in])
    init_basic_test_conditions(24, power_source_motor, RF_source, power_source_current_amp, RF_power,
                               init_freq)
    time.sleep(5)
    while RF_source.get_frequency() <= freq_limit:
        # if (run_with_current)
        # file_name = create_file_name(RF_source.get_frequency(), 0, 'pos')
        stage_sweep_move(stage_speed, stage_limit)
        measured_v_vs_h = lock_in_and_magnetic_field_thread.start()
        RF_source.set_frequency(RF_source.get_frequency() + freq_step)
        # post_run(file_save_location, file_name, measured_v_vs_h, measured_graph)
        prepare_for_next_run()
    post_test()
    # todo create full run blocks with the relevant loops


if __name__ == '__main__':
    main()
