#!/usr/bin/env python3
"""Create and validate portable per-user settings for the Fanqie novel agent."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SENSITIVE_FRAGMENTS = ("password", "passwd", "cookie", "token", "secret", "credential")


def resolve(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load(path: str | Path) -> dict[str, Any]:
    config_path = resolve(path)
    if not config_path.exists():
        raise SystemExit(f"Configuration not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_web_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def sensitive_keys(data: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            location = f"{prefix}.{key}" if prefix else str(key)
            if any(fragment in str(key).lower() for fragment in SENSITIVE_FRAGMENTS):
                found.append(location)
            found.extend(sensitive_keys(value, location))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            found.extend(sensitive_keys(value, f"{prefix}[{index}]"))
    return found


def validate(data: dict[str, Any], check_files: bool = True) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    author = data.get("author_name")
    if not isinstance(author, str) or not author.strip():
        errors.append("author_name is required")
    output_root = data.get("output_root")
    if not isinstance(output_root, str) or not output_root.strip():
        errors.append("output_root is required")
    gpts = data.get("gpts")
    if not isinstance(gpts, dict):
        errors.append("gpts must be an object")
    else:
        gpts_url = gpts.get("url")
        if not isinstance(gpts_url, str) or not is_web_url(gpts_url):
            errors.append("gpts.url must be a valid HTTP(S) URL")
        if gpts.get("use_current_chrome_session") is not True:
            errors.append("gpts.use_current_chrome_session must be true")
    fanqie = data.get("fanqie")
    if not isinstance(fanqie, dict):
        errors.append("fanqie must be an object")
    else:
        workbench_url = fanqie.get("workbench_url", "")
        if workbench_url and (not isinstance(workbench_url, str) or not is_web_url(workbench_url)):
            errors.append("fanqie.workbench_url must be blank or a valid HTTP(S) URL")
        if fanqie.get("use_current_chrome_session") is not True:
            errors.append("fanqie.use_current_chrome_session must be true")
        if fanqie.get("ai_used") is not True:
            errors.append("fanqie.ai_used must be true for this workflow")
        if fanqie.get("trial_ratio") != 30:
            errors.append("fanqie.trial_ratio must be 30 for this workflow")
    word = data.get("word")
    if not isinstance(word, dict):
        errors.append("word must be an object")
    else:
        template = word.get("template_path", "")
        if template:
            template_path = resolve(template)
            if template_path.suffix.lower() != ".docx":
                errors.append("word.template_path must be a DOCX file")
            elif check_files and (not template_path.exists() or template_path.stat().st_size == 0):
                errors.append(f"word.template_path is missing or empty: {template_path}")
        if word.get("visual_qa") is not False:
            errors.append("word.visual_qa must be false for this workflow")
    safety = data.get("safety")
    if not isinstance(safety, dict):
        errors.append("safety must be an object")
    elif safety.get("submit_for_review") is not False or safety.get("publish") is not False:
        errors.append("safety submit_for_review and publish must remain false")
    for key in sensitive_keys(data):
        errors.append(f"sensitive credential field is forbidden: {key}")
    return errors


def cmd_init(args: argparse.Namespace) -> None:
    path = resolve(args.config)
    if path.exists() and not args.force:
        raise SystemExit(f"Configuration already exists: {path}. Use --force to replace it.")
    data = {
        "schema_version": 1,
        "author_name": args.author_name,
        "output_root": str(resolve(args.output_root)),
        "gpts": {
            "url": args.gpts_url,
            "account_hint": args.gpts_account_hint,
            "use_current_chrome_session": True,
        },
        "fanqie": {
            "workbench_url": args.fanqie_workbench_url,
            "account_hint": args.fanqie_account_hint,
            "use_current_chrome_session": True,
            "ai_used": True,
            "trial_ratio": 30,
            "category_strategy": "agent_recommend_current_options",
        },
        "word": {
            "template_path": str(resolve(args.word_template)) if args.word_template else "",
            "visual_qa": False,
        },
        "safety": {"submit_for_review": False, "publish": False},
    }
    errors = validate(data, check_files=not args.skip_file_checks)
    if errors:
        raise SystemExit("\n".join(errors))
    atomic_write(path, data)
    print(path)


def cmd_validate(args: argparse.Namespace) -> None:
    data = load(args.config)
    errors = validate(data, check_files=not args.skip_file_checks)
    if errors:
        raise SystemExit("\n".join(errors))
    print("configuration verified")


def cmd_show(args: argparse.Namespace) -> None:
    print(json.dumps(load(args.config), ensure_ascii=False, indent=2))


def cmd_get(args: argparse.Namespace) -> None:
    value: Any = load(args.config)
    for part in args.key.split("."):
        if not isinstance(value, dict) or part not in value:
            raise SystemExit(f"Unknown configuration key: {args.key}")
        value = value[part]
    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False))
    elif isinstance(value, bool):
        print("true" if value else "false")
    else:
        print(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--config", required=True)
    init.add_argument("--author-name", required=True)
    init.add_argument("--output-root", required=True)
    init.add_argument("--gpts-url", required=True)
    init.add_argument("--gpts-account-hint", default="")
    init.add_argument("--fanqie-workbench-url", default="")
    init.add_argument("--fanqie-account-hint", default="")
    init.add_argument("--word-template", default="")
    init.add_argument("--skip-file-checks", action="store_true")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    check = sub.add_parser("validate")
    check.add_argument("--config", required=True)
    check.add_argument("--skip-file-checks", action="store_true")
    check.set_defaults(func=cmd_validate)

    show = sub.add_parser("show")
    show.add_argument("--config", required=True)
    show.set_defaults(func=cmd_show)

    get = sub.add_parser("get")
    get.add_argument("--config", required=True)
    get.add_argument("--key", required=True)
    get.set_defaults(func=cmd_get)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
