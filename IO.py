import RPi.GPIO as GPIO


def gettemp():
    return 80


def setfan(state):
    pass

   
def setac(state):
    if state:
        # Always turn on the fan when the ac is on
        setfan(True)