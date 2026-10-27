# PS-20261025-20: portable invocation first smoke

2026-10-26, Remote-PS-C. Base code `74b16db6afe4a76def817e9f643a156b7b8389c0`. Quality remains REJECTED; delivery is BLOCKED.

The local full archive was 198734997 bytes, SHA-256 `a35ebffce09edb0e005bbe6ba6bae3050b0e3087df5bf0f63c1f23d6aed9cb71`. All 466 internal files were verified. A fresh detached shared Git checkout and separate venv with copied locked dependency libraries were created under `D:/fpga/receive-check/PS-20261025-20-hubert-fargan-v1`. This was a local archive test, not a GitHub download. No fresh pip installation is claimed.

The relative-path documented command loaded the models and wrote audio, then exited with error:

```text
ValueError: 'bundle\\fixed_male4.wav' is not in the subpath of 'D:\\fpga\\receive-check\\PS-20261025-20-hubert-fargan-v1\\code'
```

`infer` used `output.relative_to(ROOT)` while a CLI-supplied output could remain relative. The fix resolves the three CLI paths once at the entry point. It does not alter any inference or training math. The corrected command must be retested from a new clean checkout before reporting success. The old package is superseded and will not be published.

An authenticated GitHub repository read returned `private=false`. `ARTIFACTS.md:18` and `交接/远端模型交付与接收.md:39` require a private repository Release. No Release creation/upload was attempted and visibility/rules were not changed. The user has been asked to provide a permitted private destination or explicitly authorize public release. The code and failure evidence can continue to be submitted normally. No quality gate, locked data, playback or hardware operation is affected.
