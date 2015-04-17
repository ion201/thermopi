#!/usr/bin/python3

# Write commands for IOService.py to /tmp/gpiocomm
# All commands take the form--
# <channel>:<state 0|1>
# or
# <channel>:clean
# <channel>:setup
#        -1:exit  -- only used by IOServiceStop.py


def gettemp_w1(device_id)
    path = '/sys/bus/w1/devices/%s/w1_slave' % device_id
    with open(path, 'r') as temperature_file:
        temp = float(temperature_file.read().split('=')[-1]) / 1000
        
    return temp


class IO:
    def init(config):
        IO.ch_fan = int(config['gpio_channel_fan'])
        try:
            IO.ch_ac = int(config['gpio_channel_ac'])
        except ValueError:
            IO.ch_ac = None
        try:
            IO.ch_heat = int(config['gpio_channel_heat'])
        except ValueError:
            IO.ch_heat = None

        IO.units = config['units']  # 'F' or 'C'

        IO.therm_device_driver = config['therm_device_driver']
        IO.therm_device_id = config['therm_device_id']
        
        IO.out_file = '/tmp/gpiocomm'
        
        with open(IO.out_file, 'w') as comm_file:
            comm_file.write('')
        
        with open(IO.out_file, 'a') as comm_file:
            if IO.ch_fan:
                comm_file.write('%s:clean\n' % IO.ch_fan)
                comm_file.write('%s:setup\n' % IO.ch_fan)
            if IO.ch_ac:
                comm_file.write('%s:clean\n' % IO.ch_ac)
                comm_file.write('%s:setup\n' % IO.ch_ac)
            if IO.ch_heat:
                comm_file.write('%s:clean\n' % IO.ch_heat)
                comm_file.write('%s:setup\n' % IO.ch_heat)


    def gettemp():
        # /sys/bus/w1/devices/28-000006153d8f/w1_slave, t=[temp] on second line
        if not IO.therm_device_id or not IO.therm_device_driver:
            return 0

        if IO.therm_device_driver == 'w1':
            temp = gettemp_w1(IO.therm_device_id)
        
        if IO.units == 'F':  # All functions should return temp in Celsius
            temp = temp * 1.8 + 32
        if IO.units == 'K':
            temp += 273
        temp = round(temp, 1)

        return temp


    def setfan(state):
        """True -> on; False -> off; (or anything which will eval to t/f)"""
        if not IO.ch_fan:
            return
        
        with open(IO.out_file, 'a') as comm_file:
            comm_file.write('%s:%s\n' % (IO.ch_fan, int(bool(state))))


    def setac(state):
        if not IO.ch_ac:
            return
        
        with open(IO.out_file, 'a') as comm_file:
            comm_file.write('%s:%s\n' % (IO.ch_ac, int(bool(state))))
        
        IO.setfan(state)


    def setheat(state):
        if not IO.ch_heat:
            return
        
        with open(IO.out_file, 'a') as comm_file:
            comm_file.write('%s:%s\n' % (IO.ch_heat, int(bool(state))))
        
        IO.setfan(state)
