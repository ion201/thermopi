#!/usr/bin/python3

import flask
import os
import pickle
import time
from urllib import request
from urllib.error import HTTPError
import json
import threading
import time
from hashlib import md5  # Super secure

import IO


app = flask.Flask(__name__)
# Use this line to force cookies to expire
# every time the application is restarted
app.secret_key = os.urandom(32)


def periodicrun(props):
    global units, DEGREES
    i = 0
    while True:
        time.sleep(1)
        i += 1
        if i % 5 == 0:
            props['temp_inside'] = '%d %s%s' % (IO.gettemp(), DEGREES, units)
        if i % 10 == 0:
            with open('status.pickle', 'wb') as f:
                pickle.dump(props, f, pickle.HIGHEST_PROTOCOL)
        if i % 60 == 0:
            props['temp_outside'] = '%s %s%s' % (getoutsidetemp(), DEGREES, units)
        

def getoutsidetemp():
    url = 'http://api.worldweatheronline.com/free/v2/weather.ashx'
    url += '?key=%s&q=%s&num_of_days=0&format=json' % (
          api_key, location)
    try:
        data = json.loads(request.urlopen(url).readall().decode('utf-8'))
        return data['data']['current_condition'][0]['temp_%s' % units]
    except HTTPError:
        return "err"

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
        props['trigger_temp'] = 99
        
    with open('settings.conf', 'r') as settings_file:
        config = json.load(settings_file)
        
    global api_key, location, units
    api_key = config['api_key']
    location = config['location']
    units = config['units']
    
    props['temp_inside'] = '%d %s%s' % (IO.gettemp(), DEGREES, units)
    props['temp_outside'] = '%s %s%s' % (getoutsidetemp(), DEGREES, units)

    if not os.path.exists('passwords.txt'):
        with open('passwords.txt', 'w') as f:
            f.write('admin:%s\n' % md5(b'admin').hexdigest())
        
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # Create this thread only once
        threading.Thread(target=periodicrun, args=(props,)).start()


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
    
    return flask.render_template('root.html', success_message='Event added!',
                                 **dict(props, **flask.session))


@app.route('/deleteevent', methods=['GET'])
def deleteevent():
    eventIndex = int(flask.request.args['index'])
    props['events'].pop(eventIndex)
    return flask.redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return flask.render_template('login.html')
        
    user = flask.request.form['username']
    # md5 hash is client-side because I'll be using http
    # Note: I'm aware md5 isn't wholly secure. I don't care because
    # it's still substantially better than plain text
    password = flask.request.form['password']

    with open('passwords.txt', 'r') as f:
        users = dict(line.split(':') for line in f.read().split())

    if password != users[user]:
        return flask.render_template('login.html', error='Invalid username or password')

    flask.session['current_user'] = user

    return flask.redirect('/')

@app.route('/logout', methods=['GET'])
def logout():
    flask.session['current_user'] = ''
    return flask.redirect('/login')


@app.route('/requestuser', methods=['GET', 'POST'])
def requestuser():
    if flask.request.method == 'GET':
        return flask.redirect('/login')
    
    username = flask.request.form['req_username']
    password = flask.request.form['req_password_1']
    
    with open('user_requests.txt', 'a') as f_req:
        f_req.write('%s:%s\n' % (username, password))
    
    return flask.render_template('login.html', error='Request sent')

@app.route('/admin', methods=['GET'])
def adminpanel():
    if flask.session['current_user'] != 'admin':
        return flask.redirect('/')
        
    with open('user_requests.txt', 'r') as f_req:
        request_users = dict(line.split(':') for line in f_req.read().split())
    with open('passwords.txt', 'r') as f_users:
        all_users = dict(line.split(':') for line in f_users.read().split())
        
    if flask.request.args:
        if flask.request.args['action'] == 'confirm':
            new_user = flask.request.args['user']
            all_users[new_user] = request_users[new_user]
            request_users.pop(new_user)
        elif flask.request.args['action'] == 'deny':
            request_users.pop(flask.request.args['user'])
            
        elif flask.request.args['action'] == 'delete':
            if flask.request.args['user'] != 'admin':
                all_users.pop(flask.request.args['user'])
            
        with open('user_requests.txt', 'w') as f_req:
            for user, passwd in request_users.items():
                f_req.write('%s:%s\n' % (user, passwd))
        with open('passwords.txt', 'w') as f_users:
            for user, passwd in all_users.items():
                f_users.write('%s:%s\n' % (user, passwd))
    
    return flask.render_template('admin.html', requests=request_users.keys(), all_users=all_users)


@app.route('/', methods=['GET'])
def rootdir():
    # This is a good place to start
    if not 'current_user' in flask.session or not flask.session['current_user']:
        return flask.redirect('/login')
    page = flask.render_template('root.html', **dict(props, **flask.session))
    return page
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, debug=True)
