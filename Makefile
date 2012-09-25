CC=gcc
CFLAGS=-O2 -Wall -g -I.
DEPS = sockhelp.h
OBJ = sockhelp.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

all: lexiconchecker/lexicon_checker

lexicon_checker: lexiconchecker/lexicon_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

.PHONY: clean

clean:
	rm -f $(ODIR)/*.o *~ core $(INCDIR)/*~ lexicon_checker 
