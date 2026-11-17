# Quickstart

This guide walks you through your first plan with trio. It assumes no programming background, so domain experts from any field can follow every step. Developers, designers, independent developers and small teams can skim the parts they already know.

Throughout, you stay in charge of what gets built and whether it is right. The agents support you in the roles you choose to hand over, and check each other.

**Before you start.** trio fits two situations: you bring expertise in a field, or you bring an idea that has not taken shape yet. Its premise is that you stay in charge at the key moments:

- the plan and its prototypes;
- the decisions at each stop;
- the walkthrough;
- the merge.

If you want a whole app from one sentence without taking part in those moments, trio is not the right tool.

[中文版](QUICKSTART_zh.md)

## What you do, and what you never have to do

| You do | You never have to |
| --- | --- |
| Say what you want, in your own words, with examples or screenshots from tools you like | Read or write code |
| Answer a few decisions per stop; each has a default, so silence is fine | Write tests or fix test failures |
| Look at the real pages when asked, and say what feels wrong | Resolve merge conflicts or manage branches |
| Say the words that allow irreversible steps, such as "merge and push" | Remember the process: trio tells the agents what to do |
| Keep real client data out of the agents' test runs | |

Expect about 10 to 30 minutes of your time per stop, and an hour or two for each walkthrough.

## What you need

1. **Two agent sessions.** One will be the **reviewer**, which plans and checks; the other will be the **builder**, which writes the code. They can be two different tools (for example Claude Code and Codex) or two separate sessions of the same tool. Two different vendors check each other best.
2. **trio installed in both tools** (step 1 below).
3. **Python 3.9 or later**, for trio's small helper scripts.
4. **A project folder** for your app. If you do not have one yet, ask the reviewer to create it as a git repository; you do not need to learn git.
5. **Some sample data that is not real**, or permission for the agents to make it up. The agents test only on made-up (synthetic) data.

## Seven steps

### 1. Install trio

trio is a plugin that carries one skill, the instructions your agents follow. Install it in both tools.

**Claude Code**: run these two commands in a terminal.

```bash
claude plugin marketplace add yuson95/trio-workflow
```

```bash
claude plugin install trio-workflow@trio
```

**Codex, Cursor, or several tools at once**: download the repository, then copy trio into each tool.

```bash
git clone https://github.com/yuson95/trio-workflow.git
```

```bash
python trio-workflow/tools/install_local.py install --target codex
```

Choose the targets that match your tools: `claude`, `codex`, `cursor`. Use one way per tool; installing both ways makes the tool see trio twice.

**Any other agent**: put the full path of `plugins/trio-workflow/skills/trio-workflow/SKILL.md` into its instructions, as described in the plugin README.

### 2. Set up the project with the reviewer

Open the reviewer in your project folder and say:

> Set up the trio workflow for this project. The reviewer is <tool A>, the builder is <tool B>.

It asks you everything in one message, each question with a default: the goal, where client data lives, what may be sent outside, and which phrases you will use to allow merging. Answer what you know and keep the defaults for the rest. It then creates a **handoff folder** next to your project. Every agent reads and writes its files there, so nothing depends on any one chat.

### 3. Describe what you want

Tell the reviewer what the app is for, who uses it, and what a good result looks like. Screenshots of tools you like, a spreadsheet you use today, or a sketch on paper all help more than long text.

The reviewer reads the existing code, tries out anything uncertain, and writes **plan 1**:

- every requirement says what you will see on screen;
- every screen change comes with a **prototype**, a picture of the page before any code is written;
- every open question carries a default.

You confirm the prototypes, or pick between variants.

### 4. Start the builder

Open the builder and paste the kickoff prompt that the reviewer wrote into the `PROMPTS` file of the handoff folder. The builder works on its own until the first **stop**, a fixed point where work pauses for review. Then it replies with one line, for example "Reached stop 1, material at …".

### 5. At every stop, get an independent review

Open a **new** reviewer session and say "review plan 1 stop 1" (or, in Chinese, "审查方案一停点1"), pasting the builder's line. The reviewer reruns the checks itself, tries the pages on a copy with made-up data, and writes a result file. It ends with:

- a **verdict**: PASS, PASS+NOTES or FAIL;
- the few **decisions** it needs from you, each with a default;
- a short text for the builder.

Answer the decisions, or stay silent to accept the defaults. Then tell the builder: "Review result at <path>; fix accordingly and continue."

Do not tell the builder "passed" before the reviewer's result says so.

### 6. Walk through the real pages

Before the end of the plan, and in the middle of plans that change many pages, the builder prepares a test copy of the app with results already computed. You get:

- an address to open;
- a list of pages in walking order;
- a contact sheet of screenshots, one row per page and one column per situation (empty, full, many records, narrow screen), with the old version beside the new one.

Say what feels wrong in plain words. The reviewer sorts every remark into one of four groups and makes sure each one has a lasting fix:

| Group | Lasting fix |
| --- | --- |
| a broken convention | a rule plus an automatic check |
| a gap in the specification | a new line in the template |
| a bug | a test |
| a matter of taste | a choice between prototypes |

### 7. Finish the plan

When the final review says PASS, tell the reviewer "merge and push" (or "merge only"). It merges, confirms the result, and restarts your running app if you have one. Then plan 2 starts from step 3.

## Words you will see

| Word | Meaning |
| --- | --- |
| **plan** | One chunk of work with a goal, requirements and stops; usually days to two weeks |
| **stop** | A fixed point where the builder pauses and the reviewer checks independently |
| **batch** | A small piece of a plan that one builder worker completes and proves |
| **verdict** | The reviewer's PASS, PASS+NOTES or FAIL, tied to an exact version of the code |
| **prototype** | A picture of a page before it is built |
| **walkthrough** | You trying the real pages on a test copy |
| **synthetic data** | Made-up data that looks real; the only data agents test with |
| **main** | The official version of your app; changes reach it only after your "merge" |
| **handoff folder** | The folder where the plans, progress files and review results live |
| **PR mode** | Optional: every batch becomes a pull request with automatic tests; stops stay as they are. Worth it once your project lives on GitHub |

## Common mistakes

| Mistake | Instead |
| --- | --- |
| Telling the builder it passed before the review is done | Wait for the result file; it sometimes finds problems the builder's own checks missed |
| Skipping the walkthrough because the checks are green | Green checks cannot tell whether a page makes sense; only you can |
| Giving the builder a new wish mid-batch without telling the reviewer | Tell the reviewer, who writes it down and decides where it belongs |
| One huge plan | Several plans of one to two weeks each, each ending in something you can use |
| Letting agents work on real client files | Keep real data outside the project; agents use synthetic copies |

## Where to read more

- The workflow plate, with the whole process on one page: [English](workflow/trio-workflow.png) · [中文](workflow/trio-workflow_zh.png)
- The plugin guide, for installation details and pstack: [plugins/trio-workflow/README.md](../plugins/trio-workflow/README.md)
