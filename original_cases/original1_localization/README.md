# Original environment 1: delivery and request localization

This module supplies the small post-processing step and reference evidence for the manuscript's original-environment-1 example. The simulator is the existing original_tables/sources/six observer with original1 mobility. It does not introduce another simulation variant or another independent replicate.

Analyze archived inputs with `python analyze_localization.py --input /path/to/analysis_data/original1_localization --output /path/to/new/results --check-reference`. To regenerate from the existing original_tables six-suite simulation, pass its WORK/six/runs directory as --input. `select_inputs.py --work WORK --output /path/to/new/inputs` reproduces the minimal selections and records full-source and distributed hashes.

All-flow final delivery is 5854 to 5941 of 5985 (99 gained, 12 lost). The target flow, node 4 to node 24, changes from 1099 to 1187 of 1199 (93 gained, 5 lost). The 7/99 localization comparison uses the same 100 packets generated in [106,116) s, sequences 459-558, with delivery observed through 210 s. It does not count receptions by receive-clock time inside that window; that different quantity would be 4/99.

The fourth source RREQ is observed at 106.579 s. At 106.579200195 s node 3 takes the guard with an INVALID entry, the previous sender equal to the stored next hop, and 9.939392525 s remaining lifetime. The reference ledger retains matching node-3/node-8 guard observations for requests 4, 5 and 6. The analysis does not claim that every later network-wide gain/loss is caused by this one branch event.

Both the full freshly regenerated traces and the selected archival inputs produce the five reference files byte-for-byte. Application events retain every flow and remain byte-identical; target request/reason subsets are selected by stable source/destination identities, not by the outcome. See analysis_data/original1_localization/PROVENANCE.json for the exact rules and hashes. No original trace is replaced.

Code is GPL-2.0-only; original data and documentation are CC BY 4.0 with the four-author attribution in the enclosing release. Existing upstream license terms remain unchanged.

## Integrated v2.0.1 layout

This module is under `code/original_cases/original1_localization/`. Its separate data root is `analysis_data/original1_localization/`. Prefer the package-level unified REPRODUCE.py commands in `code/README.md`. Paths naming old standalone data layouts in historical provenance describe original locations, not required local directories. No build or execution logs are distributed.
