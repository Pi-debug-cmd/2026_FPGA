param(
    [Parameter(Mandatory = $true)][int]$Round,
    [Parameter(Mandatory = $true)][int]$Steps,
    [Parameter(Mandatory = $true)][double]$LearningRate,
    [ValidateSet('all', 'output', 'gru_output')][string]$Trainable = 'all',
    [ValidateSet('train1', 'train2', 'train3')][string[]]$Roles = @('train1', 'train2', 'train3')
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = 'C:\Users\World\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$assetRoot = 'C:\Users\World\Desktop\2026_FPGA'
$output = Join-Path $repo "build\generated\hubert_world_round${Round}_20261029"
$deps = @(
    "$assetRoot\build\generated\world_deps",
    "$assetRoot\build\generated\llvc_cpu_deps",
    "$assetRoot\build\generated\seed_audio_deps",
    "$assetRoot\build\generated\seed_cpu_deps",
    "$assetRoot\build\generated\eval_deps_20261016"
) -join ';'
$env:PYTHONPATH = $deps
& $python (Join-Path $PSScriptRoot 'finetune_fixed_male_hubert_world_20261029.py') `
    --cache-manifest (Join-Path $repo 'build\generated\fixed_male_teacher_pairs_20261029\cache_manifest.json') `
    --checkpoint "$assetRoot\build\generated\hubert_world_round88_20261027\paired_causal_gru.pt" `
    --output $output --experiment-round $Round --steps $Steps --learning-rate $LearningRate `
    --trainable $Trainable --roles $Roles
if ($LASTEXITCODE -ne 0) { throw "fine-tune failed: $LASTEXITCODE" }
& $python (Join-Path $PSScriptRoot 'apply_world_temporal_postfilter_round47_20261026.py') `
    --asset-root $assetRoot --generated-root "$assetRoot\build\generated" `
    --checkpoint (Join-Path $output 'paired_causal_gru.pt') --output (Join-Path $output 'candidates') `
    --gain 1.6 --experiment-round $Round --source-relative '人物音频资料/男声/标准录音 4.wav'
if ($LASTEXITCODE -ne 0) { throw "candidate generation failed: $LASTEXITCODE" }
$env:PYTHONPATH = 'C:\Users\World\.codex\visualizations\2026\10\24\01a16cde-f3e4-72f1-90c2-c09dddce4302\ps_opt_worktree\build\generated\seed_eval_deps'
& $python (Join-Path $PSScriptRoot 'evaluate_seed_fixed_male_strict_20261024.py') `
    --asset-root $assetRoot --manifest (Join-Path $output 'candidates\strict_manifest.json') `
    --output (Join-Path $output 'strict_evaluation.json')
if ($LASTEXITCODE -ne 0) { throw "strict evaluation failed: $LASTEXITCODE" }
