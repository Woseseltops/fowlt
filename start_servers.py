import subprocess

def command(command):
    command = command.split(' ');
    result = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0].decode();
    print(result);

#Get settings
raw_settings = open('server settings','r').readlines();
settings = {};

for i in raw_settings:
    key, value = i.split(' ');
    settings[key] = value[:-1];

#Start up timbl server
command(settings['timblserver_location']+' --config=timbl_servers/confusibles.conf');
