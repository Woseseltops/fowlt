fowlt
=====

An English version of the context based spell checker Valkuil.net.

DESCRIPTION

Fowlt.net is the English version of the Dutch context based spell checker Valkuil.net (available on http://www.valkuil.net). A context based spell checker tries to find and correct errors by comparing bits of a text to the large data set it was trained on. If a word is not expected on the basis of this training data, Valkuil.net marks it as an error. Because of this, Fowlt.net can make smarter decisions than standard spell checkers.

INSTALLATION

1. Downloading Fowlt
Fowlt can be used on any computer with Python 2. To obtain Fowlt from GitHub:

  $ git clone git://github.com/Woseseltops/fowlt.git

2. Installing PyNLPl
Fowlt makes use of the PyNLPl Python library, which can be installed with '$ easy_install pynlpl'. In case you don't have permission to use easy_install, you can also clone PyNLPl from GitHub into the Fowlt directory (https://github.com/proycon/pynlpl).

3. Compiling modules
Several modules need to be compiled before use. This can be done automatically by doing a make command from the main directory.

UPDATING

To keep Fowlt up to date, regularly check back on GitHub for changes and obtain the latest using a simple:

  fowlt$ git pull
