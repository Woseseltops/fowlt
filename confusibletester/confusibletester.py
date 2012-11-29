from __future__ import division
import random
import subprocess
import sys

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
    """Calculates accuracy, the confusible option distribution and the confusion matrices for the data""";

    confidence_list = [0, 0.05, 0.1, 0.15, 0.20, 0.25, 0.3, 0.35, 0.40, 0.45, 0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95,0.99];
    accuracies = {};
    confusion_matrices = {};

    for i in confidence_list:
        accuracies[i] = (calculate_accuracy(filename+'.test.IGTree.gr.out',i));

    distr = calculate_confusible_distribution(filename);

    #Create and test a file with errors added
    errorlines = make_error_file(filename + '.test',10,options);
    test(filename+'.test.errors',filename+'.train.IGTree');

    for i in confidence_list:
        print 'cm' + str(i);
        confusion_matrices[i] = calculate_confusion_matrix(filename+'.test.errors',errorlines,i,options);

    return accuracies, distr, confusion_matrices;

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

def calculate_confusion_matrix(filename,errorlines,threshold,options):
    """Calculate the cm by basically doing the test procedure again, but on a file with errors added""";
    
    f = open(filename+'.IGTree.gr.out','r');

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
        match = prediction.strip().lower() == actual_word.strip().lower();
        total_confidence = max(confidences.values())/sum(confidences.values());

        #Add data for accuracy
        if ' '.join(words[:7]).strip() in errorlines:
            if not match and total_confidence > threshold:
                tp += 1;
#                if threshold == 0.0:
#                    print('TP'+i);
            else:
                fn += 1;
#                if threshold == 0:
#                    print('FN'+i);
        else:
            if not match and total_confidence > threshold:
                fp += 1;
                if threshold == 0:
                    print('FP'+i);
            else:
                tn += 1;
#                if threshold == 0:              
#                    print('TN'+i);

    return (tp,fp,fn,tn);

def make_error_file(filename,error_proportion,options):
    """Substitutes a number of correct confusible options for the incorrect one.""";

    #Grab the data  
    lines = open(filename,'r').readlines();
    linenr = len(lines);
    errornr = round(linenr / error_proportion)

    errorline_nrs = [];

    #Decide on which lines to add errors
    while len(errorline_nrs) < errornr:
        line = random.randrange(linenr);

        if line not in errorline_nrs:
            errorline_nrs.append(line);

    #Add the errors
    open(filename+'.errors','w').write('')
    outputf = open(filename+'.errors','a'); 

    errorlines = [];

    for n,i in enumerate(lines):

        if n in errorline_nrs:    
            current_line = i.split(' ');
            new_line = ' '.join(current_line[:-2]);
            actual_word = current_line[-2].strip().lower();

            error = '';
            while error in ['',actual_word]:
                error = random.choice(options);

            new_line += ' '+ error +' \n';

           
            outputf.write(new_line);
            errorlines.append(new_line.strip());
        else:
            outputf.write(i);

    print(errorlines);
    return errorlines;

def make_large_error_file(filename,error_proportion,options):
    """For every line, also give the error variant""";

    #Grab the data  
    lines = open(filename,'r').readlines();
    linenr = len(lines);
    errornr = linenr;

    errorlines = [];

    #Decide on which lines to add errors
    for i in range(linenr*2):
        if i%2 == 1:
            errorlines.append(i);

    #Add the errors
    open(filename+'.errors','w').write('')
    outputf = open(filename+'.errors','a'); 

    for n,i in enumerate(lines):

        #Write the actual 
        outputf.write(i);

        current_line = i.split(' ');
        new_line = ' '.join(current_line[:-2]);
        actual_word = current_line[-2].strip().lower();

        error = '';
        while error in ['',actual_word]:
            error = random.choice(options);
        
        outputf.write(new_line + ' '+ error +'\n');

    return errorlines;

def show_metrics(output,accuracies,distribution,confusion_matrices):

    open(output,'w').write('');
    output = open(output,'a');

    output.write(' \nDISTRIBUTION PROPORTIONS\n');
    
    for k,v in distribution.items():
        output.write(str(k)+' '+str(v)+'\n');

    output.write(' \nPREDICTION ACCURACY\n');

    output.write('Threshold\tAccuracy\tCorrect\tTotal\n');

    for k,v in sorted(accuracies.items()):
        output.write(str(k)+'\t'+str(v[0])+'\t'+str(v[1])+'\t'+str(v[2])+'\n');

    output.write('\nCONFUSION MATRIX, NO ABSTAINING\n');
    cm = confusion_matrices[0];

    output.write('-True positive: '+str(cm[0])+'\n');
    output.write('-False positive: '+str(cm[1])+'\n');
    output.write('-False negative: '+str(cm[2])+'\n');
    output.write('-True negative: '+str(cm[3])+'\n');

    output.write('\nCONFUSION MEASURES, NO ABSTAINING\n');
    precision = cm[0] / (cm[0]+cm[1])
    recall = cm[0] / (cm[0]+cm[2])

    output.write('\n-Detection precision: '+str(precision)+'\n');
    output.write('-Detection recall: '+str(recall)+'\n');
    output.write('-Detection accuracy: '+str((cm[0] + cm[3])/ (sum(cm)))+'\n');
    output.write('-F-measure: '+ str(2 * ((precision * recall)/(precision + recall)))+'\n'); 

    output.write('\nDETECTION ACCURACY, ABSTAINING\n');

    output.write('Threshold\tAccuracy\n');

    for k,v in sorted(confusion_matrices.items()):
        output.write(str(k)+'\t'+str((v[0] + v[3])/ (sum(v)))+'\n');

    output.write('\nDETECTION F-MEASURE (PRECISION,RECALL), ABSTAINING\n');

    output.write('Threshold\tF-measure\tPrecision\tRecall\n');

    for k,v in sorted(confusion_matrices.items()):
        precision = v[0] / (v[0]+v[1])
        recall = v[0] / (v[0]+v[2])
        output.write(str(k)+'\t'+str(2 * ((precision * recall)/(precision + recall)))+'\t'+str(precision)+'\t'+str(recall)+'\n');

#=======

if len(sys.argv) != 2:
    print('confusibletester.py [inputfile]');
    quit();
else:
    filename = sys.argv[1];
    output = sys.argv[1] + '.output';

if 'bal' in filename:
    options = filename[:-9].split(',');
else:
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
accuracies, distribution, confusion_matrices = calculate_metrics(filename,options);
show_metrics(output,accuracies,distribution,confusion_matrices);

print('==Done');
