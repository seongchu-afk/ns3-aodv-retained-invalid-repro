# Retained INVALID routes in ns-3 AODV: corrective v2.0.1

Version: 2.0.1. Version DOI: https://doi.org/10.5281/zenodo.24090944. Git tag: v2.0.1. Published v2.0.0 and https://doi.org/10.5281/zenodo.23827740 remain unchanged.

The intervention remains the INVALID-only same-next-hop guard against official ns-3.47. The isolated patch, instrumented variants and deliberately unsafe detector control are distinct. This correction adds original-paper reproduction modules omitted from v2.0.0; it does not change scientific C++/CSV bytes, reported sample sizes, or the eight v2.0.0 analysis references.

## Requirements

Tested baseline: Linux x86-64, Python 3.12, GCC 14.2 with C++23. Install the four pinned dependencies from requirements.txt in a fresh virtual environment. Allow several GB for simulations. Upstream ns-3 is not bundled.

Official archive: https://www.nsnam.org/releases/ns-3.47.tar.bz2
SHA-256: 8b3adca956c834ea436b915986ab8fd053e90041acae7426895d595aaa3ccc39
The official AODV routing source must hash to 43b8ff9e5ccd4c737422de1ebb191c1913cdfb33259c1bb2dab6d9720d77c79e.

## Unified commands

From this code directory, use a separate fresh output directory:

```sh
python REPRODUCE.py analysis --input /path/to/analysis_data --output /path/to/results
python REPRODUCE.py smoke --archive /path/to/ns-3.47.tar.bz2 --output /path/to/smoke
python REPRODUCE.py originals --archive /path/to/ns-3.47.tar.bz2 --output /path/to/originals
python REPRODUCE.py full --archive /path/to/ns-3.47.tar.bz2 --output /path/to/full
```

- **analysis** verifies the code/data manifests, reanalyzes the existing 195 temporal/natural/combined executions and 240 ensemble metric records, checks all eight baseline outputs, then analyzes staged Table 4, retention Figures 2–3, the wireless VALID control, Figure 5, original1 localization and the new queue-observer evidence. Inputs and distributed source files are not written. Each module has its own output directory; revision results are under `revision/`.
- **smoke** preserves the bounded v2.0.0 scope: four handler-program executions, one stock/patch ensemble pair, two natural fixtures and three restored-path fixtures, plus 15 synthetic return tests. It does not execute the full original or revision matrix.
- **originals** starts from the official archive, builds a clean base and all original harnesses, then runs S1 handler calls, natural95, six paired environments, the new queue observer, 12 staged executions, 24 retention executions and two VALID-control fixtures. Figure 5 and original1 selections/analyses are regenerated from the resulting six-suite traces.
- **full** runs all 435 revision simulations (195 + 240), their analysis and handler checks, then the complete originals workflow. It requires no archived raw data. To additionally compare generated staged/retention/VALID traces against distributed raw bytes, supply `--reference-input /path/to/analysis_data` to originals or full.

`--jobs N` controls supported parallel builds/runs. `--plan` prints the commands without building, running or writing. Simulation workflows re-extract ns-3 under `experiments/ns-3.47`; previous base/build/run directories are moved to the selected output's `previous_experiments/` directory. Use one workflow per source copy at a time. Outputs must not overlap the input tree. Module-specific entry points remain available; see their READMEs.

## Coverage and evidence limits

See MANUSCRIPT_COVERAGE.md and MANUSCRIPT_COVERAGE.json for all six figures, seven tables and additional narrative examples. Every completed workflow writes COVERAGE_VALIDATION.json, which distinguishes analysis checks from fresh simulation and from reference-only original-table coverage.

The minimal analysis archive includes 975 original scientific CSVs for the 195 revision cases, 240 ensemble metric records, 96 staged CSVs, 120 retention CSVs, six VALID-control CSVs, documented six-suite selections and one new queue-observer CSV. Full historical ensemble and original six-suite low-level traces are not distributed; full/originals can regenerate them. Selected Figure 5 and original1 inputs come from regenerated original six-suite evidence, not recovered historical raw files.

The historical additional S3 direct queue-observer source and raw trace remain unrecovered. The separate new read-only observer and its distributed output reproduce 31 FIFO evictions and 64 retry-exhaustion drops. New supporting evidence is not claimed as historical source recovery.

Strict return detection means a non-loopback IPv4 interface TX followed by RX at the same node, with matching IPv4/application identity, strictly earlier TX time and lower RX TTL. An IPv4 TX trace alone does not establish transmission of a DATA PPDU: Figure 5 includes an IP TX followed by ARP failure without a DATA PPDU at node 7. This terminology clarification changes no predicate or counts. The study does not establish topology-wide loop freedom or general recovery.

Validation claims are scoped in VALIDATION.json. A completed archive analysis is not a completed fresh 240-execution ensemble rerun. All 240 ensemble executions have now been freshly rerun using newly compiled final scientific harnesses against the previously clean official base, with no old run cache. All 240 records (10 scientific quantities plus identifiers/exit status) match, and all three derived tables are byte-identical. The 195-case fresh validation separately reproduced all 975 CSVs. This does not claim a single newly integrated full-command execution or byte comparison of all 240 low-level CSVs.

## Licensing and citation

Code and patches are GPL-2.0-only. Original data and documentation are CC-BY-4.0, not an alternative license for the code. Preserve existing third-party terms. See LICENSES/NOTICE.md, CITATION.cff, CHANGELOG.md and provenance records.

The unified `originals` command has also passed end-to-end from a source-only copy with a newly extracted and built official base and all research code recompiled. Its optional external comparisons matched 96 staged, 120 retention and six VALID-control CSVs. Original S1/S3/S4, Figure 5, original1 and the new queue observer also passed. See `ORIGINALS_VALIDATION.json` and `VALIDATION.json`; the integrated `full` command itself was not executed end-to-end.
