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
    comm_file = '/tmp/gpiocomm'
    
    if not os.path.exists(comm_file):
        with open(comm_file, 'w') as file:
            file.write('')
    
    with open(comm_file, 'r') as file:
        commands = file.read().split()
    
    for command in commands:
        channel, directive = command.split(':')
        channel = int(channel)

        if directive == 'clean':
            cleanchannel(channel)
        elif directive == 'setup':
            setupchannel(channel)
        else:
            setchannel(channel, bool(int(directive)))
    
    with open(comm_file, 'w') as file:
        file.write('')


def init():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    while True:
        time.sleep(1)
        processcommands()


if __name__ == '__main__':
    init()
