#!/usr/bin/python3

comm_file = '/srv/thermopi/gpiocomm.tmp'

with open(comm_file, 'a') as file:
    file.write('-1:exit\n')
