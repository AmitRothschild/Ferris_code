# Ferris FMR main
# import pathlib
import sys
from threading import Thread
# import logging
import time
# import pandas as pd
# import numpy as np
from pylablib.devices import Thorlabs
from pymeasure import instruments
from PowerSource import PowerSource
from RFSource import RFSource
from PowerSourceKeithley import PowerSourceKeithley
import math
import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation
import csv

MM_TO_STEPS_RATIO = 34304


def pre_test():
    """
    initialize all devices and home the stage
    :return: devices as objects
    """
    power_source_motor = PowerSource(2, 'GPIB2::10::INSTR')
    power_source_motor.enable_output(False)
    rf_source = RFSource('USB0::0x03EB::0xAFFF::181-4396D0000-1246::0::INSTR')
    power_source_cur_amp = PowerSourceKeithley(3, 'GPIB2::1::INSTR')
    power_source_cur_amp.enable_output(False)
    time.sleep(10)
    with Thorlabs.KinesisMotor("27004822") as stage:
        stage.home(force=True)
        print('started homing')
        stage.wait_for_home()
        print('homing complete')
    lock_in = instruments.srs.SR830('GPIB2::8::INSTR')
    for i in range(10):
        lock_in.snap('R', 'X', 'Y', 'Theta')
        time.sleep(0.1)
    print('initialized lock in amp')
    return lock_in, power_source_motor, rf_source, power_source_cur_amp


# closing all clients
def post_test(power_source_motor, power_source_current_amp, rf_source):
    """
    turn off all outputs and close clients
    :param power_source_motor: power source object
    :param power_source_current_amp: power source object
    :param rf_source:rf source object
    """
    power_source_motor.enable_output(False)
    power_source_motor.close_client()
    rf_source.enable_output(False)
    rf_source.close_client()
    time.sleep(5)
    power_source_current_amp.enable_output(False)
    power_source_current_amp.close_client()


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


# def live_update_fig(i, path):
#     """
#     function that is used for the live update of the measured data for now it plots R vs magnetic field
#     :param i: iterator
#     :param path:path for the data file
#     :return:
#     """
#     with open(path, newline='') as f:
#         reader = csv.reader(f)
#         data = list(reader)
#         magnetic_field = [float(item[0]) for item in data]
#         r = [float(item[1]) for item in data]
#     plt.cla()
#     plt.plot(magnetic_field, r)


def init_basic_test_conditions(stage_location, power_source, rf_source, power_source_rf_amp, rf_power, rf_init_freq):
    """
    create all clients and make sure that test conditions are correct
    :param stage_location: initial stage location
    :param power_source:  2 channel power source for the motor object
    :param rf_source: rf source object
    :param power_source_rf_amp: 3 channel power source for rf amp and current driven tests
    :param rf_power: rf power in dBm
    :param rf_init_freq: initial rf frequency for th run
    :return: none
    """
    move_stage(stage_location)
    power_source.set_voltage(2, 14.5)
    power_source.set_current(2, 0.55)
    power_source.enable_output(True)
    power_source_rf_amp.set_voltage(1, 12)
    power_source_rf_amp.set_current(1, 0.7)
    power_source_rf_amp.set_voltage(2, 5)
    power_source_rf_amp.set_current(2, 0.03)
    power_source_rf_amp.enable_single_channel(1, True)
    power_source_rf_amp.enable_single_channel(2, True)
    time.sleep(3)
    rf_source.set_frequency(rf_init_freq)
    rf_source.set_power(rf_power)
    rf_source.enable_output(True)


def lock_in_and_stage_data_thread(end_location, lock_in, location, field, r, x, y, theta):
    """
    thread for the lock in data acquisition, data is passed as reference - must be mutable data type
    :param end_location: stage end location
    :param lock_in: lock in object
    :param location: reference to the location lst
    :param field: reference to the magnetic field list
    :param r: reference to the r list
    :param x: reference to the x list
    :param y: reference to the y list
    :param theta: reference to the theta list
    """
    fieldnames = ["magnetic filed", "R"]
    # counter = 0
    with open('temp data.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
    with Thorlabs.KinesisMotor("27004822") as stage:
        while stage.get_position() / MM_TO_STEPS_RATIO > end_location:
            # lock_in_and_stage_data_thread.counter +=1
            lock_in_measurement = lock_in.snap('R', 'X', 'Y', 'Theta')
            location.append(stage.get_position() / MM_TO_STEPS_RATIO)
            field.append(location_to_magnetic_field(stage.get_position() / MM_TO_STEPS_RATIO))
            r.append(lock_in_measurement[0])
            x.append(lock_in_measurement[1])
            y.append(lock_in_measurement[2])
            theta.append(lock_in_measurement[3])
            info = {'magnetic filed': field[-1], 'R': r[-1]}
            with open('temp data.csv', 'a', encoding='UTF8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(info)
            # counter += 1
            # if counter % 10 == 0:
            #     plt.cla()
            #     plt.plot(field, r)
            # plt.show(block=False)
            time.sleep(0.05)
    print('sweep is done')


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
    rf_power = float(run_parameters[1])
    init_freq = float(run_parameters[2])
    freq_limit = float(run_parameters[3])
    freq_step = float(run_parameters[4])
    speed = float(run_parameters[5])
    stage_limit = float(run_parameters[6])
    init_cur = float(run_parameters[7])
    cur_limit = float(run_parameters[8])
    cur_step = float(run_parameters[9])
    return file_location, rf_power, init_freq, freq_limit, freq_step, speed, stage_limit, init_cur, cur_limit, cur_step


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


def post_run(file_save_location, file_name, measured_data):
    plt.plot(measured_data[1], measured_data[2])
    plt.savefig('test_fig.png', format="png")
    # data = [mag_lst, r_lst]
    # file_save_location + '\\' + file_name + 'txt'
    # np.savetxt(file_save_location + '\\' + file_name + 'txt', data, fmt='%d')
    # with open(file_save_location, 'a') as f:
    #     data_as_str = measured_v_vs_h.to_string(header=True, index=False)
    #     f.write(data_as_str)


def prepare_for_next_run(option, device, step, stage_location):
    if step == 0:
        move_stage(stage_location)
        return
    if option == 1:
        device.set_frequency(device.get_frequency() + step)
    else:
        device.set_current(3, device.get_current() + step)


def meas_v_and_a(power_source, v_lst, cur_lst, stop):
    while True:
        v_lst.append(power_source.get_voltage(3))
        cur_lst.append(power_source.get_current(3))
        print((v_lst[-1], cur_lst[-1]))
        if stop:
            break


def switch_polarity(power_source, pos):
    """
    switch current polarity
    :param power_source: power source object
    :param pos: position to switch to
    """
    if pos == 'pos':
        power_source.set_voltage(2, 5)
    else:
        power_source.set_voltage(2, 0)


# def increment_current(power_source, cur_val, step):
#     power_source.set_current(3, cur_val + step)


def create_file_name(cur_freq, app_cur, pos):
    return str(cur_freq) + "_GHz_" + str(pos) + str(app_cur) + '_amp'


def main():
    # path = str(pathlib.Path(__file__).parent.resolve()) + '\\temp data.csv'
    file_save_location, rf_power, init_freq, freq_limit, freq_step, stage_speed, stage_limit,\
        init_cur, cur_limit, cur_step = organize_run_parameters(sys.argv[1:])
    lock_in, power_source_motor, rf_source, power_source_current_amp = pre_test()
    init_basic_test_conditions(24, power_source_motor, rf_source, power_source_current_amp, rf_power,
                               init_freq)
    time.sleep(5)
    polarity = 'pos'
    running_cur = init_cur
    while rf_source.get_frequency() <= freq_limit:
        while abs(running_cur) <= cur_limit:
            stop_threads = False
            if running_cur == 0:
                power_source_current_amp.enable_single_channel(3, False)
            else:
                power_source_current_amp.enable_single_channel(3, True)
            position_lst, mag_field_lst, r_lst, x_lst, y_lst, theta_lst, v_lst, cur_lst = [], [], [], [], [], [], [], []
            lock_in_and_magnetic_field_thread = Thread(target=lock_in_and_stage_data_thread,
                                                       args=[stage_limit, lock_in, position_lst, mag_field_lst, r_lst,
                                                             x_lst, y_lst, theta_lst])
            voltage_current_meas_thread = Thread(target=meas_v_and_a, args=[power_source_current_amp, v_lst, cur_lst,
                                                                            lambda: stop_threads])
            # file_name = create_file_name(rf_source.get_frequency(), 0, 'pos')
            stage_sweep_move(stage_speed, stage_limit)
            lock_in_and_magnetic_field_thread.start()
            voltage_current_meas_thread.start()
            lock_in_and_magnetic_field_thread.join()
            stop_threads = True
            voltage_current_meas_thread.join()
            power_source_current_amp.enable_single_channel(3, False)
            post_run(file_save_location, 'aaa', [position_lst, mag_field_lst, r_lst,
                                                 x_lst, y_lst, theta_lst])
            if running_cur == 0:
                prepare_for_next_run(2, power_source_current_amp, cur_step, 24)
            else:
                if polarity == 'pos':
                    switch_polarity(power_source_current_amp, 'neg')
                    prepare_for_next_run(2, power_source_current_amp, 0, 24)
                    running_cur = -running_cur
                    polarity = 'neg'
                else:
                    switch_polarity(power_source_current_amp, 'pos')
                    prepare_for_next_run(2, power_source_current_amp, cur_step, 24)
                    running_cur += cur_step
                    polarity = 'pos'
        prepare_for_next_run(1, rf_source, freq_step, 24)
    post_test(power_source_motor, power_source_current_amp, rf_source)
    # todo live update the graph


if __name__ == '__main__':
    main()
