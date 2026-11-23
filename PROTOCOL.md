# Reconstruction and evaluation protocol

## 1. Authorized inputs

The experimental unit is a pair of distinct source roles A and B. An authorized reconstruction manifest needs the cohort, pair ID, original recording IDs, exact source file IDs and byte hashes, source-to-role assignment, approved crop start samples and normalized anchor hashes. For every scene it additionally needs the recipe ID, three-bit condition, onset samples, duration samples, nominal gain in dB for each role and reference WAV hash. QA mappings need the setting, pair, recipe, condition, factor, displayed order, semantic role and exact question identity. Reuse the approved values and preserve leading zeros in condition IDs. These are schema requirements. No real manifest rows are bundled.

P8 uses evaluation foreground clips from the DESED synthetic soundbank. P9 uses the FSD50K evaluation split. Check the exact archive and upstream license row, then verify each actual source file's SHA-256 before decoding. Distinguish dataset clip identifiers from the original Freesound recording identifiers used for dependence. Resolve aliases with the archived recording mapping.

## 2. Historical sound rendering

Decode with python-soundfile to float32. If multichannel, reduce channels by an arithmetic mean over channels using float32 arithmetic. Require 44,100 Hz and use no resampling. Use zero-based, half-open sample windows. Map seconds to samples by rounding seconds multiplied by 44,100 using Python's round behavior. Normalization and mixing use float64 sample arrays. Preserve embedded background and competing sounds in the source recording.

| Cohort recipe | Early slot (s) | Late slot (s) | Short crop (s) | Long crop (s) | Nominal contrast (dB) |
| --- | ---: | ---: | ---: | ---: | ---: |
| P8 R0 | 2.0 | 7.0 | 0.50 | 1.00 | 12 |
| P8 R1 | 1.0 | 6.0 | 0.40 | 0.90 | 10 |
| P9 C0 | 2.0 | 7.0 | 0.50 | 1.00 | 12 |
| P9 C1 | 1.5 | 6.5 | 0.60 | 1.10 | 11 |

Historical gain measurement uses the P3 full-source activity detector. Form RMS frames of 20 ms at a 5 ms hop, adding a final frame ending at the file end if needed. Use a single frame for a shorter nonempty input. Take 20 log10 of sqrt(mean(x squared) + 1e-20), using the legacy RMS log floor. Mark frames above or equal to the largest of −50 dBFS, peak frame level minus 30 dB, and the 20th percentile plus 8 dB. The following two cropping policies deliberately differ.

- **P8** Read the approved anchor time. The rendered long prefix begins at round(start seconds × sample rate). For measuring reference active RMS, place the right crop bound at round((start seconds + recipe long seconds) × sample rate), following the historical measurement expression. Use active frames with centers inside that window and the union of their sample spans clipped to the window. When selected frames yield no active samples, the legacy RMS helper uses the full crop. For each recipe multiply the raw long prefix by 10 raised to ((−27 − measured active RMS in dBFS)/20). Derive the short from the start of that normalized long crop. P8's separate raw canonical anchor check uses the 1 s excerpt, even for R1.
- **P9** Use the approved integer anchor start and the 1.10 s canonical window. Form a sample mask from the union of active frames over the whole source, then crop both the samples and mask. Derive the gain for −27 dBFS from active samples in that full anchor and reuse it for both recipes. The approved-input checks require active samples in the canonical anchor and in the four configured length prefixes. Verify the historical worst loud-prefix peak guard (at most −1 dBFS). Take all recipe crops as prefixes of the one normalized anchor, with no short-crop renormalization.

Place the two normalized prefixes in a zero-filled, 10 s mono buffer in role A then role B order. Condition bits are Position, Duration, Level. A bit of 0 selects role A and a bit of 1 selects role B for earlier, longer or louder respectively. Apply +contrast/2 dB to the louder role and −contrast/2 dB to the other role, using the linear multiplier 10 raised to (gain/20). No additional background, fades, overlap or peak normalization is part of these recipes. Check maximum absolute mix amplitude before encoding.

Encode PCM_32 WAV via the pinned historical python-soundfile/libsndfile path. P8 casts the completed mix to float32 immediately before encoding. P9 passes the completed float64 mix. Receiver-side recovery should check sample rate, channels, length and signed decoded PCM32 samples against the authorized reference. A source file or WAV container SHA-256 applies to file bytes. Raw or normalized source-sample digest fields use little-endian float64 array bytes and the manifest's stated crop. Compare the right kind of digest. Differences in encoder versions or headers can change byte hashes even when decoded PCM agrees.

The included in-memory mixer starts with approved normalized arrays or a caller-supplied verified RMS measurement. It illustrates prefixing, exact placement, gain, dtype staging and sample hashing. Obtaining or measuring approved anchors, validating real source hashes, and PCM encoding with the historical library remain external. The synthetic test performs no WAV writes and supplies no evidence of perceived event timing, duration, loudness or factor independence.

## 3. Questions and responses

For each pair, recipe and condition, ask Position, Duration and Level in AB and BA. Role A/B identifies the source. Display A/B identifies the first/second option and changes with order. Semantic GT is fixed for both orderings. The illustrative prompts in the code show the mapping. Exact historical prompt serialization requires the archived model-specific wrappers and prompt records.

The sound-name parser first tries an exact normalized name on the first nonempty line, allowing the historical answer prefixes. Failing that, a unique whole-name mention in the normalized response is valid. The strict letter-choice parser accepts one ASCII A/B letter with optional whitespace and a terminal period or exclamation point. Use the matching displayed role to recover the semantic answer. Both parsers take the response and displayed options and do not take GT.

The bundled implementations require two sound names that remain distinct and nonempty after normalization, and an AB or BA permutation of source roles. Raw input is text or `None`. Treat a false validity flag as a `None` answer when passing parser output to the metric helpers. Metric rows use GT `A` or `B`, with `None` reserved for an invalid answer. The IR counter checks whether GT polarity changes as required by the intervention type. The caller supplies matched edge rows and is responsible for their completeness, provenance and deduplication.

## 4. Scoring and uncertainty

Endpoint accuracy uses all endpoints, including invalid responses in its denominator. Validity counts parsable endpoints. Both-valid coverage uses all AB/BA pairs as denominator. Conditional semantic agreement uses only both-valid pairs as denominator and counts identical source choices. An empty both-valid denominator is unestimable.

A one-bit toggle connects two scenes for the same pair and recipe. Each physical edge is scored for every question and both matched display orders. Joint correctness requires both semantic endpoints to match their respective GT. The 3 × 3 IR matrix has question rows and intervention columns. Target cells are on the diagonal; off-target cells are elsewhere. Count both valid, semantic flip and invariance separately. Strict target correctness requires the four responses across the two scenes and orders to be correct.

For historical statistical replay, build components by connecting source pairs that share original recording IDs. Sort the frozen component labels within each setting. Resample as many components as in that setting with replacement, maintaining all within-component rows. Compute a ratio of summed numerators to summed denominators per draw. Use identical draws across the two interfaces when estimating paired contrasts. For pointwise 95% intervals take linear 2.5 and 97.5 percentiles of finite replicates. Main Table 6 uses seed 20261112 and Figures 2/4 use seed 20260906, with 10,000 draws each and NumPy PCG64. Appendix A has a distinct historical procedure with 1,000 within-GT permutations followed by its 10,000 component draws and seed 20261102. A generic paired bootstrap alone cannot reproduce that separate permutation workflow. These intervals are exploratory and dependence-aware.

The interval SVG takes point estimates and CIs supplied by the caller. Use short textual labels suitable for the plot's label column. The target-edge plot name is “Target-edge joint correctness.” Historical Table/Appendix assembly and the exact manuscript graphical assets require separately controlled tooling and inputs.
