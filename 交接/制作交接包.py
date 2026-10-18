from pathlib import Path
import shutil, hashlib, json, os, time
OUT=Path(r"D:\交接")
ROOT=OUT/"核心材料"
WORK=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
mapping=[
 (Path(r"D:\总进度\7020验收记录"), ROOT/"验收记录"),
 (Path(r"D:\总进度\目标人物语音"), ROOT/"目标人物原始语音"),
 (Path(r"D:\总进度\目标人物分析\SeedVC下一阶段\inputs\target_t6_8s.wav"), ROOT/"目标参考"/"target_t6_8s.wav"),
 (Path(r"D:\Tools_FPGA\image\zynq.img"), ROOT/"官方启动镜像"/"zynq.img"),
 (WORK/"board_budget_20261005",ROOT/"board_budget_20261005"),
 (WORK/"deploy_runtime",ROOT/"deploy_runtime"),
 (WORK/"kernel_module",ROOT/"kernel_module"),
 (WORK/"pl_kernels"/"build_2018",ROOT/"pl_kernels"/"build_2018"),
 (WORK/"pl_kernels"/"gemm_s8"/"gemm_s8.cpp",ROOT/"pl_kernels"/"gemm_s8"/"gemm_s8.cpp"),
 (WORK/"pl_kernels"/"gemm_s8"/"gemm_s8.h",ROOT/"pl_kernels"/"gemm_s8"/"gemm_s8.h"),
 (WORK/"pl_kernels"/"pointwise_s8"/"pointwise_s8_packed.cpp",ROOT/"pl_kernels"/"pointwise_s8"/"pointwise_s8_packed.cpp"),
 (WORK/"pl_kernels"/"pointwise_s8"/"pointwise_s8.h",ROOT/"pl_kernels"/"pointwise_s8"/"pointwise_s8.h"),
 (WORK/"pl_kernels"/"pointwise_s8"/"run_hls_packed.tcl",ROOT/"pl_kernels"/"pointwise_s8"/"run_hls_packed.tcl"),
 (WORK/"board_support",ROOT/"board_support"),
 (WORK/"vendor_base_2022_2",ROOT/"vendor_base_2022_2"),
 (Path(r"D:\g_ip"),ROOT/"g_ip"),
 (Path(r"D:\g_build\proj"),ROOT/"g_build"/"proj"),
 (WORK/"neural_reference"/"LLVC",ROOT/"neural_reference"/"LLVC"),
 (WORK/"neural_reference"/"RVC"/"assets"/"hubert_base",ROOT/"neural_reference"/"RVC"/"assets"/"hubert_base"),
 (WORK/"neural_reference"/"cross_evaluators",ROOT/"neural_reference"/"cross_evaluators"),
 (WORK/"neural_reference"/"dependency_source_audit",ROOT/"neural_reference"/"dependency_source_audit"),
 (WORK/"neural_reference"/"cache"/"hf"/"hub"/"models--openai--whisper-small",ROOT/"neural_reference"/"cache"/"hf"/"hub"/"models--openai--whisper-small"),
]
NR=WORK/"neural_reference"
for src in NR.iterdir():
    if src.is_file() and src.suffix.lower() in (".py",".json",".txt"):
        mapping.append((src,ROOT/"neural_reference"/src.name))
missing=[]
for i,(src,dst) in enumerate(mapping,1):
    if not src.exists():
        missing.append(str(src));continue
    print(f"{i}/{len(mapping)} {src}",flush=True)
    if src.is_dir():
        shutil.copytree(src,dst,dirs_exist_ok=True,ignore=shutil.ignore_patterns("__pycache__","*.pyc",".Xil"))
    else:
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
files=[]
for p in ROOT.rglob("*"):
    if p.is_file():
        h=hashlib.sha256()
        with p.open("rb") as f:
            for block in iter(lambda:f.read(4*1024*1024),b""):
                h.update(block)
        files.append({"path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,"sha256":h.hexdigest()})
manifest={"created_local":"2026-10-09","root":"核心材料","files":files,"missing_sources":missing,"source_mapping":[{"from":str(a),"to":str(b.relative_to(OUT))} for a,b in mapping]}
(OUT/"文件校验清单.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print("DONE",len(files),"files",sum(x["bytes"] for x in files),"bytes","missing",missing,flush=True)
