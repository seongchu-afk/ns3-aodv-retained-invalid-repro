# Retained INVALID routes in ns-3 AODV: v2 reproduction

Version: 2.0.0. Versioned archive: https://doi.org/10.5281/zenodo.23827740 . See CITATION.cff and LICENSES/NOTICE.md for citation, attribution and the separate code/data license scopes.

This package covers the INVALID-only same-next-hop guard intervention against official ns-3.47. The executable patch is in patches/ns-3.47-invalid-only.patch. The instrumented stock/patch sources and intentionally unsafe no-guard detector control are separate research harnesses. No other proposed protocol repair is included.

## Requirements and source identity

Tested configuration: Linux x86-64, Python 3.12, GCC 14.2 with C++23, and the four exact versions in requirements.txt. Use a fresh virtual environment: `python3 -m venv .venv`, activate it, then `python -m pip install -r requirements.txt`. Allow several GB of working storage. The official upstream source archive is not duplicated in this distribution.

Download ns-3.47.tar.bz2 from https://www.nsnam.org/releases/ns-3.47.tar.bz2 . Required SHA-256: 8b3adca956c834ea436b915986ab8fd053e90041acae7426895d595aaa3ccc39. The builder verifies both this archive and the unmodified AODV routing source before compiling. The source hash must be 43b8ff9e5ccd4c737422de1ebb191c1913cdfb33259c1bb2dab6d9720d77c79e.

## One authoritative v2 entry point

1. Analyze existing evidence: use the sibling analysis_data directory from the versioned Zenodo archive, then run `python REPRODUCE.py analysis --input /path/to/analysis_data --output /path/to/results`. This verifies the packaged input manifest, executes 15 strict-return tests, analyzes all 195 temporal/natural/combined cases and the 240 ensemble per-run metric records, and compares eight outputs byte-for-byte with the reference files.
2. Fresh build and bounded smoke: `python REPRODUCE.py smoke --archive /path/to/ns-3.47.tar.bz2`. This builds upstream and all harnesses, runs both stock/patch local handler programs, one paired ensemble case, the natural retained-state stock/patch pair and restored safety stock/patch/unsafe triple. Strict TX/RX/TTL return detection is used in smoke and full analysis.
3. Full revision matrix: `python REPRODUCE.py full --archive /path/to/ns-3.47.tar.bz2 --output /path/to/results`. This runs 240 ensemble plus 195 temporal/natural/combined simulations, then invokes the same v2 analyzer. Previous local run directories are moved aside before simulation, so cached scientific observations are not silently reused.

No original workspace, historical script tree, bundled binary, unpublished credentials or remote service is needed. Inputs are read without modification; results are written separately. The relative path manifest fixes all six mobility traces. All supplied scientific CSVs and C++ sources are exact preserved copies except transformations explicitly recorded in PROVENANCE.json.

## Scope of the minimal evidence

The analysis-data archive contains the five original CSV inputs needed by each of 195 v2 cases, minimal scientific status fields, and all 240 ensemble metric records. Raw CSV bytes are unchanged. Machine paths, commands, elapsed execution time and cache fingerprints are removed from copied status metadata; original and distributed hashes plus the exact transformation are recorded. This is a new distribution with new checksums, not a renamed copy of the earlier complete-raw archive.

Ensemble analysis reuses recorded per-run measurements. Regenerating their lower-level packet/airtime traces requires full simulation. Unused exploratory histories and the disconnected initial pilot are not included; neither is silently counted as recovery evidence. The original full evidence archive remains a separate historical artifact.

The authoritative strict packet-return predicate requires the same node and IPv4/application identity, a strictly earlier physical TX and a later physical RX with lower TTL. Loopback is excluded. Source-0/main-flow counts and all-observed-node/flow counts are separately labelled. Natural/combined artificial-perturbation qualification is not applicable, represented by null/blank, not failure. The release does not establish topology-wide loop freedom or general network recovery.

See METHODS.md, DATA_DICTIONARY.md, PROVENANCE.json and VALIDATION.json for scope, fixed inputs and checks. This release uses a fixed version and SHA-256 manifest; cite the version DOI rather than a mutable branch link.

## Original manuscript S1–S4

`original_tables/` is the distinct portable module for the original 99 paired handler cases, natural95 lifecycle evidence and six historical paired environments. Its four reference tables remain byte-identical to the original supplement. After the upstream base has been built, follow `original_tables/README.md` with `--ns3 /path/to/experiments/ns-3.47` and a fresh separate work directory. These are the original manuscript cases, not additions to the 435-run revision matrix.

One provenance gap is explicit: the original supplemental direct queue-observer source and trace cited by S3 were not recovered. A separately labelled, opt-in new observer regenerates the 31 FIFO evictions and 64 retry-exhaustion drops. It does not substitute for claiming recovery of the original source. The original application/lifecycle/RREQ evidence is regenerated from preserved historical sources.
