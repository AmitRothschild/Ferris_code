# Ferris FMR main
# import pathlib
import os
import sys
from threading import Thread
# import logging
import time
import pandas as pd
import numpy as np
from pylablib.devices import Thorlabs
from pymeasure import instruments
from PowerSource import PowerSource
from RFSource import RFSource
from PowerSourceKeithley import PowerSourceKeithley
from PowerSourceKeysightFastMeas import PowerSourceFastMeas
import math
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime

from matplotlib.animation import FuncAnimation
import csv

matplotlib.use('Agg')


MM_TO_STEPS_RATIO = 34304
INIT_LOCATION = 24


def pre_test(rf_power, init_freq):
    """
    initialize all devices and home the stage
    :return: devices as objects
    """
    rf_source = RFSource('USB0::0x03EB::0xAFFF::181-4396D0000-1246::0::INSTR')
    rf_source.enable_output(False)
    power_source = PowerSourceKeithley(3, 'GPIB2::1::INSTR')
    power_source.enable_output(False)
    current_source = PowerSourceFastMeas(1, 'GPIB2::23::INSTR')
    current_source.enable_output(False)
    time.sleep(10)
    print('started homing')
    with Thorlabs.KinesisMotor("27004822") as stage:
        stage.home(force=True)
        stage.wait_for_home()
        print('homing complete')
    lock_in = instruments.srs.SR830('GPIB2::8::INSTR')
    for i in range(10):
        lock_in.snap('R', 'X', 'Y', 'Theta')
        time.sleep(0.1)
    print('initialized lock in amp')
    init_basic_test_conditions(INIT_LOCATION, power_source, rf_source, current_source, rf_power,
                               init_freq)
    return lock_in, power_source, rf_source, current_source


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


def move_stage(location):
    """
    move the stage to a desired location
    :param location: desired location in mm
    """
    time.sleep(2)
    with Thorlabs.KinesisMotor("27004822") as stage:
        stage.setup_velocity(None, None, MM_TO_STEPS_RATIO)
        print('stage is moving to ', location)
        stage.move_to(location * MM_TO_STEPS_RATIO)
        while stage.is_moving():
            print('stage is moving...')
            time.sleep(0.5)
        print('stage arrived at final location ', stage.get_position() / MM_TO_STEPS_RATIO)


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


def init_basic_test_conditions(stage_location, power_source, rf_source, current_source, rf_power, rf_init_freq):
    """
    create all clients and make sure that test conditions are correct
    :param stage_location: initial stage location
    :param power_source:  3 channel power source
    :param rf_source: rf source object
    :param current_source: bipolar current source
    :param rf_power: rf power in dBm
    :param rf_init_freq: initial rf frequency for th run
    :return: none
    """
    move_stage(stage_location)
    power_source.set_voltage(1, 12)
    power_source.set_current(1, 0.7)
    power_source.set_voltage(2, 8) # change to 24 when done
    power_source.set_current(2, 0.4) # change to 0.6 when done
    power_source.set_voltage(3, 6)
    power_source.set_current(3, 0.1)
    power_source.enable_output(True)
    current_source.set_operation_mode(1)
    current_source.set_voltage(6)
    time.sleep(50)
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
    # fieldnames = ["magnetic filed", "R"]
    # with open('temp data.csv', 'w', encoding='UTF8', newline='') as f:
    #     writer = csv.DictWriter(f, fieldnames=fieldnames)
    print('time started the lock in thread')
    print(datetime.now().strftime("%H:%M:%S"))
    with Thorlabs.KinesisMotor("27004822") as stage:
        while stage.get_position() / MM_TO_STEPS_RATIO > end_location:
            lock_in_measurement = lock_in.snap('R', 'X', 'Y', 'Theta')
            location.append(stage.get_position() / MM_TO_STEPS_RATIO)
            field.append(location_to_magnetic_field(stage.get_position() / MM_TO_STEPS_RATIO))
            r.append(lock_in_measurement[0])
            x.append(lock_in_measurement[1])
            y.append(lock_in_measurement[2])
            theta.append(lock_in_measurement[3])
            # info = {'magnetic filed': field[-1], 'R': r[-1]}
            # with open('temp data.csv', 'a', encoding='UTF8', newline='') as f:
            #     writer = csv.DictWriter(f, fieldnames=fieldnames)
            #     writer.writerow(info)
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


def get_stage_pos():
    """
    function that returns the stage's current location - this function can run only in debug mode
    :return: stage location
    """
    with Thorlabs.KinesisMotor("27004822") as stage:
        pos = stage.get_position() / MM_TO_STEPS_RATIO
        return pos


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
    a = 4119, b = -0.3221, c = 638.8, d = -0.09755
    :param stage_location: stage location in mm
    :return: magnetic field in Oe
    """
    a = 4119
    b = -0.3221
    c = 638.8
    d = -0.09755
    return a * math.exp(b * stage_location) + c * math.exp(d * stage_location)


def post_run(file_save_location, file_name, measured_data):
    """
    function that saves the data from the run
    :param file_save_location: path to data
    :param file_name: desired file name
    :param measured_data: all measured data
    """
    now = datetime.now()
    cur_date = now.strftime("%d_%m_%Y_%H_%M_")
    plt.cla()
    plt.plot(measured_data[0], measured_data[1])
    full_name = cur_date+file_name
    fig_full_name = os.path.join(file_save_location, full_name+'.png')
    data_full_name = os.path.join(file_save_location,  full_name+'.txt')
    plt.savefig(fig_full_name, format="png")
    data = np.column_stack([measured_data[0], measured_data[1], measured_data[2], measured_data[3], measured_data[4],
                           measured_data[5]])
    np.savetxt(data_full_name, data, fmt=['%.8f', '%.8f', '%.8f', '%.8f', '%.8f', '%.8f'])


def set_next_iter_setting(option, device, step, stage_location):
    """
    prepares the system for the next run
    :param option: indicates the function what operation to do
    :param device: object with the relevant device (power source / rf source)
    :param step: increment value (current / rf frequency)
    :param stage_location: indicate the desired stage location
    """
    move_stage(stage_location)
    if step == 0:
        return
    if option == 1:
        device.set_frequency(device.get_frequency() + step)
    elif option == 2:
        device.set_current(-device.get_current() + step)
    else:
        device.set_current(abs(device.get_current()) + step)


def meas_v_and_a(power_source, v_lst, cur_lst, stop):
    """
    Thread for the voltage and current measurement
    :param power_source: power source object
    :param v_lst: list of the measured voltage
    :param cur_lst: list of the measured current
    :param stop: flag that indicates the thread to stop
    :return: lists of measured voltage and current
    """
    init_res = 0
    notice = False
    while True:
        v_lst.append(power_source.get_voltage())
        cur_lst.append(power_source.get_current())
        if len(v_lst) == 1:
            init_res = v_lst[0]/cur_lst[0]
        cur_res = v_lst[-1]/cur_lst[-1]
        if cur_res > 1.1*init_res and not notice:
            notice = True
            print('!!! Please note that resistance increased by 10% !!!')
        if stop():
            print('!!!done!!!')
            break


def increment_running_current(power_source, running_cur):
    """
    Set the applied current to the given value
    :param power_source: power source object
    :param running_cur: new DC current value
    """
    power_source.set_current(running_cur)
    power_source.enable_output(True)


def create_file_name(cur_freq, app_cur):
    """
    This function creates the file name using the given parameters
    :param cur_freq: applied rf frequency
    :param app_cur: applied DC current
    :param pos: applied DC current polarity
    :return: file name
    """
    return str(cur_freq) + "_GHz_" + str(app_cur) + '_amp'


def get_input_from_user():
    """
    This function asks the user for the parameters that will be used for this run
    :return: relevant run parameters
    """
    path = input('Specify save location')
    rf_power = float(input('Specify rf power in dbm'))
    init_freq = float(input('Specify initial rf frequency'))
    freq_step = float(input('Specify rf frequency steps, if freq step is 0 only a single run will be done regardless '
                            'of the frequency limit'))
    freq_lim = float(input('Specify rf frequency limit'))
    stage_speed = float(input('Specify stage speed'))
    stage_lim = float(input('Specify stage movement limit'))
    run_with_applied_current = input('Do you want to run with applied current? (Y for yes / N for no)')
    while run_with_applied_current not in ['Y', 'N']:
        run_with_applied_current = input('Invalid input, use Y or N only')
    if run_with_applied_current == 'N':
        init_cur, cur_lim, cur_step = 0, 0, 0
    else:
        init_cur = float(input('Specify initial current'))
        cur_lim = float(input('Specify current limit'))
        cur_step = float(input('Specify current steps'))
    return path, rf_power, init_freq, freq_lim, freq_step, stage_speed, stage_lim, init_cur, cur_lim, cur_step


def hard_coded_or_user_input():
    """
    Ask the user what from where to take the input parameters
    :return: True for user parameter False for hardcoded parameters
    """
    user_decision = input('Do you wish to enter inputs or use the hardcoded input? (Y for user input / N for hardcoded)')
    while user_decision not in ['Y', 'N']:
        user_decision = input('Invalid input, use Y or N only')
    return True if user_decision == 'Y' else False


def print_cur_settings(cur_freq, running_cur):
    """
    This function prints the run setting to the console
    :param cur_freq: applied rf frequency
    :param running_cur: applied DC current
    """
    print('\n\n')
    print('############################################################################')
    print('current run is at ', cur_freq, ' GHz and applying current of', running_cur, ' A')
    print('##############################################################')
    print('\n\n')


def input_handler():
    """
    This function handles the input taking part for the run
    :return:
    """
    use_user_input = hard_coded_or_user_input()
    if use_user_input:
        file_save_location, rf_power, init_freq, freq_limit, freq_step, stage_speed, stage_limit, init_cur, cur_limit, \
            cur_step = get_input_from_user()
    else:
        file_save_location, rf_power, init_freq, freq_limit, freq_step, stage_speed, stage_limit, init_cur, cur_limit, \
            cur_step = organize_run_parameters(sys.argv[1:])
    return file_save_location, rf_power, init_freq, freq_limit, freq_step, stage_speed, stage_limit, init_cur,\
        cur_limit, cur_step


def prepare_for_next_iteration(running_current, current_source, current_step, polarity):
    """
    this function sets the correct current for the next iteration
    :param running_current: applied current  in the current runs
    :param current_source: current source object
    :param current_step: current increment size
    :param polarity: current polarity
    :return:
    """
    print('preparing for the next iteration')
    if running_current == 0:
        set_next_iter_setting(2, current_source, current_step, INIT_LOCATION)
        running_current += current_step
    else:
        if polarity == 'pos':
            running_current = -running_current
            set_next_iter_setting(2, current_source, 0, INIT_LOCATION)
            polarity = 'neg'
        else:
            running_current = abs(running_current) + current_step
            set_next_iter_setting(3, current_source, current_step, INIT_LOCATION)
            polarity = 'pos'
    return running_current, polarity


def main():
    """
    The main function of the Ferris FMR control script - this function initiates all the function calls
    :return: None
    """
    file_save_location, rf_power, init_freq, freq_limit, freq_step, stage_speed, stage_limit, init_cur, cur_limit,\
        cur_step = input_handler()
    lock_in, power_source, rf_source, current_source = pre_test(rf_power, init_freq)
    run_with_cur = False if cur_limit == 0 else True
    time.sleep(5)
    polarity = 'pos'
    running_cur = init_cur
    while rf_source.get_frequency() <= freq_limit:
        while abs(running_cur) <= cur_limit:
            stop_threads = False
            if running_cur == 0:
                current_source.enable_output(False)
            else:
                increment_running_current(current_source, running_cur)
            print('start time')
            print(datetime.now().strftime("%H:%M:%S"))
            position_lst, mag_field_lst, r_lst, x_lst, y_lst, theta_lst, v_lst, cur_lst = [], [], [], [], [], [], [], []
            lock_in_and_magnetic_field_thread = Thread(target=lock_in_and_stage_data_thread,
                                                       args=[stage_limit, lock_in, position_lst, mag_field_lst, r_lst,
                                                             x_lst, y_lst, theta_lst])
            voltage_current_meas_thread = Thread(target=meas_v_and_a, args=[current_source, v_lst, cur_lst,
                                                                            lambda: stop_threads])
            file_name = create_file_name(rf_source.get_frequency(), running_cur)
            print_cur_settings(rf_source.get_frequency(), running_cur)
            stage_sweep_move(stage_speed, stage_limit)
            lock_in_and_magnetic_field_thread.start()
            if running_cur != 0:
                voltage_current_meas_thread.start()
            lock_in_and_magnetic_field_thread.join()
            print('time joined the lock in thread')
            print(datetime.now().strftime("%H:%M:%S"))
            if not lock_in_and_magnetic_field_thread.is_alive():
                stop_threads = True
            if voltage_current_meas_thread.is_alive():
                voltage_current_meas_thread.join()
            current_source.enable_output(False)
            post_run(file_save_location, file_name, [mag_field_lst, r_lst, x_lst, y_lst, theta_lst, position_lst])
            print('end time')
            print(datetime.now().strftime("%H:%M:%S"))
            if run_with_cur:
                running_cur, polarity = prepare_for_next_iteration(running_cur, current_source, cur_step,
                                                                   polarity)
            else:
                break
            time.sleep(10)
        if freq_step > 0:
            set_next_iter_setting(1, rf_source, freq_step, INIT_LOCATION)
        else:
            break
    post_test(power_source, current_source, rf_source)
    # todo live update the graph


if __name__ == '__main__':
    main()
