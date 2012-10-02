/* confusible spellmod 

   syntax: confusible_checker <word1> <word2> <threshold> <valkuil-inst>

*/

#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include "sockhelp.h"
#include<unistd.h>

#define PORT "2000"
#define MACHINE "localhost"
#define NRFEAT 7
#define MINOCC 10.
#define DEBUG 1

int main(int argc, char *argv[])
{
  FILE *bron;
  float distweight[1024];
  char word1[1024];
  char capword1[1024];
  char word2[1024];
  char capword2[1024];
  float total,max,threshold;
  int  i,j,mid,sock,connected,nrdist,maxnr;
  char classifyline[32768];
  char line[32768];
  char buff[32768];
  char buffer[1024];
  char feats[NRFEAT][1024];
  char *part;
  char category[1024];
  char match;

  strcpy(word1,argv[1]);
  strcpy(capword1,word1);
  capword1[0]-=32;

  strcpy(word2,argv[2]);
  strcpy(capword2,word2);
  capword2[0]-=32;

  sscanf(argv[3],"%f",&threshold);
  if ((threshold<0.5)||
      (threshold>1.0))
    {
      fprintf(stderr,"[confusible_checker] ERROR: threshold value not between 0.5 and 1.0\n");
      exit(1);
    }

  // process inst file

  // first, start up communications with the Timbl server
  ignore_pipe();
  sock=make_connection(PORT,SOCK_STREAM,MACHINE);
  if (sock==-1)
    {
      fprintf(stderr,"the confusible server is not responding\n");
      exit(1);
    }
  else
    connected=1;

  // cut off the Timbl welcome message
  sock_gets(sock,buff,sizeof(buff)-1); 

  // cut off the Timbl base message
  sock_gets(sock,buff,sizeof(buff)-1); 

  // tell the Timbl server to use the word1-word2 base
  sprintf(buffer,"base %s-%s\n",
	  word1,word2);
  sock_puts(sock,buffer);

  // cut off the Timbl acknowledgement
  sock_gets(sock,buff,sizeof(buff)-1); 
  
  mid=NRFEAT/2;
  bron=fopen(argv[4],"r");
  fgets(line,32768,bron);
  while (!feof(bron))
    {
      part=strtok(line," \n");
      for (i=0; ((part!=NULL)&&(i<NRFEAT)); i++)
	{
	  strcpy(feats[i],part);
	  part=strtok(NULL," \n");
	}
      if (!((strcmp(feats[mid],"<begin>")==0)||
	    (strcmp(feats[mid],"<end>")==0)))
	{
	  match=0;
	  if ((strcmp(feats[mid],word1)==0)||
	      (strcmp(feats[mid],capword1)==0)||
	      (strcmp(feats[mid],word2)==0)||
	      (strcmp(feats[mid],capword2)==0))
	    match=1;
	  
	  fprintf(stdout,"%s",
		  feats[mid]);
	  
	  if (match)
	    {
	      // call Timbl
	      strcpy(classifyline,"c ");
	      for (j=0; j<NRFEAT; j++)
		{
		  if (j!=mid)
		    strcat(classifyline,feats[j]);
		  strcat(classifyline," ");
		}
	      strcat(classifyline,"?\n");

	      if (DEBUG)
		fprintf(stderr,"\ncalling Timbl with %s",
			classifyline);
	      
	      sock_puts(sock,classifyline);
	      sock_gets(sock,buff,sizeof(buff));
	      
	      if (DEBUG)
		fprintf(stderr,"getting back: %s\n",
			buff);
	      
	      part=strtok(buff," \n");
	      part=strtok(NULL," \n");
	      strcpy(category,"");
	      for (j=1; j<strlen(part)-1; j++)
		{
		  strcat(category," ");
		  category[j-1]=part[j];
		}
	      while ((part!=NULL)&&
		     (strcmp(part,"{")!=0))
		part=strtok(NULL," \n");
	      
	      if (part!=NULL)
		{
		  nrdist=0;
		  while ((part!=NULL)&&
			 (strcmp(part,"}")!=0))
		    {
		      part=strtok(NULL," \n");
		      if (strcmp(part,"}")!=0)
			{
			  part=strtok(NULL," \n");
			  if (part[strlen(part)-1]==',')
			    sscanf(part,"%f,",&distweight[nrdist]);
			  else
			    sscanf(part,"%f",&distweight[nrdist]);
			  nrdist++;
			}
		    }
		  if (DEBUG)
		    {
		      fprintf(stderr,"distro of %d:",
			      nrdist);
		      for (i=0; i<nrdist; i++)
			fprintf(stderr," %.0f",
				distweight[i]);
		    }
		  
		  max=0.0;
		  total=0.0;
		  for (i=0; i<nrdist; i++)
		    {
		      total+=distweight[i];
		      if (distweight[i]>max)
			{
			  max=distweight[i];
			  maxnr=i;
			}
		    }
		  
		  if (DEBUG)
		    fprintf(stderr," - max %6.3f certainty\n",
			    (max/total));
		  
		  if ((max/total>=threshold)&&
		      (max/total<1.0)&&
		      (total>MINOCC))
		    {
		      if (strcmp(category,feats[mid])!=0)
			{
			  fprintf(stdout," %s",
				  category);
			  fprintf(stderr,"corrected %s into %s\n",
				  feats[mid],category);
			}
		    }
		}
	    }
	  fprintf(stdout,"\n");
	}
      fgets(line,32768,bron);
    }
  fclose(bron);
  close(sock);

  return 0;
}
