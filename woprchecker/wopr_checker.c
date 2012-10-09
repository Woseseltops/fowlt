/* WOPR spellmod 

   syntax: wopr_checker <valkuil-inst>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include "sockhelp.h"
#include<unistd.h>

#define PORT "2001"
#define MACHINE "localhost"
#define MINLEN 5
#define NRFEAT 7
#define DEBUG2 1
#define DEBUG 1

int main(int argc, char *argv[])
{
  FILE *bron;
  int  i,j,mid,sock,connected,withletters,nrexceptions=0;
  float letterratio;
  char classifyline[32768];
  char word[1024];
  char word2[1024];
  char line[32768];
  char buff[32768];
  char feats[NRFEAT][1024];
  char ***exceptions;
  char *part;
  char inflection,exception;

  // read exceptions

  bron=fopen(argv[1],"r");
  fgets(line,32768,bron);
  while (!feof(bron))
    {
      nrexceptions++;
      fgets(line,32768,bron);
    }
  fclose(bron);
  exceptions=malloc(nrexceptions*sizeof(char**));
  bron=fopen(argv[1],"r");
  for (i=0; i<nrexceptions; i++)
    {
      fscanf(bron,"%s %s ",
	     word,word2);
      exceptions[i]=malloc(2*sizeof(char*));
      exceptions[i][0]=malloc((strlen(word)+1)*sizeof(char));
      exceptions[i][1]=malloc((strlen(word2)+1)*sizeof(char));
      strcpy(exceptions[i][0],word);
      strcpy(exceptions[i][1],word2);
    }
  if (DEBUG2)
    fprintf(stderr,"read %d exception pairs from %s\n",
	    nrexceptions,argv[1]);

  // process inst file

  // first, start up communications with the WOPR server
  ignore_pipe();
  sock=make_connection(PORT,SOCK_STREAM,MACHINE);
  if (sock==-1)
    {
      fprintf(stderr,"the WOPR server is not responding\n");
      exit(1);
    }
  else
    connected=1;

  mid=NRFEAT/2;
  bron=fopen(argv[2],"r");
  fgets(line,32768,bron);
  while (!feof(bron))
    {
      part=strtok(line," \n");
      for (i=0; ((part!=NULL)&&(i<NRFEAT)); i++)
	{
	  strcpy(feats[i],part);
	  part=strtok(NULL," \n");
	}

      strcpy(word,feats[mid]);

      if (!((strcmp(word,"<begin>")==0)||
	    (strcmp(word,"<end>")==0)))
	{

	  fprintf(stdout,"%s",
		  word);

	  withletters=0;
	  for (i=0; i<strlen(word); i++)
	    if (((word[i]>='A')&&(word[i]<='Z'))||
		((word[i]>='a')&&(word[i]<='z')))
	      withletters++;

	  letterratio=(1.*withletters)/(1.*strlen(word));


	  if (letterratio>0.5)
	    {

	      /*
	      ignore_pipe();
	      sock=make_connection(PORT,SOCK_STREAM,MACHINE);
	      if (sock==-1)
		{
		  fprintf(stderr,"the WOPR server is not responding\n");
		  exit(1);
		}
	      else
		connected=1;
	      */

	      // call WOPR
	      strcpy(classifyline,"");
	      for (j=0; j<NRFEAT; j++)
		{
		  if (j!=mid)
		    {
		      strcat(classifyline,feats[j]);
		      strcat(classifyline," ");
		    }
		}
	      strcat(classifyline,word);
	      strcat(classifyline,"\n");
	      
	      if (DEBUG2)
		fprintf(stderr,"calling WOPR with %s",
			classifyline);
	      
	      sock_puts(sock,classifyline);
	      sock_gets(sock,buff,sizeof(buff));
	      
	      if (DEBUG2)
		fprintf(stderr,"getting back: %s\n",
			buff);
	      
	      part=strtok(buff,"\t\n");
	      
	      while ((part!=NULL)&&
		     (strcmp(part,"__EMPTY__")!=0))
		{
		  // special WOPR check
		  exception=0;
		  for (i=0; ((i<nrexceptions)&&(!exception)); i++)
		    {
		      if (((strcmp(word,exceptions[i][0])==0)&&
			   (strcmp(part,exceptions[i][1])==0))||
			  ((strcmp(word,exceptions[i][1])==0)&&
			   (strcmp(part,exceptions[i][0])==0)))
			{
			  exception=1;
			  if (DEBUG)
			    fprintf(stderr,"WOPR caught an exception (%s %s) and will remain silent\n",
				word,part);
			}
		    }

		  // check: plural?
		  inflection=0;
		  if (!exception)
		    {
		      if ((((part[strlen(part)-1]=='s')&&
			    (word[strlen(word)-1]!='s')))||
			  (((part[strlen(part)-1]!='s')&&
			    (word[strlen(word)-1]=='s'))))
			inflection=1;
		      if ((((part[strlen(part)-1]=='e')&&
			    (word[strlen(word)-1]!='e')))||
			  (((part[strlen(part)-1]!='e')&&
			    (word[strlen(word)-1]=='e'))))
			inflection=1;
		      if ((((part[strlen(part)-1]=='n')&&
			    (word[strlen(word)-1]=='t')))||
			  (((part[strlen(part)-1]=='t')&&
			    (word[strlen(word)-1]=='n'))))
			inflection=1;
		    }
		  if ((!inflection)&&
		      (!exception))
		    {
		      fprintf(stdout," %s",
			      part);
		      fprintf(stderr,"WOPR corrects [%s] into [%s]\n",
			      word,part);
		    }
		  part=strtok(NULL,"\t\n");
		}

	      //close(sock);

	    } 
	  fprintf(stdout,"\n");
	}
      fgets(line,32768,bron);
    }
  fclose(bron);
  close(sock);

  return 0;
}


