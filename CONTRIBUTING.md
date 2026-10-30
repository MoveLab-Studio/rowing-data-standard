# Contributing

Participation is open. You do not need to be a company, a RITA member, or
invited by anyone to file an issue or a proposal. Decisions on what goes into a
release are made by RITA's Data Standards Working Group — see
[GOVERNANCE.md](GOVERNANCE.md).

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

Typos, formatting and wording that changes no requirement can go straight to a
pull request.

## State your affiliation

State your affiliation when you argue for something that favours it. Everyone
here has a commercial position in rowing hardware or software — that is the
point, not a problem. "Our device already does it this way" is a legitimate and
often decisive argument; it just needs saying out loud.

Discussion follows RITA's antitrust guidelines: talk about the file format, not
prices, costs, customers or launch plans. See
[GOVERNANCE.md](GOVERNANCE.md#antitrust).

## Licensing of contributions

By opening an issue, a proposal or a pull request, you agree that what you
submit may be included in the standard under the licence of the path it lands
in: CC BY 4.0 for the specification and registry, Apache 2.0 for code,
schemas and sample data. You also agree to the patent
commitment. [`LICENSE.md`](LICENSE.md) has the full terms. There is no separate
contributor licence agreement to sign.

If your employer needs to approve that, get the approval before you submit.

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

## Working on the Python library

```sh
cd python
pip install -e ".[dev]"   # Python 3.11+
pytest
ruff check src tests
```

See [`python/README.md`](python/README.md) for what the library covers.
