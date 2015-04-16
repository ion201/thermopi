#!/usr/bin/python3

comm_file = '/tmp/gpiocomm'

with open(comm_file, 'a') as file:
    file.write('-1:exit\n')
