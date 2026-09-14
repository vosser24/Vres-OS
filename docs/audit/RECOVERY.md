# Recovery chain

The original bundle available in this session contained the initial scaffold `0010888`. The separately
available source ZIP contained additional work but not all later chat-described commits or tests.
This audit cloned that bundle, overlaid the supplied source ZIP and committed the recovered, unverified
baseline as `e332df7`. Its test suite reproduced 41 passing cases with unavailable PostgreSQL integration
modules skipped. No later historical count was used as proof.

Subsequent local checkpoints are ordinary Git commits with actual source/test changes. Original input ZIP
and bundle are preserved outside this checkout. Additive migrations 007–009 do not rewrite recovered 001–006.
The current package version is a new alpha preview, not a claim to recover every previously described feature.

A release is only the clean commit recorded in the external release manifest. Download its matching source
ZIP and Git bundle. The release process restores the bundle into a separate checkout and checks the exported
source/wheel bytes against that commit. A folder link or an uncommitted chat claim is not a durable release.
