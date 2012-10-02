import sys

def provide_window(position,words_around):
    new_position = position + 3;
    left = words_around[new_position-3:new_position];
    right = words_around[new_position+1:new_position+4];

    return ' '.join(left) + ' ' + ' '.join(right);
    
#Get input files
try:
    searchstrings = sys.argv[1].split(',');

    #Correct the string for input issues
    for n,i in enumerate(searchstrings):
        searchstrings[n] = searchstrings[n].replace("\'","'");

    corpus = sys.argv[2];

    print('Looking for '+str(searchstrings));
except:
    print('cofusible.py [searchstring1,searchstring2,searchstring3] [corpus]');
    quit();

lines = open(corpus,'r').readlines();

#Prepare output
outputfile = sys.argv[1];
output = '';

#Walk through the lines
for nl, l in enumerate(lines):
    l = l.replace('\n','');

    try:
        previous_line = lines[nl-1].replace('\n','');
    except:
        previous_line = '_ _ _ _ _';

    try:
        next_line = lines[nl+1].replace('\n','');
    except:
        next_line = '_ _ _ _ _';
    
    words = l.split(' ');
    words_around = previous_line.split(' ')[-3:] + words + next_line.split(' ')[:3];

    #Check for each search string
    for ss in searchstrings:

        for nw, w in enumerate(words):
            if ss == w:

                window = provide_window(nw,words_around);               
                output += window + ' ' + w + ' ' + '\n';

open(outputfile,'w').write(output);

#TODO
# Bij inputregels korter dan drie woorden raakt ie in de problemen
