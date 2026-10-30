# rowing-data (Python)

[![Python sample](https://github.com/Rowing-Industry-Trade-Association/rowing-data-standard/actions/workflows/python.yml/badge.svg)](https://github.com/Rowing-Industry-Trade-Association/rowing-data-standard/actions/workflows/python.yml)

An example Python implementation of the [Rowing Data Standard](../spec/FIT_STANDARD.md).

This package implements part of **1.0-RC**, the release candidate for 1.0 (see
[Scope](#scope)). The standard may still change before the final 1.0.

## Scope

Implements 1.0-RC **§4 native FIT fields**, **§5.1 core metrics** (IDs 0–9
and 19), and Session **RecordingStrategy** (ID 10), under
application UUID `89e86158-6d47-5c98-9d46-7d29437f27b9`. Producers write
protocol version 1 in `DeveloperDataId.application_version`. A file that omits
it is still read.

Stroke rate is native `cadence256` (scale 256) plus `cadence`, rounded to the
nearest integer. This library does not write developer field `StrokeRate` (93)
or native `fractional_cadence`.

`RecordingStrategy` includes TimeSampled (3). `StrokeState` (ID 96) is written
only for that strategy: 0 Unknown, 1 Waiting, 2 Drive, 3 Dwell, 4 Recovery.

Force is `AverageDriveForce` (6) and `PeakDriveForce` (7), in newtons. Fields 4
and 5 are not part of this sample.

`SlipThreshold` (94) and `WashThreshold` (95) are optional session fields, in
newtons, written when set.

**Not implemented** (later work, or blocked on defects in the text):

- Oarlock summary fields 11–18
- Dual-oarlock 200–211
- In-stroke axis metadata 90–92, curve arrays, curve summaries, `.instroke.json`

`WorkoutState` (ID 9) uses the FIT intensity values: 0 Active, 1 Rest, 2 Warmup,
3 Cooldown, 4 Recovery, 5 Interval, 6 Other. An unknown value is read as Other.
When a lap's `intensity` disagrees with a record, the lap wins. Every lap
written here sets native `intensity`. A session with no laps is written as one
active lap. `RowingSession.moving_time_s()` sums timer time over every lap except
`Rest`, and `validate` warns about rowing data inside a rest lap (light rowing is
`Recovery`).

`AverageBoatSpeed` (ID 8) uses scale 100 (0.01 m/s). When a file declares the
same units and a different scale, the reader uses the scale in the file. Scale
is a UINT8 and 255 is its invalid value, so an older scale of 255 does not
surface; that missing scale is still read as 255 m/s steps.

Heart rate is the native `heart_rate` field. When no sensor is connected, omit
it rather than write 0. `cycle_length16` is the distance the boat travels in
one stroke cycle, not cumulative `distance` and not handle travel (DriveLength).

**Older files:** DriveLength at scale 100 / metres. This reader decodes
with **the standard's units (mm)** and records a `field_scale` warning. It does not
silently convert old files into millimetres.

Developer fields are interpreted only when they use the standard application
UUID.

## Install

From the repository root:

```text
pip install -e "./python[dev]"
```

Use Python 3.11 or later.

## Example

```python
from pathlib import Path
from rowing_data import STANDARD_VERSION, read_fit, validate, write_fit

assert STANDARD_VERSION == "1.0-RC"
session = read_fit("workout.fit")
write_fit(session, Path("copy.fit"))
issues = validate(session)  # includes warnings captured during read_fit
```

## Development

```text
cd python
pytest
ruff check src tests
```

CI runs exactly these two commands on Python 3.11, 3.12 and 3.13
([`.github/workflows/python.yml`](../.github/workflows/python.yml)), and only
when something under `python/` changes. The interop test against the
`rowingdata` golden FIT file skips on CI, since that file is not in this
repository.

## Licence

[Apache License 2.0](../LICENSES/Apache-2.0.txt), test fixtures included. See
[`LICENSE.md`](../LICENSE.md). The FIT protocol and SDK are Garmin's; using this
library does not grant rights to FIT.
