#!/bin/bash

if [[ $(id -u) -ne 0 ]]
then
    echo 'This script must be run as root'
    exit 0
fi

if [ `pwd` != '/srv/thermopi' ]
then
    # Copy the files
    cp -r ../thermopi /srv/
    cd /srv/thermopi
fi

if [ `pidof systemd` ]
then
    # Run installer for systemd components
else
    # Let's assume if it's not systemd it will use /etc/init.d
fi
