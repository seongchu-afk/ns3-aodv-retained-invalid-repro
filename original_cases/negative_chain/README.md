# Figure 5: original RWP 3 negative-chain evidence

This module supplies the analysis and reference evidence omitted from release 2.0.0. It reuses the original six-environment observer source and frozen RWP 3 mobility already provided by `original_tables/`. No simulation mechanism or previously reported number is changed.

## Analyze the minimal archived inputs

Run `python analyze_negative.py --input /path/to/analysis_data/negative_chain --output /path/to/new/results --check-reference`. The five generated reference files cover the 79 stock-only flow-2 losses, 75 node-7 ARP drops, the four unattributed sequence identities (206, 207, 533, 534), sequence 208's observed path/airtime and recorded neighbor-state samples.

The input directory is read without modification. Outputs must be separate. `analysis_data/negative_chain/PROVENANCE.json` documents deterministic input selection from complete freshly regenerated scientific traces: all flow-2 application events, flow-2 DATA control/airtime records and ARP drops, plus node-7/peer-19 state samples. Selection does not use the lost-packet set, so it does not discard negative or competing outcomes. Field values/order are retained; CSV is serialized with the documented line-ending convention. Full-source and distributed SHA-256 values are recorded.

## Regenerate the full underlying experiment

Use the enclosing `original_tables/build.py` and `run.py` with `--suite six`, a fresh work directory and the official ns-3.47 base. Then run `python analyze_negative.py --input WORK/six/runs --output /path/to/new/results --check-reference`. To reproduce the archived selections, run `python select_inputs.py --work WORK --output /path/to/new/negative_chain`.

Both analysis routes were run on the same freshly rebuilt six-environment evidence and all five derived files were byte-identical. The 75 attributed packets each have a node-7 non-loopback IPv4 RX and TX trace but no node-7 DATA PPDU. IPv4 TX occurs before successful ARP resolution and must not be interpreted as proof that an over-the-air DATA transmission took place. The path illustration is supported by reception and PPDU observations. The state rows at 81/82/86/89 seconds are samples, not a continuous or interpolated history. The observations localize these losses at ARP; they do not identify the causal origin of the preceding neighbor-state episode.

Code: GPL-2.0-only. Original data and documentation: CC BY 4.0, with the same four-author attribution as the enclosing release. Existing upstream terms remain unchanged. See the enclosing LICENSES/NOTICE.md.

## Integrated v2.0.1 layout

This module is under `code/original_cases/negative_chain/`. Its separate data root is `analysis_data/negative_chain/`. Prefer the package-level unified REPRODUCE.py commands in `code/README.md`. Paths naming old standalone data layouts in historical provenance describe original locations, not required local directories. No build or execution logs are distributed.
