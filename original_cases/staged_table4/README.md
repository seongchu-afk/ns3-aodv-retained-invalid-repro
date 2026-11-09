# Staged temporal regression: all twelve Table 4 runs

This portable module restores the original staged L/E/E2/P experiment across stock, INVALID-only (`patch`), and no-guard (`unsafe`) implementations. It is separate from the extended temporal regressions and original supplementary Tables S1–S4. It does not replace or alter any published version. It includes source, fixed settings, byte-identical reference traces, and independent entry points for building, running and analyzing all twelve cases.

## Quick start

Python 3 standard library is sufficient for analysis. From this module directory:

```sh
python3 REPRODUCE.py analysis --input /path/to/analysis_data/staged_table4 --work /path/to/work/analysis_check
```

Full simulation needs a Linux C++23 compiler, Python 3, CMake and GNU Make, plus an optimized ns-3.47 build with aodv, wifi, mobility, applications, flow-monitor, olsr, dsdv and dsr. Supply the clean source/build tree explicitly:

```sh
python3 REPRODUCE.py full --ns3 /path/to/ns-3.47 --work /path/to/work/full_check
```

For a split release, the 96 raw CSVs are distributed in `analysis_data/staged_table4/traces/` rather than in the source archive. `--input` accepts either the CSV directory or its parent containing `traces/`. This source-only package always needs the separate `--input` for archive analysis. Full simulation does not require old traces: it checks the small Table4_expected.csv and historical summary. Add `--reference-input /path/to/analysis_data/staged_table4` to request the optional 96-file byte comparison.

`/path/to/ns-3.47` is a user-supplied placeholder, not a project-specific machine dependency. Do not pass an existing work directory containing a prior `build` or `runs` directory. No previous research binary is accepted. To inspect individual stages:

```sh
python3 build.py --ns3 /path/to/ns-3.47 --work /path/to/work/manual
python3 run.py --ns3 /path/to/ns-3.47 --work /path/to/work/manual
python3 analyze.py --input /path/to/work/manual/runs --out /path/to/work/manual/analysis --reference-input /path/to/analysis_data/staged_table4
```

Obtain the official ns-3.47 source archive separately. Its required SHA-256 is `8b3adca956c834ea436b915986ab8fd053e90041acae7426895d595aaa3ccc39`. After checking that hash, extract it and build from its root:

```sh
./ns3 configure --build-profile=optimized --enable-modules=aodv,wifi,mobility,applications,flow-monitor,olsr,dsdv,dsr --disable-examples --disable-tests -- -G "Unix Makefiles"
./ns3 build -j 4
```

The build script expects the normal ns-3.47 `build/include`, `build/lib`, and `cmake-cache/src/aodv` layout. It checks the ns-3 version and original routing/routing-table source identities before compilation. Shared libraries and six unmodified AODV objects are reused from that base. Lifecycle instrumentation, all three routing variants and both observer executables are always compiled again from the supplied scientific sources. The sources never modify the clean ns-3 tree.

## Outputs and expected results

All generated traces, executables, logs, commands and path-bearing build records stay in the specified work directory, conventionally `/path/to/work/`. Do not include that directory in a source release. The portable module's manifest excludes it and Python cache files. When splitting code and raw data into separate archives, regenerate each archive's manifest for its actual contents; the code manifest must not require absent raw data. The analyzer never silently skips missing reference CSVs when a reference directory is requested.

- `cases.json`: exact twelve-case configuration.
- `EVIDENCE_INVENTORY.md`: source/input/trace mapping assembled before the rerun.
- `reference/Table4_expected.csv`: twelve rows transcribed from the staged results.
- `analysis_data/staged_table4/traces/` in the separate analysis-data package: 96 original, unchanged CSVs, eight per run.
- `analysis/Table4_recomputed.csv` and `analysis/ANALYSIS.json` under the work directory: recomputed counts, qualification detail, source-return identities, and optional byte comparisons.
- `analysis/*-strict-return-pairs.csv`: exact trace lines, times, interfaces and TTLs for auditable return pairs.
- `VALIDATION.json`: sanitized local validation summary, not a substitute for rerunning.

Delivery, in stock/patch/unsafe order: L and E are 0/95, 95/95, 95/95; E2 is 0/4, 4/4, 4/4; P is 0/4 in all variants. E fails its intended expiry qualification in all three variants and remains a failed fixture. E-unsafe exhibits one continuous 3.999807767 s cycle without data return. P-unsafe exhibits one continuous 3.118710097 s cycle and four strict source returns. The other ten runs show no active cycle or return. The four E and ten P cycle intervals are adjacent snapshot segments, not independent cycles. P is an artificial, unreachable-destination hazard test, not a delivery-performance comparison.

## Observation rules and limitations

The historical staged analysis already used a complete IPv4/application identity, non-loopback IPv4 interface TX/RX, strictly earlier TX time, and decreased return TTL. It did not use weak IpForward counts. The reused version-2.0.0 strict matcher adds Decimal timestamp comparison, input validation and explicit evidence pairs. These rules reproduce the original return counts here without changing the scientific claim.

A packet identity comprises source and destination IP, IP protocol, IP identification, application flow and sequence. Packet UID is auxiliary, not part of that identity. Interface 0 is excluded. A repeated non-loopback IPv4 interface TX at a node is separately reported and is zero in every case; it is not equivalent to a return. `strict_returned_datagrams` deduplicates identities across returning nodes, preserving the historical metric. The matcher's `any_node_identity_count` counts node-plus-datagram identities and is not generally interchangeable. Both are four for P-unsafe here. The weak source-RX diagnostic retained by the matcher is not used as the Table 4 return result.

Cycles use present, VALID, positive-lifetime routes to 10.1.1.4, exclude self-loops, traverse the finite graph without a depth cutoff and deduplicate cyclic rotations. Durations end at the next snapshot, earliest route expiry or simulation stop. The original staged snapshot policy coalesces instrumented mutation callbacks at a timestamp and does not cover all transient in-handler states. Unlike the extended experiment's policy, it does not stop traversal specifically at destination node 3. Source-byte preservation retains the historical observation policy.

E2's first B invalidation is a natural purge at 18.058192233 s, with no target RERR preceding that invalidation. The same INVALID entry (next hop S, sequence 0) persists through 43 snapshots when the request-time endpoint at 28.509200233 s is included; there are 42 strictly before that endpoint. A later target RERR is transmitted at 22.054192233 s and received by B at 22.054376466 s. It does not replace the already INVALID entry. Thus “no target RERR anywhere in the run” would be inaccurate; the qualification concerns the cause and time of the initial invalidation and the retained entry.

These are twelve fixed regression executions, not independent statistical samples or a proof of universal loop freedom. See PROVENANCE.json, MODIFICATIONS.md and LICENSES/NOTICE.md for identity and licensing.

## Integrated v2.0.1 layout

This module is under `code/original_cases/staged_table4/`. Its separate data root is `analysis_data/staged_table4/`. Prefer the package-level unified REPRODUCE.py commands in `code/README.md`. Paths naming old standalone data layouts in historical provenance describe original locations, not required local directories. No build or execution logs are distributed.
