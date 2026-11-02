# lessonforge: Lesson & Exercise Generator

**PKG-45 · AppsTechLabs CRM catalogue · D. People and daily operations**

`lessonforge` is a command-line tool that turns a **topic** into a **ready-to-teach lesson plan with exercises and
an answer key, written in French**, for private schools and training centres. It uses the Claude API, validates every
result automatically, and ships with a **gold validation suite** that measures how reliable it really is.

```bash
lessonforge generate "Pythagoras' theorem" --level 4e --duration 55 --exercises 6 -o lesson.md
```

---

## Table of contents

1. [What it does](#what-it-does)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Output format](#output-format)
7. [How it works](#how-it-works)
8. [Gold validation](#gold-validation)
9. [Project structure](#project-structure)
10. [Tests](#tests)
11. [Troubleshooting](#troubleshooting)
12. [Limitations](#limitations)
13. [Contributing and license](#contributing-and-license)

---

## What it does

Given a topic, a level, an audience and a session length, `lessonforge` produces:

- a lesson title and 2–5 observable **objectives**;
- **prerequisites** and **materials**;
- a **timed lesson flow** (hook, explanation, guided practice, independent practice, wrap-up) whose durations add up
  to exactly the requested session length;
- **key points** to retain;
- the requested number of **exercises** (multiple choice, true/false, fill in the blank, open question, calculation)
  with a difficulty level, the correct answer and an explanation for each;
- a **homework** task and **assessment criteria**.

You can export it as a Markdown **teacher version** (with answer key), a **student handout** (no answer key, no
teacher notes), or **JSON** for use in other software.

What makes it reliable rather than just a prompt:

| Feature | What it gives you |
|---|---|
| Constrained output | One tool call with a strict JSON schema, so the structure is always the same |
| Deterministic checks | Durations, exercise counts, answer formats and language are verified without AI |
| Correction loop | When a check fails, the exact errors are sent back to the model (up to 3 attempts) |
| No silent failures | A lesson that is still invalid is never delivered without a warning and a non-zero exit code |
| Clean refusals | A topic that is too vague (such as "maths") or unsuitable is declined with a reason; no lesson is invented |
| Gold validation | 20 fixed cases, including an independent re-solving of every answer key, with a published pass rate |

---

## Requirements

- **Python 3.10 or newer** (tested on 3.12)
- An **Anthropic API key** (the cohort's Claude API key)
- Internet access to `api.anthropic.com`
- Python packages (installed for you, see below):
  - `anthropic >= 0.40`
  - `pydantic >= 2.5`
  - `python-dotenv >= 1.0`
  - `pytest >= 8.0` (only to run the tests)

---

## Installation

### 1. Get the project

Unzip `lessonforge.zip`, or clone the repository, then open a terminal in the project folder (the one that contains
`pyproject.toml`).

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
```

Activate it:

| System | Command |
|---|---|
| Windows (PowerShell) | `venv\Scripts\Activate.ps1` |
| Windows (Command Prompt) | `venv\Scripts\activate.bat` |
| macOS / Linux | `source venv/bin/activate` |

### 3. Install

```bash
pip install -r requirements.txt
pip install -e .
```

- `pip install -r requirements.txt` installs the libraries the code depends on.
- `pip install -e .` installs the project in *editable* mode and creates the `lessonforge` command. Changes you make
  to the code apply immediately, with no reinstall.

> **Don't want to install the package?** Run only `pip install -r requirements.txt`, then replace `lessonforge` with
> `python -m lessonforge.cli` in every command in this document.

Check that it works:

```bash
lessonforge --help
```

---

## Configuration

### API key

The tool reads the key from the `ANTHROPIC_API_KEY` environment variable. The simplest way is a `.env` file:

1. Copy the template:
   - Windows: `copy .env.example .env`
   - macOS / Linux: `cp .env.example .env`
2. Open `.env` and replace the placeholder:

   ```
   ANTHROPIC_API_KEY=sk-ant-your-real-key
   ```

   Use **no quotes**, **no spaces** around `=`, and nothing after the key.

The `.env` file is searched in the folder you run the command from, then in its parent folders. If the variable is
already set in your terminal, **the terminal value wins over the file**.

Setting it in the terminal instead:

| Shell | Command |
|---|---|
| PowerShell | `$env:ANTHROPIC_API_KEY="sk-ant-..."` |
| Command Prompt | `set ANTHROPIC_API_KEY=sk-ant-...` |
| macOS / Linux | `export ANTHROPIC_API_KEY=sk-ant-...` |

> **Security:** never commit `.env`, paste your key in code, or share it in screenshots. `.gitignore` already excludes
> `.env`. Keep real keys out of `.env.example`.

### Model

The default model is `claude-sonnet-5-5`. To change it:

- for one run: `lessonforge --model claude-opus-5-5 generate "Fractions"` (the `--model` option goes **before**
  `generate` or `gold`);
- for every run: add `LESSONFORGE_MODEL=claude-opus-5-5` to your `.env`.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | yes | Your Anthropic API key |
| `LESSONFORGE_MODEL` | no | Claude model to use (default `claude-sonnet-5-5`) |

---

## Usage

The tool has two commands: `generate` (make a lesson) and `gold` (measure reliability).

### `lessonforge generate TOPIC`

```bash
lessonforge generate "Pythagoras' theorem" --level 4e --duration 55 --exercises 6 -o lesson.md
```

| Option | Default | Description |
|---|---|---|
| `TOPIC` | (required) | The lesson topic, at least 3 characters. Any language works; the lesson is written in French |
| `--level` | `3e` | Class or course level, free text (`CM2`, `6e`, `Terminale`, `BTS`, `Beginner`...) |
| `--audience` | `school` | `school` (private school) or `center` (training centre, adult learners) |
| `--duration` | `55` | Session length in minutes, from 20 to 240 |
| `--exercises` | `6` | Number of exercises, from 2 to 15 |
| `--format` | `md` | `md` (Markdown document) or `json` (structured data) |
| `--student` | off | Student handout: removes objectives, teacher notes, assessment criteria and the answer key |
| `-o`, `--output` | prints to screen | File to write the result to |

Global option (placed before the command):

| Option | Description |
|---|---|
| `--model` | Claude model to use (default: `$LESSONFORGE_MODEL`, then `claude-sonnet-5-5`) |

**Examples**

```bash
# Teacher version for a school class
lessonforge generate "Adding fractions" --level CM2 --duration 45 -o fractions_teacher.md

# Student handout (no answer key)
lessonforge generate "Adding fractions" --level CM2 --duration 45 --student -o fractions_student.md

# Training centre session
lessonforge generate "Excel: basic formulas" --audience center --level Beginner --duration 90 -o excel.md

# JSON for another application
lessonforge generate "Ohm's law" --level 3e --format json -o ohm.json

# Use a different model for this run only
lessonforge --model claude-opus-5-5 generate "Photosynthesis" --level 4e
```

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Lesson generated and fully valid |
| `1` | Generation failed, or the lesson still breaks the contract after all attempts (the problems are listed on screen) |
| `2` | Topic too short (under 3 characters) |
| `3` | Topic declined: too vague or unsuitable (the reason is printed) |

When the exit code is `1` because of remaining problems, the lesson is **still written**, preceded by a warning that
lists exactly what is wrong. It is never delivered silently as if it were valid.

### `lessonforge gold`

```bash
lessonforge gold --cases gold/cases.jsonl --threshold 0.9 --out reports/
```

| Option | Default | Description |
|---|---|---|
| `--cases` | `gold/cases.jsonl` | Path to the gold cases file |
| `--out` | `reports` | Folder where the reports are written |
| `--threshold` | `0.9` | Minimum pass rate, from 0 to 1. Below it, the exit code is `1` |
| `--no-judge` | off | Skip the independent answer-key check (faster and cheaper, but weaker) |
| `--limit` | `0` (all) | Run only the first N cases |

See [Gold validation](#gold-validation) for what it checks.

---

## Output format

### Markdown

The lesson is a French document. Teacher version, in this order:

```
# <title>
*<level> · <duration> min*

## Objectifs
## Prérequis
## Matériel
## Déroulé            (numbered stages with minutes, activities and teacher notes)
## À retenir
## Exercices          (numbered, with difficulty; multiple-choice options labelled a) b) c) d))
## Devoir
## Critères d'évaluation
## Corrigé (réservé à l'enseignant)    (answer and explanation for each exercise)
```

The student handout keeps only the title, key points, exercises and homework.

### JSON

`--format json` returns the full structure:

```json
{
  "status": "ok",
  "decline_reason": "",
  "title": "...",
  "level": "4e",
  "duration_minutes": 55,
  "objectives": ["..."],
  "prerequisites": ["..."],
  "materials": ["..."],
  "stages": [
    {"name": "...", "minutes": 10, "activity": "...", "teacher_notes": ""}
  ],
  "key_points": ["..."],
  "exercises": [
    {
      "type": "mcq",
      "difficulty": "easy",
      "statement": "...",
      "choices": ["...", "...", "...", "..."],
      "answer": "...",
      "explanation": "..."
    }
  ],
  "homework": "...",
  "assessment_criteria": ["..."]
}
```

| Field | Values |
|---|---|
| `status` | `ok` or `declined` (when declined, only `decline_reason` is filled, in English) |
| `exercises[].type` | `mcq`, `true_false`, `fill_in_blank`, `open_question`, `calculation` |
| `exercises[].difficulty` | `easy`, `medium`, `hard` |
| `exercises[].answer` | For `mcq`: the exact text of one choice. For `true_false`: exactly `True` or `False` (shown as Vrai/Faux in the Markdown) |

---

## How it works

```
 topic, level, audience, duration, n exercises
                    │
                    ▼
        ┌───────────────────────┐
        │ 1. Generate           │  one Claude call, JSON-schema tool (schema.py, prompts.py, llm.py)
        └───────────┬───────────┘
                    ▼
        ┌───────────────────────┐
        │ 2. Validate           │  pydantic schema + deterministic checks (checks.py)
        └───────────┬───────────┘
              valid │ invalid
                    │     └──► 3. Re-ask with the exact list of errors (max 3 attempts, generator.py)
                    ▼
        ┌───────────────────────┐
        │ 4. Render             │  Markdown teacher / student, or JSON (render.py)
        └───────────────────────┘
```

### The deterministic checks (`checks.py`)

A lesson is valid only if all of these hold:

- the title, key points and homework are present;
- there are **2 to 5 objectives** and **at least 3 stages**;
- the stage durations add up to **exactly** the requested duration;
- the number of exercises is **exactly** the requested number;
- from 4 exercises on, there are **at least 2 difficulty levels**;
- every exercise has a statement, an answer and an explanation, and no two statements are identical;
- `mcq`: exactly 4 distinct choices, and the answer is the **exact text** of one of them;
- `true_false`: the answer is exactly `True` or `False`;
- `fill_in_blank`: the statement contains `____`;
- exercises other than `mcq` have no `choices`;
- the text is **in French** (a stopword-based detector rejects English output).

### Refusals

The prompt tells the model to decline instead of inventing a lesson when the topic is a whole subject
("maths") or is dangerous or unrelated to teaching. The result has `status: "declined"` and a one-sentence reason in
English, and `generate` exits with code `3`.

### Why these design choices

- **Structured output over free text:** every field can be checked by code, so mistakes are caught instead of
  trusted.
- **Errors fed back to the model:** retries are targeted ("stages add up to 50, expected 55"), not blind regeneration.
- **The LLM is behind a small interface (`llm.py`):** the tests replace it with a fake, so the whole pipeline is
  tested without network access or cost.

---

## Gold validation

The gold step answers one question honestly: **how often does the tool produce a correct, usable lesson?**
It replays a fixed set of cases and reports the pass rate, **failures included**. Replay it after every change to a
prompt, the schema, a check or the model.

```bash
lessonforge gold --threshold 0.9
```

### The gold set

`gold/cases.jsonl` contains **20 cases**: 18 real topics (primary school to final year, plus accounting, Excel, first
aid and CV writing) and **2 topics that must be declined** ("maths" and an unsafe request). One JSON object per line.
Lines starting with `#` are ignored.

| Field | Required | Description |
|---|---|---|
| `id` | yes | Unique case identifier (`G01`...) |
| `topic` | yes | Topic sent to the tool |
| `level` | no | Default `3e` |
| `audience` | no | `school` (default) or `center` |
| `duration` | no | Minutes, default 55 |
| `exercises` | no | Number of exercises, default 6 |
| `expect` | no | `ok` (default) or `declined` |
| `must_include` | no | List of groups of terms. For each group, **at least one** term must appear in the lesson |
| `must_not_include` | no | Terms that must **not** appear (for example content above the level) |

Example:

```json
{"id":"G01","topic":"Pythagoras' theorem","level":"4e","duration":55,"exercises":6,"must_include":[["hypoténuse"],["carré"]]}
```

`must_include` and `must_not_include` are matched against the **French** lesson text, ignoring case and accents, so
those terms are written in French.

### What makes a case pass

A case passes only if **all** of its checks pass:

1. **Contract:** the lesson passes every deterministic check above on the allowed attempts.
2. **Required concepts:** every `must_include` group is satisfied and no `must_not_include` term appears.
3. **Independent answer-key check:** a second Claude call **solves every exercise without seeing the expected
   answer**. For `mcq` and `true_false`, answers are compared exactly. For other types, a grader call decides whether
   the two answers are equivalent in substance (strict on numbers, dates and formulas). **Any disagreement fails
   the case.** This is the guard against wrong answer keys.
4. **Declined cases:** the tool must decline, with a reason, and must **not** produce a lesson.

A case also fails if the model wrongly declines a valid topic, or if the API call fails.

### Reports

Each run writes two files in `--out`:

- `gold_report.md`: the pass rate, a table of every case, and a "Failures" section with the exact cause of each one;
- `gold_report.json`: the same data for programs.

The exit code is `0` if the pass rate reaches `--threshold`, otherwise `1`.

### Cost

A passing case typically needs 1 generation call plus 1–2 judge calls, and more if a retry was needed. A full run of
20 cases is therefore a few dozen API calls. Use `--no-judge` or `--limit 5` for a cheaper check while developing.

### Recorded results

> Fill this in after running the gold suite with your key, and keep it up to date after every change.

| Date | Model | Pass rate | Failed cases and causes |
|---|---|---|---|
| _to be completed_ | _to be completed_ | _to be completed_ | _to be completed_ |

---

## Project structure

```
lessonforge/
├── README.md
├── pyproject.toml            # package metadata and the `lessonforge` command
├── requirements.txt          # runtime dependencies
├── requirements-dev.txt      # runtime + pytest
├── .env.example              # template for your API key (copy to .env)
├── .gitignore
├── lessonforge/
│   ├── __init__.py
│   ├── cli.py                # command-line interface: generate, gold
│   ├── generator.py          # generate → validate → retry loop
│   ├── prompts.py            # system prompt, user prompt, retry prompt
│   ├── schema.py             # pydantic models: Request, Lesson, Stage, Exercise
│   ├── checks.py             # deterministic validation rules
│   ├── judge.py              # independent re-solving of the answer keys
│   ├── gold.py               # gold runner and report writer
│   ├── render.py             # Markdown rendering (teacher / student)
│   └── llm.py                # Anthropic API wrapper (the only file that calls Claude)
├── gold/
│   └── cases.jsonl           # the 20 gold cases
└── tests/
    ├── fakes.py              # fake Claude client and a sample lesson
    └── test_all.py
```

`llm.py` is the only file that talks to the API. That is where the model call happens and where the default model is
set.

---

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Run it from the project folder (the one containing `pyproject.toml`). **15 tests** cover the deterministic checks,
the retry loop, the "never deliver an invalid lesson silently" guarantee, Markdown rendering, the gold runner
(passing, failing, declined cases, report counts), the shipped gold file, and `.env` loading. They use a fake client:
**no API key and no cost**.

---

## Troubleshooting

| Problem | Cause and fix |
|---|---|
| `ANTHROPIC_API_KEY is missing` | No key found. Create `.env` in the folder you run from, or set the variable in the terminal |
| `401 authentication_error: invalid x-api-key` | The key was found but Anthropic rejected it. Check that `.env` contains exactly `ANTHROPIC_API_KEY=sk-ant-...` (no quotes, spaces or leftover placeholder), that the key is complete, and that it has not been revoked. Also check that a stale key is not set in the terminal, since it overrides `.env` (`echo $env:ANTHROPIC_API_KEY` in PowerShell, `echo %ANTHROPIC_API_KEY%` in Command Prompt) |
| `.env` seems ignored | The file may be saved as `.env.txt` (Notepad does this). Show file extensions in File Explorer, or create it with VS Code. It must be in the folder you run from or a parent |
| `lessonforge` is not recognized | The package is not installed or the virtual environment is not active. Activate `venv`, run `pip install -e .`, or use `python -m lessonforge.cli` |
| `The model's answer was cut off at ... tokens` | The answer hit the token limit. Reduce `--exercises`, or raise `max_tokens` in `lessonforge/llm.py` |
| Warning: the lesson does not fully meet the contract | After 3 attempts a check still fails. The problems are listed. Run it again, reduce `--exercises`, or try a stronger model with `--model` |
| `Topic not handled: ...` (exit code 3) | The topic was declined as too vague or unsuitable. Narrow it to one lesson, for example "Adding fractions" instead of "maths" |
| `python -m pytest`: no tests found, or `test_all.py` not found | `test_all.py` is inside `tests/` and is run through pytest, not with `python test_all.py`. Run `python -m pytest -q` from the project folder |
| Validation error about `duration` or `exercises` | Values must be within range: duration 20–240, exercises 2–15 |

---

## Limitations

- **Lessons are generated in French only.** The prompts, the checks (including the French-language detector) and the
  section headings assume French. The code, CLI and reports are in English.
- **Correctness is checked, not guaranteed.** The independent answer-key check catches many wrong answers and
  ambiguous questions, but two Claude calls agreeing does not prove a fact is right. Have a teacher review the
  lesson before using it in class, especially for history, science and legal or accounting content.
- **The curriculum is not verified.** The tool adapts to the level you give it, but it does not check a specific
  national syllabus.
- **Text only.** No images, diagrams, geometric figures or audio. Exercises that need a figure are described in words.
- **Open questions** are only checked by the independent grader for equivalence with the model's own answer, which is
  weaker than for multiple-choice and calculation exercises.
- **The gold set is small** (20 cases). A high pass rate on it is a useful signal, not a proof of quality on every
  topic.
- **Each lesson costs API usage.** Retries and the gold run cost more than a single generation.

---

## Contributing and license

To change behaviour, edit the matching file (prompt in `prompts.py`, rules in `checks.py`, structure in `schema.py`),
add or adjust a gold case in `gold/cases.jsonl`, run `python -m pytest -q`, then run `lessonforge gold` and record
the result in the table above.

License: _to be defined before publishing (add a `LICENSE` file)._
