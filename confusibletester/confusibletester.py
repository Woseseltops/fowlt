import random
import subprocess

def command(command):
    command = command.split(' ');
    result = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0].decode();
    print(result);

def split(filename,testpart):
    """Splits the data into a trainingfile and a testfile, based on the proportion in testpart."""

    #Load the data
    lines = open(filename,'r').readlines();

    #Calculate how senteces to take
    testpart_size = int(round(len(lines)*testpart));

    #Take this number of sentences
    testcorpus = [];
    for i in range(testpart_size):
        testcorpus.append(lines.pop(random.randrange(len(lines))));

    #Save the result
    open(filename+'.train','w').write(''.join(lines));
    open(filename+'.test','w').write(''.join(testcorpus));

def train(filename):
    command('timbl -f '+filename+' -a1 +D +vdb -I '+filename+'.IGTree');

def test(filename,model):
    command('timbl -t '+filename+' -i '+model+' -a1 +D +vdb');

def calculate_metrics(filename):
    """Calculates x and x and x""";

    f = open(filename,'r');

    for i in f:
        raw_confidences = i.split('{')[1][:-2].split(',');
        confidences = {};

        for j in raw_confidences:
            key, value = j.strip().split(' ');
            confidences[key.strip()] = float(value.strip());

        print(confidences)
        print(max(confidences.values())/sum(confidences.values()));

#=======

filename = 'advice,advise.inst';

print('==Splitting data');
split(filename,0.1);
print('==Done');

print('==Training Timbl');
train(filename+'.train');
print('==Done');

print('==Testing the model');
test(filename+'.test',filename+'.train.IGTree');
print('==Done');

print('==Calculating metrics');
metrics = calculate_metrics(filename+'.test.IGTree.gr.out');
print(metrics);
print('==Done');
