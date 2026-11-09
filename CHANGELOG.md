# Changelog

## 2.0.1 (2026-11-09)

Correct the original-paper coverage omissions in v2.0.0 by adding the 12 staged Table 4 executions, the original 24 retention-window executions for Figures 2–3, and the failed/corrected wireless VALID-entry guard control. Add Figure 5 negative-chain and original1 request-localization analyses with documented minimal selections from regenerated six-suite traces. Add the new supplementary queue-observer evidence for 31 FIFO evictions and 64 retry-exhaustion drops.

Add a unified analysis/originals/full entry point, separate outputs, read-only input validation, optional exact-raw comparisons, a command-plan option and a complete manuscript coverage index. The queue verifier gains an optional --output directory; its assertions are unchanged. The original scientific C++/CSV bytes and all v2.0.0 baseline test references are preserved. Strict return documentation now explicitly identifies non-loopback IPv4 interface events, not proof of DATA PPDU emission.

These changes repair distribution and workflow coverage, not the protocol intervention or reported sample sizes. The original additional direct queue-observer source and raw trace are still unrecovered. New supporting evidence is labelled separately. Figure 2 evidence distinguishes RERR invalidation in run 1 from expiry-triggered purge in runs 2–3. E remains an unqualified staged fixture; the wireless injection timing correction remains retrospective.

Version DOI: https://doi.org/10.5281/zenodo.24090944. The full 240-execution ensemble rerun has now passed exact record and derived-table checks; its low-level CSV bytes were not exhaustively compared. See VALIDATION.json for completed checks.

## 2.0.0 (2026-11-09; unchanged)

Published at https://doi.org/10.5281/zenodo.23827740 and repository tag v2.0.0, commit f11e814b448baf2d830d5b42d3a63b726b71d181. This existing release is not replaced or relabelled.

The unified originals workflow was validated end-to-end in an isolated source-only copy with a newly extracted and built official base. It passed original S1/S3/S4, staged 96/96 CSV comparisons, retention 120/120, VALID-control 6/6, both five-file derived analyses and new queue 31+64 checks. A final S3 report-only wording correction was rechecked without rerunning simulations. Separate 195-case and 240-execution validation does not imply that the integrated full command itself was run end-to-end.
