fowlt
=====

An English version of the context based spell checker Valkuil.net.

**DESCRIPTION**

Fowlt.net is the English version of the Dutch context based spell checker Valkuil.net (available on http://www.valkuil.net). A context based spell checker tries to find and correct errors by comparing bits of a text to the large data set it was trained on. If a word is not expected on the basis of this training data, Valkuil.net marks it as an error. Because of this, Fowlt.net can make smarter decisions than standard spell checkers.

**HOW TO INSTALL**

1. __Download Fowlt__.
Fowlt can be used on any Linux pc with Python 2. To obtain Fowlt from GitHub:

  $ git clone git://github.com/Woseseltops/fowlt.git

2. __Instal PyNLPl__.
Fowlt makes use of the PyNLPl Python library, which can be installed with '$ easy_install pynlpl'. In case you don't have permission to use easy_install, you can also clone PyNLPl from GitHub into the Fowlt directory (https://github.com/proycon/pynlpl).

3. __Install ucto, timbl and timblserver and tell the setting where you installed them__.
Fowlt makes use of already existing NLP and machine learning software. Ucto (http://ilk.uvt.nl/ucto/), timbl and timblserver (http://ilk.uvt.nl/timbl/) can be installed easily. At the moment, only timblserver can be installed at an alternative location. Whether you do so or not, please make sure the setting 'timblserver_location' in the file 'server settings' (in the main directory) points to the right place.

4. __Compile the modules__.
Several modules need to be compiled before use. This can be done automatically by doing a make command from the main directory.

**HOW TO USE**

1. __Start the servers__.
Fowlt currently makes uses of a timblserver that should be running on localhost. You can start this timblserver (if timblserver is installed) by running start_servers.py.

2. __Start the processchain__.
Once the servers are running, you can use Fowlt itself by running fowlt_processchain.py. This script currently takes only one argument, which can be any document that contains plain UTF-8 text.

**HOW TO UPDATE**

To keep Fowlt up to date, regularly check back on GitHub for changes and obtain the latest using a simple:

  fowlt$ git pull

**HOW TO EXPAND**

If you want, you can add your own confusible checker modules to Fowlt. This is done as follows:

1. __Make sure you have a file with lots of text to train Fowlt on__.
The British National Corpus was used for the modules included in the standard Fowlt installation. You don't have to exclude the utterances that aren't relevant for what you want to train the model for; Fowlt will select all relevant material automatically.

2. __Create a language model__.
This can be done automatically by running 'confusible_trainer/confusible_trainer.py [word1,word2,word3] [corpus]'. The first argument is a comma-separated list of words you want to train your module on, the second argument is the corpus you selected. Three files will be created: and instance file (the training material), an IGTree file and IGTree.wgt file (the actual language model created by Timbl).

3. __Add your new module to Fowlt__.
You have to add your new module both to the Fowlt server and the Fowlt client server. More info on this will added later.
