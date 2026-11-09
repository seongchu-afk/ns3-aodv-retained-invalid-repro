# Retention-window evidence for Figures 2 and 3

This v2.0.1 module restores the **24-run retention-window experiment**: retained, after_delete, cold, and second (five-node motif), each with RNG run indices 1–3 and stock/INVALID-only implementations. It is distinct from the 78-run sensitivity study. It does not replace that study, the natural 95-packet task, or any previously published tag. These retention sources and traces were missing from the published version 2.0.0 package; this module does not claim they were in that release.

## Reproduce

Requirements: Linux, Python 3.11.8 or newer, a C++23-capable GCC compiler (validated with GCC 14), CMake, the normal ns-3.47 build prerequisites, and the official ns-3.47 source archive. No third-party Python packages are needed for compilation, running or analysis. Research binaries are never supplied.

Use a writable work directory **outside this module**. From this module directory:

```sh
sha256sum -c CODE_SHA256SUMS
python3 build.py --archive /path/to/ns-3.47.tar.bz2 --work ../retention-work --jobs 4
python3 run.py --work ../retention-work
python3 analyze.py --input ../retention-work --out ../retention-analysis --check-expected
```

The official archive SHA-256 must be:

`8b3adca956c834ea436b915986ab8fd053e90041acae7426895d595aaa3ccc39`

Obtain the archive through the [official ns-3.47 release page](https://www.nsnam.org/releases/ns-3-47/). The build verifies its exact hash before extracting, then builds the optimized base with aodv,wifi,mobility,applications,flow-monitor,olsr,dsdv,dsr enabled. If those pristine optimized base libraries already exist, the tested alternate command is:

```sh
python3 build.py --ns3 /path/to/clean/ns-3.47 --work ../retention-work
```

Only **non-AODV upstream shared libraries** are reused in this route. All eight AODV translation units for each implementation, including helper, packet, cache, neighbor, queue, table and protocol code, are newly compiled (seven common objects, plus each of the two protocol variants); the observer is newly compiled. Every AODV `.cc` and `.h` in the supplied base must match the pinned hashes. The official headers suffice: this experiment does not use the later fixtures' `DiagnosticAccess` friend declarations. No later fixture header is silently substituted.

The recorded validation used the `--ns3` route against a base already built from that official archive. The `--archive` bootstrap route is provided for clean reproduction but was not rebuilt a second time specifically for this module. Logs, binaries and machine-specific command records are generated only in the chosen external work directory.

## Separate code and original data

The code distribution contains the files in `CODE_FILE_LIST.txt`, verified by `CODE_SHA256SUMS`, plus the generated `MANIFEST.json` for the integrated split package. It contains sources, configuration, derived expected tables and source/trace identities, but no original run CSVs. A fresh build/run/analyze needs only those code files and the pinned official ns-3.47 base. It does not need any old research directory or downloaded raw evidence.

The separately distributed original data belongs at `analysis_data/retention_figures/`, with 120 CSV files under `runs/`. Its own `FILE_LIST.txt` and `SHA256SUMS` inventory the data payload.

`--input` accepts either a data root containing `runs/` or a directory containing the CSV files directly. `--runs` remains a compatibility alias. `--reference-input` is optional and adds direct byte-for-byte comparison with separately installed original CSVs. Even without that option, all 120 new trace hashes are checked against pinned original identities in `PROVENANCE.json`, and all derived references and state/prefix/schedule checks remain active.

For data-only verification, no compiler or simulator is required:

```sh
python3 analyze.py --input /path/to/analysis_data/retention_figures --out ../retention-archived-analysis --check-expected
```

To compare a fresh rerun directly with separately downloaded original bytes:

```sh
python3 analyze.py --input ../retention-work --reference-input /path/to/analysis_data/retention_figures --out ../retention-compared --check-expected
```

The runner executes exactly 24 jobs. Existing runs are not overwritten and failed executions are not automatically retried or retimed. The analyzer exits unsuccessfully with `--check-expected` if any expected metric, necessary trace, paired prefix, state qualification or four-packet schedule fails to match.

## Fixed experiment and interpretation

`config/matrix.json` freezes every job, main-task time, RNG seed/run, assigned stream starts, ARP timeout, diagnostic mode, 512-byte packet size and 0.1-second interval. The source fixes the remaining radio, routing and topology setup. Four explicit main packets are offered at mainAt + 0, 0.1, 0.2, 0.3 s; simulation stops at 60 s. Each row pair is a whole-run comparison, not four independent replications.

| Condition | Runs | Stock delivered / 4 | INVALID-only delivered / 4 | Observed B state at request |
|---|---|---|---|---|
| retained | 1, 2, 3 | 0, 0, 0 | 4, 4, 4 | INVALID; old next hop is requester |
| after_delete | 1, 2, 3 | 4, 3, 3 | 4, 3, 3 | ABSENT after observed purge |
| cold | 1, 2, 3 | 4, 4, 4 | 4, 4, 4 | ABSENT; no prior destination lifecycle |
| second | 1, 2, 3 | 0, 0, 0 | 4, 4, 4 | INVALID; old next hop is requester |

All 24 runs accept all four main packets, pass state/schedule qualifications and retain all zero or shared-loss outcomes. All 12 stock/patch pairs have identical application and control-event prefixes before the main task. The six successful INVALID-only retention-motif runs deliver packet 0 after 14.531029–43.913126 ms. This range does not describe the cold-start or post-deletion cases. Zero delivery through 60 s is right-censored observation, not proof of permanent unreachability or universal loop freedom.

## Figure and evidence crosswalk

- **Figure 2**: `expected/F2_timeline.csv` contains six stock histories: retained and after_delete, separately, for each run index. These are two request-timing conditions, not stock-versus-patch bars. It includes actual invalidation action, observed purge-deletion time, task start and first B lookup. Run 3's stock deletion differs between conditions: 27.982192233 s (retained) and 27.069192233 s (after_delete). Keep both observed times.
- **Figure 3**: `expected/F3_matrix.csv` contains the 12 paired rows, 24 whole-run outcomes. `expected/matrix.csv` preserves every original analysis field, including 1 s/5 s/final delivery, request counts and airtime.
- **Timing range**: `expected/diagnostic_first_packet.csv` records all six eligible packet-0 timing values, without filtering the minimum or maximum.
- **Qualification**: `expected/qualifications.csv` records first B lookup, actual state, old next hop, remaining lifetime, invalidation/deletion and exact four-packet checks. `expected/paired_prefixes.csv` records all 12 prefix checks.
- **Original raw evidence**: `analysis_data/retention_figures/runs/` in the separate data distribution holds five unmodified CSVs per execution, 120 files total: application events, request-branch reasons, route lifecycle, control events and PPDU airtime. Those are all inputs read by the original summary and the added figure/qualification checks. Other diagnostic CSVs, XML, binary files and runtime logs are not necessary to reproduce these Figures 2/3 claims and are not distributed here.
- **Original analysis**: `expected/SUMMARY.json` and `expected/matrix.csv` are copied unchanged from the original experiment. The new analyzer preserves its metric expressions and adds explicit qualification, prefix, figure-data and exact-identity tests. Control airtime includes the actual HELLO label; discovery airtime excludes HELLO. These sums are PPDU transmission durations across nodes, not channel busy time.
- **Reproduction result**: `expected/REPRODUCED.json` records fresh local validation: all 24 executions succeeded; all 120 necessary CSVs, the complete original summary and the original matrix reproduced exactly. It is a summary without machine paths or runtime logs.

**Text precision:** the traces do not support describing all three invalidations as route-error invalidations. Run 1 is `rerr_after_invalidate`; runs 2 and 3 are `purge_after_invalidate`. A faithful description is: “the entry at B becomes INVALID at about 12 s, through RERR processing in run 1 and expiry during purge in runs 2 and 3.” The module preserves these measured actions rather than editing the evidence to fit prose.

## Provenance and licensing

`PROVENANCE.json` records the original and distributed source hashes, fixed inputs, exact raw CSV identities and original supporting-script hashes. `MODIFICATIONS.md` explains the only changes to the four scientific sources: dated comment notices. Source bytes after each notice are unchanged. Upstream copyright and author notices remain intact.

Code is GPL-2.0-only. Original simulation inputs, measurements, result tables and explanatory documentation are CC BY 4.0. See `LICENSE`, `LICENSES/NOTICE.md` and the license texts/notices. `CODE_SHA256SUMS` and `CODE_FILE_LIST.txt` cover the code distribution. The separate data root has its own `SHA256SUMS` and `FILE_LIST.txt`. No prior release, manuscript or published tag is modified by this module.

## Integrated v2.0.1 layout

This module is under `code/original_cases/retention_figures/`. Its separate data root is `analysis_data/retention_figures/`. Prefer the package-level unified REPRODUCE.py commands in `code/README.md`. Paths naming old standalone data layouts in historical provenance describe original locations, not required local directories. No build or execution logs are distributed.
