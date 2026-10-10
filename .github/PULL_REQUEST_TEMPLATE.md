## What this changes

Briefly, in terms of what a file or an implementation looks like afterwards.

## Class of change

Tick one. If you are unsure between two, tick the heavier.

- [ ] **Editorial** — typo, formatting, or wording that changes no requirement
- [ ] **Substantive** — new or changed field, changed conformance requirement.
      *Requires a linked proposal.*
- [ ] **Structural** — governance, licensing, repository scope
- [ ] Repository plumbing only — templates, CI, docs about the process

## Links

- Issue:
- Proposal:

## Compatibility

**Does any existing conforming file become non-conforming, or change meaning?**

- [ ] No
- [ ] Yes — described below

Existing files in the wild are the main constraint on this project, and a change
that quietly invalidates them is the one failure mode with no remedy. If yes,
say what breaks and for whom.

## Checklist

- [ ] One logical change — no unrelated fixes bundled in
- [ ] Paragraphs I did not change are not reflowed (keeps the diff readable)
- [ ] [`registry/field-ids.md`](../registry/field-ids.md) updated, if any field ID
      is touched
- [ ] Linked issue closed or updated, if this resolves one
- [ ] RFC 2119 keywords are deliberate, and state producer and consumer
      obligations separately where they differ
- [ ] Version number in `spec/FIT_STANDARD.md` **not** changed — versions are
      assigned at release
- [ ] Implementation evidence linked, for anything that changes file contents
