#----------------------------------------------
#   Master script for Fowlt processing chain
#----------------------------------------------

import sys
import os
import codecs
import datetime
import shutil
from threading import Thread
from Queue import Queue
from pynlpl.textprocessors import Windower
import pynlpl.formats.folia as folia


#################### ABSTRACT MODULE  #################################

class AbstractModule(object): #Do not modify
    def __init__(self, doc, rootdir, outputdir, idmap, threshold, settings):
        self.doc = doc
        self.rootdir = rootdir
        self.outputdir = outputdir
        self.done = False
        self.failed = False
        self.idmap = idmap
        self.accuracy_level = self.set_accuracy_level(threshold);
	self.settings = settings
        super(AbstractModule, self).__init__()

        if threshold in ['SA','A','T']:
            if self.accuracy_level:
                self.threshold = self.accuracy_level[threshold];
            else:
                self.threshold = 0.5
        else:            
            self.threshold = threshold;

    def errout(self,msg):
        s = "[" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] PROCESSING-CHAIN ['+self.NAME+']: ' + msg        
        try:
            print >>sys.stderr, s.encode('utf-8')
        except:
            pass
    
    def runcmd(self,cmd):
        global statusfile
        if not standalone:
            clam.common.status.write(statusfile, "Running module " + self.NAME,50)
        errout("\tCalling module " + self.NAME + ": " + cmd)
        r = os.system(cmd)        
        if r:
            self.errout("\tModule failed!")
            self.failed = True
        else:
            self.done = True
            self.errout("\tModule done")
            
    def readcolumnedoutput(self, outputfile):
        f = codecs.open(outputfile,'r','utf-8')
        for linenumber, instance in enumerate(f.readlines()):
            #get the Word ID based on line number
            try:
                wordid = self.idmap[linenumber]
            except IndexError:
                self.errout("ERROR processing results of module " + self.NAME + ": Unable to find word ID for line  " + str(linenumber))
                continue
            
            #get the word with that ID from the FoLiA document
            try:
                word = self.doc.index[wordid]
            except KeyError:
                self.errout("Unable to find word with ID: " + wordid)
                continue
            
            #split the instance line into multiple fields
            fields = instance.split(' ')
            
            yield word, fields
                            
            
        f.close()

    def set_accuracy_level(self,threshold):

        return False;

    def addcorrection(self, word, **kwargs  ):                
    
        self.errout("Adding correction for " + word.id + " " + str(word))
        
        #Determine an ID for the next correction    
        correction_id = word.generate_id(folia.Correction)        
            
        if 'suggestions' in kwargs:
            #add the correction
            word.correct(         
                suggestions=kwargs['suggestions'],
                id=correction_id,
                set='fowltset',
                cls=kwargs['cls'],            
                annotator=kwargs['annotator'],
                annotatortype=folia.AnnotatorType.AUTO,
                datetime=datetime.datetime.now()
            )
        elif 'suggestion' in kwargs:
            #add the correction
            word.correct(         
                suggestion=kwargs['suggestion'],
                id=correction_id,
                set='fowltset',
                cls=kwargs['cls'],            
                annotator=kwargs['annotator'],
                annotatortype=folia.AnnotatorType.AUTO,
                datetime=datetime.datetime.now()
            )
        else:
            raise Exception("No suggestions= specified!")
            

    def adderrordetection(self, word, **kwargs):
        self.errout("Adding correction for " + word.id + " " + str(word))

        
        #add the correction
        word.append(         
            folia.ErrorDetection(
                self.doc, 
                set='Fowltset',
                cls=kwargs['cls'],            
                annotator=kwargs['annotator'],
                annotatortype='auto',
                datetime=datetime.datetime.now()
            )
        )    
        
    def splitcorrection(self, word, newwords,**kwargs):

	str_newwords = '';

	for nw in newwords:
	    str_newwords += str(nw)+' ';

        self.errout("Splitting " + str(word) + " into " + str_newwords);

        sentence = word.sentence()
        newwords = [ folia.Word(self.doc, generate_id_in=sentence, text=w) for w in newwords ]        
        kwargs['suggest'] = True
        kwargs['datetime'] = datetime.datetime.now()
        word.split(
            *newwords,
            **kwargs
        )
        
    def mergecorrection(self, newword, originalwords, **kwargs):

	str_originalwords = '';

	for ow in originalwords:
	    str_originalwords += str(ow)+' ';

        self.errout("Merging " + str_originalwords + " into " + newword);

        sentence = originalwords[0].sentence()
        if not sentence:
            raise Exception("Expected sentence for " + str(repr(originalwords[0])) + ", got " + str(repr(sentence)))
        newword = folia.Word(self.doc, generate_id_in=sentence, text=newword)         
        kwargs['suggest'] = True
        kwargs['datetime'] = datetime.datetime.now()
        sentence.mergewords(
            newword,        
            *originalwords,
            **kwargs
        )
                
    
        
        
#################### MODULE DEFINITIONS #################################

class ErrorListModule(AbstractModule):
    NAME = "errorlistmodule"
 
    def process_result(self):                
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'errorlist_checker.test.out'):                                            
                if len(fields) > 1:
                    #Add correction suggestion
                    #(The last field holds the suggestion? (assumption, may differ per module))
                    suggs = [];
                    splits = [];
                    for x in fields[1:]:
                        corr = str(x.strip());
                        if corr != str(word) and '__' not in corr:
                            suggs.append(corr);
                        elif '__' in corr: 
                            splits+= corr.split('__');

                    if len(suggs) > 0:                            
                        self.addcorrection(word, suggestions=suggs, cls='Frequent-mistake', annotator=self.NAME)

                    if len(splits) > 0:
                        self.splitcorrection(word, splits, cls='Frequent-mistake', annotator=self.NAME)

            f.close()        
            
    def run(self):
        self.errout("MODULE: " + self.NAME)
                
        #Call module and ask it to produce output
        self.runcmd('python ' + self.rootdir + 'errorlistchecker/errorlist_checker.py ' + self.rootdir + 'output/input.tok.txt ' + self.rootdir + 'errorlistchecker/fowlt_errorlist ' + self.outputdir + 'errorlist_checker.test.out')

# --- Add new module classes here, and don't forget to declare them in the list below: ---

class LexiconModule(AbstractModule):
    NAME = "lexiconmodule"
    
    def process_result(self):

	#Load exceptions
	exceptions = open('lexiconchecker/exceptions','r').read().strip().split('\n');

        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'lexicon_checker.test.out'):                                            
                if len(fields) >= 2 and str(word).lower() not in exceptions:
                    #Add correction suggestion
                    #(The last field holds the suggestion? (assumption, may differ per module))
		    suggs = [];
		    for x in fields[1:]:
                        
                        if str(x.strip()).lower() != str(word).lower():
                            suggs.append(x.strip());
                        
                    if len(suggs) > 0:
                        self.addcorrection(word, suggestions=suggs, cls='Looked-like-frequent-word', annotator=self.NAME)
            f.close()                  
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'lexiconchecker/lexicon_checker ' + self.rootdir + 'lexiconchecker/freqlist_google_formatted ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'lexicon_checker.test.out')

class SplitCheckerModule(AbstractModule): #(merges in FoLiA terminology)
    NAME = "splitcheckermodule"
    
    def process_result(self):
        if self.done:
            merges = []
            merge = []
            text = []
            prev = ''
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'split_checker.test.out'):           
                if len(fields) >= 2:
                    #Add correction suggestion                
                    if prev and fields[-1] != prev:
                        if merge: 
                            merges.append(merge)
                            text.append(prev)
                            merge = []
                    else:
                        merge.append(word)
                    prev = fields[-1]
                else:
                    if merge: 
                        merges.append(merge)
                        text.append(prev)
                        merge = []  
                    prev = ''
            if merge: 
                merges.append(merge)      
                text.append(prev)
            f.close()                  
            for i, mergewords in enumerate(merges):
                #Add correction suggestion
                newword = text[i].strip()
                self.mergecorrection(newword, mergewords, cls='space-error', annotator=self.NAME)    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'splitchecker/split_checker ' + self.rootdir + 'lexiconchecker/freqlist_google_formatted ' + self.rootdir + 'splitchecker/exceptions ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'split_checker.test.out')

class RunOnCheckerModule(AbstractModule): #(splits in FoLiA terminology)
    NAME = "runoncheckermodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'runon_checker.test.out'):
                if len(fields) > 2:
                    self.splitcorrection(word, fields[1:], cls='space-error', annotator=self.NAME)
            f.close()                  
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'runonchecker/runon_checker ' + self.rootdir + 'lexiconchecker/freqlist_google_formatted ' + self.rootdir + 'runonchecker/exceptions ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'runon_checker.test.out')

class ItsItsModule(AbstractModule):
    NAME = "it'sitsmodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.990,'A':0.990,'T':0.8};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'itsits.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker it\\\'s its ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'itsits.test.out ' + self.settings['timblserver_address'])

class YoureYourModule(AbstractModule):
    NAME = "you'reyourmodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.990,'A':0.975,'T':0.850};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'youreyour.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker you\\\'re your ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'youreyour.test.out ' + self.settings['timblserver_address'])

class ThanThenModule(AbstractModule):
    NAME = "thanthenmodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.975,'A':0.925,'T':0.5};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'thanthen.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                         
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker than then ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'thanthen.test.out ' + self.settings['timblserver_address'])

class LoseLooseModule(AbstractModule):
    NAME = "loseloosemodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.990,'A':0.990,'T':0.7};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'loseloose.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker lose loose ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'loseloose.test.out ' + self.settings['timblserver_address'])

class EffectAffectModule(AbstractModule):
    NAME = "effectaffectmodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.990,'A':0.990,'T':0.850};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'effectaffect.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker effect affect ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'effectaffect.test.out ' + self.settings['timblserver_address'])

class LieLayModule(AbstractModule):
    NAME = "lielaymodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.990,'A':0.990,'T':0.925};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'lielay.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker lie lay ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'lielay.test.out ' + self.settings['timblserver_address'])

class WhetherWeatherModule(AbstractModule):
    NAME = "whetherweathermodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.990,'A':0.990,'T':0.6};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'whetherweather.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker whether weather ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'whetherweather.test.out ' + self.settings['timblserver_address'])

class WhoWhichThatModule(AbstractModule):
    NAME = "whowhichthatmodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.990,'A':0.990,'T':0.850};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'whowhichthat.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/3confusible_checker who which that ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'whowhichthat.test.out ' + self.settings['timblserver_address'])

class TheyreTheirThereModule(AbstractModule):
    NAME = "they'retheirtheremodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.990,'A':0.990,'T':0.7};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'theyretheirthere.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/3confusible_checker they\\\'re their there ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'theyretheirthere.test.out ' + self.settings['timblserver_address'])

class DontDoesntModule(AbstractModule):
    NAME = "don'tdoesn'tmodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.990,'A':0.950,'T':0.5};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'dontdoesnt.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker don\\\'t doesn\\\'t ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'dontdoesnt.test.out ' + self.settings['timblserver_address'])

class ToTooTwoModule(AbstractModule):
    NAME = "twotootwomodule"

    def set_accuracy_level(self,threshold):
        return {'SA':0.990,'A':0.975,'T':0.5};

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'totootwo.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/3confusible_checker to too two ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'totootwo.test.out ' + self.settings['timblserver_address'])

class AdviceAdviseModule(AbstractModule):
    NAME = "adviceadvisemodule"

    def set_accuracy_level(self,threshold):
        return False;

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'adviceadvise.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker advice advise ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'adviceadvise.test.out ' + self.settings['timblserver_address'])

class AnySomeModule(AbstractModule):
    NAME = "anysomemodule"

    def set_accuracy_level(self,threshold):
        return False;

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'anysome.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker any some ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'anysome.test.out ' + self.settings['timblserver_address'])

class LessFewerModule(AbstractModule):
    NAME = "lessfewermodule"

    def set_accuracy_level(self,threshold):
        return False;

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'lessfewer.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Well-known-mistake', annotator=self.NAME)
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker less fewer ' + str(self.threshold) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'lessfewer.test.out ' + self.settings['timblserver_address'])

class WoprCheckerModule(AbstractModule):
    NAME = "woprcheckermodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'wopr_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='unlikely-word', annotator=self.NAME)
            f.close()                      
        
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'woprchecker/wopr_checker ' + self.rootdir + 'woprchecker/wopr_exceptions ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'wopr_checker.test.out ' + self.settings['wopr_address'])

###################### MODULE DECLARATION  ###############################################

#Add all desired modules classes here here:

modules = [WoprCheckerModule,ErrorListModule,LexiconModule,ItsItsModule,YoureYourModule,ThanThenModule,
           LoseLooseModule,WhoWhichThatModule,WhetherWeatherModule,LieLayModule,EffectAffectModule,
           TheyreTheirThereModule,DontDoesntModule,ToTooTwoModule,AdviceAdviseModule,AnySomeModule,
           LessFewerModule,
           SplitCheckerModule,RunOnCheckerModule]

##########################################################################################


try:
    import clam.common.data
    import clam.common.status
    standalone = False
except ImportError: 
    standalone = True
    print sys.stderr, "WARNING: CLAM modules not found, trying to run standalone...."

id = None
bindir = ''

try:
    sys.argv[1];
except:
    print >>sys.stderr, "Syntax: processchain.py [inputfile]";
    quit();

if sys.argv[1] == 'clam':
    standalone = False
    #called from CLAM: processchain.py clam datafile.xml 
    rootdir = sys.argv[2]
    bindir = sys.argv[3]
    if bindir[-1] != '/':
        bindir += '/'
    datafile = sys.argv[4]
    outputdir = sys.argv[5]
    if outputdir[-1] != '/':
        outputdir += '/'
    statusfile = sys.argv[6] 
   
    clamdata = clam.common.data.getclamdata(datafile)    
    try:
        inputfile = str(clamdata.inputfile('textinput'))
    except:
        inputfile = str(clamdata.inputfile('foliainput'))
    
    threshold = float(clamdata['sensitivity'])
    
else:
    standalone = True

    try:
        inputfile = sys.argv[1];
#        if len(sys.argv) >= 3:
#            id = sys.argv[2]
    except:
        print >>sys.stderr, "Syntax: processchain.py [inputfile] [[threshold/accuracy]]"
        sys.exit(1)

    #Get threshold
    try:
        if str(sys.argv[2]) == 'ST':
            threshold = 0.5
        elif str(sys.argv[2]) in ['T','A','SA']:
            threshold = str(sys.argv[2])
        else:
            threshold = float(sys.argv[2])
    except:
        threshold = 0.5

    #Get input file
    try:
        open(inputfile);
    except:
        print >>sys.stderr, "Input file does not exist";
        sys.exit(1);

    #Get settings
    raw_settings = open('client_settings','r').readlines();
    settings = {};

    for i in raw_settings:
        key, value = i.split(' ');
        settings[key] = value[:-1];

    rootdir = ''
    outputdir = 'output/' #stdout
    statusfile = '/tmp/fowltstatus'
    
#detect ID from filename
if not id:
    id = os.path.basename(inputfile).split('.',1)[0].replace(' ','_')

def errout(msg):
    print >>sys.stderr,  "[" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] PROCESSING-CHAIN: ' + msg
    

#Step 1 - Tokenize input text (plaintext) and produce FoLiA output 


if inputfile[-4:] == '.xml':
    shutil.copyfile(inputfile, outputdir+id+'.xml')
else:    
    if not standalone:
        clam.common.status.write(statusfile, "Starting Tokeniser",1)
    os.system('dos2unix ' + inputfile)
    errout("Starting tokeniser...")
    if sys.argv[1] == 'clam':
        os.system(bindir + 'ucto -c /var/www/etc/ucto/tokconfig-nl -x ' + id + ' ' + inputfile + ' > ' + outputdir + id + '.xml')
    else:
        os.system(bindir + 'ucto -c ' + os.getcwd() + '/ucto_config/tokconfig-fowlt -x ' + id + ' ' + inputfile + ' > ' + outputdir + id + '.xml')

    errout("Tokeniser finished")

if not standalone:
    clam.common.status.write(statusfile, "Reading FoLiA document",2)

#Step 2 - Read FoLiA document
doc = folia.Document(file=outputdir + id + '.xml')
doc.declare(folia.Correction, 'fowltset' )
doc.declare(folia.ErrorDetection, 'fowltset' )

if not standalone and doc.metadatatype == folia.MetaDataType.NATIVE:
    if 'donate' in clamdata and clamdata['donate']:
        doc.metadata['donate'] = "yes"
        errout("Donated")
    else:
        doc.metadata['donate'] = "no"
        errout("Not donated")

#Presuming that each token will be on one line, make a mapping from lines to IDs
idmap = [ w.id for w in doc.words() ]

########## Extract data for modules ##############

if not standalone:
    clam.common.status.write(statusfile, "Extracting data for modules",3)

f = open(outputdir + 'input.tok.txt','w')
for currentword in doc.words():
    f.write( str(currentword) + ' ')
f.close()

f = open(outputdir + 'agreement_checker.test.inst','w')
for prevword3, prevword2, prevword, currentword, nextword, nextword2, nextword3 in Windower(doc.words(),7):
    f.write( str(prevword3) + ' ' + str(prevword2) + ' ' + str(prevword) + ' ' + str(currentword) + ' ' + str(nextword) + ' ' + str(nextword2) + ' ' + str(nextword3) + ' ' + str(currentword) + '\n')
f.close()


###### BEGIN CALL MODULES (USING PARALLEL POOL) ######
# (nothing to edit here)

errout( "Calling modules")
if not standalone:
    clam.common.status.write(statusfile, "Calling Modules",4)

def processor():
    while True:
        job = queue.get() 
        job.run()
        queue.task_done()

queue = Queue() 
threads = 4

for i in range(threads):  
    thread = Thread(target=processor)  
    thread.setDaemon(True)  
    thread.start()  

modules = [ Module(doc,rootdir,outputdir,idmap, threshold, settings) for Module in modules ]
for module in modules:
    queue.put(module)

queue.join()   
#all modules done

#process results and integrate into FoLiA
for module in modules:
    module.process_result()

###### END ###### 

#Store FoLiA document
if not standalone:
    clam.common.status.write(statusfile, "Saving document",99)
errout( "Saving document")
doc.save()

if not standalone:
    clam.common.status.write(statusfile, "All done",100)
errout("All done!")
sys.exit(0)
