#!/bin/bash

if [[ $(id -u) -ne 0 ]]
then
    echo 'This script must be run as root'
    exit 0
fi

if [ `pwd` != '/srv/thermopi' ]
then
    echo -n 'Copying files to /srv... '
    rsync -rog ../thermopi /srv/
    cd /srv/thermopi
    echo 'Done!'
fi

#Get the system's package manager
commandExists(){
    [ $(which $1) ]
}

echo -n 'Installing dependencies... '
if commandExists apt-get
then
    apt-get install apache2 libapache2-mod-wsgi-py3

elif commandExists pacman
then
    pacman -S apache mod_wsgi
else
    echo 'Package manager not supported! Continue [y]/n?'
    while read a;
    do
        if [[ $a == 'n' || $a == 'N' ]]
        then
            echo 'Canceling installation...'
            exit
        fi
    done
fi

echo 'Done!'

if [ `pidof systemd` ]
then
    # Run installer for systemd components
    echo -n 'Installing and starting systemd service... '
    cp thermopiIO.service /etc/systemd/system/
    systemctl enable thermopiIO
    systemctl start thermopiIO
    echo 'Done!'
else
    # Let's assume if it's not systemd it will use /etc/init.d
    echo 'You should be using systemd...'
    echo -n 'Installing and starting service thermopiIO... '
    cp thermopiIO.sh /etc/init.d/
    service thermopiIO start
    echo 'Done!'
fi

echo 'Add the following to your apache virtual hosts file and restart apache:'
echo 'listen 80
<VirtualHost *:80>

    DocumentRoot /srv/thermopi
    ServerName yourdomain.com:80
    
    WSGIDaemonProcess thermopiServer user=<user> group=<group> threads=5
    WSGIScriptAlias / /srv/thermopi/Server.wsgi
    
    <Directory /srv/thermopi>
        Require all granted
        
        WSGIProcessGroup thermopiServer
        WSGIApplicationGroup %{GLOBAL}
        
    </Directory>
    
</VirtualHost>'

