#include <iostream>
#include <sstream>
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <algorithm>
#include <fstream>
#include <map>
#include <math.h>
#include <fcntl.h>
#include "431project.h"

int validateConfiguration(std::string configuration)
{
  int argArray[18];
  int size = 0;
  if(!isan18dimconfiguration(configuration))
  {
    return 0;
  }
  for(int argNum =0; argNum <18; ++argNum)
  {
    int j = 2*argNum;
    std::string argString = configuration.substr(j,1);
    int arg = atoi(argString.c_str());
    argArray[argNum] = arg;
    if(argArray[argNum] >= GLOB_dimensioncardinality[argNum])
    {
      return 0;
    }
  }
  size = argArray[0] + 3;
  if(argArray[11] < argArray[0])
  {
    return 0;
  }
  if(argArray[11] > 3)
  {
    return 0;
  }
  if(argArray[15] != argArray[0] + 3 + argArray[8] + 5 + argArray[9] - 13)
  {
    return 0;
  }
  if(argArray[14] != argArray[0] + 3 + argArray[6] + 5 + argArray[7] - 13)
  {
    return 0;
  }
  if(argArray[16] + 4 != argArray[11] + 4 + argArray[10] + 8 + argArray[12] - 13)
  {
    return 0;
  }
  return 1;
}
std::string generateNextConfigurationProposal(std::string currentconfiguration, std::string bestEXECconfiguration, std::string bestEDPconfiguration, int optimizeforEXEC, int optimizeforEDP)
{
  std::string nextconfiguration=GLOB_baseline;
  while(GLOB_seen_configurations[nextconfiguration])
  {
    unsigned int testParameter[18];
    std::stringstream ss;
    do
    {
      testParameter[0] = rand()%4;
      testParameter[1] = 1;
      testParameter[2] = 0;
      testParameter[3] = rand()%6;
      testParameter[4] = rand()%4;
      testParameter[5] = 0;
      testParameter[6] = 6;
      testParameter[7] = rand()%3;
      testParameter[8] = 6;
      testParameter[9] = rand()%3;
      testParameter[10] = 6;
      testParameter[11] = rand()%4;
      testParameter[12] = 3;
      testParameter[13] = 2;
      testParameter[14] = testParameter[0] + 3 + testParameter[6] + 5 + testParameter[7] - 13;
      testParameter[15] = testParameter[0] + 3 + testParameter[8] + 5 + testParameter[9] - 13;
      testParameter[16] = testParameter[11] + 4 + testParameter[10] + 8 + testParameter[12] - 13 - 4;
      testParameter[17] = 0;
      for(int dim = 0; dim<17; ++dim)
      {
        ss << testParameter[dim] << " ";
      }
      ss << testParameter[17];
      nextconfiguration=ss.str();
      ss.str("");
    }
    while((GLOB_seen_configurations[nextconfiguration])||(!validateConfiguration(nextconfiguration)));
    if(!validateConfiguration(nextconfiguration))
    {
      fprintf(stderr,"Exiting with error; Configuration Proposal invalid:\n%s\n", nextconfiguration.c_str());
      exit(-1);
    }
  }
  return nextconfiguration;
}
