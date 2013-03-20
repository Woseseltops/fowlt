/* aspell spellmod

   use aspell's pipe mode to to typo checking

   args: aspell_checker <lexicon> <1-word-per-line>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<ctype.h>

#define MAXLD 1 // be conservative...
#define LDTHRESHOLD 7
#define FREQFACTOR 10000
#define MINLENGTH 5
#define MINFREQTHRESHOLD 10000
#define MAXNRCLOSEST 5
#define DEBUG2 0
#define DEBUG 1

int levenshtein(char *stra, char *strb);
int ld1(char *stra, char *strb);
unsigned long sdbm(char *str);
int isNumber(char str[]);

int main(int argc, char *argv[])
{
  FILE *bron,*aspell;
  char **lexicon;
  unsigned long *freqs;
  unsigned long *hash;
  char word[1024];
  char capword[1024];
  char commandline[1024];
  char closestword[MAXNRCLOSEST+1][1024];
  int  closest[MAXNRCLOSEST+1];
  unsigned long closestfreq[MAXNRCLOSEST+1];
  unsigned long thishash;
  int  i,j,k,l,thislev,nrlex=0,nrclosest=0,nraspell,readnr,wordlen,lexlen;
  FILE *context;
  char inlex,cap,hyp,inflection,tokstatus;
  char aspellline[32768];
  char memline[32768];
  char *part;
  char aspellword[1024];

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

  /* run aspell on input.tok.txt */
  sprintf(commandline,"aspell --lang=en --pipe < %s > input.tok.aspell\n",
	  argv[2]);
  if (DEBUG)
    fprintf(stderr,"executing: %s",
	    commandline);
  system(commandline);

  context=fopen(argv[2],"r");
  aspell=fopen("input.tok.aspell","r");
  fgets(aspellline,32768,aspell);

  while (!feof(context))
    {
      fscanf(context,"%s ",word);

      wordlen=strlen(word);
      
      nrclosest=0;

      tokstatus=1;
      if (strstr(",.!?:;\'\"(){}[]\\/|€",word))
	tokstatus=0;
      if (tokstatus)
	if (isNumber(word))
	  tokstatus=0;
      if (strstr(word,"http://"))
	tokstatus=0;
      if (strstr(word,"@"))
	tokstatus=0;

      if (tokstatus)
	{

	  fgets(aspellline,32768,aspell);
	  strcpy(memline,aspellline);
	  part=strtok(aspellline," \n");

	  if (strcmp(part,"&")==0)
	    {
	      // read alternatives from aspellline 

	      part=strtok(NULL," \n");

	      if (strcmp(part,word)==0)
		{
		  part=strtok(NULL," \n");
		  sscanf(part,"%d",&nraspell);
		  
		  if (DEBUG2)
		    fprintf(stderr,"[%s] [%d options]\n",
			    word,nraspell);
		  
		  inlex=0;
		  thishash=sdbm(word);
		  for (k=0; ((k<nrlex)&&(!inlex)); k++)
		    {
		      if (thishash==hash[k])
			{
			  inlex=1;
			  if (DEBUG2)
			    fprintf(stderr,"word [%s] in lexicon, with frequency %ld\n",
				    word,freqs[k]);
			}
		    }

		  // read extra string (offset)
		  part=strtok(NULL," \n");

		  for (k=0; k<nraspell; k++)
		    {
		      part=strtok(NULL," \n");
		      strcpy(aspellword,"");
		      for (l=0; l<strlen(part)-1; l++)
			{
			  strcat(aspellword," ");
			  aspellword[l]=part[l];
			}

		      if (!strstr(aspellword,"-"))
			{
			  lexlen=strlen(aspellword);
			  if ((lexlen>wordlen+MAXLD)||
			      (wordlen>lexlen+MAXLD))
			    thislev=MAXLD+1;
			  else
			    thislev=levenshtein(aspellword,word);
			  
			  if (thislev<=MAXLD)
			    {
			      inflection=0;
			      // check: plural?
			      if ((((aspellword[strlen(aspellword)-1]=='s')&&
				    (word[strlen(word)-1]!='s')))||
				  (((aspellword[strlen(aspellword)-1]!='s')&&
				    (word[strlen(word)-1]=='s'))))
				inflection=1;
			      if ((((aspellword[strlen(aspellword)-1]=='e')&&
				    (word[strlen(word)-1]!='e')))||
				  (((aspellword[strlen(aspellword)-1]!='e')&&
				    (word[strlen(word)-1]=='e'))))
				inflection=1;
			      if ((((aspellword[strlen(aspellword)-1]=='n')&&
				    (word[strlen(word)-1]=='t')))||
				  (((aspellword[strlen(aspellword)-1]=='t')&&
				    (word[strlen(word)-1]=='n'))))
				inflection=1;
			      if (!inflection)
				{
				  j=0;
				  while ((j<nrclosest)&&
					 (freqs[k]<closestfreq[j]))
				    j++;
				  if (j<nrclosest)
				    {
				      // move up
				      for (l=nrclosest; l>j; l--)
					{
					  strcpy(closestword[l],closestword[l-1]);
					  closest[l]=closest[l-1];
					  closestfreq[l]=closestfreq[l-1];
					}
				    }
				  // insert
				  strcpy(closestword[j],aspellword);
				  closest[j]=thislev;
				  closestfreq[j]=freqs[k];
				  if (nrclosest<MAXNRCLOSEST)
				    nrclosest++;
				}
			    }  
			}
		    }
		  if (DEBUG2)
		    {
		      fprintf(stderr,"closest to %s:\n",
			      word);
		      for (i=0; i<nrclosest; i++)
			fprintf(stderr," %2d %s\n",
				i,closestword[i]);
		      
		    }
		}
	    }
	}

      fprintf(stdout,"%s",
	      word);

      // post-filter (too bad for all the work done before):
      // don't correct capitalized words, don't correct words with
      // hyphens

      cap=0;
      if ((word[0]>='A')&&
	  (word[0]<='Z'))
	cap=1;
      hyp=0;
      if (strstr(word,"-"))
	hyp=1;
      
      if ((nrclosest>0)&&
	  (wordlen>=MINLENGTH)&&
	  (!cap)&&
	  (!hyp))
	{
	  for (i=0; i<nrclosest; i++)
	    fprintf(stdout," %s",
		    closestword[i]);
	  if (DEBUG)
	    {
	      fprintf(stderr,"correction suggestions for %s: ",
		      word);
	      for (i=0; i<nrclosest; i++)
		fprintf(stderr," %s",
			closestword[i]);
	      fprintf(stderr,"\n");
	    }
          fprintf(stdout," 0.6");
	}
      
      fprintf(stdout,"\n");      
    }
  fclose(aspell);
  fclose(context);  

  return 0;
}

int ld1(char *stra, char *strb)
{
  int i,j,k,l,m,ld=2;

  i=0;
  while ((i<strlen(stra))&&
	 (i<strlen(strb))&&
	 (stra[i]==strb[i]))
    i++;

  j=strlen(stra);
  k=strlen(strb);

  l=1;
  while (((j-l)>=i)&&
	 ((k-l)>=i)&&
	 (stra[j-l]==strb[k-l]))
    l++;
  l--;

  if (j>k)
    ld=j-(l+i);
  else
    ld=k-(l+i);

  if (DEBUG2)
    {
      if (ld<=MAXLD)
	{
	  fprintf(stderr,"ld %d between %s and %s; j %d, k %d, i %d, l %d\n",
		  ld,stra,strb,j,k,i,l);
	}
    }

  return ld;
}

int levenshtein(char *stra, char *strb) {
  int i, j, k, l, m1, m2, m3, laa, r;
  int lengtha, lengthb, lengthmin;
  int **d;
  char *a;

  lengtha = strlen(stra);
  lengthb = strlen(strb);
  lengthmin = lengtha;
  if(lengthb > lengthmin) lengthmin = lengthb;

  a = (char*)malloc((lengthmin+2)*sizeof(char));
  d = (int**)malloc((lengthmin+2)*sizeof(int*));
  for(i = 0; i < lengthmin + 2; i++) d[i] = (int*)malloc((lengthmin+2)*sizeof(int));
  for(i = 0; i <= lengtha; i++) a[i] = stra[i];

  laa = lengtha;
  d[0][0] = 0;
  for(i = 1; i <= lengtha; i++) d[i][0] = d[i-1][0]+1;
  for(j = 1; j <= lengthb; j++) d[0][j] = d[0][j-1]+1;

  for(i = 1; i <= laa; i++) {
    for(j = 1;j <= lengthb; j++) {
      r = 0;
      if(a[i-1] != strb[j-1]) {
	r = 1;
	a[i-1] = strb[j-1];
      }
      m1 = d[i-1][j-1]+r;
      for(k = lengtha; k >= i-1; k--) a[k+1] = a[k];
      a[j-1] = strb[j-1];
      lengtha++;
      m2 = d[i][j-1]+1;
      for(k = i-1; k < lengtha; k++) a[k] = a[k+1];
      lengtha--;
      m3 = d[i-1][j]+1;
      r = m1;
      if( m2 < r) r = m2;
      if(m3 < r) r = m3;
      d[i][j] = r;
      lengtha = laa;
      for(l = 0; l <= lengtha; l++) a[l] = stra[l];
    } 
  }

  r = d[lengtha][lengthb];
  free(a);
  for(i = 0; i < lengthmin+2; i++) free(d[i]);
  free(d);
  return(r);
}

unsigned long sdbm(char *str)
{
  unsigned long hash = 0;
  int c;

  while (c = *str++)
    hash = c + (hash << 6) + (hash << 16) - hash;

  return hash;
}

int isNumber(char str[])
{
  int i;
  int len = strlen(str);
  int res=1;

  for (i=0; ((i<len)&&(res)); i++)
    {
      if (!(((str[i]>='0')&&(str[i]<='9'))||
	    (str[i]=='.')||
	    (str[i]==',')||
	    (str[i]=='-')))
	res=0;
    }

  return res;
}

