# UI acceptance

Automated checks prove that the code does what was written down. They cannot prove that a page is what the operator wants: names, units, rounding, ordering, empty states and layout are judged by looking. This file makes that judgment **early** (a prototype before code), **cheap** (screenshots and a prepared walkthrough) and **cumulative**: each finding is turned into structure, so the next walkthrough finds less.

It applies to every requirement whose review gate is not "none", that is, every change the operator will see or use.

## 1. Prototype before code (reviewer, when planning)

- **Attach a prototype to every review-gated requirement.** Any of these will do:
  - an HTML mockup (`*_MOCKUP.html`);
  - an annotated screenshot of the current page;
  - a reference screenshot the operator supplied, for example from another tool.

  The plan carries a `Prototype:` line with the path (`原型：` in a Chinese plan).
- **Make the prototype realistic**:
  - synthetic values in the project's units, names and rounding;
  - the longest realistic label;
  - the empty state;
  - the narrow-screen layout when the page is used on small screens.
- **When several layouts are plausible**, show two or three variants side by side and let the operator pick (settle forks by running).
- **At stop 1** the operator confirms the prototype or picks a variant. Record the choice as a decision, with the prototype path.
- `scripts/check_plan.py` reports a review-gated requirement that has no prototype line.

## 2. Screenshot matrix (builder, before the walkthrough and at every stop that changes UI)

- **Two captures** ([builder.md](builder.md) step 9). The discovery capture, early, finds defects while batches are still open. The acceptance capture, on the frozen candidate, is the stop's evidence. The acceptance capture retakes the candidate side only; keep the `main` side unless `main` moved.
- **Pages**: every page the stop changed. Take them from the diff and from the plan's "You see" lines.
- **States**, by default (the plan may add more):

  | State | File-name key |
  | --- | --- |
  | empty project | `empty` |
  | complete synthetic project with results | `full` |
  | many runs or records (the project's large synthetic copy) | `many` |
  | narrow screen, 390 px wide | `narrow` |
  | second language, for pages with new labels | `lang-<code>` |
- **Capture** each page and state on `main` and on the candidate, through the project's verification recipe:
  - name each file `<page>__<state>.png`;
  - put the `main` screenshots in `<evidence dir>/main/` and the candidate's in `<evidence dir>/candidate/`.
- **Build the contact sheet**: `python <skill dir>/scripts/screenshot_sheet.py <evidence dir> --states empty full many narrow`. It writes `index.html` with one row per page and one column per state, `main` beside the candidate. Each cell is marked `unchanged`, `new`, `removed` or `missing`.
- **A state that cannot be reached** gets one line in the stop material saying why. A state is never skipped silently.

## 3. Visual review (before the operator sees anything)

- **Who**: someone other than the author.
  - Prefer a model from a different family.
  - If only the builder's own family is available, the builder still runs the pass, marks it "same family", and the reviewer repeats it at the stop.
- **Against what**:
  - the project's UI conventions document;
  - the confirmed prototypes;
  - the "You see" lines.
- **Checklist**:
  - names: no raw IDs, the same term for the same thing on every page, one language per page;
  - units, rounding, the "<1" rule, column alignment of numbers;
  - sort orders: dates and months chronological, categories in the documented order;
  - empty, loading and stale states: they explain themselves and offer the next action;
  - narrow width: no overflow, no truncated labels, tables either scroll or reflow;
  - charts: colors unique within a chart, the palette applies everywhere, legends match the series;
  - consistency with neighboring pages and with the prototype.
- **A finding counts only with**: the page, the state, the screenshot path, the convention or prototype detail it breaks, and the expected result. Findings without a screenshot do not count.
- **Fix the findings before the walkthrough**, then recapture the affected cells and rebuild the sheet.

## 4. Walkthrough and findings into structure

- **Prepare** an isolated instance with one prepared synthetic project per state, results already computed. Give the operator:
  - the address;
  - a page list in walking order;
  - the contact sheet.

  The operator should see results without typing any data.
- **When to walk through**: for plans whose UI changes span several pages, add a walkthrough after the first UI batch, as well as the one before the final stop.
- **Record the findings.** The reviewer turns the operator's findings into `batch-notes/WALKTHROUGH_<key>_<stop>.md`:

  | ID | Page / state | What the operator saw (their words) | Class | Route | Owner | Done |
- **Classify every finding, then route it**:

  | Class | Example | Route |
  | --- | --- | --- |
  | convention breach | a raw ID shown, a wrong unit | Add or clarify the rule in the UI conventions document, then add a test or lint so it cannot recur |
  | spec gap | nobody said what an empty project shows | Add a field to the plan template, or a state or checklist item to sections 2–3 |
  | bug | months sorted alphabetically | A failing test, then the fix |
  | taste | spacing feels cramped | A prototype choice for the operator; if the choice generalizes, record it in the conventions document |
- **Retro** ([merge.md](merge.md)): every convention, spec-gap and bug finding has its structural fix landed or scheduled in a named later plan.
