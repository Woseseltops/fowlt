#!/usr/bin/env python
#-*- coding:utf-8 -*-

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
    def __init__(self, doc, rootdir, outputdir, idmap, settings):
        self.doc = doc
        self.rootdir = rootdir
        self.outputdir = outputdir
        self.done = False
        self.failed = False
        self.idmap = idmap
        self.settings = settings
        super(AbstractModule, self).__init__()

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

    def get_threshold(self):

        own_threshold = 0;

        if threshold in ['SA','A','T']:
            if threshold_settings[self.NAME]:
                own_threshold = threshold_settings[self.NAME][threshold];
            else:
                own_threshold = 0.5
        else:            
            own_threshold = threshold;

        return own_threshold

    def addcorrection(self, word, **kwargs  ):                
    
        self.errout("Adding correction for " + word.id + " " + unicode(word).encode('utf-8'))
        
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
                datetime=datetime.datetime.now(),
		confidence = kwargs['confidence']
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
                datetime=datetime.datetime.now(),
		confidence = kwargs['confidence']
            )
        else:
            raise Exception("No suggestions= specified!")
            

    def adderrordetection(self, word, **kwargs):
        self.errout("Adding correction for " + word.id + " " + unicode(word).encode('utf-8'))
        
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

        self.errout("Splitting " + unicode(word).encode('utf-8') + " into " + str_newwords);

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
                    #Add correction suggestion and confidence (two last fields)
                    suggs = [];
                    splits = [];
                    for x in fields[1:]:
                        corr = str(x.strip());
                        if corr != str(word) and '__' not in corr:
                            suggs.append(corr);
                        elif '__' in corr: 
                            splits+= corr.split('__');

                    if len(suggs) > 0:                            
                        self.addcorrection(word, suggestions=suggs, cls='Frequent-mistake', annotator=self.NAME, confidence = 1)

                    if len(splits) > 0:
                        self.splitcorrection(word, splits, cls='Frequent-mistake', annotator=self.NAME, confidence = 1)

            f.close()        
            
    def run(self):
        self.errout("MODULE: " + self.NAME)
                
        #Call module and ask it to produce output
        self.runcmd('python ' + self.rootdir + 'errorlistchecker/errorlist_checker.py ' + self.outputdir + 'input.tok.txt ' + self.rootdir + 'errorlistchecker/fowlt_errorlist ' + self.outputdir + 'errorlist_checker.test.out')

# --- Add new module classes here, and don't forget to declare them in the list below: ---

class LexiconModule(AbstractModule):
    NAME = "lexiconmodule"
    
    def process_result(self):

	#Load exceptions
	exceptions = open(self.rootdir+'lexiconchecker/exceptions','r').read().strip().split('\n');

        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'lexicon_checker.test.out'):                                            
                if len(fields) >= 2 and str(word).lower() not in exceptions:
                    #Add correction suggestion and confidence (two last fields)
		    suggs = [];
		    for x in fields[1:-1]:
                        
			#Make sure the suggestion isn't equal to a uppercase, dashed, etc. version of the word
                        if raw(str(x)) != raw(str(word)):
                            suggs.append(x.strip());
                        
                    if len(suggs) > 0:
                        self.addcorrection(word, suggestions=suggs, cls='Looks-like-frequent-word', annotator=self.NAME, confidence = fields[-1])
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
	    confidence_values = []
            prev = ''
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'split_checker.test.out'):           
                if len(fields) >= 2:

                    confidence_values.append(fields[-1])
                    #Add correction suggestion                
                    if prev and fields[-2] != prev:
                        if merge: 
                            merges.append(merge)
                            text.append(prev)
                            merge = []
                    else:
                        merge.append(word)
                    prev = fields[-2]
                else:
                    if merge: 
                        merges.append(merge)
                        text.append(prev)
                        merge = []  
                    prev = ''
            if merge: 
                merges.append(merge)      
                text.append(prev)
 	        confidence_values.append(fields[-1])
            f.close()                  

            for i, mergewords in enumerate(merges):
                #Add correction suggestion and confidence (two last fields)
                newword = text[i].strip()
                self.mergecorrection(newword, mergewords, cls='space-error', annotator=self.NAME, confidence=float(confidence_values[i*2]))  
    
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
                    self.splitcorrection(word, fields[1:-1], cls='space-error', annotator=self.NAME, confidence= fields[-1])
            f.close()                  
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'runonchecker/runon_checker ' + self.rootdir + 'lexiconchecker/freqlist_google_formatted ' + self.rootdir + 'runonchecker/exceptions ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'runon_checker.test.out')

class ItsItsModule(AbstractModule):
    NAME = "it'sitsmodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'itsits.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error it\\\'s its ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'itsits.test.out ' + self.settings['timblserver_address'])

class YoureYourModule(AbstractModule):
    NAME = "you'reyourmodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'youreyour.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error you\\\'re your ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'youreyour.test.out ' + self.settings['timblserver_address'])

class ThanThenModule(AbstractModule):
    NAME = "thanthenmodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'thanthen.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                         
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error than then ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'thanthen.test.out ' + self.settings['timblserver_address'])

class LoseLooseModule(AbstractModule):
    NAME = "loseloosemodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'loseloose.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error lose loose ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'loseloose.test.out ' + self.settings['timblserver_address'])

class EffectAffectModule(AbstractModule):
    NAME = "effectaffectmodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'effectaffect.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error effect affect ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'effectaffect.test.out ' + self.settings['timblserver_address'])

class LieLayModule(AbstractModule):
    NAME = "lielaymodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'lielay.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error lie lay ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'lielay.test.out ' + self.settings['timblserver_address'])

class WhetherWeatherModule(AbstractModule):
    NAME = "whetherweathermodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'whetherweather.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error whether weather ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'whetherweather.test.out ' + self.settings['timblserver_address'])

class WhoWhichThatModule(AbstractModule):
    NAME = "whowhichthatmodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'whowhichthat.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/3confusible_checker_error who which that ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'whowhichthat.test.out ' + self.settings['timblserver_address'])

class TheyreTheirThereModule(AbstractModule):
    NAME = "they'retheirtheremodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'theyretheirthere.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/3confusible_checker_error they\\\'re their there ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'theyretheirthere.test.out ' + self.settings['timblserver_address'])

class DontDoesntModule(AbstractModule):
    NAME = "don'tdoesn'tmodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'dontdoesnt.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error don\\\'t doesn\\\'t ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'dontdoesnt.test.out ' + self.settings['timblserver_address'])

class ToTooTwoModule(AbstractModule):
    NAME = "totootwomodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'totootwo.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/3confusible_checker_error to too two ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'totootwo.test.out ' + self.settings['timblserver_address'])

class AdviceAdviseModule(AbstractModule):
    NAME = "adviceadvisemodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'adviceadvise.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error advice advise ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'adviceadvise.test.out ' + self.settings['timblserver_address'])

class AnySomeModule(AbstractModule):
    NAME = "anysomemodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'anysome.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error any some ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'anysome.test.out ' + self.settings['timblserver_address'])

class LessFewerModule(AbstractModule):
    NAME = "lessfewermodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'lessfewer.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error less fewer ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'lessfewer.test.out ' + self.settings['timblserver_address'])

class PracticePractiseModule(AbstractModule):
    NAME = "practicepractisemodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'practicepractise.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error practice practise ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'practicepractise.test.out ' + self.settings['timblserver_address'])

class ChoseChooseModule(AbstractModule):
    NAME = "chosechoosemodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'chosechoose.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error chose choose ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'chosechoose.test.out ' + self.settings['timblserver_address'])

class QuiteQuietModule(AbstractModule):
    NAME = "quitequietmodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'quitequiet.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion and confidence (two last fields)
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Well-known-confusion', annotator=self.NAME, confidence = fields[-1])
            f.close()                      
    
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'confusiblechecker/confusible_checker_error quite quiet ' + str(self.get_threshold()) + ' ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'quitequiet.test.out ' + self.settings['timblserver_address'])

class WoprCheckerModule(AbstractModule):
    NAME = "woprcheckermodule"

    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'wopr_checker.test.out'):
                if len(fields) >= 2:
		    #Filter suggestions
		    suggs = [];

		    for x in fields[1:]:
			if raw(x) != raw(str(word)):
			    suggs.append(x);

                    #Add correction suggestion (The last field holds the suggestion? (assumption, may differ per module))
		    if len(suggs) > 0:
                    	self.addcorrection(word, suggestions=suggs, cls='unlikely-word', annotator=self.NAME, confidence = 0.91)
            f.close()                      
        
    def run(self):                
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'woprchecker/wopr_checker ' + self.rootdir + 'woprchecker/wopr_exceptions ' + self.outputdir + 'agreement_checker.test.inst > ' + self.outputdir + 'wopr_checker.test.out ' + self.settings['wopr_address'])

class AspellModule(AbstractModule):
    NAME = "aspellmodule"
    
    def process_result(self):
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'aspell_checker.test.out'):
                if len(fields) >= 2:
                    #Add correction suggestion
                    #(The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:-1]], cls='Looks-like-frequent-word', annotator=self.NAME, confidence = fields[-1])
        
    def run(self):
        #Call module and ask it to produce output
        self.runcmd(self.rootdir + 'aspellchecker/aspell_checker ' + self.rootdir + 'lexiconchecker/freqlist_google_formatted ' + self.outputdir + 'input.tok.txt > ' + self.outputdir + 'aspell_checker.test.out')

#################### FUNCTIONS  #################################

def raw(word):
    """Returns the lowercase, stripped, quoteless and dashless version of a word"""

    try:
        return word.strip().lower().replace('-','').replace('\'','').replace('`','').replace('’','');
    except:
        return word.strip().lower().replace('-','').replace('\'','').replace('`','');

###################### MODULE DECLARATION  ###############################################

#Add all desired modules classes here here:

modules = [WoprCheckerModule,ErrorListModule,LexiconModule,AspellModule,ItsItsModule,YoureYourModule,
           ThanThenModule,LoseLooseModule,WhoWhichThatModule,WhetherWeatherModule,LieLayModule,
           EffectAffectModule,TheyreTheirThereModule,DontDoesntModule,ToTooTwoModule,AdviceAdviseModule,
           AnySomeModule,LessFewerModule,PracticePractiseModule,ChoseChooseModule,QuiteQuietModule,
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
#        if len(sys.argv) >= 4:
#            id = sys.argv[3]
    except:
        print >>sys.stderr, "Syntax: processchain.py [inputfile] [[threshold/accuracy]]"
        sys.exit(1)

    #Get input file
    try:
        open(inputfile);
    except:
        print >>sys.stderr, "Input file does not exist";
        sys.exit(1);

    rootdir = ''
    outputdir = 'output/' #stdout
    statusfile = '/tmp/fowltstatus'

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

#Get settings
raw_settings = open(rootdir+'client_settings','r').readlines();
settings = {};

for l in raw_settings:
    key, value = l.split(' ');
    settings[key] = value[:-1];

lines = open(rootdir+'thresholds','r').readlines();
threshold_settings = {};

for l in lines:
    tokens = l.strip().split('\t');
    try:
         threshold_settings[tokens[0]] = {'SA':float(tokens[-3]),'A':float(tokens[-2]),'T':float(tokens[-1])};
    except:
         pass;
    
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
        os.system(bindir + 'ucto -c ' + rootdir + '/ucto_config/tokconfig-fowlt -x ' + id + ' ' + inputfile + ' > ' + outputdir + id + '.xml')
    else:
        os.system(bindir + 'ucto -c ' + rootdir + 'ucto_config/tokconfig-fowlt -x ' + id + ' ' + inputfile + ' > ' + outputdir + id + '.xml')

    errout("Tokeniser finished")

if not standalone:
    clam.common.status.write(statusfile, "Reading FoLiA document",2)

#Step 2 - Read FoLiA document
doc = folia.Document(file=outputdir + id + '.xml')
doc.declare(folia.Correction, 'fowltset' )
doc.declare(folia.ErrorDetection, 'fowltset' )
doc.language(value='eng');

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
    f.write( str(currentword).replace('’','\'') + ' ')
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

modules = [ Module(doc,rootdir,outputdir,idmap, settings) for Module in modules ]
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
