import sys
import subprocess

class Buff():
    def __init__(self,searchstrings):
        self.buff = {};
        self.searchstrings = searchstrings;

        for ss in self.searchstrings:
            self.buff[ss] = [];

    def add_output(self,output,searchword):
        self.buff[searchword].append(output);
        all_filled = True;
        return_string = '';

        for ss in self.buff:
            if len(self.buff[ss]) == 0:
                all_filled = False;
                break;

        if all_filled:
            for ss in self.buff:
                return_string+= self.buff[ss].pop();

        return return_string;

def command(command):
    command = command.split(' ');
    result = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0].decode();
    print(result);

def clean(string):
    while '  ' in string:
        string = string.replace('  ',' ');
    
    if string[-1] == ' ':
        string = string[:-1];

    return string.replace('\n','');

def add_three_words_right(lines,nl):
    wordpointer = 0;
    linepointer = 1;
    next_line = [];

    while len(next_line) < 3:
       
        words_to_investigate = clean(lines[nl + linepointer]).split(' ');

        if len(words_to_investigate) == wordpointer:
            linepointer+= 1;
            words_to_investigate = clean(lines[nl + linepointer]).split(' ');       
            wordpointer = 0;

        next_line.append(words_to_investigate[wordpointer]);    
        wordpointer += 1;
        
    return next_line;

def add_three_words_left(lines,nl):
    wordpointer = 1;
    linepointer = 1;
    previous_line = [];

    while len(previous_line) < 3:
       
        words_to_investigate = clean(lines[nl - linepointer]).split(' ');

        if len(words_to_investigate) == wordpointer-1:
            linepointer+= 1;
            words_to_investigate = clean(lines[nl - linepointer]).split(' ');       
            wordpointer = 1;

        previous_line.insert(0,words_to_investigate[-wordpointer]);    
        wordpointer += 1;
        
    return previous_line;

def provide_window(position,words_around,error_as_feature):
    new_position = position + 3;
    left = words_around[new_position-3:new_position];
    right = words_around[new_position+1:new_position+4];

    #Normally don't display the error
    if not error_as_feature:
        error = '';
    else:
        error = words_around[new_position] + ' ';

    return ' '.join(left) + ' ' + error + ' '.join(right);

###### Script starts here #######
    
#Get input files
try:
    searchstrings = sys.argv[1].split(',');

    #Correct the string for input issues
    for n,i in enumerate(searchstrings):
        searchstrings[n] = searchstrings[n].replace("\'","'");

    corpus = sys.argv[2];

    if '-balanced' in sys.argv:
        balanced = True;
        print('Creating a balanced instance file with '+str(searchstrings));
    else:
        balanced = False;
        print('Creating a non-balanced instance file with '+str(searchstrings));    

    if '-error_as_feature' in sys.argv:
        error_as_feature = True;
    else:
        error_as_feature = False;
    
except:
    print('confusible.py searchstring1,searchstring2,searchstring3 corpus [-balanced] [-error_as_feature]');
    quit();

lines = ['_ _ _'] + open(corpus,'r').readlines() + ['_ _ _'];

#Prepare output
outputfile = sys.argv[1];
output = '';

sentence_buffer = Buff(searchstrings);

#Walk through the lines
for nl, l in enumerate(lines):
    l = clean(l);
  
    words = l.split(' ');

    #Check for each search string
    for ss in searchstrings:

        for nw, w in enumerate(words):
            if ss.lower() == w.lower():

                previous_line = add_three_words_left(lines,nl);
                next_line = add_three_words_right(lines,nl);
                words_around = previous_line + words + next_line;

                window = provide_window(nw,words_around,error_as_feature);

                if not balanced:
                    output += window + ' ' + w + ' ' + '\n';
                else:
                    output += sentence_buffer.add_output(window + ' ' + w + ' ' + '\n',ss.lower());

#Save the instances
open(outputfile+'.inst','w').write(output);
print('Instance file saved');

#Train with Timbl
#print('Starting up Timbl');
#command('timbl -f '+outputfile+'.inst -a1 +D +vdb -I '+outputfile+'.IGTree');
#print('Done');
