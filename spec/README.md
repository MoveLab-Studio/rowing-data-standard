# The specification

[`FIT_STANDARD.md`](FIT_STANDARD.md) is the deliverable. Everything else in this
repository exists to support editing it.

## Status

**Draft v0.1, not ratified.** The text started as v1.2, renumbered to `0.1` on
adoption here so that the version number stops implying a ratified standard,
and has been revised here since.

Version numbers `1.0` to `1.2` appearing inside the document refer to releases
that predate this repository, not to anything tagged here.

`main` is the current draft. A tagged GitHub release is a ratified version — that
is the difference, and it is the only thing an implementer should cite.

## Why it is one file

Splitting the specification into per-section files would reduce merge conflicts
and make pull requests easier to review. It has not been done, because the group
already knows this document as a single file and because divergence from the
upstream copy should be a deliberate decision rather than a side effect of
setting up a repository.

Worth revisiting once there are several editors working in parallel.

## Machine-readable form

The specification has no normative machine-readable schema in this repository.
Implementations currently hand-transcribe the field tables from the prose.

Generating a schema from this document — or making the schema normative and the
prose descriptive — is worth considering before the first release. Two hand-kept
copies of the same field table will drift, and this draft has shown it: v1.2
moved `EffectiveLength` (16) to millimetres and left the per-side pair 210/211 in
metres until it was corrected here.

## Editing

- Keep RFC 2119 keywords (`MUST`, `SHOULD`, `MAY`) deliberate, in capitals, and
  state producer and consumer obligations separately where they differ.
- Every field needs seven things: message type, ID, base type, scale, units, a
  definition precise enough to argue with, and a typical range.
- Say what a consumer does when the field is **absent**. Every developer field is
  optional in FIT, so every one of them has an absent case.
- Update [`../registry/field-ids.md`](../registry/field-ids.md) in the same pull
  request when you touch a field ID.
- Do not reflow paragraphs you are not changing — an unreadable diff is how a
  change gets waved through unexamined.
