# Acoustic-relation evaluation protocol

Code and protocol companion for *Acoustic-Relation Reliability and Interface Sensitivity in Audio-Language Models*. The study pairs two sound sources and tests whether answers track changes to the queried acoustic relation and remain correct across changes to other factors or answer-option order. The included example uses invented names and hand-authored numerical arrays and runs on the CPU with Python 3.10 or later.

## Quick start

From this directory run the synthetic smoke test.

~~~text
python -B smoke.py
~~~

Expected summary (timing varies).

~~~text
Ran 4 tests in ...s

OK
~~~

For a local environment with the optional historical PCG64 bootstrap generator, create a virtual environment and install the pinned numerical dependency.

~~~text
python -m venv .venv
~~~

In PowerShell use the interpreter at the following relative path.

~~~powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements-bootstrap.txt
& .\.venv\Scripts\python.exe -B smoke.py
~~~

On POSIX systems use .venv/bin/python for both commands. The synthetic test suite itself installs no packages. The optional installation accesses the machine's configured package index.

With NumPy installed, call the optional generator from the virtual environment.

~~~powershell
& .\.venv\Scripts\python.exe -B -c "from p79_protocol.stats import historical_draws; print(historical_draws(2, 20261112).shape)"
~~~

~~~sh
.venv/bin/python -B -c 'from p79_protocol.stats import historical_draws; print(historical_draws(2, 20261112).shape)'
~~~

Expected output is `(10000, 2)`. The four default smoke tests exercise the paired-rate and percentile functions with explicit synthetic draws.

## Upstream datasets and required permissions

- [DESED_synthetic v2.2, official distribution](https://zenodo.org/records/4560893). For P8 obtain DESED_synth_soundbank.tar.gz and use the evaluation foreground directory of that soundbank. Consult the accompanying license_eval.tsv for original credits and clip-specific terms. Foreground short and foreground on/off directories are distinct ingredients.
- [FSD50K v1.0, official distribution](https://zenodo.org/records/4060432). For P9 obtain both FSD50K.eval_audio.z01 and FSD50K.eval_audio.zip, then follow the official split-archive extraction directions. Obtain FSD50K.metadata.zip and FSD50K.doc.zip for source provenance and license terms. FSD50K.ground_truth.zip supplies the original dataset labels, which are separate from the experiment's relation labels. Use the evaluation split and cross-check original Freesound IDs against eval_clips_info_FSD50K.json and LICENSE-DATASET. Source recordings have clip-specific licenses in addition to the terms of the distributed metadata.

Some upstream clips have attribution, use or redistribution restrictions. Keep source credits and the applicable terms when obtaining data. The original clip IDs, approved anchor manifest and per-scene recipes require separate permission and are not included in this public repository. See [rights and notices](RIGHTS_AND_NOTICES.md).

## Reproduction scope

With this directory alone, run eight synthetic factorial conditions, generate 48 synthetic QA keys, exercise both parser behaviors, count endpoint, order, and edge metrics, test shared component resampling, and generate an interval SVG in memory.

With separately authorized inputs, the utilities support the following steps.

| Area | Executable in this package | Additional historical steps |
| --- | --- | --- |
| Audio scenes | Normalize using a caller-supplied RMS measurement, crop and place arrays, apply nominal gains, and hash sample values | Source selection, measured active-RMS extraction, file decoding, PCM WAV encoding, and reference verification |
| Questions | Generate factorial QA keys, construct the semantic GT/AB–BA mapping, and make illustrative prompts | Model-specific prompt templates, wrapper serialization, and inference |
| Parsing and evaluation | Apply the independent sound-name and letter-choice parser implementations, then count endpoint, AB/BA, and matched-edge outcomes | Provenance joins and validation against the controlled responses and frozen manifests |
| Bootstrap | Generate PCG64 draw indices with optional NumPy, resample ordered component counts in pairs, and compute percentile intervals | Derive components from real recording IDs, assemble historical tables, and perform the separate Appendix A permutation workflow |
| Figures | Produce an interval SVG from supplied estimates and interval bounds | Assemble manuscript figures, including heatmaps, from controlled result inputs and historical plotting code |

[The reconstruction protocol](PROTOCOL.md) specifies the historical method and input contracts. When using `parse()` with the metric helpers, map an invalid parse to `None` using its validity flag. For example, strict letter-choice reply `A.` in a `BA` display maps to semantic source `B`; an explanation after the letter is invalid.

Exact reconstruction of the 672 evaluation mixtures requires the approved source IDs, source-specific recipes and anchors, original recordings, and the historical decoder and encoder. Exact rescoring of the 40,320 responses and reproduction of the reported numerical tables and figures require controlled responses, manifests, and further tooling. For four models, parts of the effective generation and stopping configuration remain unresolved in the archived evidence.

## Attribution and license

- Software author and copyright holder: Jeongin Ju
- Manuscript authors: Jeongin Ju and Sungbin Im
- Affiliation: School of Electronic Engineering, Soongsil University
- License: [MIT](LICENSE)

MIT applies only to copyright-holder-owned code, authored documentation, and the independently created synthetic fixture. Original audio, response dumps, actual source IDs and source-specific recipe manifests, model weights, and third-party materials remain outside this package. Separately obtained third-party materials retain their own licenses.

The code-and-protocol package is publicly available at
https://github.com/jji1023/acoustic-relation-evaluation.

The audited P85 code snapshot is available at
[commit 3db5ebb](https://github.com/jji1023/acoustic-relation-evaluation/tree/3db5ebb53e88cd23f10ca0c0a6756cee71e15fbc).

[Rights and notices](RIGHTS_AND_NOTICES.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

