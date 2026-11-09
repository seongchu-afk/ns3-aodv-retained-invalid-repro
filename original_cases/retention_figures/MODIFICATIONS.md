# Modified-source identification

On 2026-11-09, a prominent dated comment was prepended to each of the four original round16 scientific source files. No executable code changed in this step. All original scientific source bytes follow the notice unchanged, with their original SHA-256 embedded in the notice and recorded in PROVENANCE.json. This date identifies release preparation, not when the earlier scientific modifications were originally made.

- sources/observer.cc: controlled four-packet retention fixtures and read-only application, network and airtime observations.
- sources/stock-routing.cc: ns-3 AODV with the existing request-reason instrumentation; stock protocol decisions retained.
- sources/patch-routing.cc: the identical instrumentation plus the INVALID-only guard exemption.
- sources/lifecycle-rtable.cc: existing route invalidation and purge-deletion observation instrumentation.

After removing the new comments, stock and patch differ by exactly one predicate: `if (toDst.GetNextHop() == src)` becomes `if (toDst.GetNextHop() == src && toDst.GetFlag() != INVALID)`. Original upstream copyright, GPL identifiers and author attribution remain intact. No unrelated temporal fixture headers are bundled. The build verifies and uses pristine ns-3.47 headers, since no extra diagnostic friend access is needed here.

New portable build.py and run.py wrappers replace historical machine-specific build paths and freeze handling. They preserve the original scientific sources and all 24 fixed job arguments. analyze.py preserves the original metric expressions with portable input/output paths, and adds qualification, exact-output comparison and Figure 2/3 data exports. These wrapper changes are not described as comment-only. Original build.py, run.py and analyze.py identities are recorded in PROVENANCE.json.

The 2026-11-09 code/data split adds an explicit external `--input` data root, keeps `--runs` as an alias, and makes direct original-byte comparison optional through `--reference-input`. Required raw trace identities remain code-side hashes. No scientific C++ source, job argument or metric expression changed.
