from servers import serverhelp

settings = serverhelp.get_settings();

#Start up timbl server
serverhelp.command(settings['timblserver_location']+' --config=servers/confusibles.conf');

