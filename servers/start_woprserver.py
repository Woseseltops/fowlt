import serverhelp

settings = serverhelp.get_settings();

#Start up the WOPR server if the settings say so
print('Starting up server');

try:
    if settings['wopr_large_corpus'] == '1':
        serverhelp.command(settings['wopr_location']+' -r server_sc -p ibasefile:woprserver/BNC.ibase,timbl:"-a1 +D",lexicon:woprserver/BNC.lex,port:3001,keep:1,max_distr:250');

    elif settings['wopr_large_corpus'] == '0':
        serverhelp.command(settings['wopr_location']+' -r server_sc -p ibasefile:woprserver/BNC_small.ibase,timbl:"-a1 +D",lexicon:woprserver/BNC_small.lex,port:3001,keep:1,max_distr:250');

except AttributeError:
    print('An error occured. Make sure all your settings are correct.');
