from __future__ import division
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

    #Calculate how muchsenteces to take
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

def calculate_metrics(filename,options):
    """Calculates all metrics""";

    accuracies = {};

    for i in [0, 0.05, 0.1, 0.15, 0.20, 0.25, 0.3, 0.35, 0.40, 0.45, 0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95,0.99]:
        accuracies[i] = (calculate_accuracy(filename+'.test.IGTree.gr.out',i));

    distr = calculate_confusible_distribution(filename);

    confusion_matrix = calculate_confusion_matrix(filename,0,options);

    return accuracies, distr, confusion_matrix;

def calculate_accuracy(filename,threshold):

    f = open(filename,'r');

    total = 0;
    correct = 0;

    for i in f:
        #Grab all needed values from output file
        words, raw_confidences = i.split('{');
        words = words.split(' ');
        actual_word = words[-2];
        prediction = words[-3];
        raw_confidences = raw_confidences[:-2].split(',');
        confidences = {};
        
        for j in raw_confidences:
            key, value = j.strip().split(' '); 
            confidences[key.strip()] = float(value.strip());

        #Check for match, calculate confidence
        match = prediction == actual_word;
        total_confidence = max(confidences.values())/sum(confidences.values());


        #Add data for accuracy
        if total_confidence > threshold:
            total += 1;
            if match:
                correct += 1;

    return (correct/total,correct,total);

def calculate_confusible_distribution(filename):

    confusible_options = {};
    total = 1;

    f = open(filename,'r');

    for i in f:
        #Get the word (last one of this line)
        option = i.split(' ')[-2];

        #Count the confusible options
        if option in confusible_options.keys():
            confusible_options[option] += 1;
        else:
            confusible_options[option] = 1;
        total += 1;

    #Counts -> proportions
    for i in confusible_options:
        confusible_options[i] = confusible_options[i] / total;

    return confusible_options;

def calculate_confusion_matrix(filename,threshold,options):

    #Test an alternative test file, with errors added
    errorlines = make_error_file(filename + '.test',10,options);
    test(filename+'.test.errors',filename+'.train.IGTree');

    f = open(filename+'.test.errors.IGTree.gr.out','r');

    tp = 0;
    fp = 0;
    fn = 0;
    tn = 0;

    for n, i in enumerate(f):
        #Grab all needed values from output file
        words, raw_confidences = i.split('{');
        words = words.split(' ');
        actual_word = words[-2];
        prediction = words[-3];
        raw_confidences = raw_confidences[:-2].split(',');
        confidences = {};
        
        for j in raw_confidences:
            key, value = j.strip().split(' '); 
            confidences[key.strip()] = float(value.strip());

        #Check for match, calculate confidence
        match = prediction == actual_word;
        total_confidence = max(confidences.values())/sum(confidences.values());

        #Add data for accuracy
        if total_confidence > threshold:
            if n in errorlines:
                if not match:
                    tp += 1;
                else:
                    fn += 1;
            else:
                if not match:
                    fp += 1;
                else:
                    tn += 1;             

    return (tp,fp,fn,tn);

def make_error_file(filename,error_proportion,options):
    """Substitutes a number of correct confusible options for the incorrect one.""";

    #Grab the data  
    lines = open(filename,'r').readlines();
    linenr = len(lines);
    errornr = round(linenr / error_proportion)

    errorlines = [];

    #Decide on which lines to add errors
    while len(errorlines) < errornr:
        line = random.randrange(linenr);

        if line not in errorlines:
            errorlines.append(line);

    #Add the errors
    open(filename+'.errors','w').write('')
    outputf = open(filename+'.errors','a'); 

    for n,i in enumerate(lines):

        if n in errorlines:    
            current_line = i.split(' ');
            new_line = ' '.join(current_line[:-2]);
            actual_word = current_line[-2];

            error = '';
            while error in ['',actual_word]:
                error = random.choice(options);
            
            outputf.write(new_line + ' '+ error +'\n');
        else:
            outputf.write(i);

    return errorlines;

#=======

filename = 'advice,advise.inst';

options = filename[:-5].split(',');

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
accuracies, distribution, cm = calculate_metrics(filename,options);

print(' \n-Distribution proportions:');

for k,v in distribution.items():
    print k,v;

print(' \n-Prediction accuracy');

for k,v in sorted(accuracies.items()):
    print k,v;

print '\n-True positive: ',cm[0];
print '-False positive: ',cm[1];
print '-False negative: ',cm[2];
print '-True negative: ',cm[3];

precision = cm[0] / (cm[0]+cm[1])
recall = cm[0] / (cm[0]+cm[2])

print '\n-Detection precision: ', precision;
print '-Detection recall: ', recall;
print '-Detection accuracy: ', (cm[0] + cm[3])/ (sum(cm));
print '-F-measure: ', 2 * ((precision * recall)/(precision + recall)); 

print('==Done');
