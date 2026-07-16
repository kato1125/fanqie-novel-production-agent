#!/usr/bin/env python3
"""Atomic checkpoints for the one-pass Fanqie short-novel GPTs agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from settings import load as load_user_settings
from settings import resolve as resolve_user_path
from settings import validate as validate_user_settings


STATE_NAME = "生产状态.json"
LOG_NAME = "生产日志.md"
CHAPTER_STAGES = [
    "pending",
    "generating",
    "generated",
    "text_saved",
    "word_saved",
    "finalized",
]
ARTIFACT_KINDS = [
    "template",
    "topics",
    "planning",
    "merged_docx",
    "fanqie_upload_source",
    "cover",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def state_path(book_dir: str | Path) -> Path:
    return Path(book_dir).expanduser().resolve() / STATE_NAME


def log_path(book_dir: str | Path) -> Path:
    return Path(book_dir).expanduser().resolve() / LOG_NAME


def load(book_dir: str | Path) -> dict[str, Any]:
    path = state_path(book_dir)
    if not path.exists():
        raise SystemExit(f"Checkpoint not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_save(book_dir: str | Path, data: dict[str, Any]) -> None:
    directory = Path(book_dir).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = now()
    fd, temporary = tempfile.mkstemp(prefix=".生产状态.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, directory / STATE_NAME)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_log(book_dir: str | Path, action: str, detail: str) -> None:
    path = log_path(book_dir)
    if not path.exists():
        path.write_text("# 生产日志\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"- {now()} | {action} | {detail}\n")


def parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "y", "是"}:
        return True
    if lowered in {"0", "false", "no", "n", "否"}:
        return False
    raise argparse.ArgumentTypeError(f"Not a boolean: {value}")


def cmd_init(args: argparse.Namespace) -> None:
    directory = Path(args.book_dir).expanduser().resolve()
    user_settings: dict[str, Any] = {}
    settings_file: Path | None = None
    if args.settings_file:
        settings_file = resolve_user_path(args.settings_file)
        user_settings = load_user_settings(settings_file)
        settings_errors = validate_user_settings(user_settings)
        if settings_errors:
            raise SystemExit("\n".join(settings_errors))
        output_root = resolve_user_path(user_settings["output_root"])
        try:
            directory.relative_to(output_root)
        except ValueError:
            raise SystemExit(f"Book directory must be inside configured output_root: {output_root}")
    author = args.author or user_settings.get("author_name")
    if not author:
        raise SystemExit("Author is required through --settings-file or --author")
    template = args.template
    if template is None:
        template = user_settings.get("word", {}).get("template_path") or None
    configured_gpts_url = user_settings.get("gpts", {}).get("url")
    configured_fanqie = user_settings.get("fanqie", {})
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / STATE_NAME
    if path.exists() and not args.force:
        raise SystemExit(f"Checkpoint already exists: {path}. Use --force to replace it.")
    timestamp = now()
    data = {
        "schema_version": 3,
        "agent": "fanqie-short-novel-gpts-agent",
        "configuration": {
            "path": str(settings_file) if settings_file else None,
            "gpts_account_hint": user_settings.get("gpts", {}).get("account_hint", ""),
            "fanqie_account_hint": configured_fanqie.get("account_hint", ""),
            "fanqie_workbench_url": configured_fanqie.get("workbench_url", ""),
        },
        "book": {
            "title": args.title,
            "author": author,
            "folder": str(directory),
            "engineering_package": args.engineering_package,
            "target_words": args.target_words,
            "chapters_total": args.chapters_total,
        },
        "browser": {"gpts_url": configured_gpts_url, "fanqie_draft_url": None, "fanqie_draft_id": None},
        "workflow": {
            "current_step": "initialized",
            "next_action": "upload_engineering_package",
            "completed_steps": [],
            "topic_selection": None,
            "topic_confirmed": False,
            "topic_selection_policy": "user_only",
            "chapter_generation_policy": "once",
            "literary_review": False,
            "merged_docx_provider": "gpts",
            "local_merge_allowed": False,
            "publish_authorized": False,
            "publish_authorization_evidence": None,
            "submitted_for_review": False,
            "published": False,
        },
        "chapters": {},
        "artifacts": {kind: template if kind == "template" else None for kind in ARTIFACT_KINDS},
        "fanqie": {
            "content_uploaded": False,
            "chapters_formatted": False,
            "ai_used": configured_fanqie.get("ai_used", True),
            "categories": [],
            "trial_ratio": configured_fanqie.get("trial_ratio", 30),
            "draft_saved": False,
        },
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    atomic_save(directory, data)
    append_log(directory, "init", f"title={args.title}")
    print(path)


def cmd_show(args: argparse.Namespace) -> None:
    data = load(args.book_dir)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        workflow = data["workflow"]
        print(f"书名: {data['book']['title']}")
        print(f"当前步骤: {workflow['current_step']}")
        print(f"下一动作: {workflow['next_action']}")
        print(f"章节: {len(data['chapters'])}/{data['book'].get('chapters_total') or '?'}")
        print(f"允许发布: {workflow['publish_authorized']}")


def relocate_value(value: Any, old_root: Path, new_root: Path) -> Any:
    if not isinstance(value, str) or not value:
        return value
    path = Path(value).expanduser()
    try:
        relative = path.resolve().relative_to(old_root)
    except ValueError:
        return value
    return str(new_root / relative)


def cmd_relocate(args: argparse.Namespace) -> None:
    old_root = Path(args.book_dir).expanduser().resolve()
    new_root = Path(args.new_book_dir).expanduser().resolve()
    if not old_root.exists():
        raise SystemExit(f"Current book directory does not exist: {old_root}")
    if old_root != new_root:
        if new_root.exists():
            raise SystemExit(f"Refusing to overwrite existing destination: {new_root}")
        new_root.parent.mkdir(parents=True, exist_ok=True)
        old_root.rename(new_root)
    data = load(new_root)
    data["book"]["title"] = args.title
    data["book"]["folder"] = str(new_root)
    data["book"]["engineering_package"] = relocate_value(
        data["book"].get("engineering_package"), old_root, new_root
    )
    for kind, value in data["artifacts"].items():
        data["artifacts"][kind] = relocate_value(value, old_root, new_root)
    for chapter in data["chapters"].values():
        for field in ("text_file", "word_file"):
            chapter[field] = relocate_value(chapter.get(field), old_root, new_root)
    atomic_save(new_root, data)
    append_log(new_root, "relocate", f"{old_root} -> {new_root}; title={args.title}")
    print(new_root)


def cmd_advance(args: argparse.Namespace) -> None:
    data = load(args.book_dir)
    workflow = data["workflow"]
    previous = workflow["current_step"]
    if args.complete_previous and previous not in workflow["completed_steps"]:
        workflow["completed_steps"].append(previous)
    workflow["current_step"] = args.step
    workflow["next_action"] = args.next_action
    atomic_save(args.book_dir, data)
    append_log(args.book_dir, "advance", f"{previous} -> {args.step}; next={args.next_action}")


def cmd_confirm_topic(args: argparse.Namespace) -> None:
    data = load(args.book_dir)
    data["workflow"]["topic_selection"] = args.selection
    data["workflow"]["topic_confirmed"] = True
    data["workflow"]["current_step"] = "topic_confirmed"
    data["workflow"]["next_action"] = "send_selection_to_same_gpts"
    atomic_save(args.book_dir, data)
    append_log(args.book_dir, "confirm_topic", args.selection)


def cmd_chapter(args: argparse.Namespace) -> None:
    data = load(args.book_dir)
    key = str(args.number)
    chapter = data["chapters"].setdefault(
        key,
        {
            "number": args.number,
            "title": args.title,
            "stage": "pending",
            "generation_count": 0,
            "text_file": None,
            "word_file": None,
        },
    )
    old_stage = chapter["stage"]
    if args.stage == "generating" and old_stage != "generating":
        if chapter.get("generation_count", 0) >= 1:
            raise SystemExit(
                f"Chapter {args.number} has already been generated once; repeat generation is forbidden"
            )
        chapter["generation_count"] = 1
    if CHAPTER_STAGES.index(args.stage) < CHAPTER_STAGES.index(old_stage) and not args.allow_regress:
        raise SystemExit(f"Refusing chapter regression: {old_stage} -> {args.stage}")
    if args.title:
        chapter["title"] = args.title
    if args.text_file:
        chapter["text_file"] = str(Path(args.text_file).expanduser().resolve())
    if args.word_file:
        chapter["word_file"] = str(Path(args.word_file).expanduser().resolve())
    chapter["stage"] = args.stage
    chapter["updated_at"] = now()
    atomic_save(args.book_dir, data)
    append_log(args.book_dir, "chapter", f"{args.number}: {old_stage} -> {args.stage}")


def cmd_artifact(args: argparse.Namespace) -> None:
    data = load(args.book_dir)
    data["artifacts"][args.kind] = str(Path(args.path).expanduser().resolve())
    atomic_save(args.book_dir, data)
    append_log(args.book_dir, "artifact", f"{args.kind}={args.path}")


def cmd_browser(args: argparse.Namespace) -> None:
    data = load(args.book_dir)
    browser = data["browser"]
    for field in ("gpts_url", "fanqie_draft_url", "fanqie_draft_id"):
        value = getattr(args, field)
        if value is not None:
            browser[field] = value
    atomic_save(args.book_dir, data)
    append_log(args.book_dir, "browser", "browser identifiers updated")


def cmd_fanqie(args: argparse.Namespace) -> None:
    data = load(args.book_dir)
    fanqie = data["fanqie"]
    for field in ("content_uploaded", "chapters_formatted", "ai_used", "draft_saved"):
        value = getattr(args, field)
        if value is not None:
            fanqie[field] = value
    if args.categories is not None:
        fanqie["categories"] = [item.strip() for item in args.categories.split(",") if item.strip()]
    if args.trial_ratio is not None:
        if not 0 <= args.trial_ratio <= 100:
            raise SystemExit("trial_ratio must be between 0 and 100")
        fanqie["trial_ratio"] = args.trial_ratio
    atomic_save(args.book_dir, data)
    append_log(args.book_dir, "fanqie", "Fanqie draft settings updated")


def cmd_authorize_publish(args: argparse.Namespace) -> None:
    if args.value and not args.evidence:
        raise SystemExit("Explicit user authorization evidence is required when enabling publication")
    data = load(args.book_dir)
    workflow = data["workflow"]
    workflow["publish_authorized"] = args.value
    workflow["publish_authorization_evidence"] = args.evidence if args.value else None
    atomic_save(args.book_dir, data)
    append_log(args.book_dir, "authorize_publish", f"authorized={args.value}")


def cmd_mark_publication(args: argparse.Namespace) -> None:
    data = load(args.book_dir)
    workflow = data["workflow"]
    if (args.submitted_for_review or args.published) and not workflow["publish_authorized"]:
        raise SystemExit("Publication is not authorized")
    if args.published and not args.submitted_for_review:
        raise SystemExit("Cannot mark published without submitted_for_review")
    workflow["submitted_for_review"] = args.submitted_for_review
    workflow["published"] = args.published
    atomic_save(args.book_dir, data)
    append_log(args.book_dir, "publication", f"review={args.submitted_for_review}, published={args.published}")


def tracked_files(data: dict[str, Any]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    configuration = data.get("configuration", {}).get("path")
    if configuration:
        result.append(("configuration", configuration))
    package = data["book"].get("engineering_package")
    if package:
        result.append(("engineering_package", package))
    for name, path in data["artifacts"].items():
        if path:
            result.append((f"artifact.{name}", path))
    for number, chapter in data["chapters"].items():
        for field in ("text_file", "word_file"):
            if chapter.get(field):
                result.append((f"chapter.{number}.{field}", chapter[field]))
    return result


def cmd_verify(args: argparse.Namespace) -> None:
    data = load(args.book_dir)
    errors: list[str] = []
    for label, value in tracked_files(data):
        path = Path(value).expanduser()
        if not path.exists():
            errors.append(f"missing {label}: {path}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"empty {label}: {path}")
    configuration = data.get("configuration", {}).get("path")
    if configuration and Path(configuration).expanduser().exists():
        try:
            current_settings = load_user_settings(configuration)
            errors.extend(f"configuration: {item}" for item in validate_user_settings(current_settings))
            if current_settings.get("author_name") != data["book"].get("author"):
                errors.append("configuration author_name differs from checkpoint author")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"configuration cannot be read: {error}")
    workflow = data["workflow"]
    required_policies = {
        "topic_selection_policy": "user_only",
        "chapter_generation_policy": "once",
        "literary_review": False,
        "merged_docx_provider": "gpts",
        "local_merge_allowed": False,
    }
    for key, expected in required_policies.items():
        if workflow.get(key) != expected:
            errors.append(f"workflow policy mismatch: {key} must be {expected!r}")
    for number, chapter in data.get("chapters", {}).items():
        if chapter.get("generation_count", 0) > 1:
            errors.append(f"chapter {number} generation_count exceeds one")
    if (workflow["submitted_for_review"] or workflow["published"]) and not workflow["publish_authorized"]:
        errors.append("publication state exists without authorization")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print("checkpoint verified")


def cmd_resume(args: argparse.Namespace) -> None:
    data = load(args.book_dir)
    workflow = data["workflow"]
    print(json.dumps({
        "configuration": data.get("configuration", {}).get("path"),
        "current_step": workflow["current_step"],
        "next_action": workflow["next_action"],
        "gpts_url": data["browser"]["gpts_url"],
        "fanqie_draft_url": data["browser"]["fanqie_draft_url"],
        "publish_authorized": workflow["publish_authorized"],
    }, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--book-dir", required=True)
    init.add_argument("--title", required=True)
    init.add_argument("--engineering-package")
    init.add_argument("--settings-file")
    init.add_argument("--author")
    init.add_argument("--target-words")
    init.add_argument("--chapters-total", type=int)
    init.add_argument("--template")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    show = sub.add_parser("show")
    show.add_argument("--book-dir", required=True)
    show.add_argument("--json", action="store_true")
    show.set_defaults(func=cmd_show)

    relocate = sub.add_parser("relocate")
    relocate.add_argument("--book-dir", required=True)
    relocate.add_argument("--new-book-dir", required=True)
    relocate.add_argument("--title", required=True)
    relocate.set_defaults(func=cmd_relocate)

    advance = sub.add_parser("advance")
    advance.add_argument("--book-dir", required=True)
    advance.add_argument("--step", required=True)
    advance.add_argument("--next-action", required=True)
    advance.add_argument("--complete-previous", action="store_true")
    advance.set_defaults(func=cmd_advance)

    topic = sub.add_parser("confirm-topic")
    topic.add_argument("--book-dir", required=True)
    topic.add_argument("--selection", required=True)
    topic.set_defaults(func=cmd_confirm_topic)

    chapter = sub.add_parser("chapter")
    chapter.add_argument("--book-dir", required=True)
    chapter.add_argument("--number", required=True, type=int)
    chapter.add_argument("--title")
    chapter.add_argument("--stage", required=True, choices=CHAPTER_STAGES)
    chapter.add_argument("--text-file")
    chapter.add_argument("--word-file")
    chapter.add_argument("--allow-regress", action="store_true")
    chapter.set_defaults(func=cmd_chapter)

    artifact = sub.add_parser("artifact")
    artifact.add_argument("--book-dir", required=True)
    artifact.add_argument("--kind", required=True, choices=ARTIFACT_KINDS)
    artifact.add_argument("--path", required=True)
    artifact.set_defaults(func=cmd_artifact)

    browser = sub.add_parser("browser")
    browser.add_argument("--book-dir", required=True)
    browser.add_argument("--gpts-url")
    browser.add_argument("--fanqie-draft-url")
    browser.add_argument("--fanqie-draft-id")
    browser.set_defaults(func=cmd_browser)

    fanqie = sub.add_parser("fanqie")
    fanqie.add_argument("--book-dir", required=True)
    fanqie.add_argument("--content-uploaded", type=parse_bool)
    fanqie.add_argument("--chapters-formatted", type=parse_bool)
    fanqie.add_argument("--ai-used", type=parse_bool)
    fanqie.add_argument("--categories")
    fanqie.add_argument("--trial-ratio", type=int)
    fanqie.add_argument("--draft-saved", type=parse_bool)
    fanqie.set_defaults(func=cmd_fanqie)

    authorize = sub.add_parser("authorize-publish")
    authorize.add_argument("--book-dir", required=True)
    authorize.add_argument("--value", required=True, type=parse_bool)
    authorize.add_argument("--evidence")
    authorize.set_defaults(func=cmd_authorize_publish)

    publication = sub.add_parser("mark-publication")
    publication.add_argument("--book-dir", required=True)
    publication.add_argument("--submitted-for-review", required=True, type=parse_bool)
    publication.add_argument("--published", required=True, type=parse_bool)
    publication.set_defaults(func=cmd_mark_publication)

    verify = sub.add_parser("verify")
    verify.add_argument("--book-dir", required=True)
    verify.set_defaults(func=cmd_verify)

    resume = sub.add_parser("resume")
    resume.add_argument("--book-dir", required=True)
    resume.set_defaults(func=cmd_resume)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
