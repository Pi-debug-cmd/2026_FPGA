struct PitchTracker {
    float ring[512]={},low1=0,low2=0;unsigned wr=0,div=0,filled=0;
    std::vector<float> values;unsigned next=0,quietblocks=0;
    double current=0,median=0,confidence=0,rms=0;
    void push(float v){low1+=.35f*(v-low1);low2+=.35f*(low1-low2);if(++div==4){div=0;ring[wr]=low2;wr=(wr+1)&511;if(filled<512)filled++;}}
    void update(){
        current=0;confidence=0;if(filled<224)return;
        float x[224],d[58];double mean=0,en=0;
        for(int i=0;i<224;i++){x[i]=ring[(wr+512-224+i)&511];mean+=x[i];}mean/=224;
        for(float &v:x){v-=float(mean);en+=v*v;}rms=std::sqrt(en/224);
        if(rms<.002){if(++quietblocks>77){values.clear();next=0;median=0;}return;}quietblocks=0;
        float sum=0;d[0]=1;
        for(int lag=1;lag<=57;lag++){float a=0;for(int i=0;i<160;i++){float z=x[i]-x[i+lag];a+=z*z;}sum+=a;d[lag]=sum>1e-20f?a*lag/sum:1;}
        for(int lag=9;lag<57;lag++)if(d[lag]<.15f && d[lag]<=d[lag-1] && d[lag]<d[lag+1]){
            // Reject weak half-period dips when the full-period match is much stronger.
            int full=0;for(int k=std::max(9,lag*2-2);k<=std::min(56,lag*2+2);k++)
                if(d[k]<=d[k-1]&&d[k]<d[k+1]&&d[k]<.45f*d[lag]&&d[lag]>.025f)if(!full||d[k]<d[full])full=k;
            if(full)lag=full;
            double denom=d[lag-1]-2*d[lag]+d[lag+1];double delta=std::fabs(denom)>1e-12?.5*(d[lag-1]-d[lag+1])/denom:0;
            delta=std::max(-.5,std::min(.5,delta));current=4000/(lag+delta);confidence=1-d[lag];
            if(values.size()<151)values.push_back(float(current));else{values[next]=float(current);next=(next+1)%151;}
            auto sorted=values;std::sort(sorted.begin(),sorted.end());median=sorted[sorted.size()/2];return;
        }
    }
};
