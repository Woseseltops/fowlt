import sys
import subprocess

def command(command):
    command = command.split(' ');
    result = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0].decode();
    print(result);

def add_three_words_right(lines,nl):
    wordpointer = 0;
    linepointer = 1;
    next_line = [];

    while len(next_line) < 3:
       
        words_to_investigate = lines[nl + linepointer].replace('\n','').split(' ');

        if len(words_to_investigate) == wordpointer:
            linepointer+= 1;
            words_to_investigate = lines[nl + linepointer].replace('\n','').split(' ');       
            wordpointer = 0;

        next_line.append(words_to_investigate[wordpointer]);    
        wordpointer += 1;
        
    return next_line;

def add_three_words_left(lines,nl):
    wordpointer = 1;
    linepointer = 1;
    previous_line = [];

    while len(previous_line) < 3:
       
        words_to_investigate = lines[nl - linepointer].replace('\n','').split(' ');

        if len(words_to_investigate) == wordpointer-1:
            linepointer+= 1;
            words_to_investigate = lines[nl - linepointer].replace('\n','').split(' ');       
            wordpointer = 1;

        previous_line.insert(0,words_to_investigate[-wordpointer]);    
        wordpointer += 1;
        
    return previous_line;

def provide_window(position,words_around):
    new_position = position + 3;
    left = words_around[new_position-3:new_position];
    right = words_around[new_position+1:new_position+4];

    return ' '.join(left) + ' ' + ' '.join(right);

###### Script starts here #######
    
#Get input files
try:
    searchstrings = sys.argv[1].split(',');

    #Correct the string for input issues
    for n,i in enumerate(searchstrings):
        searchstrings[n] = searchstrings[n].replace("\'","'");

    corpus = sys.argv[2];

    print('Looking for '+str(searchstrings));
except:
    print('confusible.py [searchstring1,searchstring2,searchstring3] [corpus]');
    quit();

lines = ['_ _ _'] + open(corpus,'r').readlines() + ['_ _ _'];

#Prepare output
outputfile = sys.argv[1];
output = '';

#Walk through the lines
for nl, l in enumerate(lines):
    l = l.replace('\n','');
  
    words = l.split(' ');

    #Check for each search string
    for ss in searchstrings:

        for nw, w in enumerate(words):
            if ss.lower() == w.lower():

                previous_line = add_three_words_left(lines,nl);
                next_line = add_three_words_right(lines,nl);
                words_around = previous_line + words + next_line;

                window = provide_window(nw,words_around);               
                output += window + ' ' + w + ' ' + '\n';

#Save the instances
open(outputfile+'.inst','w').write(output);
print('Instance file saved');

#Train with Timbl
print('Starting up Timbl');
command('timbl -f '+outputfile+'.inst -a1 +D +vdb -I '+outputfile+'.IGTree');
print('Done');
