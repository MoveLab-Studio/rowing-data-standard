# Proposals

A proposal is how a substantive change to the standard gets considered: a new
field, a changed type, scale or unit, a new conformance requirement, or anything
that could invalidate an existing conforming file.

Small stuff does not need one. Typos, formatting and wording that changes no
requirement go straight to a pull request. Questions, ambiguities and defects in
the text go to the issue tracker. When in doubt, open an issue and we will sort
out which it is.

## Process

1. **Open an issue first.** Describe the problem, not your solution. A useful
   number of ideas dissolve here because the specification already covered it,
   or because someone explains why the obvious fix breaks a shipping device.
2. **Copy [`template.md`](template.md)** to `NNNN-short-title.md`, taking the
   next free number. Numbers are sequential and permanent, including for
   declined proposals — a declined proposal is a record of a decision and stays
   in the repository.
3. **Open a pull request** adding the proposal file. The discussion happens on
   that pull request, so the reasoning stays attached to the text.
4. **Objection window: minimum 14 days** from when participants can actually see
   it. Longer over holidays. A standard that slips past the one person who knew
   why a field existed is a bad standard.
5. **Demonstrate it.** Anything touching what goes into the file must be
   implemented and shown to round-trip in at least one implementation before it
   is adopted. Text-only clarifications are exempt.
6. **Decide.** The chair puts the proposal on a release's milestone, and the
   [Data Standards Working Group](../GOVERNANCE.md) decides it: consensus where
   possible, otherwise a majority vote. Every proposal gets a recorded outcome —
   `adopted`, `deferred`, or `declined` with a brief reason.
7. **Merge.** An adopted proposal is merged with status `adopted`, the
   specification is updated, and
   [`registry/field-ids.md`](../registry/field-ids.md) is updated with it in the
   same pull request. It is published in the next release. A breaking change is
   announced in at least one release before the release that makes it.

Anyone can write, comment on and implement a proposal. Only the outcome is the
DSWG's. Visible agreement from implementers and no sustained technical
objection is the strongest case a proposal can bring to it.

## What gets a proposal declined

Not to discourage anyone — these are just the patterns that come up:

- **No implementation can produce it.** Precision that no device measures is not
  a specification, it is a wish.
- **It silently invalidates existing files.** Sometimes necessary, never quiet.
  Say so in the Compatibility section and expect scrutiny.
- **It reuses a field ID.** Never happens — a deprecated field keeps its number
  permanently, because files carrying the old meaning already exist. Deprecation
  binds producers, not consumers: producers stop writing it, readers must keep
  reading it. See [`registry/field-ids.md`](../registry/field-ids.md).
- **It leaves the absent case undefined.** Every developer field is optional in
  FIT, so every field has an absent case and a consumer needs to know it.
- **It belongs to transmission, not storage.** How a device streams live data is
  out of scope for this standard.

## Status values

`draft` · `under discussion` · `adopted` · `deferred` · `declined` ·
`withdrawn` · `superseded by NNNN`

Adopted and declined proposals both stay. The declined ones save the next person
from re-proposing the same thing, and record why.

## Index

| # | Title | Status |
|---|---|---|
| — | *No proposals yet.* | |
