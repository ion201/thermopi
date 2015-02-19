#WSGI has a much stricter environment than simply running
#the script with python. This is a problem and using this file
#will produce internal server errors
import sys
sys.path.insert(0, '/srv/thermopi')
from Server import app as application
