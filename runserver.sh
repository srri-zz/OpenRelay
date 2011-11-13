# From http://nathanvangheem.com/news/gunicorn-startup-script-for-django
#!/bin/sh
ADDRESS='127.0.0.1'
GUNICORN="gunicorn_django"
PROJECTLOC="."
PIDLOC="/tmp"
WORKERS=2
DEFAULT_ARGS="--workers=$WORKERS --daemon --bind=$ADDRESS:"
BASE_CMD="$GUNICORN $DEFAULT_ARGS"

SERVER1_PORT='8000'
SERVER1_PID="$PIDLOC/$SERVER1_PORT.pid"

start_server () {
  if [ -f $1 ]; then
    #pid exists, check if running
    if [ "$(ps -p `cat $1` | wc -l)" -gt 1 ]; then
       echo "Server already running on ${ADDRESS}:${2}"
       return
    fi
  fi
  cd $PROJECTLOC
  echo "starting ${ADDRESS}:${2}"
  $BASE_CMD$2 --pid=$1 settings_local_server.py
}

stop_server (){
  if [ -f $1 ] && [ "$(ps -p `cat $1` | wc -l)" -gt 1 ]; then
    echo "stopping server ${ADDRESS}:${2}"
    kill -9 `cat $1`
    rm $1
  else 
    if [ -f $1 ]; then
      echo "server ${ADDRESS}:${2} not running"
    else
      echo "No pid file found for server ${ADDRESS}:${2}"
    fi
  fi
}

case "$1" in
'start')
  start_server $SERVER1_PID $SERVER1_PORT 
  ;;
'stop')
  stop_server $SERVER1_PID $SERVER1_PORT
  ;;
'restart')
  stop_server $SERVER1_PID $SERVER1_PORT
  sleep 2
  start_server $SERVER1_PID $SERVER1_PORT
  ;;
*)
  echo "Usage: $0 { start | stop | restart }"
  ;;
esac

exit 0
