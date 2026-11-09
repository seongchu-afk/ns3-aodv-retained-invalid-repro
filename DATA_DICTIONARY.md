# File and field index

- experiments/sources: ensemble and handler harnesses, stock/INVALID-only instrumented AODV, diagnostic headers.
- experiments/temporal_sources: controlled, natural and combined harnesses; stock/INVALID-only/unsafe AODV; lifecycle observer; three immutable small mobility fixtures.
- experiments/mobility.json and mobility/*.csv: six fixed 25-node trajectories and SHA-256 hashes.
- analysis/analyze_temporal.py: the single authoritative v2 temporal analyzer. analysis/strict_returns.py implements the shared predicate; analysis/test_strict_returns.py contains 15 synthetic tests.
- reference/ensemble_summary.csv: six environments × nine metrics, each with n=20 paired differences, means, standard deviations, signs, range, median and descriptive intervals. reference/paired_runs.csv contains all 120 pairs.
- reference/temporal_extended_summary.csv: all 195 finalized cases and explicit scientific qualification/recovery/cycle/return fields.
- reference/counterexample_summary.csv and combined_summary.csv: natural qualification fields, with blank artificial_perturbation_qualified.
- reference/recovery_windows.csv: all one-second generation cohorts. `eventual_rate` is fraction eventually delivered; `timely_rate` also requires latency <=1 s.
- reference/TEMPORAL_EXTENDED.json: the full nested counterpart, including first relevant route, state lineage, overlap and reason-label counts.
- analysis_data/*_runs/<case>/trace-events.csv: application send/receive events. flow=1 is the main flow.
- trace-route-snapshots.csv: synchronous destination-scoped state; flags 0=VALID, 1=INVALID, 2=IN_SEARCH.
- trace-control-events.csv: ordered physical/loopback IPv4 TX/RX records, packet identities and TTLs. interface=0 is local loopback in these fixtures.
- trace-reason.csv: reason-labelled routing-handler observations; trace-graph.csv: geometric-path observations.
- status.json in analysis_data: only config, version, run, exit_code and historical qualification_pass. For natural/combined cases the last field is an inapplicable historical artificial gate; use derived retained_invalid_qualified/concurrent_search_observed instead.
- analysis_data/ENSEMBLE_COMPLETE.json: all 240 scientific per-run ensemble measurements. This permits statistical recalculation, not independent extraction of measurements from lower-level traces.
- Generated return_evidence/<suite>/<case>.csv: strict matching TX/RX event pairs with original CSV line numbers, interfaces, timestamp/order, TTL and identity. The three unsafe temporal baseline cases have 32 returned main-flow identities each.

`strict_source0_main_return_count` counts distinct source-0/main-flow sequences. `strict_any_observed_node_identity_count` counts node-plus-identity pairs, so the same packet returning to two nodes counts twice. `strict_matched_rx_event_count` counts RX events including repeats. Null/blank means inapplicable or unavailable, not zero.
