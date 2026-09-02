# rowing-data (Python)

[![Python sample](https://github.com/MoveLab-Studio/rowing-data-standard/actions/workflows/python.yml/badge.svg)](https://github.com/MoveLab-Studio/rowing-data-standard/actions/workflows/python.yml)

A **draft** Python implementation of the [Rowing Data Standard](../spec/FIT_STANDARD.md).

This package implements **Draft v0.1**, which is not ratified. Field IDs, scales
and units may still change. Do not treat this library as a stable contract for
shipping products.

## Scope

Implements Draft v0.1 **§4 native FIT fields**, **§5.1 core metrics** (IDs 0–9,
19, and **StrokeRate 93**), and Session **RecordingStrategy** (ID 10), under
application UUID `89e86158-6d47-5c98-9d46-7d29437f27b9`.

That is conformance **Levels 1–2** as in §7, plus StrokeRate (93). §7’s Level 2
bullet list omits 93; §5.1 still requires native `cadence` when rate is known,
so this library writes and reads ID 93.

**Not implemented** (Level 3–4, or blocked on draft defects):

- Oarlock summary fields 11–18
- Dual-oarlock 200–211 (210/211 have a metres vs millimetres conflict in the draft)
- In-stroke axis metadata 90–92, curve arrays, curve summaries, `.instroke.json`
- WorkoutState enumeration (the draft has no value table; ID 9 is an opaque UINT8)

**Pre-v1.2 files:** DriveLength used scale 100 / metres. This reader decodes
with **v0.1 units (mm)** and records a `field_scale` warning. It does not
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

assert STANDARD_VERSION == "0.1"
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
