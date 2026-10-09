# Rowing Data Standard for Garmin FIT Format

> ### ⚠️ Draft — not ratified
>
> This document is a **working draft**. Nothing in it is final: field IDs, scales,
> units and the conformance language itself are all open to
> change until the governance group ratifies a version. Do not treat any part of
> this text as a stable contract for shipping products yet.
>
> **Authorship.** The technical content of this draft was written by Sander
> Roosendaal and previously released as v1.0 to v1.2. It is carried over here
> unchanged apart from this banner and the version number.
>
> **This repository is the sole home of the standard.** The text, the issue
> tracker, proposals and implementation work all live here. Earlier copies
> elsewhere are superseded and should not be used or cited.
>
> **Why 0.1 and not 1.2.** The text was renumbered on adoption by the governance
> group. A `1.x` number implies a ratified standard that an implementer can build
> against, and nothing here has been ratified — so the version was reset to a
> `0.x` series that states what this actually is. **No technical content changed
> in the renumbering.** What number the first ratified release carries is still
> open — note that `1.0` to `1.2` are already taken by the earlier lineage below,
> so that needs settling before the first tag.
>
> Version numbers **1.0 to 1.2** appearing later in this document refer to those
> earlier releases. They really were published under those numbers and are cited
> by existing files and implementations, so the references are left exactly as
> they stand.
>
> **Known inconsistencies are left in place, not silently corrected.** Several
> parts of this text contradict each other — units and field ID ranges
> among them. They are raised on the issue tracker
> so each one is decided on the record, because a "fix" to a unit or a scale
> changes what goes into the file.


**Version:** 0.1 — draft, not ratified  
**Date:** August 31, 2026  
**Supersedes:** v1.2 (3 August 2026) — renumbered, same technical content  
**Application ID:** `89e86158-6d47-5c98-9d46-7d29437f27b9` (UUID v5 from DNS:rowingdata)

## 1. Introduction

### 1.1 Purpose

This document defines a standard for encoding rowing-specific data within the Garmin FIT (Flexible and Interoperable Data Transfer) format. The standard enables interoperability between rowing devices, software platforms, and data analysis tools through consistent use of FIT developer fields.

### 1.2 Scope

This standard specifies:

- Developer field definitions for rowing-specific metrics
- Recording strategies for different device types
- Requirements for data consumers
- In-stroke curve data encoding
- Native FIT field usage for rowing

### 1.3 Target Audience

- Rowing device manufacturers (ergometers, smart oarlocks, GPS devices)
- Software developers (training platforms, analysis tools)
- Data platform operators

### 1.4 Application ID

All developer fields defined in this standard MUST use the **standard's application ID** to prevent namespace collisions.

**Format:** 16-byte UUID array as required by FIT SDK `DeveloperDataIdMessage`

**UUID:** `89e86158-6d47-5c98-9d46-7d29437f27b9`

This UUID v5 is deterministically generated from DNS namespace with name "rowingdata" (`uuid.uuid5(uuid.NAMESPACE_DNS, 'rowingdata')`), ensuring consistency across implementations. The FIT SDK requires the application_id field to be a 16-byte array representation of this UUID.

### 1.5 Protocol Version

The protocol version identifies the encoding a file follows. It is separate from the version of this document: most revisions of the document clarify text or add optional fields and leave the protocol version unchanged.

Producers MUST write the protocol version in the `application_version` field (UINT32) of the `DeveloperDataId` message that carries the standard's application ID.

**Current protocol version:** `1`

The protocol version is incremented only for a breaking change: one that changes the meaning of a field an existing file may contain. Adding a field is not a breaking change.

Consumers:

- MUST NOT reject a file because `application_version` is absent. Files written before this field was defined do not carry it.
- SHOULD treat an absent `application_version` as a file following the field definitions that predate protocol version 1.
- MAY warn when `application_version` is higher than the highest version they support, and SHOULD still read the fields they understand.

### 1.6 Conformance Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

## 2. Recording Strategies

### 2.1 Overview

Different device types generate FIT Record messages at different frequencies. Consumers MUST support all three approaches:

### 2.2 Stroke-Boundary Recording

**Definition:** One Record message per completed stroke cycle.

**Characteristics:**
- Each Record represents a complete stroke
- Stroke-specific metrics (drive time, force, angles) describe that specific stroke
- GPS position MAY be interpolated or repeated across strokes
- REQUIRED when in-stroke curve data is present

**Typical devices:** Indoor ergometers, instrumented oarlocks, on-water measurement systems with stroke detection, rowing-specific data loggers

### 2.3 GPS-Update Recording

**Definition:** Record messages generated at GPS position updates.

**Characteristics:**
- Records generated when GPS data is available (typically ~1 Hz, but irregular)
- Stroke metrics MAY be averaged, interpolated, or represent the most recent stroke
- GPS position is precisely measured at record time
- CANNOT include in-stroke curve data (curves require stroke boundaries)
- `total_cycles` field MAY repeat across multiple records (same stroke) or skip values (multiple strokes between GPS updates)

**Typical devices:** GPS-enabled sports watches, multi-sport fitness devices, smartphone applications with GPS tracking

### 2.4 Time-Sampled Recording

**Definition:** Record messages generated at a regular time interval, independent of stroke boundaries and GPS updates.

**Characteristics:**
- Records generated at a fixed rate chosen by the producer (for example 1 Hz or 10 Hz)
- Several records MAY fall within one stroke cycle; a record MAY also span more than one stroke at low sample rates
- The phase of the stroke at record time MAY be given by the **StrokeState** developer field (ID 96, §5.1)
- Stroke-specific metrics describe the most recent completed stroke
- CANNOT include in-stroke curve data (curves require stroke boundaries)

**Typical devices:** Ergometer monitors and apps that log at a fixed rate, research and coaching data loggers

### 2.5 RecordingStrategy Metadata Field

To indicate the recording approach, producers MAY include the **RecordingStrategy** developer field (ID 10, UINT8) on the **Session message**.

| Value | Name | Description |
|-------|------|-------------|
| 0 | Unknown | Recording strategy unspecified (consumers MUST handle all approaches) |
| 1 | StrokeBoundary | One Record per stroke cycle |
| 2 | GPSUpdate | Records at GPS position updates |
| 3 | TimeSampled | Records at a regular time interval |

**Message Type:** Session (one value per file)

**Base Type:** UINT8  
**Scale:** 1  
**Units:** (none)

When omitted or zero, consumers MUST NOT assume any particular strategy.

## 3. Consumer Requirements

### 3.1 Mandatory Requirements

Consumers MUST:

1. **Support all recording strategies** without requiring configuration
2. **Not assume 1:1 correspondence** between Record messages and strokes
3. **Not interpolate stroke-specific developer fields** between records (DriveLength, StrokeDriveTime, Catch, Finish, oarlock angles, etc.) - these describe discrete stroke events
4. **Detect stroke occurrences** by monitoring changes in the native `total_cycles` field:
   - When `total_cycles` changes between consecutive records, at least one stroke occurred
   - If change is >1, multiple strokes occurred but per-stroke data for intermediate strokes is unavailable
5. **Calculate stroke rate** from native `cadence256` when present, else from integer `cadence` — not from record message frequency
6. **Handle missing developer fields gracefully** (all developer fields are optional)

### 3.2 Recommended Requirements

Consumers SHOULD:

1. Read `RecordingStrategy` from Session message when present for optimization
2. Validate that in-stroke curve data only appears with `RecordingStrategy=StrokeBoundary` (or Unknown)

### 3.3 Optional Behaviors

Consumers MAY:

1. Optimize parsing based on `RecordingStrategy` value (e.g., skip stroke detection in StrokeBoundary files)
2. Issue warnings when encountering unexpected combinations (e.g., GPS-update with in-stroke data)

## 4. Native FIT Field Mappings

Producers SHOULD use these native FIT fields for rowing data:

| FIT Field | Type | Usage | Notes |
|-----------|------|-------|-------|
| timestamp | UINT32 | Record timestamp | Seconds since Garmin epoch (1989-12-31 UTC) |
| distance | UINT32 | Cumulative distance | Meters, scale 100 |
| cadence | UINT8 | Stroke rate (integer spm) | Strokes per minute, **rounded** to the nearest integer (not truncated); MUST be written when rate is known, for consumers that do not read `cadence256` |
| cadence256 | UINT16 | Stroke rate (fractional spm) | Strokes per minute, scale 256 (1/256 spm); SHOULD be written when fractional rate is known |
| heart_rate | UINT8 | Heart rate | Beats per minute, 0-255 |
| power | UINT16 | Average power | Watts, 0-65535 |
| enhanced_speed | UINT32 | Boat speed | Meters per second (scale 1000) |
| position_lat | SINT32 | Latitude | Semicircles |
| position_long | SINT32 | Longitude | Semicircles |
| total_cycles | UINT32 | Cumulative stroke count | MAY repeat (GPS-update) or increment by >1 |
| cycle_length16 | UINT16 | Stroke distance | Distance the boat travels during this stroke cycle, scale 100, max 655m. See notes |

**Notes:**

- **heart_rate**: Heart rate is written in the native `heart_rate` field on the same Record messages as the rowing data, whether it comes from the rowing device or from a separate sensor. It is not repeated as a developer field. When no heart rate sensor is connected, producers SHOULD omit the field rather than write 0. Session and Lap averages and maxima go in the native `avg_heart_rate` and `max_heart_rate` fields.
- **cycle_length16**: The distance the boat (or, on an ergometer, the virtual boat) travels during one stroke cycle, catch to catch. It is not the cumulative distance travelled, which is `distance`, and not the travel of the handle, which is DriveLength (§5.1).

### 4.1 Sessions, Laps and Intervals

How a workout is divided into Session, Lap and Split messages follows the FIT activity file conventions, see the [FIT activity file documentation](https://developer.garmin.com/fit/file-types/activity/) and the [encoding cookbook](https://developer.garmin.com/fit/cookbook/encoding-activity-files/). This standard adds two rules for rowing:

1. **Intervals are marked with intensity.** Producers SHOULD write each work and rest interval as its own Lap, and MUST set the native `intensity` field on every Lap they write (`active` for work, `rest` for rest; the full list is under WorkoutState in §5.1).
2. **Active laps add up to moving time.** Rest and pauses MUST NOT be included in a Lap with `intensity=active`, so that a consumer gets the moving time by summing `total_timer_time` over the active Laps.

A common convention for grouping laps into workouts and splits is expected in a later version.

## 5. Developer Field Specifications

### 5.1 Core Rowing Metrics (Record-Level)

| Field Name | ID | Base Type | Scale | Units | Definition | Typical Range |
|------------|----|-----------| ------|-------|------------|---------------|
| DriveLength | 0 | UINT16 | 1 | mm | Distance traveled by handle along longitudinal axis during drive phase | 1200-1500 mm |
| StrokeDriveTime | 1 | UINT16 | 1 | ms | Duration of drive phase | 300-600 ms |
| DragFactor | 2 | UINT16 | 1 | | Resistance setting (ergometer) | Device-specific |
| StrokeRecoveryTime | 3 | UINT16 | 1 | ms | Duration of recovery phase | 500-1500 ms |
| AverageDriveForce | 6 | UINT16 | 10 | N | Average force during drive phase | 200-600 N |
| PeakDriveForce | 7 | UINT16 | 10 | N | Peak force during drive phase | 400-1200 N |
| AverageBoatSpeed | 8 | UINT16 | 255 | m/s | Average boat speed during stroke | 3-6 m/s |
| WorkoutState | 9 | UINT8 | 1 | | Training intensity of the record | See WorkoutState values below |
| StrokeWork | 19 | UINT16 | 1 | J | Work done over full stroke cycle | 100-500 J |
| StrokeState | 96 | UINT8 | 1 | | Phase of the stroke at record time | See StrokeState values below |

**Notes:**

- **DriveLength**: For OTW rowing, projection of handle trajectory on longitudinal axis. For indoor, handle travel catch-to-finish. Stored in **millimeters** (scale 1, units mm) for 1 mm precision (v1.2; v1.1 used scale 100 with units m).
- **StrokeWork**: Energy over complete stroke cycle (not drive-only). Equivalent to average power × stroke period.
- **Stroke rate** is carried by the native `cadence` and `cadence256` fields (§4), not by a developer field. Producers MUST NOT write native `fractional_cadence`: common platforms ignore it, and `cadence256` carries the same information.

**WorkoutState values:**

WorkoutState uses the values of the native FIT `intensity` enum, so a producer can copy them from the lap and a consumer can interpret them the same way.

| Value | Name | Meaning |
|-------|------|---------|
| 0 | Active | Working |
| 1 | Rest | Stationary; no rowing |
| 2 | Warmup | Warm-up |
| 3 | Cooldown | Cool-down |
| 4 | Recovery | Light rowing between work intervals |
| 5 | Interval | Work interval of a structured workout |
| 6 | Other | None of the above |

**WorkoutState rules:**

- Producers SHOULD distinguish Rest from Recovery: during Recovery the athlete is still moving, and consumers SHOULD NOT hide data recorded during it.
- When a Lap message carries native `intensity`, producers SHOULD write the same value in WorkoutState on the records within that lap. If they disagree, consumers MUST use the Lap `intensity`.
- Values above 6 are reserved. Consumers SHOULD treat an unknown value as Other.

**StrokeState values:**

| Value | Name | Meaning |
|-------|------|---------|
| 0 | Unknown | Phase not determined |
| 1 | Waiting | Not rowing; waiting for the first stroke or after stopping |
| 2 | Drive | Drive phase, catch to finish |
| 3 | Dwell | Pause at the finish, before the recovery starts |
| 4 | Recovery | Recovery phase, finish back to catch |

**StrokeState rules:**

- StrokeState is meaningful only when `RecordingStrategy=TimeSampled`. Producers SHOULD NOT write it with other recording strategies, where each record describes a whole stroke or an arbitrary moment.
- Producers that do not distinguish Dwell MAY report it as Recovery.
- Values above 4 are reserved. Consumers SHOULD treat an unknown value as Unknown.

### 5.2 Oarlock Metrics (Single, Record-Level)

| Field Name | ID | Base Type | Scale | Units | Definition |
|------------|----|-----------| ------|-------|------------|
| Catch | 11 | SINT16 | 10 | deg | Oar angle at catch (0° = perpendicular to boat) |
| Finish | 12 | SINT16 | 10 | deg | Oar angle at finish (0° = perpendicular to boat) |
| Slip | 13 | SINT16 | 10 | deg | Oar slip angle (early blade entry) |
| Wash | 14 | SINT16 | 10 | deg | Wash angle (late blade exit) |
| PeakForceAngle | 15 | SINT16 | 10 | deg | Oar angle at peak force (0° = perpendicular to boat) |
| EffectiveLength | 16 | UINT16 | 1 | mm | Effective oar lever length (rigging) |
| PeakForcePositionNorm | 17 | UINT16 | 1 | | Normalized position of peak force along drive (0-10000) |
| PeakForcePositionAbs | 18 | UINT16 | 1 | mm | Absolute handle position at peak force |

**Notes:**

- **Oar angles** (Catch, Finish, PeakForceAngle) use the rowing convention: **0° = oar perpendicular to the boat's longitudinal axis**. Negative values indicate the catch direction (oar blade toward bow, handle toward stern); positive values indicate the finish direction (oar blade toward stern, handle toward bow). This is standard oarlock/gateforce sensor convention.
- Summary fields (Catch, Finish, etc.) serve as representative values when per-side data unavailable
- **PeakForcePositionNorm**: Value in range 0-10000 representing ten-thousandths (0 = catch, 10000 = end of drive)
- **PeakForceAngle** vs **PeakForcePosition**: Angle is for oar angle sensors (OTW); Position is for handle position sensors (indoor)

### 5.3 Dual Oarlock Metrics (Record-Level)

When both port and starboard oarlocks are present, per-side metrics MAY be included:

| Field Name | ID | Base Type | Scale | Units | Side |
|------------|----|-----------| ------|-------|------|
| CatchPort | 200 | SINT16 | 10 | deg | Port |
| CatchStarboard | 201 | SINT16 | 10 | deg | Starboard |
| FinishPort | 202 | SINT16 | 10 | deg | Port |
| FinishStarboard | 203 | SINT16 | 10 | deg | Starboard |
| SlipPort | 204 | SINT16 | 10 | deg | Port |
| SlipStarboard | 205 | SINT16 | 10 | deg | Starboard |
| WashPort | 206 | SINT16 | 10 | deg | Port |
| WashStarboard | 207 | SINT16 | 10 | deg | Starboard |
| PeakForceAnglePort | 208 | SINT16 | 10 | deg | Port |
| PeakForceAngleStarboard | 209 | SINT16 | 10 | deg | Starboard |
| EffectiveLengthPort | 210 | UINT16 | 1 | mm | Port |
| EffectiveLengthStarboard | 211 | UINT16 | 1 | mm | Starboard |

**Per-side field rules:**

- Per-side fields SHOULD only be included when both port and starboard data are available
- When per-side fields are present, summary fields (IDs 11-16) SHOULD contain the average of port and starboard values
- When only one side is available, summary fields SHOULD contain that side's value
- Consumers implementing only partial support MAY ignore per-side fields and use summary fields

### 5.4 Oarlock Settings (Session-Level)

The force thresholds an oarlock system uses to determine Slip and Wash, and so the effective part of the stroke, are device settings. They do not change during a session and are written once, on the **Session message**.

| Field Name | ID | Base Type | Scale | Units | Definition | Typical Range |
|------------|----|-----------| ------|-------|------------|---------------|
| SlipThreshold | 94 | UINT16 | 1 | N | Handle force above which the blade counts as entered; Slip (ID 13) is measured from the catch to this point | 50-150 N |
| WashThreshold | 95 | UINT16 | 1 | N | Handle force below which the blade counts as exited; Wash (ID 14) is measured from this point to the finish | 50-150 N |

**Rules:**

- Producers SHOULD write these fields when they write Slip, Wash or EffectiveLength, so a consumer can tell whether values from different systems are comparable
- When absent, consumers MUST NOT assume a threshold

## 6. In-Stroke Curve Data

### 6.1 Overview

In-stroke curve data describes how a quantity develops through a single stroke. This standard puts exactly **one** curve in the FIT file, the **handle force curve** (§6.4). Every platform can present it meaningfully, whatever equipment recorded it.

All other curves, such as boat acceleration, seat position and oar angular velocity, and any curve at a higher resolution than §6.5 allows, belong in the companion JSON file (§6.6). Their meaning depends on the exact equipment that measured them, and they would quickly grow the FIT file past what is practical to exchange.

**Constraint:** In-stroke curve data MUST only appear when `RecordingStrategy=StrokeBoundary`, or when `RecordingStrategy` is absent or Unknown and each Record carrying a curve describes exactly one stroke, as curves require stroke boundaries for interpretation.

### 6.2 Field ID Allocation

| ID | Field |
|----|-------|
| 60 | HandleForceCurve (§6.4) |
| 90-92 | Axis metadata (§6.3) |

IDs 20-59 and 61-89 are reserved for future curve data. Curve field IDs are fixed; producers MUST NOT allocate them dynamically.

### 6.3 Axis Metadata Fields (Record-Level)

These fields define the X-axis interpretation for curve data on each Record:

| Field Name | ID | Base Type | Scale | Units | Definition |
|------------|----|-----------| ------|-------|------------|
| InstrokeAbscissaType | 90 | UINT8 | 1 | | X-axis semantics (enum) |
| InstrokeSampleInterval | 91 | UINT16 | 1 | (varies) | Sample spacing (interpretation depends on Type) |
| InstrokePointCount | 92 | UINT8 | 1 | | Number of points in curve arrays |

**InstrokeAbscissaType values:**

| Value | Name | InstrokeSampleInterval Meaning |
|-------|------|--------------------------------|
| 0 | UNKNOWN | Not specified. Producers MUST NOT write this value (see rules) |
| 1 | TIME_UNIFORM_MS | Milliseconds between samples |
| 2 | HANDLE_DISTANCE_UNIFORM_M | Millimeters between uniform samples along handle travel |
| 3 | OAR_ANGLE_UNIFORM_DEG | Degrees between samples (scale as documented) |
| 4 | NORMALIZED_DRIVE_0_1 | Dimensionless step size (0-1 range) |

**Rules:**

- Axis metadata fields MUST appear together on each Record containing curve data
- Producers MUST declare the X-axis explicitly: InstrokeAbscissaType MUST NOT be 0 (UNKNOWN). Consumers that encounter 0 in older files SHOULD treat the curve as shape-only, for pattern analysis and not absolute plotting
- For Type=TIME_UNIFORM_MS with known drive time: `InstrokeSampleInterval = drive_time_ms / (point_count - 1)`
- For Type=HANDLE_DISTANCE_UNIFORM_M with known drive length: `InstrokeSampleInterval = DriveLength / (point_count - 1)`; sample index `k` maps to handle position `k × InstrokeSampleInterval` from the catch
- For Type=OAR_ANGLE_UNIFORM_DEG: Domain is [Catch, Finish] angles (from fields 11-12)
- Producers SHOULD strive for consistency between axis metadata and stroke scalars, but consumers SHOULD NOT enforce strict validation

### 6.4 HandleForceCurve

| Field Name | ID | Base Type | Scale | Units | Definition |
|------------|----|-----------| ------|-------|------------|
| HandleForceCurve | 60 | UINT16 array | 10 | N | Force on the handle through the drive, sampled uniformly along the declared abscissa |

**Recommended abscissa:** HANDLE_DISTANCE_UNIFORM_M on an ergometer, TIME_UNIFORM_MS on the water.

Curve samples are **uniformly spaced** along the declared abscissa (fields 90-92). Non-uniform source data MUST be resampled before export. The unresampled data MAY additionally be stored in the companion JSON file.

The curve is produced on a best-effort basis: a producer writes the force curve its equipment measures, at the resolution it can, within the limits of §6.5.

### 6.5 Curve Array Format

Curve data MUST be encoded as **UINT16** arrays (developer fields with array size > 1):

- **Maximum points per curve:** 127 (FIT limit: 255 bytes / 2 bytes per UINT16)
- **Encoding:** Unsigned 16-bit integers in range [0, 65535]
- **Data representation:** Handle force is non-negative; negative measured values MUST be written as 0
- **Scale factor:** As declared in §6.4 and in the developer field description. Values are clipped to [0, 65535] after scaling.

### 6.6 Companion Files

Data that does not fit the FIT file MAY be shipped in a companion `.json` file. This standard does not define its contents or structure; that is up to the producer. The companion file is optional: a FIT file MUST be complete and conforming without it, and consumers MAY ignore it.

## 8. Data Quality and Validation

### 8.1 Value Ranges

Producers MUST NOT exceed FIT type limits (the value multiplied by its scale must fit the base type). Producers SHOULD NOT clamp valid measurements to “typical” ranges.

**Typical ranges** (informative, not encoding limits):

- Force: 0-2000 N typical maximum
- DriveLength: 1200-1500 mm for full strokes; arms-only strokes may be ~300 mm
- Angles: -180 to +180 degrees
- Stroke rate: 10-40 spm typical; sprint work may exceed 60 spm (up to ~100 spm)

Consumers MAY warn on values outside typical ranges but MUST accept physically valid data within type limits.

### 8.2 Missing Data

- Missing or unavailable fields SHOULD be omitted from the file
- Producers MUST NOT write placeholder values (e.g., -1, 999) for missing data; they omit the field instead
- Zero values SHOULD indicate actual measurements of zero (not missing data)

### 8.3 Consistency

While strict validation is not enforced, producers SHOULD maintain internal consistency:

- Drive + recovery time ≈ stroke period (60000 / stroke rate, in ms)
- In-stroke axis metadata consistent with stroke scalars
- Summary oarlock fields = average of per-side fields (when both present)

## 9. Field Registry

### 9.1 Reserved ID Ranges

A developer field number is a single byte (`field_definition_number`, UINT8), and 255 is the FIT invalid value for that type. Field IDs therefore range from 0 to 254. This is a hard limit of the FIT format, not an allocation choice of this standard.

| Range | Purpose | Status |
|-------|---------|--------|
| 0-19 | Core rowing metrics | Assigned |
| 20-59 | Reserved for future curve data | Available |
| 60 | HandleForceCurve | Assigned |
| 61-89 | Reserved for future curve data | Available |
| 90-92 | In-stroke axis metadata | Assigned |
| 93-199 | Extended standard fields | SlipThreshold (94), WashThreshold (95) and StrokeState (96) assigned; remainder available |
| 200-211 | Dual oarlock per-side | Assigned |
| 212-254 | Reserved for future extensions | Available |

## Appendix A: Terminology

**Stroke Cycle:** Complete rowing motion from catch through drive and recovery back to catch.

**Drive Phase:** Portion of stroke where power is applied (handle moving toward finish).

**Recovery Phase:** Portion of stroke returning to catch position (no power).

**Catch:** Position/angle at start of drive phase (blade entry for OTW).

**Finish:** Position/angle at end of drive phase (blade exit for OTW).

**Slip:** Angular difference between ideal and actual blade entry (early entry).

**Wash:** Angular difference between ideal and actual blade exit (late exit).

**Oar Angle:** Angle of oar relative to boat's longitudinal axis (0° = perpendicular).

**Effective Length:** Horizontal distance from oarlock pin to handle (rigging metric).

**Drive Length:** Actual distance handle travels during drive phase.

**Stroke Distance:** Distance boat travels during one complete stroke cycle.

**OTW:** On-the-water (as opposed to ergometer/indoor).

## Appendix B: Acknowledgments

This standard builds upon work by the rowing data community, including contributions from:

- Device manufacturers (Concept2, Nielsen-Kellerman, Quiske, RowPerfect)
- Software platforms (Intervals.icu, OpenRowingMonitor)
- Individual developers and researchers

## Appendix C: Contact and Governance

For questions, clarifications, or proposed amendments to this standard:

- **Issue tracker:** https://github.com/MoveLab-Studio/rowing-data-standard/issues
- **Proposals:** https://github.com/MoveLab-Studio/rowing-data-standard/tree/main/proposals

Proposed changes SHOULD be discussed with stakeholders before implementation to ensure ecosystem compatibility.

---

**End of Standard**
