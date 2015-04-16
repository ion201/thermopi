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
    
    with open(comm_file, 'w') as file:
        file.write('')
    
    os.chmod(comm_file, 0o666)  #Everyone can write to this file.
    
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
            setchannel(channel, bool(int(directive)))
    
    with open(comm_file, 'w') as file:
        file.write('')

    return exit_now


def init():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    exit_now = False
    while not exit_now:
        time.sleep(1)
        exit_now = processcommands()


if __name__ == '__main__':
    init()
