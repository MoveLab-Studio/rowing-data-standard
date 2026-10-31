# 0001 — Remove WorkoutState

| | |
|---|---|
| **Status** | draft |
| **Author** | Sander Roosendaal |
| **Created** | 2026-10-31 |
| **Issue** | #54 |
| **Targets** | spec §4.1, §5.1 · field ID 9 |
| **Objection window closes** | 2026-11-14 (≥ 14 days after visibility) |

## Problem

`WorkoutState` (record developer field 9) carries the training intensity of a
single record, using the values of the native FIT `intensity` enum. It is not
clear what it adds.

- The Lap message already has a native `intensity` field, and §4.1 requires
  producers to set it on every Lap. The standard therefore says the intensity is
  on the lap (§4.1) and also, optionally, on the record (§5.1). A reader of the
  standard can reasonably wonder which one is authoritative; the draft answers
  "the lap", which leaves the record field with nothing to say.
- Rest and pauses are already distinguishable without it: rest laps carry
  `intensity=rest`, active laps sum to moving time through `total_timer_time`
  (§4.1), and unplanned pauses appear as timer events in the event log.
- OpenRowingMonitor writes only active and rest laps, and has no use for
  intermediate states (issue #54). Time-sampled and GPS-based recorders may want
  a per-record state, but `StrokeState` (field 96) already covers the
  stationary-versus-rowing case for them.

## Proposal

Remove `WorkoutState` from the standard.

| Message | ID | Name | Base type | Scale | Units | Definition | Typical range |
|---|---|---|---|---|---|---|---|
| record | 9 | `WorkoutState` | UINT8 | 1 | | **Removed** | |

- **Absent behaviour** — there is nothing to be absent. Consumers take intensity
  from the Lap `intensity` field.
- **Unaware behaviour** — a consumer meets field 9 only in files written against
  an earlier draft. A consumer that does not know it ignores it, as it does any
  unknown developer field.
- **RFC 2119 level** — producers MUST NOT write field 9 as defined by the earlier
  draft. The ID is reserved and MUST NOT be reused, per the registry rule that
  IDs are never reused. Consumers have no obligation toward it.

## Spec text

§4.1, rule 1 becomes:

> 1. **Intervals are marked with intensity.** Producers SHOULD write each work and
>    rest interval as its own Lap, and MUST set the native `intensity` field on
>    every Lap they write (`active` for work, `rest` for rest, or another value of
>    the FIT `intensity` enum).

In §5.1 the WorkoutState row, the "WorkoutState values" table and the "WorkoutState
rules" are deleted. In `registry/field-ids.md` the row for ID 9 is replaced by a
reservation: "was `WorkoutState`, removed; never reused".

## Compatibility

- **Existing files** — no conforming file becomes non-conforming. A file that still
  carries field 9 is read normally; the field is ignored.
- **Existing consumers** — a consumer built against the current draft that reads
  field 9 sees it absent in new files, and must already cope with that, as every
  developer field is optional.
- **Migration** — none. Nothing in this standard has been ratified yet, and the
  removal follows the same course as the pounds force fields (#13). ID 9 stays
  reserved.

## Alternatives considered

- **Do nothing.** Leaves two places for the same information and an unclear rule
  about which wins.
- **Keep it only for time-based and GPS recorders**, as suggested on the issue.
  `StrokeState` already serves them, and a field with a different meaning
  depending on the recording strategy is harder to implement than no field.
- **Replace it with event-log start/stop markers.** Events are part of FIT already
  and need no new field, so there is nothing for this standard to add.

## Implementation

- Python: #61 removes the field and its handling. The native lap `intensity` is
  unchanged and still round-trips.
- Round-trip evidence: not applicable beyond the lap `intensity` round-trip tests,
  since nothing new is written to the file.

## Open points

- Whether the reservation of ID 9 should be stated in the registry's range map
  (done here) or only in the prose.

## Discussion record

- Issue #54: contributors asked what `WorkoutState` is for and noted the overlap
  with Lap `intensity`; the maintainer proposed removal for v1.0.
