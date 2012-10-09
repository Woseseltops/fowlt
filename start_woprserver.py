from servers import serverhelp

settings = serverhelp.get_settings();

#Start up the WOPR server if the settings say so
print('Starting up server');

if settings['wopr_large_corpus'] == '1':
    serverhelp.command(settings['wopr_location']+' -r server_sc -p ibasefile:servers/BNC.ibase,timbl:"-a1 +D",lexicon:servers/BNC.lex,port:2001,keep:1,mwl:5,max_distr:250,min_ratio:100');

elif settings['wopr_large_corpus'] == '0':
    serverhelp.command(settings['wopr_location']+' -r server_sc -p ibasefile:servers/BNC_small.ibase,timbl:"-a1 +D",lexicon:servers/BNC_small.lex,port:2001,keep:1,mwl:5,max_distr:250,min_ratio:100');
