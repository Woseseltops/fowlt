#!/usr/bin/env python
#-*- coding:utf-8 -*-

#Valkuil harvester

import sys
import os
import glob
import pynlpl.formats.folia as folia
import time
import gc
from datetime import datetime

if len(sys.argv) >= 2:
     DIR = sys.argv[1]
else:
     DIR = "userdocs/"

now = time.time()
if len(sys.argv) >= 3:
     HARVESTTIME = int(sys.argv[2])
else:
     HARVESTTIME = 10800 #three hours after last modification

if len(sys.argv) >= 4:
    DELETE = bool(int(sys.argv[3]))
else:
    DELETE = True
    
print >>sys.stderr, "Starting harvester"
print >>sys.stderr, "DIR=" + DIR
print >>sys.stderr, "HARVESTTIME=" + str(HARVESTTIME)
print >>sys.stderr, "DELETE=" + str(DELETE)


MAXFILESIZE = 10 * 1024 * 1025 #10MB

for filepath in glob.glob(DIR + '/*.xml'):
    print >>sys.stderr,filepath
    if len(filepath) > 10 and os.path.basename(filepath)[0]== 'D':
        filetime = os.path.getmtime(filepath)
        if now - filetime >= HARVESTTIME and os.path.getsize(filepath) < MAXFILESIZE: 
            print >>sys.stderr,"\tLoading"
            filename = os.path.basename(filepath)
            try:
                doc = folia.Document(file=filepath)
            except Exception as e:
                print >>sys.stderr,"Unable to load " + filepath + ": " + str(e)
                continue
                        
            if 'donate' in doc.metadata:
                donate = (doc.metadata['donate'] == 'yes')                
            else: 
                donate = False
                
            if donate:
                print >>sys.stderr,"\tdonated..processing"
        
                for word in doc.words():
                        if word.hasannotation(folia.Correction):                            
                            for correction in word.annotations(folia.Correction):
                                #data = [ w.text() if isinstance(w, folia.Word) else "NONE" for w  in word.context(3) ]
                                try:
                                    leftcontext = [ w.text() if isinstance(w, folia.Word) else "NONE" for w  in word.leftcontext(3) ]
                                    rightcontext = [ w.text() if isinstance(w, folia.Word) else "NONE" for w  in word.rightcontext(3) ]
                                except folia.NoSuchText:
                                    print >>sys.stderr, "\tError obtaining context for " + correction.id + ". Skipping correction..."
                                    continue
                                
                                suggestions = []
                                
                                if correction.hassuggestions():
                                    for i, suggestion in enumerate(correction.suggestions()):
                                        suggestions.append(suggestion.text())                                
                                
                                if correction.datetime:
                                    if isinstance(correction.datetime, datetime):
                                        timestamp = correction.datetime.strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        timestamp = correction.datetime
                                else:
                                   timestamp = datetime.fromtimestamp(filetime).strftime('%Y-%m-%d %H:%M:%S')
                                
                                if correction.hasnew():
                                    #a correction has been made
                                    correction_text = correction.new(0).text()
                                     
                                    
                                    found = -2    
                                    if correction.hassuggestions():
                                        found = -1    
                                        for i, suggestion in enumerate(correction.suggestions()):
                                            if suggestion.text() == correction.text():
                                                found = i
                                    
                                    if found == -2:    
                                        mode = 'free-correction'
                                        for errordetection in word.select(folia.ErrorDetection):                                        
                                            if errordetection.cls != 'noerror':
                                                mode = 'hinted-correction'
                                    elif found == -1:    
                                        mode = 'manual-correction'
                                    else:
                                        mode = 'accepted-correction'
 
                                    data = [timestamp, doc.id]
                                                                                
                                    if correction.hasoriginal():
                                        data += leftcontext + [correction.original(0).text()] + rightcontext    
                                    else:
                                        data += leftcontext + [word.text()] + rightcontext    
                                        
                                    data.append( mode )
                                    data.append( correction.cls )
                                    data.append( correction.annotator )
                                    if not suggestions: suggestions = ['-']
                                    data.append( "|".join(suggestions) )
                                    data.append( correction_text )                                
                                else:
                                    mode = 'ignored'
                                    for errordetection in word.select(folia.ErrorDetection):                                        
                                        if errordetection.cls == 'noerror' and errordetection.annotatortype == folia.AnnotatorType.MANUAL:
                                            #actively flagged as not being an error
                                            mode = 'discarded'
                                                                                                                                                    

                                    data = [timestamp, doc.id] + leftcontext + [word.text()] + rightcontext
                                    data.append( mode )
                                    data.append( correction.cls ) 
                                    data.append( correction.annotator )
                                    if not suggestions: suggestions = ['-']
                                    data.append( "|".join(suggestions) ) 
                                    data.append( word.text() ) #original text                                    
                                s = " ".join(data)
                                print s.encode('utf-8')
                                print >>sys.stderr, "\tHarvested a correction of type '" + mode + "'"
            else:
                print >>sys.stderr,"\tnot donated..skipping"
            del doc
            gc.collect()
               
            #delete document
            if DELETE:
                print >>sys.stderr, "\tDeleting " + filepath
                try:
                    os.unlink(filepath)
                except:
                    print >>sys.stderr, "\tERROR: Unable to delete " + filepath + ". Permission denied?"
                            
            
                

            

