import sys
from pynlpl.formats import folia

def detect_splits_and_merges(word,threshold):
    """Return suggestions for splits and merges with a confidence above the given threshold"""

    larger_correction = word.incorrection()
    if larger_correction and larger_correction.confidence > threshold:
        return larger_correction.suggestions()[0];   
    else:
        return None;

def detect_normal_corrections(word,threshold):
    """Return suggestions for normal corrections with a confidence above the given threshold"""

    try:
        correction = word.getcorrection();                   

        if correction.confidence > threshold and correction.hassuggestions():
            return correction.suggestions()[0];
        else:
            return None;

    except folia.NoSuchAnnotation:  
        return None;

#--------------

#Collect parameter values
try:
    inputfile = sys.argv[1];
    threshold = float(sys.argv[2]);

#Not enough? Show syntax
except IndexError:
    print('Syntax: fowlt2text.py input.txt confidence_threshold');
    quit();

#Preparations
output_paragraphs = [];
corrections_handled = [];
doc = folia.Document(file=inputfile);

#Iterate through all paragraphs
for paragraph in doc.paragraphs():

    current_paragraph = '';

    #For each word, try to find split, merges, and normal corrections
    for word in paragraph.words():

        suggestion = detect_splits_and_merges(word,threshold);
        
        if not suggestion:
            suggestion = detect_normal_corrections(word,threshold);

        #Add your discoveries to the output
        if suggestion:          

            #Don't handle the same correction twice (happens with merges)
            if suggestion.parent.id not in corrections_handled:
                current_paragraph += ' '+str(suggestion);
                corrections_handled.append(suggestion.parent.id);
        else:
            current_paragraph += ' '+str(word);

    output_paragraphs.append(current_paragraph.strip());

#Rebuild the text on the basis of the corrected paragraphs
print('\n\n'.join(output_paragraphs));
