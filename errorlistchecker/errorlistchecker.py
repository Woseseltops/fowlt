#------------------------------------------------------------------
# A checker that knows a lot of error-correction pairs and serves
# the corrections upon seeing an error
#------------------------------------------------------------------

import sys

def load_errors_and_corrections(errorlist):
    """Load the errors as a string, and the corrections as a dictionary with the errors as keys""";
    errorlist = open(errorlist).readlines();

    errors = [];
    corrections = {};

    for e in errorlist:
        err_corr_pair = e.split('#');
        error = err_corr_pair[0];
        correction = err_corr_pair[1:-1];
        
        errors.append(error);
        corrections[error] = correction;

    return errors,corrections;        

########################## SCRIPT STARTS HERE ###################################

#Catch cmd arguments
try:
    inputfile = sys.argv[1];
    errorlist = sys.argv[2];
    outputfile = sys.argv[3];
except:
    print('errorlistchecker.py [inputfile] [errorlist] [outputfile]');
    quit();

#Load errors and corrections
errors, corrections = load_errors_and_corrections(errorlist);

#For each word in the input, add corrections if it is in the errorlist
words = open(inputfile,'r').read().split(' ');
output = '';

for w in words:

    if len(w) > 1 and '<utt>' not in w:

        if w in errors:
            output += w + ' ' + ' '.join(corrections[w]) + '\n';
            continue;
    
    output += w + '\n';

#Write output
f = open(outputfile,'w');

f.write(output);
f.close();
