import subprocess

def command(command):
#    command = command.split(' ');
#    for n,i in enumerate(command):
#        command[n] = i.replace('__',' ');
    result = subprocess.Popen(command, shell=True).communicate()[0].decode();
    print(result);

def get_settings():
    raw_settings = open('./server settings','r').readlines();
    settings = {};

    for i in raw_settings:
        key, value = i.split(' ');
        settings[key] = value[:-1];

    return settings;
