import subprocess

def command(command,piped = False):

    if piped:
        result = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE).communicate()[0].decode();
    else:
        result = subprocess.Popen(command, shell=True).communicate()[0].decode();
    print(result);

def get_settings():
    raw_settings = open('server_settings','r').readlines();
    settings = {};

    for i in raw_settings:
        key, value = i.split(' ');
        settings[key] = value[:-1];

    return settings;
