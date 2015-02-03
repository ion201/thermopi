import RPi.GPIO as GPIO


# GPIO.output(18, 0)  # Turn fan on
# GPIO.output(18, 1)  # Turn fan off
# GPIO.output(16, 0)  # Turn AC on
# GPIO.output(16, 1)  # Turn AC off

def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(18, GPIO.OUT, initial=1)
    GPIO.setup(16, GPIO.OUT, initial=1)


def gettemp():
    return 99


def setfan(state):
    pass


def setac(state):
    if state:
        # Always turn on the fan when the ac is on
        setfan(True)
