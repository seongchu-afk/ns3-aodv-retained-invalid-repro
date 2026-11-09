# Manuscript coverage: v2.0.1

This index covers numerical results, event evidence and mechanism checks for all six manuscript figures and seven tables, plus two narrative examples. It does not promise automatic redrawing of publication figures or reproduction of manuscript typography. Paper PDF/LaTeX and graphic-layout sources are not required components of this minimal package.

Version: 2.0.1. Version DOI: https://doi.org/10.5281/zenodo.24090944. Published v2.0.0 remains unchanged at https://doi.org/10.5281/zenodo.23827740.

Paths below are relative to `code/`. Data for added modules are separately located at `analysis_data/<module>/` in the archive. `REPRODUCE.py analysis` checks archived data; `originals` rebuilds/runs original-paper experiments; `full` also reruns all 435 revision simulations. The original experiments are distinct from the revision sample counts.

## Figures

- **Figure 1: retained INVALID mechanism**: `original_tables/reference/Table_S3_natural95_timeline.csv`; module `original_tables`. Warm-up 40/40 for both; main task stock 0/95, INVALID-only 95/95. Minimum numerical workflow: originals.
- **Figure 2: retention windows**: `original_cases/retention_figures/expected/F2_timeline.csv`; module `retention_figures`. Six stock lifecycle histories; run 1 invalidates by RERR, runs 2 and 3 by expiry-triggered purge. Minimum numerical workflow: analysis.
- **Figure 3: retention matrix**: `original_cases/retention_figures/expected/F3_matrix.csv`; module `retention_figures`. Four conditions × three run indices × two implementations = 24 original executions, not the 78 sensitivity executions. Minimum numerical workflow: analysis.
- **Figure 4: original six environments**: `original_tables/reference/Table_S4_six_environment_metrics.csv`; module `original_tables`. Packet-set gain/loss/net and AODV PPDU-duration summaries. Complete original six-suite traces regenerate via originals. Minimum numerical workflow: originals.
- **Figure 5: RWP3 negative chain**: `original_cases/negative_chain/reference/negative_summary.json`; module `negative_chain`. 79 stock-only flow-2 packets; 75 node-7 ARP drops, four remaining identities, sequence 208 and discrete neighbor-state samples. Documented selections from regenerated traces. Minimum numerical workflow: analysis.
- **Figure 6: revised paired distributions**: `reference/ensemble_summary.csv`; module `revision`. 120 pairs from 240 recorded per-run measurements. Full mode regenerates the underlying traces. Minimum numerical workflow: analysis.

## Tables

- **Table 1: configuration**: `original_tables/reference/Table_S2_simulation_parameters.csv`; module `configuration`. Fixed radio, timer, traffic and RNG settings; reference/configuration evidence, not a simulated outcome. Minimum numerical workflow: reference.
- **Table 2: natural95 timeline**: `original_tables/reference/Table_S3_natural95_timeline.csv`; module `original_tables`. Historical application/lifecycle/RREQ sources plus new queue supporting evidence. Historical additional direct queue source and raw trace remain unrecovered. Minimum numerical workflow: originals.
- **Table 3: handler cases**: `original_tables/reference/Table_S1_handler_99_cases.csv`; module `original_tables`. 99 inputs per implementation, 198 calls. 17 changed outcomes, all INVALID with same next hop. Minimum numerical workflow: originals.
- **Table 4: original staged temporal**: `original_cases/staged_table4/reference/Table4_expected.csv`; module `staged_table4`. Twelve L/E/E2/P executions across three variants. P/no-guard has four strict returns; E stays unqualified. Not the 108-case extended suite. Minimum numerical workflow: analysis.
- **Table 5: sensitivity**: `reference/counterexample_summary.csv`; module `revision`. 78 natural sensitivity executions; the six retention=5 s cases remain negative controls. Minimum numerical workflow: analysis.
- **Table 6: original six environments**: `original_tables/reference/Table_S4_six_environment_metrics.csv`; module `original_tables`. 5985 application attempts per execution; AODV cost is summed PPDU durations in [60,180) s, not channel busy time. Minimum numerical workflow: originals.
- **Table 7: revised paired results**: `reference/paired_runs.csv`; module `revision`. Six environments ×20 whole-run pairs; descriptive 95% t intervals use df=19. Minimum numerical workflow: analysis.

## Additional narrative evidence

- **Narrative: wireless VALID control**: `original_cases/valid_guard_control/expected/summary.json`; module `valid_guard_control`. One qualified corrected 18.05 s wireless injection and its preceding unqualified 18 s fixture, not two independent successful controls. Minimum numerical workflow: analysis.
- **Narrative: original1 localization**: `original_cases/original1_localization/reference/localization_summary.json`; module `original1_localization`. 5854→5941 overall; 1099→1187 target flow; 7→99 among the same 100 packets generated in [106,116) s and observed through 210 s. Minimum numerical workflow: analysis.

## Validation and provenance boundaries

Archive analysis validates the added datasets and revision measurements. Original S1/S3/S4 references are retained in code; their full numerical regeneration requires originals/full because complete original handler/natural95/six logs are not bundled. Table 2 additionally has archived new queue evidence under `analysis_data/original_queue_observer/`, verified separately even in analysis mode. Table 1 is a configuration check, not a simulation output.

Staged, retention and VALID-control data preserve original scientific CSV bytes. Figure 5 and original1 data are documented selections from freshly regenerated original six-suite traces. New queue data are supporting evidence, not recovered historical raw evidence. The historical additional queue-observer source and direct trace remain unrecovered.

The 195 revision executions comprise 108 temporal, 78 natural sensitivity and nine combined cases. Their snapshot policy differs from the original staged Table 4 policy. Strict-return TX/RX denotes non-loopback IPv4 interface events, not necessarily actual DATA PPDU emission.

Analysis, bounded rerun and fresh full simulation are separate claims. A separate fresh full 240-execution ensemble rerun has passed exact per-run record and derived-table checks; the 195-case fresh validation separately reproduced all 975 scientific CSVs. These are separate validated stages, not an assertion that the integrated full command was run end-to-end. It does not claim topology-wide loop freedom. COVERAGE_VALIDATION.json records the precise executed workflow and checks for each item.

The coverage index independently passed a second archive-analysis review. The unified `originals` workflow also passed end-to-end from an isolated source-only copy with a freshly extracted and built official base; `ORIGINALS_VALIDATION.json` records the original-paper checks. `ARCHIVE_ANALYSIS_VALIDATION.json` records the separately executed archived-evidence checks. The current-workflow report is written to the selected output as `COVERAGE_VALIDATION.json`.
