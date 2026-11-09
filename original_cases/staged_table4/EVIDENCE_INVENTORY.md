# Complete staged Table 4 evidence inventory

All 12 cases are explicit in cases.json. The inventory was assembled before the new runs. No old research executable or shared library is distributed or used.

| Conditions | Variants | Harness | Mobility | HELLO | Main start | Stop | Planned |
|---|---|---|---|---|---|---|---|
| L | stock, patch, unsafe | observer.cc | natural.csv | on | 18.5 s | 45 s | 95 |
| E | stock, patch, unsafe | observer.cc | natural.csv | off | 18.5 s | 45 s | 95 |
| E2 | stock, patch, unsafe | expiry-observer.cc | expiry.csv | on | 28.5 s | 45 s | 4 |
| P | stock, patch, unsafe | observer.cc | positive.csv | off | 9.15 s | 25 s | 4 |

Every case uses seed 20261030, run 1, 512-byte UDP packets, a 0.1 s interval and 3 s ARP dead timeout. Each variant uses its matching *-routing.cc plus common lifecycle-rtable.cc, aodv-routing-protocol.h and aodv-rtable.h. The unmodified remaining AODV objects and dependent ns-3 modules come from the pinned clean ns-3.47 base.

Each of the 12 prefixes has eight byte-identical reference CSVs: events (application ledger), flows (flow totals), control-events (full IPv4/application identity, TX/RX/interface/TTL), route-snapshots (cycle states), lifecycle (invalidation origin), reason (handler decision state), qualification (perturbation checks), and graph (geometric reachability). These 96 traces are sufficient for every Table 4 statistic and qualification check. Other PHY, ARP and flow-monitor exports are ancillary and not needed here.

reference/Table4_expected.csv expands the manuscript table to 12 rows. historical_SUMMARY.csv/json and historical_QUALIFICATION_RESULTS.json preserve the original analysis results. PROVENANCE.json preserves input and distributed SHA-256 hashes and verifies all available relevant frozen source identities.
