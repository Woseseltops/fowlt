import serverhelp

pid = open('pid','r').read();
try:
    serverhelp.command('kill '+pid);
except AttributeError:
    pass;
