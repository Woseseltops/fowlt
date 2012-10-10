import serverhelp

settings = serverhelp.get_settings();

#Start up timbl server
serverhelp.command(settings['timblserver_location']+' --config=timblservers/confusibles.conf',True);

