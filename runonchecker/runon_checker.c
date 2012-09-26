/* runon spellmod

   args: runon_checker <lexicon> <valkuil-inst>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

#define MINLEN 3
#define MAXNRCHECK 256
#define THRESHOLD 3000
#define DEBUG2 1
#define DEBUG 1

unsigned long sdbm(char *str);

int main(int argc, char *argv[])
{
  FILE *bron;
  char **lexicon;
  unsigned long *freqs;
  unsigned long *hash;
  unsigned long thishash;
  char word[1024];
  char left[1024];
  char right[1024];
  float leftfraction,rightfraction;
  char checklist[MAXNRCHECK][1024];
  int  i,j,k,nrlex=0,leftpart,rightpart,readnr,nrcheck;
  unsigned long curfreq,leftfreq,rightfreq;
  FILE *context;
  char inlex,inlist,leftinlex,rightinlex,runon;

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

  context=fopen(argv[3],"r");
  while (!feof(context))
    {
      fscanf(context,"%s ",word);

      inlist=0;
      for (k=0; ((k<nrcheck)&&(!inlist)); k++)
	{
	  if (strcmp(word,checklist[k])==0)
	    inlist=1;
	}

      runon=0;
      if ((!inlist)&&
	  (strlen(word)>=(2*MINLEN)))
	{
	  curfreq=0;
	  inlex=0;
	  thishash=sdbm(word);
	  for (k=0; ((k<nrlex)&&(!inlex)); k++)
	    {
	      if (thishash==hash[k])
		{
		  curfreq=freqs[k];
		  inlex=1;
		}
	    }

	  if (!inlex)
	    {

	      for (i=MINLEN; ((!runon)&&(i<(strlen(word)-MINLEN))); i++)
		{
		  strcpy(left,"");
		  for (j=0; j<i; j++)
		    {
		      strcat(left," ");
		      left[j]=word[j];
		    }
		  strcpy(right,"");
		  for (j=i; j<strlen(word); j++)
		    {
		      strcat(right," ");
		      right[strlen(right)-1]=word[j];
		    }
		  
		  leftfreq=0;
		  leftinlex=0;
		  thishash=sdbm(left);
		  for (k=0; ((k<nrlex)&&(!leftinlex)); k++)
		    {
		      if (thishash==hash[k])
			{
			  leftfreq=freqs[k];
			  leftinlex=1;
			}
		      if (strstr(left,lexicon[k]))
			if (strlen(lexicon[k])+MINLEN>=strlen(left)) 
			  leftpart++;
		    }
		  if (leftinlex)
		    {
		      rightfreq=0;
		      rightinlex=0;
		      thishash=sdbm(right);
		      for (k=0; ((k<nrlex)&&(!rightinlex)); k++)
			{
			  if (thishash==hash[k])
			    {
			      rightfreq=freqs[k];
			      rightinlex=1;
			    }
			}
		      
		      if (rightinlex)
			{
			  
			  leftpart=0;
			  for (k=0; k<nrlex; k++)
			    {
			      if (strstr(lexicon[k],left))
				if (strlen(lexicon[k])-MINLEN>=strlen(left)) 
				  {
				    leftpart++;
				  }
			    }
			  
			  rightpart=0;
			  for (k=0; k<nrlex; k++)
			    {
			      if (strstr(lexicon[k],right))
				if (strlen(lexicon[k])-MINLEN>=strlen(right)) 
				  {
				    rightpart++;
				  }
			    }
			  if (leftpart>0)
			    leftfraction=leftfreq/(1.*leftpart);
			  else
			    leftfraction=0.0;
			  if (rightpart>0)
			    rightfraction=rightfreq/(1.*rightpart);
			  else
			    rightfraction=0.0;

			  if (DEBUG2)
			    {
			      fprintf(stderr,"[%s] is %d times part of a larger word, fraction 1 in %.0f\n",
				      left,leftpart,leftfraction);
			      fprintf(stderr,"[%s] is %d times part of a larger word, fraction 1 in %.0f\n",
				      right,rightpart,rightfraction);
			    }

			  if ((leftfraction>THRESHOLD)&&(rightfraction>THRESHOLD))
			    {
			      if (DEBUG)
				fprintf(stderr,"split run-on [%s] (freq %ld) into [%s] (freq %ld) [%s] (freq %ld)\n",
					word,curfreq,left,leftfreq,right,rightfreq);
			      runon=1;
			    }
			}
		    }
		}
	      
	    }
	  
      	}

      fprintf(stdout,"%s",
	      word);
      if (runon)
	{
	  fprintf(stdout," %s %s",
		  left,right);
	}
      fprintf(stdout,"\n");

    }
  fclose(context);  
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
