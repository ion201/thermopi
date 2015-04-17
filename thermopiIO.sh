#!/bin/sh

### BEGIN INIT INFO
# Provides:             theropiIO
# Required-Start:       $local_fs
# Required-Stop:        $local_fs
# Default-Start:        2 3 4 5
# Default-Stop:         0 1 6
# Short-Description:    Start and stop GPIO service for thermopi
# Description:          Start and stop GPIO service for thermopi
### END INIT INFO

PIDFILE='/tmp/IOService.pid'
EXEC='/srv/thermopi/IOService.py'

check_root() {
    if [[ $(id -u) -ne 0 ]]
    then
        echo 'This script must be run as root'
        exit 2
    fi
}

check_running() {
    if [[ ! $(tr -d "\r\n" < $PIDFILE|wc -c) -eq 0 ]]
    # If the file has content, check the pid
    then
        if [ -n "$(ps aux | grep $(cat $PIDFILE) | grep -v grep)" ]
        # If the pid is already running; ignore
        then
            IS_RUNNING=1
            return
        fi
    fi
    IS_RUNNING=0;
}

case $1 in
start)

    check_root
    
    check_running

    if [ $IS_RUNNING == 1 ]
    then
        echo IOService.py already running with pid `cat $PIDFILE`
        exit 2
    fi
    $EXEC &
    PID=`pidof -sx $EXEC`
    echo $PID > $PIDFILE
    echo Starting IOService.py with pid $PID
    ;;
    
stop)
    
    check_root
    
    check_running

    if [ $IS_RUNNING == 1 ]
    then
        echo Killing instances with pid `pidof -x $EXEC`
        kill $(pidof -x $EXEC)
    else
        echo 'thermopiIO.py is not running...'
    fi
    echo > $PIDFILE
    ;;
    
restart)
    check_root
    $0 stop
    $0 start
    ;;
    
status)
    check_running
    if [ $IS_RUNNING == 1 ]
    then
        PID=`pidof -sx $EXEC`
        echo thermopiIO is running with pid $PID
    else
        echo 'thermopiIO is not running'
    fi
    ;;
    
*)
    echo 'Usage: service {start|stop|restart}'
    exit 2
    ;;
    
esac

exit 0
