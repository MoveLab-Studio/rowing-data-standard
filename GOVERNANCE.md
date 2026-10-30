# Governance

The Rowing Data Standard is maintained by the **Data Standards Working Group
(DSWG)** of the [Rowing Industry Trade Association (RITA)](https://rowingindustry.com).
The first part of this document is the DSWG charter. The second describes how
this repository carries it out.

The charter refers to the standard as the "RITA Data Standard". Whether to
rename it is for the DSWG to decide; until then it keeps its name.

If the two ever disagree, the charter wins, and this file is the thing to fix.

---

## Part 1 — RITA Data Standards Working Group Charter

*Streamlined version, 23 October 2026. Chair: Michael Naughton.*

The Data Standards Working Group (DSWG) is a small team of a chair and voting
members that publishes two revisions of the RITA Data Standard each year,
drawing on recommendations from anyone in the industry.

### 1. Purpose and authority

The DSWG keeps the RITA Data Standard accurate, stable and useful. It is
chartered by the RITA Board, decides revisions itself, and reports to the Board
after each release. Meetings follow RITA's antitrust guidelines.

### 2. Composition and decisions

- **Size.** 4 to 6 members in total: a chair and 3 to 5 voting members.
- **Chair.** Leads the group, sets priorities, votes, and reports to the Board.
- **Voting members.** Review recommendations and vote on revisions.
- **Subject matter experts.** The DSWG may bring in subject matter experts at
  any time for discussion and collaboration. SMEs do not have voting rights.
- **Quorum.** A simple majority of members (more than 50%).
- **Decisions.** Consensus where possible; otherwise a majority of members
  present. Votes may be taken in person or electronically.

### 3. Recommendations

- Anyone may submit a recommendation to revise the standard, regardless of
  their company's RITA membership status, at any time, through one channel
  maintained by the DSWG.
- Each recommendation is logged and gets a recorded outcome: adopted, deferred,
  or declined with a brief reason.
- The chair sets which recommendations are considered for each release.

### 4. Revisions

- **Two releases per year.** The DSWG publishes a revised standard twice a
  year, each with release notes listing what changed and the recommendations
  addressed.
- **Notice for breaking changes.** Changes that would break existing data or
  systems are announced at least one release before they take effect.
- **Urgent fixes.** Errors that block data exchange may be corrected between
  releases by a DSWG vote.

### 5. Open standard

The RITA Data Standard is an open extension of Garmin's Flexible and
Interoperable Data Transfer (FIT) protocol. RITA's extension is free for anyone
to read, use, implement and redistribute; the FIT protocol itself remains
Garmin's and is used under Garmin's FIT license.

- **Scope of the open license.** RITA's own content, including rowing-specific
  field definitions, code lists, guidance and examples, is published under the
  Creative Commons Attribution 4.0 International License (CC BY 4.0).
  RITA-authored machine-readable files, such as schemas, templates and sample
  data, are published under the Apache License 2.0. The standard references
  Garmin's FIT documentation and does not reproduce or redistribute the FIT SDK
  or protocol.
- **FIT license.** Each implementer obtains and complies with Garmin's FIT
  Protocol License directly. Nothing in the RITA Data Standard grants rights to
  FIT.
- **Compatibility.** Every revision must remain interoperable with the FIT
  protocol and must not deviate from it. Rowing data is carried in FIT
  developer data fields unless Garmin adopts it into the FIT profile. Each
  release states the FIT protocol and SDK version it was validated against.
- **Format.** The standard is published in open, plain-text formats (such as
  Markdown, CSV and JSON) in a public repository, with every version and its
  change log kept available.
- **No fees.** No fee, royalty or RITA membership is required to use or
  implement the standard.
- **Contributions.** By submitting a recommendation, contributors agree that it
  may be included in the standard under these same licenses.
- **Name.** "RITA" and "RITA Data Standard" remain RITA's names; modified
  versions may not be presented as the official standard.

### 6. Member selection and terms

- **Eligibility.** All working group members, including the chair, must be
  employees of RITA member companies.
- **Chair.** Appointed by the RITA Board.
- **Voting members.** Nominated by the chair from an open call to RITA members
  and approved by the Board.
- **Balance.** Members should represent a mix of manufacturers, retailers and
  data users, with no more than one voting member per company.
- **Terms.** 2 years, renewable. Vacancies are filled the same way for the rest
  of the term.

This framework may be amended by a DSWG majority vote with Board approval.

---

## Part 2 — How this repository implements the charter

### The one channel for recommendations

**This repository is the channel the charter refers to.** A recommendation is
any [issue](https://github.com/Rowing-Industry-Trade-Association/rowing-data-standard/issues)
or [proposal](proposals/README.md) filed here. Nothing submitted by email, at a
meeting or in a side conversation is logged until it is written down here —
the point of one channel is that every recommendation has a public record and
an outcome.

| Charter | Here |
|---|---|
| Recommendation | An issue, or a proposal for anything that changes what goes into a file |
| Logged | The issue or proposal pull request itself |
| Outcome: adopted | Proposal status `adopted`; issue closed as completed, with the release it lands in |
| Outcome: deferred | Proposal status `deferred`; issue labelled `deferred` and left open |
| Outcome: declined | Proposal status `declined`; issue closed as not planned, with the brief reason in the closing comment |
| Chair sets what is considered | A GitHub milestone per release; the chair decides what goes on it |

### Who decides

The DSWG decides; participation is open. Anyone may file, comment, review,
implement and argue a case. Merging a change to the specification, the field
registry or a proposal's status reflects a DSWG decision, recorded on the pull
request or the issue it closes.

Subject matter experts take part in the discussion here like anyone else. They
do not vote.

### Current members

| Name | Company | Role |
|---|---|---|
| Michael Naughton | Nielsen-Kellerman | Chair |
| Tony Andrews | CrewNerd | Voting member |
| Joris Blaak | MoveLab Studio | Voting member |
| Ryan Farrell | Concept2 | Voting member |
| Scott Hamilton | Concept2 | Subject matter expert |
| Sander Roosendaal | Rowsandall | Subject matter expert |
| Nils Steffensen | Nielsen-Kellerman | Subject matter expert |
| Jaap van Ekris | OpenRowingMonitor | Subject matter expert |

Members serve two-year terms (charter §6). This table is updated by pull
request whenever the membership changes.

### Releases

- `main` is the working text between releases. It is not citable.
- **A tagged GitHub release is a published version of the standard** — the
  only thing an implementer should cite. Each release carries release notes
  listing what changed, the recommendations it addresses, and the FIT protocol
  and SDK version it was validated against.
- Before a major version, the DSWG may publish a **release candidate**, tagged
  as a GitHub pre-release (for example `v1.0-rc`). It is for implementers to
  build against and test. Changes between a release candidate and its final
  release are limited to what that testing shows is needed, and are listed in
  the final release's notes.
- Two releases a year. An urgent fix for an error that blocks data exchange can
  be released in between, by DSWG vote.
- A breaking change — one that makes an existing conforming file
  non-conforming or changes its meaning — is announced in the release notes of
  at least one release before the release that makes it.

### Licensing

| What | Licence |
|---|---|
| Specification text, field registry, code lists, guidance and examples | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| Machine-readable files — schemas, templates, sample data such as the FIT test fixtures — and example implementation code, such as the [Python library](python/) | [Apache License 2.0](LICENSES/Apache-2.0.txt) |
| The Garmin FIT protocol and SDK | Garmin's FIT Protocol License — not granted by anything in this repository |

The charter does not mention implementation code. It goes under Apache 2.0
with the other machine-readable files. [`LICENSE.md`](LICENSE.md) has the full
terms, including the contributors' patent commitment.

By opening an issue, a proposal or a pull request, you agree that what you
submit may be included in the standard under the licence of the path it lands
in.

### Antitrust

DSWG meetings follow RITA's antitrust guidelines, and so does discussion here.
The subject is the file format. Pricing, costs, customers, market allocation,
product launch plans and anything else commercially sensitive stay out of it —
"our device measures this at 0.1° resolution" is on topic; what it costs or who
buys it is not.

### Name

"RITA" and "RITA Data Standard" are RITA's names. Forking and modifying the
text is allowed under CC BY 4.0, but a modified version may not be presented as
the official standard or as endorsed by RITA.
