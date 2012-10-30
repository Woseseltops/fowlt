/* split spellmod

   args: split_checker <lexicon> <valkuil-inst>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

#define MINCOMBILENGTH 5
#define CEILINGFREQ 999999999
#define FREQRATIO 2
#define MAXNRCHECK 256
#define MINLENGTH 2
#define DEBUG 1
#define DEBUG2 0

unsigned long sdbm(char *str);

int main(int argc, char *argv[])
{
  FILE *bron;
  char **lexicon;
  unsigned long *freqs;
  unsigned long *hash;
  unsigned long thishash;
  unsigned long thiscombihash;
  char word[1024];
  char prevword[1024];
  char combitest[2048];
  char checklist[MAXNRCHECK][1024];
  int  k,nrlex=0,readnr,nrcheck;
  unsigned long prevfreq,curfreq,combifreq;
  FILE *context;
  char inlex,inlist,cinlex;
  float confidence;

  /* allocate lexicon */
  lexicon=malloc(sizeof(char*));
  freqs=malloc(sizeof(unsigned long));
  hash=malloc(sizeof(unsigned long));

  /* read lexicon */
  nrlex=0;
  bron=fopen(argv[1],"r");
  while (!feof(bron))
    {
      fscanf(bron,"%d %s ",
	     &readnr,word);

      lexicon[nrlex]=malloc((strlen(word)+1)*sizeof(char));
      strcpy(lexicon[nrlex],word);
      freqs[nrlex]=readnr;
      hash[nrlex]=sdbm(word);

      nrlex++;

      lexicon=realloc(lexicon,(nrlex+1)*sizeof(char*));
      freqs=realloc(freqs,(nrlex+1)*sizeof(unsigned long));
      hash=realloc(hash,(nrlex+1)*sizeof(unsigned long));
    }
  fclose(bron);

  if (DEBUG2)
    fprintf(stderr,"read %d words from lexicon\n",
	    nrlex);

  /* reading exception list */
  bron=fopen(argv[2],"r");
  nrcheck=0;
  while ((!feof(bron))&&
	 (nrcheck<MAXNRCHECK))
    {
      fscanf(bron,"%s ",
	     checklist[nrcheck]);
      nrcheck++;
    }
  fclose(bron);

  strcpy(prevword,"#-#=#");
  prevfreq=0;

  context=fopen(argv[3],"r");
  while (!feof(context))
    {
      fscanf(context,"%s ",word);
      sprintf(combitest,"%s%s",
	      prevword,word);

      curfreq=0;
      combifreq=0;
      inlex=0;
      inlist=0;
      cinlex=0;
      if ((strlen(combitest)>MINCOMBILENGTH)&&
	  (strlen(word)>MINLENGTH))
	{
	  thishash=sdbm(word);
	  thiscombihash=sdbm(combitest);
	  for (k=0; ((k<nrlex)&&((!inlex)||(!cinlex))); k++)
	    {
	      if (thishash==hash[k])
		{
		  curfreq=freqs[k];
		  inlex=1;
		}
	      if (thiscombihash==hash[k])
		{
		  cinlex=1;
		  combifreq=freqs[k];
		}
	    }
	  
	  if (cinlex)
	    {
	      inlist=0;
	      for (k=0; ((k<nrcheck)&&(!inlist)); k++)
		{
		  if (strcmp(combitest,checklist[k])==0)
		    inlist=1;
		}
	    }
	}
      else
	curfreq=CEILINGFREQ;

      /*
      if ((DEBUG)&&(combifreq>0))
	fprintf(stderr,"found combi [%s] (freq %ld) of [%s] (freq %ld) and [%s] (freq %ld)\n",
		combitest,combifreq,prevword,prevfreq,word,curfreq);
      */

      if ((cinlex)&&
	  (!inlist)&&
	  ((combifreq>(prevfreq/FREQRATIO))||
	   (combifreq>(curfreq/FREQRATIO))))
	{
          if (combifreq/(((prevfreq+curfreq)/FREQRATIO)/2) > 0)
          {
		  confidence = (1 - 1/((float)combifreq/((((float)prevfreq+(float)curfreq)/(float)FREQRATIO)/(float)2)));

		  fprintf(stdout," %s%6.3f\n%s %s%6.3f",
		  combitest,confidence, word,combitest,confidence);
          }
          else
          {
		  fprintf(stdout," %s 0\n%s %s 0",
		  combitest,word,combitest);
	  }
	  if (DEBUG)
	    fprintf(stderr,"found combi [%s] (freq %ld) of [%s] (freq %ld) and [%s] (freq %ld)\n",
		    combitest,combifreq,prevword,prevfreq,word,curfreq);
	}
      else
	{
	  if (strcmp(prevword,"#-#=#")==0)
	    fprintf(stdout,"%s",
		    word);
	  else
	    fprintf(stdout,"\n%s",
		    word);
	}

      strcpy(prevword,word);
      prevfreq=curfreq;
      
    }
  fclose(context);  
  fprintf(stdout,"\n");

  return 0;
}

unsigned long sdbm(char *str)
{
  unsigned long hash = 0;
  int c;

  while (c = *str++)
    hash = c + (hash << 6) + (hash << 16) - hash;

  return hash;
}
