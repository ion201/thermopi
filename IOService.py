#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import os


def setchannel(channel, state):
    """True -> on; False -> off; (or anything which will eval to t/f)"""
    GPIO.output(channel, state)


def setupchannel(channel):
    GPIO.setup(channel, GPIO.OUT, initial=0)


def cleanchannel(channel):
    GPIO.cleanup(channel)


def processcommands():
    comm_file = '/srv/thermopi/gpiocomm.tmp'

    with open(comm_file, 'r') as file:
        commands = file.read().split()

    exit_now = False

    for command in commands:
        channel, directive = command.split(':')
        channel = int(channel)

        if directive == 'clean':
            cleanchannel(channel)
        elif directive == 'setup':
            setupchannel(channel)
        elif directive == 'exit':
            exit_now = True
        else:
            try:
                setchannel(channel, bool(int(directive)))
            except RuntimeError:
                # The channel probably hasn't been set up yet. Let's do that.
                cleanchannel(channel)
                setupchannel(channel)
    
    with open(comm_file, 'w') as file:
        file.write('')

    return exit_now


def init():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    comm_file = '/srv/thermopi/gpiocomm.tmp'

    os.chmod(comm_file, 0o666)  #Everyone can write to this file.

    exit_now = False
    while not exit_now:
        time.sleep(1)
        exit_now = processcommands()


if __name__ == '__main__':
    init()
