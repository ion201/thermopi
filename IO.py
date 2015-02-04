import RPi.GPIO as GPIO

class IO:
    def init(config):
        GPIO.setmode(GPIO.BOARD)

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

        units = config['units']  # 'F' or 'C'


    def cleanup():
        GPIO.cleanup()


    def gettemp():
        # /sys/bus/w1/devices/28-000006153d8f/w1_slave, t=[temp] on second line
        return 99


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
