<p align="center">
  <a href="https://rowingindustry.com">
    <img src="assets/rita-logo.png" alt="RITA — Rowing Industry Trade Association" width="320">
  </a>
</p>

<h1 align="center">Rowing Data Standard</h1>

<p align="center">
  An open, vendor-neutral standard for rowing session data in Garmin FIT files —<br>
  indoor and on the water, from a GPS watch to an instrumented racing shell.
</p>

<p align="center">
  <a href="spec/FIT_STANDARD.md"><img alt="Specification: 1.0-RC" src="https://img.shields.io/badge/spec-1.0--RC-orange"></a>
  <a href="LICENSE.md"><img alt="Spec licence: CC BY 4.0" src="https://img.shields.io/badge/spec%20licence-CC%20BY%204.0-lightgrey"></a>
  <a href="LICENSE.md"><img alt="Code licence: Apache 2.0" src="https://img.shields.io/badge/code%20licence-Apache%202.0-blue"></a>
  <a href="https://github.com/Rowing-Industry-Trade-Association/rowing-data-standard/actions/workflows/python.yml"><img alt="Python library CI" src="https://github.com/Rowing-Industry-Trade-Association/rowing-data-standard/actions/workflows/python.yml/badge.svg"></a>
</p>

<p align="center">
  <a href="spec/FIT_STANDARD.md"><b>Read the specification</b></a> ·
  <a href="registry/field-ids.md">Field registry</a> ·
  <a href="CONTRIBUTING.md">Contribute</a> ·
  <a href="GOVERNANCE.md">Governance</a>
</p>

---

> [!IMPORTANT]
> **1.0 release candidate.** This is the candidate for the first version of the
> standard RITA publishes. Build against it and report what you find: changes
> before the final 1.0 are limited to what implementation shows is needed, and
> each is listed in the 1.0 release notes. Cite a tagged release, not `main`.

## Why

Every rowing device and app records the same stroke — catch, drive, finish,
recovery — and for years each has written it down differently. Moving a session
from an erg, an oarlock sensor or a phone into an analysis platform has meant
someone reverse-engineering someone else's file.

The Rowing Data Standard fixes the vocabulary once. It is maintained by the
[Rowing Industry Trade Association](https://rowingindustry.com), free to use,
and open to recommendations from anyone in the industry.

## What it is

- **A convention, not a new file format.** It defines rowing-specific developer
  fields *inside* standard Garmin FIT files, under one registered application
  UUID (`89e86158-6d47-5c98-9d46-7d29437f27b9`), so field IDs cannot collide
  between vendors. Any existing FIT reader keeps working; readers that know the
  standard get the rowing detail.
- **Session data, recorded after the fact.** The scope is the file a device or
  app writes when a session is finished: distance, stroke metrics, oarlock
  angles, in-stroke force curves — everything a consumer needs to reconstruct
  and analyse a completed row.
- **Useful with partial support.** Producers write the fields they actually
  measure, so a simple GPS watch and an instrumented racing shell can both
  conform.

## What it is not

- **Not a real-time or transmission protocol.** How a device streams to a phone
  or display over Bluetooth or USB is out of scope.
- **Not a certification programme.** No badge, no audit, no fee.
- **Not a change to FIT.** Every revision stays interoperable with the FIT
  protocol, and the FIT protocol and SDK remain Garmin's. Implementers obtain
  Garmin's FIT Protocol License directly.

## Repository layout

| Path | What it is |
|---|---|
| [`spec/FIT_STANDARD.md`](spec/FIT_STANDARD.md) | The specification — the actual deliverable |
| [`registry/field-ids.md`](registry/field-ids.md) | Every allocated developer field ID |
| [`proposals/`](proposals/README.md) | Substantive change proposals, one file each |
| [`python/`](python/README.md) | An example Python library that reads and writes conforming FIT files |

### Python library

[`python/`](python/README.md) implements part of 1.0-RC: native FIT fields, core
developer fields 0–9 and 19, StrokeRate 93, and Session RecordingStrategy 10.
It does not yet implement oarlock, dual-oarlock or in-stroke curves.

```sh
pip install -e "./python[dev]"   # Python 3.11+
```

## Contributing

Anyone can take part — you do not need to be a RITA member. Open an
[issue](https://github.com/Rowing-Industry-Trade-Association/rowing-data-standard/issues)
for a question, an ambiguity or an error; open a [proposal](proposals/README.md)
for a new or changed field. Implementation reports and real sample files are the
most valuable things you can bring.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before your first pull request.

## Governance

The standard is maintained by RITA's **Data Standards Working Group (DSWG)**, a
chair and three to five voting members from RITA member companies, chartered by
the RITA Board.

| Chair | Voting members | Subject matter experts |
|---|---|---|
| Michael Naughton (Nielsen-Kellerman) | Tony Andrews (CrewNerd)<br>Joris Blaak (MoveLab Studio)<br>Ryan Farrell (Concept2) | Scott Hamilton (Concept2)<br>Sander Roosendaal (Rowsandall)<br>Nils Steffensen (Nielsen-Kellerman)<br>Jaap van Ekris (OpenRowingMonitor) |

- Recommendations come in through this repository — every one is logged and
  gets a recorded outcome: adopted, deferred, or declined with a reason.
- The DSWG publishes **two releases a year**, each with release notes and the
  FIT SDK version it was validated against.
- Breaking changes are announced at least one release before they take effect.

The full charter, and how this repository carries it out, is in
[GOVERNANCE.md](GOVERNANCE.md).

## Licence

| | |
|---|---|
| Specification, field registry, guidance and examples | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| Code, schemas, templates and sample data | [Apache 2.0](LICENSES/Apache-2.0.txt) |

Contributors also commit to royalty-free licensing of any patent claim that
implementing the standard cannot avoid. [`LICENSE.md`](LICENSE.md) has the full
terms and the Garmin FIT notice.

No fee, royalty or RITA membership is needed to use or implement the standard.
You may fork and adapt the text, but a modified version may not be presented as
the official standard or as endorsed by RITA.

## Acknowledgements

The standard grew out of the rowing FIT developer field specification written
by **Sander Roosendaal** (Rowsandall). His work is the basis of its technical
content, and this standard would not exist without it.

It builds on years of community work on rowing data, from device manufacturers
(Concept2, Nielsen-Kellerman, Quiske, RowPerfect), software platforms
(Intervals.icu, OpenRowingMonitor), and the people who have been quietly parsing
each other's files for a decade. The working group that brought it to 1.0 is
listed under [Governance](#governance). Full
acknowledgements are in Appendix B of the specification.
