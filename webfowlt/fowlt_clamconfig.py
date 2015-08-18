#!/usr/bin/env python
#-*- coding:utf-8 -*-


###############################################################
# CLAM: Computational Linguistics Application Mediator
# -- Service Configuration File --
#       by Maarten van Gompel (proycon)
#       http://ilk.uvt.nl/~mvgompel
#       Induction for Linguistic Knowledge Research Group
#       Universiteit van Tilburg
#
#       Licensed under GPLv3
#
###############################################################

from __future__ import print_function, unicode_literals, division, absolute_import

from clam.common.parameters import *
from clam.common.formats import *
from clam.common.converters import *
from clam.common.viewers import *
from clam.common.data import *
from clam.common.digestauth import pwhash
from os import uname, environ
from base64 import b64decode as D
import sys

REQUIRE_VERSION = 0.9

# ======== GENERAL INFORMATION ===========

#The System ID, a short alphanumeric identifier for internal use only
SYSTEM_ID = "fowlt"

#System name, the way the system is presented to the world
SYSTEM_NAME = "Fowlt"

#An informative description for this system:
SYSTEM_DESCRIPTION = "Fowlt spelling correction for English"

# ======== LOCATION ===========
host = uname()[1]
if 'VIRTUAL_ENV' in os.environ:
    ROOT = os.environ['VIRTUAL_ENV'] + "/fowlt.clam/"
    PORT = 8080
    BINDIR = os.environ['VIRTUAL_ENV'] + '/bin/'
    FOWLTDIT = os.environ['VIRTUAL_ENV'] + '/fowlt/'

    if host == 'applejack': #configuration for server in Nijmegen
        HOST = "webservices-lst.science.ru.nl"
        URLPREFIX = 'fowlt'

        if not 'CLAMTEST' in environ:
            ROOT = "/scratch2/www/webservices-lst/live/writable/fowlt/"
            PORT = 80
        else:
            ROOT = "/scratch2/www/webservices-lst/test/writable/fowlt/"
            PORT = 81

        USERS_MYSQL = {
            'host': 'mysql-clamopener.science.ru.nl',
            'user': 'clamopener',
            'password': D(open(environ['CLAMOPENER_KEYFILE']).read().strip()),
            'database': 'clamopener',
            'table': 'clamusers_clamusers'
        }
        DEBUG = False
        REALM = "WEBSERVICES-LST"
        DIGESTOPAQUE = open(environ['CLAM_DIGESTOPAQUEFILE']).read().strip()
        SECRETKEY = open(os.environ['CLAM_SECRETKEYFILE']).read().strip()
        FOWLTDIR = "/scratch2/www/webservices-lst/live/repo/fowlt/"
        ADMINS = ['proycon','antalb','wstoop']
else:
    raise Exception("I don't know where I'm running from! Got " + host)

# ======== AUTHENTICATION & SECURITY ===========

#Users and passwords
#USERS = None #no user authentication
#USERS = { 'admin': pwhash('admin', SYSTEM_ID, 'secret'), 'proycon': pwhash('proycon', SYSTEM_ID, 'secret'), 'antal': pwhash('antal', SYSTEM_ID, 'secret') , 'martin': pwhash('martin', SYSTEM_ID, 'secret') }

#ADMINS = ['admin'] #Define which of the above users are admins
#USERS = { 'username': pwhash('username', SYSTEM_ID, 'secret') } #Using pwhash and plaintext password in code is not secure!!

#Do you want all projects to be public to all users? Otherwise projects are
#private and only open to their owners and users explictly granted access.
PROJECTS_PUBLIC = False

#Amount of free memory required prior to starting a new process (in MB!), Free Memory + Cached (without swap!)
#REQUIREMEMORY = 10

#Maximum load average at which processes are still started (first number reported by 'uptime')
#MAXLOADAVG = 1.0


# ======== WEB-APPLICATION STYLING =============

#Choose a style (has to be defined as a CSS file in style/ )
STYLE = 'classic'

# ======== ENABLED FORMATS ===========

#Here you can specify an extra formats module
CUSTOM_FORMATS_MODULE = None


# ======== PREINSTALLED DATA ===========

#INPUTSOURCES = [
#    InputSource(id='sampledocs',label='Sample texts',path=ROOT+'/inputsources/sampledata',defaultmetadata=PlainTextFormat(None, encoding='utf-8') ),
#]

# ======== PROFILE DEFINITIONS ===========

PROFILES = [
    Profile(
        InputTemplate('textinput', PlainTextFormat,"Input text",
            StaticParameter(id='encoding',name='Encoding',description='The character encoding of the file', value='utf-8'),
            CharEncodingConverter(id='latin1',label='Convert from Latin-1',charset='iso-8859-1'),
            PDFtoTextConverter(id='pdfconv',label='Convert from PDF Document'),
            MSWordConverter(id='docconv',label='Convert from MS Word Document'),
            extension='.txt',
            unique=True
        ),
        #------------------------------------------------------------------------------------------------------------------------
        OutputTemplate('foliaoutput',FoLiAXMLFormat,'FoLiA Document with spelling suggestions',
            filename='$INPUTSTRIPPEDFILENAME.xml',
            unique=True
        ),
    ),
    Profile(
        InputTemplate('foliainput', FoLiAXMLFormat,"FoLiA Document (tokenised)",
            extension='.xml',
            unique=True
        ),
        #------------------------------------------------------------------------------------------------------------------------
        OutputTemplate('foliaoutput',FoLiAXMLFormat,'FoLiA Document with spelling suggestions',
            filename='$INPUTSTRIPPEDFILENAME.xml',
            unique=True
        ),
    )
]

# ======== COMMAND ===========

#The system command. It is recommended you set this to small wrapper
#script around your actual system. Full shell syntax is supported. Using
#absolute paths is preferred. The current working directory will be
#set to the project directory.
#
#You can make use of the following special variables,
#which will be automatically set by CLAM:
#     $INPUTDIRECTORY  - The directory where input files are uploaded.
#     $OUTPUTDIRECTORY - The directory where the system should output
#                        its output files.
#     $STATUSFILE      - Filename of the .status file where the system
#                        should output status messages.
#     $DATAFILE        - Filename of the clam.xml file describing the
#                        system and chosen configuration.
#     $USERNAME        - The username of the currently logged in user
#                        (set to "anonymous" if there is none)
#     $PARAMETERS      - List of chosen parameters, using the specified flags
#
COMMAND = FOWLTDIR + "fowlt_processchain.py clam " + FOWLTDIR + ' ' + BINDIR + " $DATAFILE $OUTPUTDIRECTORY $STATUSFILE"

# ======== PARAMETER DEFINITIONS ===========

#The parameters are subdivided into several groups. In the form of a list of (groupname, parameters) tuples. The parameters are a list of instances from common/parameters.py
PARAMETERS =  [
    ('Settings', [
        #BooleanParameter(id='createlexicon',name='Create Lexicon',description='Generate a separate overall lexicon?'),
        #ChoiceParameter(id='casesensitive',name='Case Sensitivity',description='Enable case sensitive behaviour?', choices=['yes','no'],default='no'),
        #StringParameter(id='author',name='Author',description='Sign output metadata with the specified author name',maxlength=255),
	FloatParameter(id='sensitivity', name='Sensitivity', description='This will be removed later', minvalue=0.5, maxvalue=1.0, default=0.9, required=True),
        BooleanParameter(id='donate', name='Donate errors',description="Donate found errors for research?")
    ] )
]

