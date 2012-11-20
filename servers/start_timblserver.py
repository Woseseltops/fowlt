import serverhelp
import os

settings = serverhelp.get_settings();

#Start up timbl server
serverhelp.command(settings['timblserver_location']+' --config=timblservers/confusibles.conf --pidfile=' +os.getcwd() +'/pid &',True);

