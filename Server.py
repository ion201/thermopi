#!/usr/bin/python3

import flask
import os
import pickle
import time
from urllib import request
from urllib.error import HTTPError, URLError
import json
import threading
from hashlib import md5  # Super secure
import random
import logging
import shutil

from IO import IO


app = flask.Flask(__name__)
# Use this line to force cookies to expire
# every time the application is restarted
# app.secret_key = os.urandom(32)
app.secret_key = ' bbace2c841d9a06f382d1e4f5a97dc3d'


def storeobject(obj_name, obj):
    with open('pickledb/%s.pickle' % obj_name, 'wb') as file:
        pickle.dump(obj, file, pickle.HIGHEST_PROTOCOL)


def loadobject(obj_name):
    with open('pickledb/%s.pickle' % obj_name, 'rb') as file:
        obj = pickle.load(file)
    return obj


def periodicrun():
    day_map = [('Sa', '5'), ('F', '4'), ('Th', '3'),
               ('W', '2'), ('T', '1'), ('M', '0'), ('S', '6')]

    i = 0
    while True:
        time.sleep(1)
        i += 1

        props = loadobject('props')
        if i % 60 == 0:
            props['temp_outside'] = getoutsidetemp()
            storeobject('props', props)
        
        if i % 5 == 0:
            props['temp_inside'] = '%.1f' % IO.gettemp()

        if i % 10 == 0:
            storeobject('props', props);

            if props['status_ac'] == 'on':
                IO.setac(1)
            if props['status_ac'] == 'off':
                IO.setac(0)
            if props['status_ac'] == 'auto':
                IO.setac(0) if IO.gettemp() < props['trigger_temp'] else IO.setac(1)

            if props['status_heat'] == 'on':
                IO.setheat(1)
            if props['status_heat'] == 'off':
                IO.setheat(0)
            if props['status_heat'] == 'auto':
                IO.setheat(0) if IO.gettemp() > props['trigger_temp'] else IO.setheat(1)

            if props['status_fan'] == 'on':
                # 'auto' is managed by IO.setx to ensure it is always on when the ac or heat is.
                IO.setfan(1)

        if i % 31 == 0:
            t = time.localtime()
            year, month, day, hour, minute = t[:5]
            weekday = t[6]

            for event in props['events']:
                # Event format: ['weekday <SMTWThFSa>', 'time <HHMM>',
                #                'ac|heat|fan', 'auto|on|off', 'temp <TT>', 'F|C']
                weekdays = event[0]
                for d in day_map:
                    weekdays = weekdays.replace(d[0], d[1])
                if str(weekday) not in weekdays:
                    continue
                t = event[1]  # Time format: 'hhmm'
                if int(t[:2]) != hour or int(t[2:]) != minute:
                    continue
                # Time for an event! Do something?
                if (event[2] not in ('ac', 'heat', 'fan') or
                    event[3] not in ('on', 'off', 'auto')):
                    continue
                props['status_%s' % event[2]] = event[3]
                if event[4].isdecimal():
                    props['trigger_temp'] = int(event[4])
                storeobject('props', props)


def getoutsidetemp():
    props = loadobject('props')

    url = 'http://api.worldweatheronline.com/free/v2/weather.ashx'
    url += '?key=%s&q=%s&num_of_days=0&format=json' % (
          loadobject('weather_api_key'), loadobject('location'))
    try:
        data = json.loads(request.urlopen(url).readall().decode('utf-8'))
        return data['data']['current_condition'][0]['temp_%s' % props['units']]
    except (HTTPError, URLError) as e:
        logging.warning(e.args[0])
        return "err"


def gensecret():
    return ''.join(chr(random.randint(97, 122)) for i in range(64))


@app.route('/apigensalt', methods=['GET'])
def apigensecret():
    user = flask.request.args['user']
    api_user_salts[user] = gensecret()

    return api_user_salts[user]


def validateuser():
    if 'current_user' not in flask.session or not flask.session['current_user']:
        return False
    return True


def checkpassword(user, password_md5, secret_salt):
    """password_md5 should already be an md5 sum of the user's password,
    then md5'd again with the secret key before being sent over http"""
        
    with open('passwords.txt', 'r') as f:
        passwords = dict(line.split(':') for line in f.read().split())

    if password_md5 == md5((passwords[user] + secret_salt).encode('utf-8')).hexdigest():
        return True
    return False

@app.before_first_request
def onstart():
    # Use this function to initialize modules and global vars
    logging.basicConfig(filename='history.log', level=logging.WARNING,
                        format='%(asctime)s %(message)s')

    props = {}
    days_short = {'sunday': 'S', 'monday': 'M', 'tuesday': 'T', 'wednesday': 'W',
                  'thursday': 'Th', 'friday': 'F', 'saturday': 'Sa'}
    storeobject('days_short', days_short)
    
    try:
        props = loadobject('props')
    except FileNotFoundError:
        props['status_fan'] = 'auto'
        props['status_ac'] = 'off'
        props['status_heat'] = 'off'
        props['events'] = []
        props['trigger_temp'] = 75

    if not os.path.exists('settings.conf'):
        shutil.copy2('sample_settings.conf', 'settings.conf')

    with open('settings.conf', 'r') as settings_file:
        config = json.load(settings_file)

    IO.init(config)

    props['units'] = config['units']
    
    storeobject('weather_api_key', config['weather_api_key'])
    storeobject('location', config['location'])

    props['temp_inside'] = '%.1f' % IO.gettemp()
    props['temp_outside'] = getoutsidetemp()

    if not os.path.exists('passwords.txt'):
        with open('passwords.txt', 'w') as f:
            f.write('admin:%s\n' % md5(b'admin').hexdigest())

    storeobject('api_user_salts', {})
    
    storeobject('props', props)

    threading.Thread(target=periodicrun).start()


@app.route('/setstate', methods=['GET'])
def setstate():
    api_user_salts = loadobject('api_user_salts')
    if 'user' in flask.request.args:
        user = flask.request.args['user']
        password_md5 = flask.request.args['password_hash']
        if (not user in api_user_salts or
            not checkpassword(user, password_md5, api_user_salts[user])):

            return '403'
        # API will never see this new salt
        # This is just done to get rid of the old one
        api_user_salts[user] = gensecret()
    else:
        user = flask.session['current_user']
        
    storeobject('api_user_salts', api_user_salts)
    
    props = loadobject('props')

    if ('status_ac' in flask.request.args and
       ('status_heat' not in flask.request.args or flask.request.args['status_heat'] == 'off')):
        props['status_ac'] = flask.request.args['status_ac']
    if ('status_heat' in flask.request.args and
        ('status_ac' not in flask.request.args or flask.request.args['status_ac'] == 'off')):
        props['status_heat'] = flask.request.args['status_heat']

    if 'status_fan' in flask.request.args:
        props['status_fan'] = flask.request.args['status_fan']
    if 'trigger_temp' in flask.request.args:
        props['trigger_temp'] = int(flask.request.args['trigger_temp'])

    logging.warning('%s set fan:%s ac:%s heat:%s temp:%s' % (user, props['status_fan'], props['status_ac'],
                                                              props['status_heat'], props['trigger_temp']))

    storeobject('props', props)

    return flask.redirect('/')


@app.route('/newevent', methods=['GET'])
def newevent():
    validation = validateuser()
    if not validation:
        return flask.redirect('/')
        
    #with open('pickledb/days_short.pickle', 'rb') as days_short_file:
    #    days_short = pickle.load(days_short_file)
    days_short = loadobject('days_short')

    f = flask.request.args.copy()
    days = ''
    for day in f.getlist('days_select'):
        days += days_short[day]

    if f['mode_select'] == 'auto':
        temp = f['temp']
    else:
        temp = ''

    t = f['time']
    while len(t) < 4:
        t = '0' + t
    
    props = loadobject('props')

    props['events'].append([days, t, f['device_select'], f['mode_select'], temp])

    logging.warning('%s created event %s' % (flask.session['current_user'], str(props['events'][-1])))
    
    storeobject('props', props)

    return flask.redirect('/')


@app.route('/deleteevent', methods=['GET'])
def deleteevent():
    validation = validateuser()
    if not validation:
        return flask.redirect('/')

    eventIndex = int(flask.request.args['index'])
    
    props = loadobject('props')

    logging.warning('%s deleted event %s' % (flask.session['current_user'], str(props['events'][eventIndex])))

    props['events'].pop(eventIndex)
    
    storeobject('props', props)
    
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

    if 'session_salt' not in flask.session or flask.request.method == 'GET':
        flask.session['session_salt'] = gensecret()
        return flask.render_template('login.html', secret=flask.session['session_salt'])

    user = flask.request.form['username']
    password = flask.request.form['password']

    with open('passwords.txt', 'r') as f:
        passwords = dict(line.split(':') for line in f.read().split())

    if not checkpassword(user, password, flask.session['session_salt']):
        return flask.render_template('login.html', error='Invalid username or password',
                                     secret=flask.session['session_salt'])

    flask.session['session_salt'] = gensecret()  #Create a new secret after succesfful login
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
    if 'current_user' in flask.session and flask.session['current_user'] != 'admin':
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
    validation = validateuser()
    if not validation:
        return flask.redirect('/login')
    
    props = loadobject('props')
    
    page = flask.render_template('root.html', **dict(props, **flask.session))
    return page


@app.route('/api', methods=['GET'])
def api():
    """Get information only. json formatted"""

    return flask.render_template('api.html', **loadobject('props'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8056, debug=True, use_reloader=False)
