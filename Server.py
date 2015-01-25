#!/usr/bin/python3

import flask
import os
import pickle
import time
from urllib import request
import json

import IO


app = flask.Flask(__name__)
# Use this line to force cookies to expire
# every time the application is restarted
app.secret_key = os.urandom(32)


def getoutsidetemp():
    url = 'http://api.worldweatheronline.com/free/v2/weather.ashx'
    url += '?key=%s&q=%s&num_of_days=0&format=json' % (
          api_key, location)
    data = json.loads(request.urlopen(url).readall().decode('utf-8'))
    return data['data']['current_condition'][0]['temp_%s' % units]
    

def updatecontent():
    props['temp_inside'] = '%d %s%s' % (IO.gettemp(), DEGREES, units)
    props['temp_outside'] = '%s %s%s' % (getoutsidetemp(), DEGREES, units)
    
    with open('status.pickle', 'wb') as f:
        pickle.dump(props, f, pickle.HIGHEST_PROTOCOL)
        

@app.before_first_request
def onstart():
    # Use this function to initialize modules and global vars
    global DEGREES
    DEGREES = '°'
    
    global props, days_short
    props = {}
    days_short = {'sunday': 'S', 'monday': 'M', 'tuesday': 'T', 'wednesday': 'W',
                  'thursday': 'Th', 'friday': 'F', 'saturday': 'Sa'}
    try:
        with open('status.pickle', 'rb') as f:
            props = pickle.load(f)
    except FileNotFoundError:
        props['fan_status'] = 'auto'
        props['ac_status'] = 'auto'
        props['events'] = []
        
    with open('settings.conf', 'r') as settings_file:
        config = json.load(settings_file)
    
    global api_key, location, units
    api_key = config['api_key']
    location = config['location']
    units = config['units']

    updatecontent()


@app.route('/newevent', methods=['GET', 'POST'])
def newevent():
    if flask.request.method == 'GET':
        return flask.redirect('/')
        
    f = flask.request.form.copy()
    days = ''
    for day in f.getlist('days_select'):
        days += days_short[day]
    
    if f['mode_select'] == 'auto':
        temp = '%s %s%s' % (f['temp'], DEGREES, units)
    else:
        temp = 'n/a'
    
    props['events'].append([days, f['time'], f['device_select'], f['mode_select'], temp])
    updatecontent()
    
    return flask.render_template('root.html', success_message='Event added!',
                                 **dict(props, **flask.session))


@app.route('/deleteevent', methods=['GET'])
def deleteevent():
    eventIndex = int(flask.request.args['index'])
    props['events'].pop(eventIndex)
    updatecontent()
    return flask.redirect('/')


@app.route('/', methods=['GET'])
def rootdir():
    # This is a good place to start
    updatecontent()
    
    page = flask.render_template('root.html', **dict(props, **flask.session))
    return page


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, debug=True)
