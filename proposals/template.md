# NNNN — Short descriptive title

| | |
|---|---|
| **Status** | draft |
| **Author** | Name (affiliation) |
| **Created** | YYYY-MM-DD |
| **Issue** | #N |
| **Targets** | spec §X.Y · field IDs … |
| **Objection window closes** | YYYY-MM-DD (≥ 14 days after visibility) |

## Problem

What is wrong or missing today, from the point of view of someone writing or
reading a file. Describe the problem without reference to your solution.

If a real device or platform is affected, say which and how. Concrete beats
hypothetical: a file that cannot be interpreted, a value that cannot be
represented, two implementations that disagree.

## Proposal

The change, precisely. For a new or changed field, give the full row — no field
is specifiable without all seven:

| Message | ID | Name | Base type | Scale | Units | Definition | Typical range |
|---|---|---|---|---|---|---|---|
| record | | | | | | | |

Then state:

- **Absent behaviour** — what a consumer does when the field is not present.
- **Unaware behaviour** — what happens to a consumer that does not know this
  field exists and encounters it.
- **RFC 2119 level** — `MUST` / `SHOULD` / `MAY`, for producers and for
  consumers separately, and why that level rather than a stronger or weaker one.

## Spec text

The actual wording to insert into `spec/FIT_STANDARD.md`, as it should read.
Proposals that leave the drafting to someone else tend to stall.

## Compatibility

- **Existing files** — does any conforming file become non-conforming, or change
  meaning? If yes, say so plainly here. This is the section reviewers read first.
- **Existing consumers** — what does a reader built against the current draft do
  with a file using this change?
- **Migration** — if this replaces something, how long do both coexist, and does
  the old field get deprecated rather than removed? (It does. IDs are never
  reused.)

## Alternatives considered

Including doing nothing. The rejected alternatives are the most useful part of a
proposal two years from now, when someone asks why the standard works this way.

## Implementation

- Where it is implemented: link a branch, pull request or commit.
- Who else has written or read it.
- Round-trip evidence: a file written by one implementation and read correctly by
  another. Attach or link the FIT file.

Required before ratification for anything that changes file contents.

## Open points

Anything you know is unresolved. Better here than discovered after merge.

## Discussion record

Filled in as review proceeds — objections raised, how each was resolved or why
the group proceeded anyway. Amend before merge so the decision is legible without
reading the whole pull request thread.
