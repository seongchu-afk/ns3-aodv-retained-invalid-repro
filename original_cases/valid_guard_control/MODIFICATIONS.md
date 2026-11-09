# Source modifications and chronology

On 2026-11-09, a provenance/license comment was prepended to observer.cc and negative_shifted.cc, and a provenance comment was prepended to patch-routing.cc. The original scientific source body of each file is byte unchanged. Upstream authorship, copyright, contact, and SPDX notices in the routing source remain intact. PROVENANCE.json records each original and modified SHA-256. The same notice lists both original harness hashes, so their complete distributed files still differ only in the injection time.

The historical negative_shifted.cc was derived from observer.cc by changing the scheduled injection from 18 to 18.05 seconds after the 18-second attempt failed wireless reception qualification. No claim of advance registration is made. Both attempts are retained, without treating the failed attempt as successful guard evidence.

New portable Python build, run, qualification, orchestration, and test scripts were written on 2026-11-09. They use relative package paths and explicit external paths supplied by the caller. They do not reuse old execution scripts or binaries. No scientific algorithm, topology, mobility byte, request field, seed, stream, timing other than the already-existing historical correction, or original trace byte was changed.
