# Original manuscript: minimal S1–S4 reproduction module

This module is separate from the major-revision v2 experiments. It retains the four original supplementary CSV tables byte for byte, the original scientific C++ harnesses/instrumentation, and the six frozen mobility inputs. It contains no compiled programs or historical machine-specific build metadata. `PROVENANCE.json` identifies the source and SHA-256 of every recovered scientific file; the build/run/analysis wrappers are newly written portable orchestration, not recovered original scripts.

## Scope

- **S1:** Compile the original round18 real-AODV handler harness. Run 99 inputs with each routing variant. Check the observed branch against all 198 original table entries, unchanged destination state, lifetime, and scheduled forwarding headers. These are handler checks, not a claim of end-to-end loop freedom.
- **S2:** Retain the exact simulation-settings table. The source and frozen mobility files define the runnable settings. S2 is a configuration reference, not an outcome generated from a simulation.
- **S3:** Run the original round19 natural95 lifecycle harness with HELLO enabled, run 1, main start 18.5 s and ARP dead timeout 3 s. Check 40 warm-up deliveries, 95 main packets, stock 0 versus patch 95 main deliveries, five source RREQ TTLs, B invalidation and lazy deletion, and the source route's disappearance at 28.58 s. The original round19 sources add read-only lifecycle/state observation to the natural95 experiment.
- **S4:** Run the original round15 general harness with round14 stock instrumentation and round15 INVALID-only patch, for the frozen Original 1–3 and RWP 1–3 mobility inputs. Compare packet identities, gains/losses/net counts and summed AODV transmitter airtime during [60,180) s with every S4 row. This is transmitter airtime summed across nodes, not a normalized channel-occupancy ratio. The patch is not claimed to improve every environment; RWP 3 has net −56 packets.

## S3 provenance limitation

The original S3 table cites an additional direct queue-observation run (`natural95_queue_observed.csv`) for 31 FIFO evictions and 64 retry-exhaustion drops. That run's original observer source and direct trace were not recovered among the supplied inputs. Retaining the original S3 table does not establish complete recovery of its source chain. The preserved historical scientific logic here regenerates the application, RREQ, lifecycle and state evidence, but do not directly log the queue's Drop calls.

The separate `supplementary_observer/` directory contains a **new**, optional read-only observer patch against upstream ns-3.47 `aodv-rqueue.cc`. It copies packets before decoding and logs queue drops without changing queue decisions. This provides a new reproduction of the reported counts; it is not the recovered original supplementary observer. Building without `--queue-observer` uses the original source set only. No original source or reference-table bytes are modified by either build.

## Prerequisites and commands

Linux, Python 3 (standard library only), a C++23-capable GNU compiler, CMake, and `patch` for the optional observer. Use an unmodified **ns-3.47** source/build tree. The official `ns-3.47.tar.bz2` SHA-256 is `8b3adca956c834ea436b915986ab8fd053e90041acae7426895d595aaa3ccc39`.

Configure and build the base in that tree:

```sh
./ns3 configure --build-profile=optimized --enable-modules=aodv,wifi,mobility,applications,flow-monitor,olsr,dsdv,dsr --disable-examples --disable-tests
./ns3 build -j 4
```

The enclosing reproduction package's clean `experiments/ns-3.47` build may be reused. Set `NS3` to the full path of that tree and `WORK` to a fresh, empty working directory outside this source module. From this module:

```sh
python3 build.py --ns3 "$NS3" --work "$WORK"
python3 run.py --ns3 "$NS3" --work "$WORK" --jobs 2
python3 analyze.py --work "$WORK"
```

The run refuses to overwrite existing result CSVs. Choose a fresh working directory for a rerun. Scientific source files are not patched in place; compiled variants and simulation traces go in `WORK` only. `--suite handler`, `--suite natural95`, or `--suite six` can limit build/run scope. Analysis expects all three suites, or pass `--smoke` to validate handler and natural95 only.

For the optional new queue observer, use a second fresh working directory and add `--queue-observer` to the build command. The natural95 stock run then emits `natural95/runs/stock-queue.csv`. Run `python3 supplementary_observer/verify.py --work "$WORK"` to check the 31/64 queue counts and sequence ranges. Keep its findings distinct from recovered-source validation.

## Results and limitations

`handler_verification.csv` checks all 198 observations. `Table_S4_regenerated.csv` is compared with the original S4 at its published precision (half a final decimal unit for airtime). `natural95_verification.json` reports independently regenerated S3 measurements. `VALIDATION.json` is written only after these checks pass. Original S1–S4 CSVs remain in `reference/` and are never overwritten.

Exact stochastic results can depend on ns-3 version, compiler, platform and build profile. The checks deliberately fail on mismatches rather than silently updating reference values. This module follows the code/data license scopes in the package LICENSES/NOTICE.md. Existing upstream notices are retained. Release-only, comment-based modification notices are documented in MODIFICATIONS.md and PROVENANCE.json; they do not change the recovered scientific logic.
