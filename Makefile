CC=gcc
CFLAGS=-O2 -Wall -g -I.
DEPS = sockhelp.h
OBJ = sockhelp.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

all: confusible_checker wopr_checker lexiconchecker/lexicon_checker splitchecker/split_checker runonchecker/runon_checker

confusible_checker: confusiblechecker/confusible_checker.o $(OBJ)
	gcc -o confusiblechecker/$@ $^ $(CFLAGS)

wopr_checker: woprchecker/wopr_checker.o $(OBJ)
	gcc -o woprchecker/$@ $^ $(CFLAGS)

lexicon_checker: lexiconchecker/lexicon_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

split_checker: splitchecker/split_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

runon_checker: runonchecker/runon_checker.o $(OBJ)
	gcc -o $@ $^ $(CFLAGS)

.PHONY: clean

clean:
	rm -f $(ODIR)/*.o *~ core $(INCDIR)/*~ confusible_checker wopr_checker lexicon_checker split_checker runon_checker
