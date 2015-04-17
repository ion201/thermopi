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

# TODO: instructions for setting apache settings
