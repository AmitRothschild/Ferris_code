# Ferris FMR main
import sys
import threading
import logging
import time


# init all relevant devices by constructing the classes and setting the clients
def pre_test():
    pass


# closing all clients
def post_test():
    pass


# get all measurement from the lock in
def lock_in_measurement():
    pass


def power_meter_measurement():
    pass


# move the stage to a certain location
def move_stage(location):
    pass


def set_ferris_power_source():
    pass


def set_rf_source():
    pass


def init_basic_test_conditions():
    pass


def stage_sweep_move(speed, end_location):
    pass


def organize_run_parameters(run_parameters):
    pass


def main():
    organize_run_parameters(sys.argv[1:])
    pre_test()
    init_basic_test_conditions()
    # todo create full run blocks with the relevant loops





if __name__ == '__main__':
    main()
