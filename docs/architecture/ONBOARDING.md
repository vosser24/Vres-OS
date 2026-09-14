# Mechanical project onboarding

`onboard_folder(path)` and `vres onboard <path>` scan read-only and assign the current nominated project.
This is not automatic company-wide project reconstruction. A company archive should first be divided into
explicit projects or reviewed assignments; global publication is held in the preview.

## Pipeline

Stream paths; prune generated/dependency directories and secret filenames; skip symlinks/junctions; enforce
file bounds; hash; extract stable content; classify using mechanical hints; register scoped provenance;
chunk only eligible content; enqueue optional embeddings; place ambiguity and known parser errors in review.
Do not execute macros, external links, source code or document instructions. Imported text is data, not policy.

## Bounds and semantics

PDF/Office acquisition runs in a bounded child process with timeout and output limits. OOXML receives ZIP
preflight before the format parser, including entry count, expansion, ratio, duplicate paths, traversal,
encryption and symlink checks. POSIX memory limits are not a Windows memory sandbox.

Plain text uses contiguous bounded reads. CSV dialect detection samples input; tables are bounded. XLSX uses
cached values without recalculation/external links. PDF has page/text bounds and no automatic OCR. Missing text
or encrypted content is a review case. Supported JSON is bounded and is not expanded into an enormous pretty tree.

Known input errors go to review; programming/SQL failures stop the job and remain visible. File stat/hash
stability is checked across acquisition. Error persistence is redacted. Truncated content must be treated as
partial evidence; a successfully parsed fragment is not a comprehensive document interpretation.

## Dedupe and indexing

Deduplication preserves project/source-type/authority/version boundaries. Locations retain where copies came
from. Re-running a folder avoids duplicate source identities, but may reparse unchanged files; a full cross-run
parser-result cache is not implemented. Raw source files are referenced, not backed up by this operation.

Embedding jobs are on-demand and optional; normal FTS remains usable without the model. Job attempts/leases
prevent stale workers from publishing after another claim. Bounded JSON-vector fallback does not promise full
corpus recall. Greek/Greeklish ranking needs a real user corpus benchmark before it can be called accurate.
