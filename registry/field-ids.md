# Developer field ID registry

> **Draft.** Every allocation below is provisional and derived from
> [`spec/FIT_STANDARD.md`](../spec/FIT_STANDARD.md) v0.1. Where this table and
> the specification disagree, **the specification is authoritative** and the
> disagreement is a bug — please report it.
>
> References to `v1.1` and `v1.2` below are to releases that predate this
> repository, from which this draft was renumbered.

All fields in this standard live under a single FIT developer application ID, so
that field numbers cannot collide with another vendor's private developer fields:

```
Application ID : 89e86158-6d47-5c98-9d46-7d29437f27b9
Derivation     : uuid5(NAMESPACE_DNS, "rowingdata")
Encoding       : 16-byte array in DeveloperDataIdMessage, per FIT SDK
```

**Why this file exists.** The FIT developer field ID space is a single byte —
0 to 255 — shared by every field this standard will ever define. It is the one
genuinely scarce resource in the project. This table is the single place to check
before using a number, and no ID should appear in a shipped product until it is
recorded here. Two vendors independently picking ID 94 is exactly the failure
this standard exists to prevent.

**IDs are never reused.** A deprecated field keeps its number permanently,
because files carrying it already exist.

## Range map

| Range | Purpose | Status |
|---|---|---|
| 0–9, 19 | Core rowing metrics | Assigned (see below) |
| 10 | `RecordingStrategy` (`session`-level) | Assigned |
| 11–18 | Oarlock metrics, single/summary | Assigned |
| 20–59 | In-stroke curve summary statistics | Unallocated — allocation scheme unresolved, and the statistics themselves are underspecified |
| 60–89 | In-stroke curve arrays | Unallocated — allocation scheme unresolved; spec §6.2 and §9.1 disagree on this range |
| 90–92 | In-stroke axis metadata | Assigned |
| 93 | `StrokeRate` | Assigned |
| 94–199 | Extended standard fields | **Available** |
| 200–211 | Dual oarlock, per side | Assigned |
| 212–255 | Future extensions | **Reserved** |

Free capacity today: **106 fields** in 94–199, plus 44 reserved in 212–255, plus
whatever of 20–89 the curve allocation does not consume.

## Assigned fields

### Session message

| ID | Name | Base type | Scale | Units | Notes |
|---|---|---|---|---|---|
| 10 | `RecordingStrategy` | UINT8 | 1 | — | `0` Unknown, `1` StrokeBoundary, `2` GPSUpdate. One value per file. Currently `MAY`, and §3.1 requires consumers to work without it |

### Record message — core rowing metrics

| ID | Name | Base type | Scale | Units | Notes |
|---|---|---|---|---|---|
| 0 | `DriveLength` | UINT16 | 1 | mm | Handle travel along longitudinal axis during drive. Was scale 100 / m before v1.2 |
| 1 | `StrokeDriveTime` | UINT16 | 1 | ms | Drive phase duration |
| 2 | `DragFactor` | UINT16 | 1 | — | Ergometer resistance setting; device-specific meaning |
| 3 | `StrokeRecoveryTime` | UINT16 | 1 | ms | Recovery phase duration |
| 6 | `AverageDriveForce` | UINT16 | 10 | N | Average force over the drive |
| 7 | `PeakDriveForce` | UINT16 | 10 | N | Peak force over the drive |
| 8 | `AverageBoatSpeed` | UINT16 | 255 | m/s | Averaged over the stroke |
| 9 | `WorkoutState` | UINT8 | 1 | — | Rowing state indicator |
| 19 | `StrokeWork` | UINT16 | 1 | J | Full stroke cycle, not drive-only |
| 93 | `StrokeRate` | UINT16 | 100 | spm | 0.01 spm precision. Native `cadence` must still be written |

### Record message — oarlock metrics (single / summary)

Oar angle convention: **0° = oar perpendicular to the boat's longitudinal axis.**
Negative toward the catch, positive toward the finish.

| ID | Name | Base type | Scale | Units | Notes |
|---|---|---|---|---|---|
| 11 | `Catch` | SINT16 | 10 | deg | Oar angle at catch |
| 12 | `Finish` | SINT16 | 10 | deg | Oar angle at finish |
| 13 | `Slip` | SINT16 | 10 | deg | Early blade entry |
| 14 | `Wash` | SINT16 | 10 | deg | Late blade exit |
| 15 | `PeakForceAngle` | SINT16 | 10 | deg | Oar angle at peak force (angle sensors, OTW) |
| 16 | `EffectiveLength` | UINT16 | 1 | mm | Oarlock pin to handle |
| 17 | `PeakForcePositionNorm` | UINT16 | 1 | — | 0–10000, ten-thousandths of the drive |
| 18 | `PeakForcePositionAbs` | UINT16 | 1 | mm | Handle position at peak force (position sensors, indoor) |

### Record message — dual oarlock, per side

Included only when both sides are measured. Summary fields 11–16 should then
carry the port/starboard average.

| ID | Name | Base type | Scale | Units | Side |
|---|---|---|---|---|---|
| 200 | `CatchPort` | SINT16 | 10 | deg | Port |
| 201 | `CatchStarboard` | SINT16 | 10 | deg | Starboard |
| 202 | `FinishPort` | SINT16 | 10 | deg | Port |
| 203 | `FinishStarboard` | SINT16 | 10 | deg | Starboard |
| 204 | `SlipPort` | SINT16 | 10 | deg | Port |
| 205 | `SlipStarboard` | SINT16 | 10 | deg | Starboard |
| 206 | `WashPort` | SINT16 | 10 | deg | Port |
| 207 | `WashStarboard` | SINT16 | 10 | deg | Starboard |
| 208 | `PeakForceAnglePort` | SINT16 | 10 | deg | Port |
| 209 | `PeakForceAngleStarboard` | SINT16 | 10 | deg | Starboard |
| 210 | `EffectiveLengthPort` | UINT16 | 1 | mm | Port |
| 211 | `EffectiveLengthStarboard` | UINT16 | 1 | mm | Starboard |

### Record message — in-stroke axis metadata

Required together on every record carrying curve data — which for a device with
a fixed sampling regime repeats the same three values on every stroke of the
session. Whether some or all of them belong on a file-level message instead is
unresolved; note that `InstrokeSampleInterval` is genuinely per-stroke when
`InstrokeAbscissaType = TIME_UNIFORM_MS`, since §6.3 derives it from drive time.

| ID | Name | Base type | Scale | Units | Notes |
|---|---|---|---|---|---|
| 90 | `InstrokeAbscissaType` | UINT8 | 1 | — | X-axis semantics, enum below |
| 91 | `InstrokeSampleInterval` | UINT16 | 1 | varies | Meaning depends on field 90 |
| 92 | `InstrokePointCount` | UINT8 | 1 | — | Points per curve array, max 127 |

`InstrokeAbscissaType` values:

| Value | Name | `InstrokeSampleInterval` means |
|---|---|---|
| 0 | `UNKNOWN` | Nothing — shape-only curve, not for absolute plotting |
| 1 | `TIME_UNIFORM_MS` | Milliseconds between samples |
| 2 | `HANDLE_DISTANCE_UNIFORM_M` | Millimetres between samples along handle travel |
| 3 | `OAR_ANGLE_UNIFORM_DEG` | Degrees between samples; domain is [`Catch`, `Finish`] |
| 4 | `NORMALIZED_DRIVE_0_1` | Dimensionless step over a 0–1 drive |

## Curve types — not yet allocated

The draft names four curve types but assigns no fixed IDs, describing allocation
as "dynamic, per-curve-type" — start at 60 and increment. Two vendors supporting
different subsets, or the same subset in a different order, will assign different
IDs to the same curve. Until a fixed allocation is agreed, **there is no
interoperable ID for any of these** and producers should not assume a consumer
will match theirs.

| Curve | Y units | Y scale (UINT16) | Recommended abscissa | Signed? |
|---|---|---|---|---|
| `HandleForceCurve` | N | 10 | `HANDLE_DISTANCE_UNIFORM_M` (erg), `TIME_UNIFORM_MS` (OTW) | No |
| `BoatAcceleratorCurve` | m/s² | 100 | `TIME_UNIFORM_MS` | **Yes** ⚠️ |
| `OarAngleVelocityCurve` | deg/s | 10 | `TIME_UNIFORM_MS` or `OAR_ANGLE_UNIFORM_DEG` | Possibly |
| `SeatCurve` | m | 255 | `HANDLE_DISTANCE_UNIFORM_M` or `TIME_UNIFORM_MS` | No |

⚠️ Boat acceleration is negative for a large part of every stroke, but §6.5
mandates UINT16 arrays and leaves any offset transformation to the implementer,
documented only in free text. Two vendors will pick different offsets. Unresolved.

Arrays are UINT16, uniformly spaced along the declared abscissa, maximum 127
points (255-byte FIT field limit ÷ 2 bytes).

## Native FIT fields

Not part of this registry — these are standard FIT fields the standard tells
producers to use rather than reinventing. Listed for completeness because they
carry the data an unaware consumer will read.

| FIT field | Carries | Notes |
|---|---|---|
| `timestamp` | Record time | Garmin epoch, from 1989-12-31 UTC |
| `distance` | Cumulative distance | m, scale 100 |
| `cadence` | Stroke rate, integer spm | Always write for backward compatibility |
| `fractional_cadence` | Stroke rate fraction | Scale 1/128 spm |
| `heart_rate` | Heart rate | bpm |
| `power` | Average power | W |
| `enhanced_speed` | Boat speed | m/s, scale 1000 |
| `position_lat` / `position_long` | Position | Semicircles |
| `total_cycles` | Cumulative stroke count | The stroke-detection signal; may repeat or jump by >1 |
| `cycle_length16` | Distance per stroke | m, scale 100, max 655 m |

## Requesting an ID

Open a [proposal](../proposals/README.md). It must state the message type, base
type, scale, units, a precise definition, the typical range, and how a consumer
that does not understand the field behaves when it is present. A new ID is not
allocated until a working implementation has written and read it.
