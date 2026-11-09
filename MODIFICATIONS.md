# Modified-source identification

Release 2.0.0 adds a prominent dated comment to the ns-3-derived research files listed below. These files contain the project’s existing instrumentation, controlled fixtures or routing-guard variants, rather than pristine upstream ns-3. The release notice was added on 2026-11-09; it does not assert that all earlier scientific modifications were originally made on that date. No executable code was changed when adding the notice. All prior scientific source bytes follow the notice unchanged. Original upstream copyright, author and GPL identifiers remain intact.

The INVALID-only protocol change is isolated in patches/ns-3.47-invalid-only.patch. Stock research variants retain stock protocol decisions with instrumentation. Patch variants apply the stated guard change with instrumentation. The unsafe variant removes the guard as a detector control. Routing-table and header differences support the documented observations and fixtures. PROVENANCE.json files preserve the input and distributed identities.

- experiments/sources/aodv-dpd.h
- experiments/sources/aodv-id-cache.h
- experiments/sources/aodv-neighbor.h
- experiments/sources/aodv-routing-protocol.h
- experiments/sources/aodv-rqueue.h
- experiments/sources/aodv-rtable.h
- experiments/sources/patch-routing.cc
- experiments/sources/stock-routing.cc
- experiments/temporal_sources/aodv-routing-protocol.h
- experiments/temporal_sources/aodv-rtable.h
- experiments/temporal_sources/lifecycle-rtable.cc
- experiments/temporal_sources/patch-routing.cc
- experiments/temporal_sources/stock-routing.cc
- experiments/temporal_sources/unsafe-routing.cc
- original_tables/sources/handler/aodv-routing-protocol.h
- original_tables/sources/handler/aodv-rtable.h
- original_tables/sources/handler/patch-routing.cc
- original_tables/sources/handler/stock-routing.cc
- original_tables/sources/natural95/aodv-routing-protocol.h
- original_tables/sources/natural95/aodv-rtable.h
- original_tables/sources/natural95/lifecycle-rtable.cc
- original_tables/sources/natural95/patch-routing.cc
- original_tables/sources/natural95/stock-routing.cc
- original_tables/sources/six/patch-routing.cc
- original_tables/sources/six/stock-routing.cc

## Corrective packaging, 2026-11-09

v2.0.1 integrates separately inventoried original-paper modules without changing scientific C++/CSV bytes or baseline references. The root REPRODUCE.py adds unified orchestration, clean upstream rebuilding, read-only archive analysis and per-module outputs. original_tables/supplementary_observer/verify.py adds only optional report placement via --output, preserving its assertions. Metadata, path references, inventories, coverage and licensing documentation are updated. All added scientific-source modifications were already documented in each source module's dated notices and provenance.

The final `original_tables/analyze.py` changes one S3 report string only, clarifying that the historical additional direct queue source and trace remain unrecovered while the optional new observer is validated separately. Its measurement and assertion logic are unchanged. The final analyzer and coverage validator were rerun on the completed originals outputs; all 743 output CSV files remained byte-identical.
