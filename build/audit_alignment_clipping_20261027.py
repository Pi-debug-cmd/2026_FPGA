"""Measure alignment proxies and clipping on frozen public validation pairs."""
import argparse
import json
from pathlib import Path, PureWindowsPath
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = args.asset_root.resolve()
    generated = root / 'build/generated'
    import torch
    for dep in reversed(('llvc_cpu_deps','seed_audio_deps','seed_cpu_deps','world_deps')):
        sys.path.insert(0,str(generated/dep))
    schema = torch.library.Library('torchvision','DEF')
    schema.define('nms(Tensor boxes, Tensor scores, float iou_threshold) -> Tensor')
    sys.path.insert(0,str(generated/'hubert_world_round88_20261027/runtime/build'))
    import numpy as np
    import train_hubert_world_teacher_round20_20261025 as base
    import train_paired_hubert_world_gru_round26_20261025 as paired
    import audit_source_prosody_round32_20261025 as prosody
    from apply_world_temporal_postfilter_round47_20261026 import NON_F0, interpolate
    torch.set_num_threads(4)
    checkpoint = generated/'hubert_world_round88_20261027/paired_causal_gru.pt'
    assert base.sha256(checkpoint)=='e21d8175cb56a5aa3f3e7ac75578705b5deb8cb40fea07a5a73ef87d38586faa'
    cp=torch.load(checkpoint,map_location='cpu',weights_only=False)
    model=paired.ProsodyCausalWorldGRU().eval()
    model.load_state_dict(cp['model'])
    corpus=root/'交接/核心材料/board_budget_20261005/full_train_corpus_16k'
    declaration=json.loads((corpus/'manifest.json').read_text(encoding='utf-8'))
    cache=generated/'hubert_world_round25_20261025'
    assert base.sha256(cache/'cache_manifest.json')==cp['round25_manifest_sha256']
    manifest=json.loads((cache/'cache_manifest.json').read_text(encoding='utf-8'))
    records={r['stem']:r for r in manifest['records'] if r['split']=='validation'}
    hubert=base.HubertModel.from_pretrained(root/'交接/核心材料/neural_reference/RVC/assets/hubert_base',local_files_only=True).float().eval()
    anchors=[]
    for n in (5,6,7,8):
        signal=base.read_16k(root/f'人物音频资料/女声/Track {n}.wav')
        anchors.append(interpolate(base.analyze_world(signal)['output'],len(base.extract_hubert(hubert,signal))))
    del hubert
    lo,hi=np.percentile(np.concatenate(anchors),[0.1,99.9],axis=0)
    groups={'spectrum':slice(0,60),'log_f0':slice(60,61),'energy':slice(62,63),'ap':slice(63,75)}
    result={'task':'PS-20261021-10','kind':'alignment_clipping_diagnosis',
            'checkpoint_sha256':base.sha256(checkpoint),'cache_manifest_sha256':base.sha256(cache/'cache_manifest.json'),
            'anchor_statistics':'same20ms HuBERT-resampled target anchors as production candidate',
            'lag_definition':'correlation(source_energy[t], teacher_energy[t+lag]); 20ms per frame',
            'recording4_used':False,'recording5_used':False,'track9_used':False,
            'training':False,'synthesis':False,'played':False,'board_touched':False,'rows':[]}
    for row in declaration['validation']:
        record=records[row['stem']]
        path=corpus/'src'/PureWindowsPath(row['src']).name
        assert base.sha256(path)==row['src_sha']
        cache_path=cache/'cache'/record['cache']
        assert base.sha256(cache_path)==record['cache_sha256']
        data=np.load(cache_path)
        content=data['content'].astype(np.float32); target=data['target'].astype(np.float32)
        p=prosody.resample_rows(prosody.source_prosody(prosody.read_raw(path)),len(content))
        x=(((content-cp['pca_mean'])@cp['pca_projection']-cp['x_mean'])/cp['x_std']).astype(np.float32)
        x=np.concatenate((x,(p-cp['prosody_mean'])/cp['prosody_std']),axis=1).astype(np.float32)
        with torch.inference_mode():raw=model(torch.from_numpy(x[None]))[0].numpy()
        prediction=raw*cp['y_std']+cp['y_mean']
        amplified=prediction.copy()
        for group in NON_F0:
            center=amplified[:,group].mean(axis=0,keepdims=True)
            amplified[:,group]=center+1.6*(amplified[:,group]-center)
        lags=[]
        for lag in range(-10,11):
            source=p[max(0,-lag):len(p)-max(0,lag),2]
            teacher=target[max(0,lag):len(target)-max(0,-lag),62]
            lags.append({'lag':lag,'correlation':float(np.corrcoef(source,teacher)[0,1])})
        metrics={}
        for name,group in groups.items():
            truth=target[:,group]; denom=np.sqrt(np.mean(np.diff(truth,axis=0)**2))+1e-8
            stats={}
            for key,value in [('prediction',prediction),('gain1_6',amplified),('gain1_6_clipped',np.clip(amplified,lo,hi))]:
                z=(value[:,group]-truth)/cp['y_std'][group]
                absolute=np.abs(z)
                stats[key]={'normalized_smooth_l1':float(np.mean(np.where(absolute<1,0.5*z*z,absolute-0.5))),
                            'dynamic_rms_ratio':float(np.sqrt(np.mean(np.diff(value[:,group],axis=0)**2))/denom),
                            'outside_anchor_fraction':float(np.mean((value[:,group]<lo[group])|(value[:,group]>hi[group])))}
            stats['teacher_outside_anchor_fraction']=float(np.mean((truth<lo[group])|(truth>hi[group])))
            metrics[name]=stats
        result['rows'].append({'stem':row['stem'],'speaker':row['speaker'],'source_sha256':row['src_sha'],
                               'zero_lag_correlation':lags[10]['correlation'],'best_energy_lag':max(lags,key=lambda v:v['correlation']),
                               'energy_lags':lags,'groups':metrics})
        print(json.dumps({'stem':row['stem'],'best_energy_lag':result['rows'][-1]['best_energy_lag']}),flush=True)
    result['complete']=True
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
