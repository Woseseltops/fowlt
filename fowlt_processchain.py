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
    def __init__(self, doc, rootdir, outputdir, idmap, threshold):
        self.doc = doc
        self.rootdir = rootdir
        self.outputdir = outputdir
        self.done = False
        self.failed = False
        self.idmap = idmap
        self.threshold = threshold
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
        sentence = word.sentence()
        newwords = [ folia.Word(self.doc, generate_id_in=sentence, text=w) for w in newwords ]        
        kwargs['suggest'] = True
        kwargs['datetime'] = datetime.datetime.now()
        word.split(
            *newwords,
            **kwargs
        )
        
    def mergecorrection(self, newword, originalwords, **kwargs):
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
    NAME = "errorlist"
    
    def process_result(self):                
        if self.done:
            #Reading module output and integrating in FoLiA document
            for word, fields in self.readcolumnedoutput(self.outputdir + 'errorlist_comparison.test.out'):                                            
                if len(fields) > 1:
                    #Add correction suggestion
                    #(The last field holds the suggestion? (assumption, may differ per module))
                    self.addcorrection(word, suggestions=[x.strip() for x in fields[1:]], cls='Frequent-mistake', annotator=self.NAME)
            f.close()        
            
    def run(self):
        self.errout("MODULE: " + self.NAME)
                
        #Call module and ask it to produce output
        self.runcmd('python ' + self.rootdir + 'errorlistchecker/errorlistchecker.py ' + self.rootdir + 'output/input.tok.txt ' + self.rootdir + 'errorlistchecker/pyerrorlist ' + self.outputdir + 'errorlist_comparison.test.out')

# --- Add new module classes here, and don't forget to declare them in the list below: ---


###################### MODULE DECLARATION  ###############################################

#Add all desired modules classes here here:

modules = [ErrorListModule]

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
    print >>sys.stderr, "Syntax: processchain.py inputfile [id] [responsivity-threshold]";
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
        inputfile = sys.argv[1]
        if len(sys.argv) >= 3:
            id = sys.argv[2]
    except:
        print >>sys.stderr, "Syntax: processchain.py inputfile [id] [responsivity-threshold]"
        sys.exit(1)
    try:
        threshold = int(sys.argv[3])
    except:
        threshold = 0.95
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
        os.system(bindir + 'ucto -L en -x ' + id + ' ' + inputfile + ' > ' + outputdir + id + '.xml')

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

modules = [ Module(doc,rootdir,outputdir,idmap, threshold) for Module in modules ]
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
