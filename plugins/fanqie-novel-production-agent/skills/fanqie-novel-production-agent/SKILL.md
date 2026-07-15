---
name: fanqie-novel-production-agent
description: Automate end-to-end Fanqie short-novel production from an uploaded writing-engineering DOCX through topic selection, same-GPTs planning and chapter generation, checkpointed DOCX creation, whole-book review and merge, cover generation, and Fanqie draft configuration. Use when the user asks to run, resume, standardize, or inspect the 番茄小说自动生产 workflow, especially when Chrome, a custom GPTs conversation, chapter Word files, a merged manuscript, cover art, or Fanqie draft-only delivery are involved.
---

# 番茄小说自动生产 Agent

## Operating contract

Execute the workflow in [references/workflow.md](references/workflow.md). Read it before starting or resuming production. Read [references/configuration.md](references/configuration.md) before resolving any author, path, GPTs, account, or Word-template value.

Treat these rules as non-negotiable:

1. Load and validate the current user's independent configuration. Never fall back to the plugin developer's personal values.
2. Use the configured GPTs in one persistent Chrome conversation for all creative decisions and outputs.
3. Upload the complete engineering package before requesting topics.
4. Request topics only, reproduce every topic unchanged, then stop for the user's selection.
5. After selection, send routine prompts automatically. Leave title, characters, worldbuilding, structure, chapters, prose, final review, revisions, and cover creation to the same GPTs.
6. Create chapter DOCX files concurrently with later chapter generation. Do not render pages or perform visual QA; the user explicitly opted out. Perform only mechanical file checks.
7. After GPTs final review, create one merged DOCX and use its content as the sole source for Fanqie upload.
8. Configure the Fanqie draft with the configured `author_name`, AI usage `是`, recommended current categories, and trial ratio `30%`.
9. Save drafts only. Never submit for review, publish, sign, or make content public without a new, explicit user authorization.
10. Record every completed transition in the checkpoint before starting the next transition.

## Tool routing

- Use `scripts/settings.py` to create, validate, show, or read per-user configuration. Do not hand-edit shared defaults into the skill.
- Use `chrome:control-chrome` for GPTs and Fanqie because the workflow depends on each user's logged-in Chrome state. Never store or share credentials, cookies, or tokens.
- Use document-generation capabilities or the bundled builder approach for DOCX output. Prefer the configured `word.template_path` when nonempty; otherwise use a stable default template.
- Do not use local image generation for the cover when the user requires the designated GPTs to generate it.
- Use `scripts/checkpoint.py` for state writes. Do not hand-edit checkpoint JSON during normal operation.

## Checkpoint protocol

Read [references/checkpoint-schema.md](references/checkpoint-schema.md) before creating or recovering state.

Before a new or resumed book, validate the resolved configuration:

```bash
python3 scripts/settings.py validate --config "<番茄小说Agent配置.json>"
```

At a new book folder, initialize state:

```bash
python3 scripts/checkpoint.py init \
  --settings-file "<番茄小说Agent配置.json>" \
  --book-dir "<配置中的 output_root>/<书名或临时任务名>" \
  --title "<书名>" \
  --engineering-package "<工程包.docx>"
```

Before any resumed action:

```bash
python3 scripts/checkpoint.py resume --book-dir "<书籍文件夹>"
python3 scripts/checkpoint.py verify --book-dir "<书籍文件夹>"
```

After each chapter or phase, call the appropriate `chapter`, `advance`, `artifact`, `browser`, or `fanqie` subcommand. Run `python3 scripts/checkpoint.py --help` for exact arguments.

If checkpoint state conflicts with files, trust verified files and logged browser identifiers, repair the earliest inconsistent state through the script, and never regenerate or upload a completed artifact blindly.

## Human gates

Pause only at these gates unless the user adds another:

- **Setup gate:** if no valid per-user configuration exists, collect the required non-secret values once and validate them before browser or file actions.
- **Topic gate:** wait for the user to choose from the unchanged GPTs topic list.
- **Publication gate:** after the complete Fanqie draft is saved, stop. Publishing requires a fresh explicit authorization.

Do not interpret permission to auto-send GPT prompts as permission to choose a topic or publish.

## Completion report

Report the final title, chapter count, GPTs-confirmed word count, chapter folder, merged DOCX, cover path, Fanqie draft status, AI flag, categories, trial ratio, and checkpoint next action. State explicitly whether review submission or publication occurred.
