# Rowing Data Standard

An open, vendor-neutral standard for exchanging rowing session data between
devices, apps and analysis platforms — built on **Garmin FIT developer fields**
under a single registered namespace, covering both indoor and on-water rowing.

---

## ⚠️ Nothing here is definitive

**This repository is a working draft, not a published standard.** Everything in
it is provisional and open to change:

| | Status |
|---|---|
| The specification text | **Draft v0.1** — not ratified |
| Field IDs, scales and units | Proposed; may be renumbered or redefined |
| Compliance levels | Proposed; the tier boundaries are still under discussion |
| Governance | **Undecided** — a small named editorial team, an open-source project, or open participation with named editors. The group's first decision |
| Licensing | **Undecided** — no licence is granted yet, see [Licensing](#licensing) |
| Where this repository ultimately lives | In progress — RITA adoption under active discussion, see [Hosting](#hosting-and-neutrality) |

Do not build a shipping product against this text and expect it to hold. If you
are implementing today, watch this repository for the first ratified release —
a tagged release is a ratified version, `main` is not.

Nothing in this repository commits any company to adopting the standard, and no
statement here should be read as an endorsement on behalf of any organisation.

---

## What this standard is

- **A convention, not a new file format.** It defines rowing-specific developer
  fields *inside* standard Garmin FIT files, under one registered application
  UUID (`89e86158-6d47-5c98-9d46-7d29437f27b9`) so that field IDs cannot collide
  between vendors. Any existing FIT reader keeps working; readers that know the
  standard get rowing detail.
- **Session data, recorded after the fact.** The scope is the file a device or
  app writes when a session is finished — distance, stroke metrics, oarlock
  angles, in-stroke force curves. Everything a consumer needs to reconstruct and
  analyse a completed row.
- **Tiered, so partial support is still useful.** Four compliance levels let a
  simple GPS watch and an instrumented racing shell both claim conformance at
  the depth they actually measure.

## What it is **not**

- **Not a real-time or transmission protocol.** How a device streams to a phone
  or display over Bluetooth or USB is explicitly out of scope. That is a harder
  problem with more commercial sensitivity, and mixing it in would stall the
  easy win. It may become separate future work; it is not this document.
- **Not a device certification or test programme.** No badge, no audit, no fee.
- **Not owned by any single vendor.** See below.

## Repository layout

```
spec/FIT_STANDARD.md      The specification draft — the actual deliverable
registry/field-ids.md     Registry of every allocated developer field ID
proposals/                Substantive change proposals, one file each
python/                   Draft v0.1 Python library (Levels 1–2 FIT read/write)
```

A small Python package lives in [`python/`](python/README.md). It implements
**Draft v0.1** Levels 1–2: native FIT fields, core developer fields 0–9 and 19,
StrokeRate 93, and Session RecordingStrategy 10. It is not a certified or
ratified implementation, and it does not implement oarlock, dual-oarlock, or
in-stroke curves. Install with `pip install -e "./python[dev]"` (Python 3.11+).

## How to take part

1. **Read** [`spec/FIT_STANDARD.md`](spec/FIT_STANDARD.md).
2. **Open an issue** for a question, an ambiguity, or an error in the text.
   Ambiguity is a defect: if you had to guess to implement something, so will
   everyone else, and two implementations will guess differently.
3. **Open a [proposal](proposals/README.md)** instead for a new field, a changed
   type, scale or unit, or anything that could invalidate an existing file.
4. **Bring implementation experience.** "We tried to write this field and our
   device can't produce it at that precision" is worth more than any amount of
   discussion. Real files and real constraints settle arguments — a change to the
   specification is not considered proven until it has been demonstrated in a
   working implementation, and a sample FIT file is the best evidence there is.

Participation is open. You do not need to be a company, a RITA member, or
invited by anyone to file an issue or a proposal.

State your affiliation when you argue for something that favours it. Everyone
here has a commercial position in rowing hardware or software — that is the
point, not a problem. "Our device already does it this way" is a legitimate and
often decisive argument; it just needs saying out loud.

## Using AI

**Using an AI assistant here is fine.** Use whatever tools get the work done.

What does not change is that you are the author. A pull request or a proposal is
your argument, and you have to be able to defend it on the thread without going
back to the model. If you cannot say why a field is scaled the way it is, the
review has nowhere to go — and reviewer attention is the scarcest thing this
project has.

Two failure modes are worth naming, because both cost something specific here:

- **Invented specifics.** Models are fluent about field IDs, scales, units and
  section numbers, and will cheerfully produce ones that do not exist. Check
  anything concrete against [`registry/field-ids.md`](registry/field-ids.md) and
  the specification text itself before you send it.
- **Volume.** A generated proposal is long, confident and evenly weighted, which
  reads like thoroughness and reviews like noise. Say the thing in a paragraph.

The existing rules do the rest of the work. Anything that changes what goes into
a file still has to be demonstrated in a working implementation — generated code
that round-trips a real FIT file is evidence; generated prose describing it is
not.

## Licensing

**Unresolved, and it affects contributors.** There is deliberately no `LICENSE`
file yet: the v0.1 text originates with Sander Roosendaal, and relicensing
someone's document is not a call the repository host makes quietly.

Until it is settled, nobody has a granted right to redistribute or translate the
text, and no contributor licence is being asked for or granted. That is tolerable
for a draft among participants and not tolerable for a published standard, so it
needs deciding early. If it is a problem for you or your employer, say so on an
issue and hold your contribution.

## Hosting and neutrality

This repository sits under the **MoveLab Studio** GitHub organisation as a
practical placeholder — it needed an address with issues, tags and releases
faster than a new organisation could be agreed on. MoveLab does not own the
standard, and hosting carries no editorial privilege.

The intent is to move it to a neutral home, and discussions with the
[Rowing Industry Trade Association (RITA)](https://rowingindustry.com) about
adopting the standard are actively underway. RITA is the intended home.

The ask of RITA is deliberately minimal: lend the standard its name and host the
discussion at its meetings. **No budget, no secretariat and no administrative
burden** are being requested. Adoption remains a decision for RITA's members and
board to take in their own time, and nothing here presumes the outcome or speaks
on RITA's behalf.

Decide this before the first tagged release — implementers will start citing the
URL, and moving it afterwards breaks links and citations.

## Who is working on this

Listed as initial participants in getting the draft moving:

| | |
|---|---|
| Sander Roosendaal | Rowsandall — original author of the draft |
| Michael Naughton | Nielsen-Kellerman |
| Tony Andrews | CrewNerd |
| Joris Blaak | MoveLab Studio — repository maintenance |
| Jaap van Ekris | OpenRowingMonitor — initial FIT fields and type definitions |

This list describes who has been active so far, not a closed membership or an
appointed committee. It is wrong the moment someone else shows up — corrections
and additions by issue or pull request are welcome.

## Prior art and acknowledgements

The draft builds on years of community work on rowing data, including from
device manufacturers (Concept2, Nielsen-Kellerman, Quiske, RowPerfect) and
software platforms (Intervals.icu, OpenRowingMonitor), and on the accumulated
practice of the people who have been quietly parsing each other's files for a
decade. Full acknowledgements are in Appendix B of the specification.
