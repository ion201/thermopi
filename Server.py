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
import random
import logging
import shutil

from IO import IO


app = flask.Flask(__name__)
# Use this line to force cookies to expire
# every time the application is restarted
app.secret_key = os.urandom(32)


def periodicrun(props):
    global DEGREES
    i = 0
    while True:
        time.sleep(1)
        i += 1
        if i % 5 == 0:
            props['temp_inside'] = '%.1f' % IO.gettemp()
        if i % 10 == 0:
            with open('status.pickle', 'wb') as f:
                pickle.dump(props, f, pickle.HIGHEST_PROTOCOL)
        if i % 60 == 0:
            props['temp_outside'] = getoutsidetemp()


def getoutsidetemp():
    url = 'http://api.worldweatheronline.com/free/v2/weather.ashx'
    url += '?key=%s&q=%s&num_of_days=0&format=json' % (
          api_key, location)
    try:
        data = json.loads(request.urlopen(url).readall().decode('utf-8'))
        return data['data']['current_condition'][0]['temp_%s' % props['units']]
    except HTTPError:
        return "err"


def gensecret():
    flask.session['session_salt'] = ''.join(chr(random.randint(97, 122)) for i in range(64))


@app.before_first_request
def onstart():
    # Use this function to initialize modules and global vars
    logging.basicConfig(filename='history.log', level=logging.WARNING,
                        format='%(asctime)s %(message)s')

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
        props['status_fan'] = 'auto'
        props['status_ac'] = 'auto'
        props['status_heat'] = 'auto'
        props['events'] = []
        props['trigger_temp'] = 99

    if not os.path.exists('settings.conf'):
        shutil.copy2('sample_settings.conf', 'settings.conf')

    with open('settings.conf', 'r') as settings_file:
        config = json.load(settings_file)

    IO.init(config)

    global api_key, location
    api_key = config['api_key']
    location = config['location']
    props['units'] = config['units']

    props['temp_inside'] = '%.1f' % IO.gettemp()
    props['temp_outside'] = getoutsidetemp()

    if not os.path.exists('passwords.txt'):
        with open('passwords.txt', 'w') as f:
            f.write('admin:%s\n' % md5(b'admin').hexdigest())

    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # Run these functions only once; not when reloaded
        threading.Thread(target=periodicrun, args=(props,)).start()


@app.route('/setstate', methods=['GET'])
def setstate():
    props['status_ac'] = flask.request.args['ac_status']
    props['status_heat'] = flask.request.args['heat_status']
    props['status_fan'] = flask.request.args['fan_status']
    props['trigger_temp'] = int(flask.request.args['trigger_temp'])

    logging.warning('%s set trigger temp to %i' % (flask.session['current_user'], props['trigger_temp']))

    return flask.redirect('/')


@app.route('/newevent', methods=['GET'])
def newevent():
    f = flask.request.args.copy()
    days = ''
    for day in f.getlist('days_select'):
        days += days_short[day]

    if f['mode_select'] == 'auto':
        temp = f['temp']
    else:
        temp = ''

    props['events'].append([days, f['time'], f['device_select'], f['mode_select'], temp])

    logging.warning('%s created event %s' % (flask.session['current_user'], str(props['events'][-1])))
    
    return flask.redirect('/')


@app.route('/deleteevent', methods=['GET'])
def deleteevent():
    eventIndex = int(flask.request.args['index'])
    
    logging.warning('%s deleted event %s' % (flask.session['current_user'], str(props['events'][eventIndex])))
    
    props['events'].pop(eventIndex)
    return flask.redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """How authentification works:
    Account setup: password is transferred as a plain text md5 hash
        and is vulnerable to interception over http at this time
    Normal login: GET request generates new 64-byte random secret which is embedded in the page js.
        When a password is entered, we get the md5 hash then append the secret to this hash
        and then hash it again.
        Result: an attackter cannot use intercepted data to log in :)"""
    if flask.request.method == 'GET':
        gensecret()
        return flask.render_template('login.html', secret=flask.session['session_salt'])

    user = flask.request.form['username']
    password = flask.request.form['password']

    with open('passwords.txt', 'r') as f:
        passwords = dict(line.split(':') for line in f.read().split())

    if password != md5((passwords[user] + flask.session['session_salt']).encode('utf-8')).hexdigest():
        return flask.render_template('login.html', error='Invalid username or password', secret=flask.session['session_salt'])

    gensecret()  #Create a new secret after succesfful login
    flask.session['current_user'] = user
    # logging.warning('%s logged in' % user)

    return flask.redirect('/')

@app.route('/logout', methods=['GET'])
def logout():
    # logging.warning('%s logged out' % flask.session['current_user'])
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
    
    return flask.render_template('login.html', error='Request sent', secret=flask.session['session_salt'])

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
    

@app.route('/api-get', methods=['GET'])
def apiget():
    """Get information only. json formatted"""

    return flask.render_template('api.html', **props)


@app.route('/api-post', methods=['GET'])
def apipost():
    """Use get request args to set server data"""
    return flask.render_template('api.html', **props)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, debug=True)
