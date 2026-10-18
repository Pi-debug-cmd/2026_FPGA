/* Compare every reduced-model PL matrix against a CPU int8 dot product. */
#include "llvc_runtime.h"
#include "gemm_backend.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc,char **argv){
    if(argc!=2)return 2;
    llvc_t model;
    if(llvc_load(&model,argv[1]))return 3;
    uint8_t *input=calloc(26*512,1);
    int32_t *output=calloc(26*512,sizeof(int32_t));
    if(!input||!output)return 4;
    unsigned total_errors=0;
    for(unsigned mi=0;mi<N_MATS;++mi){
        unsigned ic=mi<6||mi==15?384:192;
        unsigned oc=mi<6||mi==14?384:192;
        unsigned frames=mi==7||mi==8||mi==11||mi==12?26:13;
        for(unsigned t=0;t<frames;++t)
            for(unsigned k=0;k<ic;++k)
                input[t*512+k]=(uint8_t)(int8_t)((t*17+k*11+mi*7)%255-127);
        if(gemm_run_mi(mi,mw(&model,mi),input,output,frames,ic,oc))return 5;
        unsigned errors=0;int32_t max_diff=0,first_expected=0,first_actual=0;
        const uint8_t *w=mw(&model,mi);
        for(unsigned t=0;t<frames;++t)for(unsigned j=0;j<oc;++j){
            int32_t want=0;
            for(unsigned k=0;k<ic;++k)
                want+=(int8_t)input[t*512+k]*(int8_t)w[k*512+j];
            int32_t got=output[t*512+j];
            int32_t diff=got>want?got-want:want-got;
            if(diff){if(!errors){first_expected=want;first_actual=got;}errors++;
                if(diff>max_diff)max_diff=diff;}
        }
        printf("matrix=%u in=%u out=%u frames=%u errors=%u max_diff=%d first_expected=%d first_actual=%d\n",
               mi,ic,oc,frames,errors,max_diff,first_expected,first_actual);
        fflush(stdout);total_errors+=errors;
    }
    printf("total_errors=%u\n",total_errors);
    return total_errors?1:0;
}
