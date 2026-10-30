#include "../kernel/world_exp_ioctl.h"
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <algorithm>
#include <time.h>
static double Now() {timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+t.tv_nsec*1e-9;}
int main(int argc,char **argv) {
  if(argc!=3) return 2;
  FILE *in=fopen(argv[1],"rb"), *expected=fopen(argv[2],"rb");
  int fd=open("/dev/world_exp",O_RDWR|O_CLOEXEC);
  if(!in || !expected || fd<0) {perror("probe open");return 3;}
  world_exp_packet p; unsigned long frames=0,errors=0; std::vector<double> timings;
  __u64 gold[WORLD_EXP_BINS];
  while(fread(p.input,sizeof(p.input),1,in)==1) {
    if(fread(gold,sizeof(gold),1,expected)!=1) return 4;
    memset(p.output,0xa5,sizeof(p.output));
    double t=Now();
    if(ioctl(fd,WORLD_EXP_PROCESS,&p)) {perror("probe ioctl");return 5;}
    timings.push_back((Now()-t)*1e6);
    for(int i=0;i<WORLD_EXP_BINS;++i) if(p.output[i]!=gold[i]) {
      if(errors<8) fprintf(stderr,"frame=%lu bin=%d got=%016llx expected=%016llx\n",frames,i,(unsigned long long)p.output[i],(unsigned long long)gold[i]);
      ++errors;
    }
    ++frames;
  }
  if(!feof(in) || fgetc(expected)!=EOF || !frames) return 6;
  double sum=0; for(double x:timings) sum+=x;
  std::sort(timings.begin(),timings.end());
  printf("{\"frames\":%lu,\"bins\":%lu,\"mismatches\":%lu,\"mean_us\":%.3f,\"p95_us\":%.3f,\"max_us\":%.3f}\n",frames,frames*WORLD_EXP_BINS,errors,sum/frames,timings[(frames-1)*95/100],timings.back());
  close(fd);fclose(in);fclose(expected);return errors?7:0;
}
