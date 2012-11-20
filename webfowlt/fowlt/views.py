from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse,HttpResponseForbidden, HttpResponseNotFound
from django.conf import settings
from django.shortcuts import redirect
from django.views.decorators.cache import cache_control

import random
import json
import clam.common.client
import clam.common.data
import pynlpl.formats.folia as folia
import os.path
import time
import hashlib
import datetime
from lxml import etree


@cache_control(no_cache=True,max_age=0, must_revalidate=True)
def start(request):
    return render_to_response('index.html') 

def process(request):
    """Process a given text and redirect to viewer"""
    if 'text' in request.REQUEST and request.REQUEST['text']:
        text = request.REQUEST['text']
    elif 'uploadfile' in request.FILES:
        text = request.FILES['uploadfile'].read()
    else:
        return render_to_response('error.html',{'errormessage': "Er is geen geldige tekst ingevoerd!"} ) 
        
    
    #generate a random ID for this project
    id = 'D' + hex(random.getrandbits(128))[2:-1]
    
    #create CLAM client
    if 'CLAMUSER' in dir(settings):
        client = clam.common.client.CLAMClient(settings.CLAMSERVICE,settings.CLAMUSER, settings.CLAMPASS)
    else:
        client = clam.common.client.CLAMClient(settings.CLAMSERVICE)    
    #creat project
    client.create(id)
    
    #get specification
    clamdata = client.get(id)
        
    #add input file
    try:
        client.addinput(id, clamdata.inputtemplate('textinput'), text, filename=id +'.txt',encoding='utf-8')
    except Exception, e:
        try:
            client.delete(id)
        except:
            pass
        return render_to_response('error.html',{'errormessage': "Kon het gekozen bestand niet toevoegen. Dit kan meerdere oorzaken hebben. Valkuil accepteert momenteel alleen platte UTF-8 gecodeerde tekst-bestanden. Met name Microsoft Word bestanden zijn nog niet ondersteund in dit stadium!",'debugmessage':str(e)} ) 
        
    if 'donate' in request.REQUEST and request.REQUEST['donate'] == 'yes':
        donate = True
    else:
        donate = False
        
    #start CLAM
    client.start(id, sensitivity=request.REQUEST['sensitivity'], donate=donate)
                
    while clamdata.status != clam.common.status.DONE:
        clamdata = client.get(id)  
        if clamdata == clam.common.status.DONE:
            break
        else:
            time.sleep(1) #wait 1 second before polling status again
    
    #retrieve output file
    found = False
    for outputfile in clamdata.output:
        if str(outputfile)[-4:] == '.xml':
            try:
                outputfile.loadmetadata()
            except:
                continue
            if outputfile.metadata.provenance.outputtemplate_id == 'foliaoutput' and not found:
                outputfile.copy(settings.DOCDIR + id + '.xml')        
                found = True
        elif outputfile == 'error.log':
                outputfile.copy(settings.DOCDIR + id + '.log')        
                
            

    if not found:
        return HttpResponseForbidden("Unable to retrieve file from CLAM Service")        
        
    #remove project    
    client.delete(id)
           
    return redirect('/' + id + '/', permanent=False)            



def about(request):
    return render_to_response('about.html') 
    
def under_construction(request):
    return render_to_response('under_construction.html') 

def help(request):
    return render_to_response('help.html')     


@cache_control(private=True,no_cache=True,max_age=0, must_revalidate=True)
def viewer(request, id):
    """Main viewer"""
    if os.path.exists(settings.DOCDIR + id + '.xml'):
        #we load the XML in a tree first, because we need it later on for XSLT as well, and only want it in memory once
        xmldoc = etree.parse(settings.DOCDIR + id + '.xml')
        
        #Now parse it using FoLiA library
        foliadoc = folia.Document(tree=xmldoc)
        
        
        errors = []
        
        done = {}
        
        #extract all errors (will be passed as JSON for javascript)
        for word in foliadoc.words():
            cls = 'noerror'
            error = {}            
            found = False
            
            if word.cls in ['DATE','TIME','URL','E-MAIL']:
                #always ignore correction suggestions for dates, times, urls and emails
                continue
            
            
            incorrection = word.incorrection()
            
            if incorrection  and not incorrection.id in done and incorrection.hascurrent():                
                done[incorrection.id] = True
                
                if not 'classes' in error:                                            
                    error['classes'] = []
                cls =  incorrection.cls 
                error['classes'].append( cls )
                if not 'suggestions' in error:                                            
                    error['suggestions'] = []
                for suggestion in incorrection.suggestions():
                    error['suggestions'] += [ " ".join( w.text() for w in suggestion if isinstance(w,folia.Word) ) ]                    
                if not 'correctionid' in error:
                    error['correctionid'] = incorrection.id                      
                                    
                error['wordid'] = word.id

                error['tokencorrection'] = True;
                error['multispan'] = [ w.id for w in incorrection.current()[1:] ]
                
                error['errnum'] = len(errors)
                error['text'] = str(word)                
                error['occ'] = 1 #number of occurences                        
                errors.append(error)  
            else:
                    
                found = False
                skip = False
                
                try:
                    for correction in word.annotations(folia.Correction):
                        if correction.hasnew():
                            skip = True
                            break
                        elif correction.hassuggestions():
                            found = True
                            if not 'classes' in error:                                            
                                error['classes'] = []
                            cls =  correction.cls 
                            error['classes'].append( cls )
                            if not 'suggestions' in error:                                            
                                error['suggestions'] = []
                            for suggestion in correction.suggestions():
                                if not suggestion.text() in error['suggestions']:
                                    error['suggestions'].append( suggestion.text())
                            if not 'correctionid' in error:
                                error['correctionid'] = correction.id                    
                            
                except folia.NoSuchAnnotation:
                    pass
                
                    
                if not skip:
                    try:
                        for detection in word.annotations(folia.ErrorDetection):
                            if detection.cls != 'noerror':
                                found = True
                                if not 'classes' in error:                                            
                                    error['classes'] = []
                                error['classes'].append( detection.cls )
                            else:
                                skip = True
                                found = False
                                break                            
                    except folia.NoSuchAnnotation:                    
                        pass
                    
                if found and error and not skip:
                    error['wordid'] = word.id
                    error['tokencorrection'] = False;
                    error['multispan'] = [];
                    error['errnum'] = len(errors)
                    error['text'] = str(word)                
                    error['occ'] = 1 #number of occurences
                    errors.append(error)                         
                
        #Compute number of occurences multiple times
        for i, error1 in enumerate(errors):
            for j, error2 in enumerate(errors):
                if i < j and error1['wordid'] != error2['wordid'] and error1['text'] == error2['text'] and not error1['tokencorrection'] and not error2['tokencorrection']:
                     error1['occ'] += 1
                     error2['occ'] += 1        
                        
        #Let XSLT do the basic conversion to HTML
        xslt = etree.parse(settings.ROOT_DIR + '/webvalkuil/style/folia-embed.xsl')
        transform = etree.XSLT(xslt)
        html = transform(xmldoc)


        return render_to_response('viewer.html', {'text': etree.tostring(html, pretty_print=True), 'errors': json.dumps(errors),'errorcount': len(errors)} ) 
    else:
        return HttpResponseNotFound("No such document")

def text(request, id):
    if os.path.exists(settings.DOCDIR + id + '.xml'):
        foliadoc = folia.Document(file=settings.DOCDIR + id + '.xml')        
        response = HttpResponse(str(foliadoc), mimetype="text/plain");
        response['Content-Type'] = 'text/plain; charset=utf-8'
        return response
    else:
        return HttpResponseNotFound("No such document")
        
def xml(request, id):
    if os.path.exists(settings.DOCDIR + id + '.xml'):
        foliadoc = folia.Document(file=settings.DOCDIR + id + '.xml')        
        return HttpResponse(foliadoc.xmlstring(), mimetype="text/xml");
    else:
        return HttpResponseNotFound("No such document")        

def log(request, id):
    if os.path.exists(settings.DOCDIR + id + '.log'):
        f = open(settings.DOCDIR + id + '.log')
        log = f.readlines()
        f.close()
        return HttpResponse(log, mimetype="text/plain");
    else:
        return HttpResponseNotFound("No such document")        
        
def ignore(request, id):
    if os.path.exists(settings.DOCDIR + id + '.xml'):
        wordid = request.REQUEST['wordid']
                    
        t = 0
        while os.path.exists(settings.DOCDIR + id + '.xml.lock') and (time.time() - os.path.getmtime(settings.DOCDIR + id + '.xml.lock')) < 30:            
            time.sleep(0.1)
            t += 0.1
            if t > 10:
                return HttpResponseForbidden("File is locked, other action in progress")
                    
        #set lock
        f = open(settings.DOCDIR + id + '.xml.lock','w')
        f.close()
                        
                    
        #Load document
        foliadoc = folia.Document(file=settings.DOCDIR + id + '.xml')
        
        try:
            w = foliadoc.index[wordid]
        except KeyError:
            os.unlink(settings.DOCDIR + id + '.xml.lock')
            return HttpResponseNotFound("No such word in document")    


        annotator = hashlib.md5(request.META['REMOTE_ADDR']).hexdigest()
        w.append( folia.ErrorDetection(foliadoc, cls="noerror", annotator=annotator, annotatortype=folia.AnnotatorType.MANUAL ))        
        foliadoc.save()
        os.unlink(settings.DOCDIR + id + '.xml.lock')
        return HttpResponse("OK", mimetype="text/plain")
    else:
        return HttpResponseNotFound("No such document")
        

def correct(request, id):
    if os.path.exists(settings.DOCDIR + id + '.xml'):

        if not 'wordid' in request.REQUEST or not 'class' in request.REQUEST  or not 'new' in request.REQUEST:
            return HttpResponseForbidden("Incomplete request")

        wordid = request.REQUEST['wordid']
        cls = request.REQUEST['class']
        new = request.REQUEST['new']
        if 'correctionid'  in request.REQUEST:
            reuse = request.REQUEST['correctionid']
        else:
            reuse = None
        
        if 'correctall' in request.REQUEST:
            correctall = request.REQUEST['correctall'] #original, correct all that match
        else:
            correctall = None
        annotator = hashlib.md5(request.META['REMOTE_ADDR']).hexdigest()
                        
        t = 0
        while os.path.exists(settings.DOCDIR + id + '.xml.lock') and (time.time() - os.path.getmtime(settings.DOCDIR + id + '.xml.lock')) < 30:            
            time.sleep(0.1)
            t += 0.1
            if t > 10:
                return HttpResponseForbidden("File is locked, other action in progress")

        #set lock
        f = open(settings.DOCDIR + id + '.xml.lock','w')
        f.close()
    
        #Load document
        try:
            foliadoc = folia.Document(file=settings.DOCDIR + id + '.xml')
        except:
            os.unlink(settings.DOCDIR + id + '.xml.lock')
            return HttpResponseNotFound("Unable to load document (this should not happen)")    
        
        try:
            w = foliadoc.index[wordid]
        except KeyError:
            os.unlink(settings.DOCDIR + id + '.xml.lock')
            return HttpResponseNotFound("No such word in document")    
            
        
        changed = False
        
        
        if w.incorrection() and new.strip().find(' ') == -1: #merge
            c = w.incorrection()
            c.datetime = datetime.datetime.now()
            s = w.sentence()
            
            s.mergewords( folia.Word(foliadoc, generate_id_in=s, text=new), *c.current(), reuse=reuse, datetime=datetime.datetime.now()  )
            changed = True                                
        elif new.strip() == '': #deletion
            s.deleteword(w)
            changed = True
        elif new.strip().find(' ') != -1: #split
            
            s = w.sentence()
            newwords = []
            for newword in new.strip().split(' '):
                newwords.append(folia.Word(foliadoc, generate_id_in=s, text=newword))
                
            w.split( *newwords,datetime=datetime.datetime.now(), reuse=reuse )                                
            changed = True
        else:
            q = [] #queue of all words to be corrected
            if correctall:                
                for w2 in doc.words():
                    if w2.text() == correctall:
                        q.append(w2)
            else:
                q = [w]
            for w in q:
                changed = True
                if reuse and not correctall:
                    w.correct(new=new, cls=cls, annotator=annotator, annotatortype=folia.AnnotatorType.MANUAL, datetime=datetime.datetime.now(), reuse=reuse)
                else:
                    w.correct(new=new, cls=cls, annotator=annotator, annotatortype=folia.AnnotatorType.MANUAL, datetime=datetime.datetime.now())
        
        if changed:
            foliadoc.save()
        
        os.unlink(settings.DOCDIR + id + '.xml.lock')
        
        return HttpResponse("OK", mimetype="text/plain")
    else:
        return HttpResponseNotFound("No such document")


    #return success or failure code (text update handled client-side)
