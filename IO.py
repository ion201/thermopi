import RPi.GPIO as GPIO

class IO:
    def init(config):
        GPIO.setmode(GPIO.BOARD)
        
        GPIO.cleanup()

        IO.ch_fan = int(config['gpio_channel_fan'])
        GPIO.setup(IO.ch_fan, GPIO.OUT, initial=1)
        try:
            IO.ch_ac = int(config['gpio_channel_ac'])
            GPIO.setup(IO.ch_ac, GPIO.OUT, initial=1)
        except ValueError:
            IO.ch_ac = None
        try:
            IO.ch_heat = int(config['gpio_channel_heat'])
            GPIO.setup(IO.ch_heat, GPIO.OUT, initial=1)
        except ValueError:
            IO.ch_heat = None

        IO.units = config['units']  # 'F' or 'C'

        IO.therm_device_id = config['therm_device_id']


    def gettemp():
        # /sys/bus/w1/devices/28-000006153d8f/w1_slave, t=[temp] on second line
        if not IO.therm_device_id:
            return 0

        path = '/sys/bus/w1/devices/%s/w1_slave' % IO.therm_device_id
        with open(path, 'r') as f:
            temp = float(f.read().split('=')[-1]) / 1000

        if IO.units == 'F':  # Device reads in Celcius
            temp = temp * 1.8 + 32
        round(temp, 1)

        return temp


    def setfan(state):
        """True -> on; False -> off; (or anything which will eval to t/f)"""
        GPIO.output(IO.ch_fan, not state)


    def setac(state):
        if not IO.ch_ac:
            return

        if state:  # if the ac is on, the fan must be
            setfan(True)

        GPIO.output(IO.ch_ac, not state)


    def setheat(state):
        if not IO.ch_heat:
            return

        if state:
            setfan(state)

        GPIO.output(IO.ch_heat, not state)
