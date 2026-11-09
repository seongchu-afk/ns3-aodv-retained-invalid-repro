# Wireless VALID-entry guard negative control

This portable module preserves both the initial unqualified wireless fixture and its later timing correction. It reproduces an actual RREQ transmission, reception, and VALID-entry guard return in ns-3.47. Direct invocation of a routing handler is not a substitute for this test. This module is included in version 2.0.1; it changes no prior published release or manuscript.

## Reproduce

Analysis needs only Python 3 and the standard library. Pass the separately distributed scientific trace directory (or its parent containing `traces/`):

```sh
python3 REPRODUCE.py analysis --input /path/to/analysis_data/valid_guard_control --work /path/to/work/analysis
```

Full simulation does not require original raw traces. It freshly compiles the patch routing module and both harnesses, executes the two fixed cases, then checks the small expected summary:

```sh
python3 REPRODUCE.py full --ns3 /path/to/ns-3.47 --work /path/to/work/full
```

Optionally append `--reference-input /path/to/analysis_data/valid_guard_control` to compare the six required qualification traces byte for byte with the originals. The source-only distribution has no `raw/` directory. Always supply the separate `--input` for archive analysis. Use a fresh work directory for each invocation. Generated commands, binaries, logs, traces, and path-bearing execution records stay in the specified work directory, conventionally `/path/to/work/`, and are not release files.

Individual stages and analyzer checks are available:

```sh
python3 build.py --ns3 /path/to/ns-3.47 --work /path/to/work/manual
python3 run.py --ns3 /path/to/ns-3.47 --work /path/to/work/manual
python3 analyze.py --input /path/to/work/manual/runs --out /path/to/work/manual/analysis
python3 test_analysis.py --input /path/to/analysis_data/valid_guard_control
```

## Clean ns-3 base

Use the official ns-3.47 source archive, whose SHA-256 is `8b3adca956c834ea436b915986ab8fd053e90041acae7426895d595aaa3ccc39`. Obtain it separately from https://www.nsnam.org/releases/ns-3-47/ and verify the hash. The following command is run from the extracted ns-3.47 root:

```sh
./ns3 configure --build-profile=optimized --enable-modules=aodv,wifi,mobility,applications,flow-monitor,olsr,dsdv,dsr --disable-examples --disable-tests -- -G "Unix Makefiles"
./ns3 build -j 4
```

A Linux C++23 compiler, Python 3, CMake, and GNU Make are required. The module expects normal `build/include`, `build/lib`, and `cmake-cache/src/aodv` directories. It verifies the version and the upstream routing/routing-table source hashes. Non-AODV shared libraries and seven unmodified AODV objects are reused from this clean base. The routing implementation and both observer executables are always freshly compiled. The base tree is never modified and no old research binary is accepted. The local validation used GCC 14.2.0. All 26 scientific outputs from this one execution per case matched their historical originals; this broader byte comparison is retained only in private validation. The public raw-data whitelist contains only the six traces required for the qualification.

## Results and qualification

- Initial injection at 18 s: S's request PPDU begins at 18.00005 s for 150,000 ns. The request interval is [18.00005, 18.00020) s. B starts a 798,000 ns DATA PPDU at the same instant, spanning [18.00005, 18.000848) s. B has no physical RREQ reception and no handler outcome for request 9001. This is an unqualified test of the guard, preserved as a failure rather than counted as successful negative evidence.
- Corrected injection at 18.05 s: the PPDU begins at 18.05005 s without overlapping B transmission. B receives it at 18.050200233 s and returns through `loop_guard_next_hop_equals_sender`. Its route flag is 0 (VALID), next hop and previous sender are both 10.1.1.1, and remaining lifetime is 2.949799767 s. B sends no RREP in [18.05, 18.06) and never forwards this request.

The original harnesses differ only in the injection scheduling literal, 18 versus 18.05 seconds. Identical comment-only notices were added to both so this remains the sole difference in the distributed files. The corrected timing followed the failed fixture. This is a retrospective qualification correction, not a preregistered experiment. There is one qualified fixed wireless regression and its preceding failed fixture, not two independent statistical samples and not a proof of universal loop freedom.

The required input whitelist is `valid_negative_patch-{reason,control-events,airtime}.csv` and `valid_negative_shifted-{reason,control-events,airtime}.csv`. Missing any required file fails analysis. Extra files are not used.

The analyzer uses physical interface TX/RX, request origin/destination/ID, packet identity, exact decimal PPDU overlap, route state at the handler, and the no-reply window. Its small expected result includes the concrete timing and route fields, not just a Boolean pass. It rejects missing traces, missing radio reception, a different request, INVALID/expired routes, wrong sender predicates, a missing collision record, and an unexpected B reply. Request UIDs are supplemental correlation within each run, not cross-run identity.

## Package contents and provenance

- `sources/`: original scientific harnesses and patched routing implementation, with dated comment-only notices. Existing upstream notices are retained.
- `cases.json`, `configuration.json`, `mobility/negative.csv`: fixed configuration and unchanged mobility input.
- `expected/summary.json`: small expected result, readable without raw traces.
- `PROVENANCE.json`, `MODIFICATIONS.md`: original hashes, actual changes, and chronology.
- `analysis_data/valid_guard_control/traces/` in the separate data package: six original scientific CSV files, byte unchanged: reason, control-events, and airtime for each case. FlowMonitor XML, application/flow summaries, empty OLSR files, and other general observer byproducts are not distributed. The source can regenerate them; they are not inputs to this qualification analyzer.
- `MANIFEST.json` and `SHA256SUMS`: source-distribution inventory, excluding `raw/`, `/path/to/work/`, and Python caches. The separate raw manifest covers the data directory. The integration has placed the unchanged traces in `analysis_data/valid_guard_control`.
- `VALIDATION.json`: sanitized local checks. It records a fresh build and one execution per case, not a substitute for reproduction.

Source code is GPL-2.0-only. Original data and documentation are CC-BY-4.0. See `LICENSES/NOTICE.md` for scope and attribution. Keep private build artifacts out of both source and data releases.

## Integrated v2.0.1 layout

This module is under `code/original_cases/valid_guard_control/`. Its separate data root is `analysis_data/valid_guard_control/`. Prefer the package-level unified REPRODUCE.py commands in `code/README.md`. Paths naming old standalone data layouts in historical provenance describe original locations, not required local directories. No build or execution logs are distributed.
