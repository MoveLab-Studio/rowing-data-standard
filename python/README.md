# rowing-data (Python)

A **draft** Python implementation of the [Rowing Data Standard](../spec/FIT_STANDARD.md).

This package implements **Draft v0.1**, which is not ratified. Field IDs, scales
and units may still change. Do not treat this library as a stable contract for
shipping products.

Current scope is conformance **Levels 1–2**: native FIT Record/Session fields
plus core rowing developer fields under application UUID
`89e86158-6d47-5c98-9d46-7d29437f27b9`.

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
issues = validate(session)
```

## Development

```text
cd python
pytest
ruff check src tests
```
