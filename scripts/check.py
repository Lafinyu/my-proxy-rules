#!/usr/bin/env python3
"""Validate source rules and deterministic generated files."""

from __future__ import annotations

import ipaddress
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

import build


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "rules.toml"
ALLOWED_TYPES = {"local", "quixoticheart"}
DOMAIN_RULES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
IP_RULES = {"IP-CIDR": 4, "IP-CIDR6": 6}
SENSITIVE_PATTERNS = [
    (
        "GitHub Token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    ),
    (
        "Token 配置项",
        re.compile(r"(?im)^\s*(?:github[_-]?)?token\s*="),
    ),
    (
        "密码配置项",
        re.compile(r"(?im)^\s*(?:password|passwd)\s*="),
    ),
    (
        "代理节点链接",
        re.compile(r"(?i)\b(?:ss|ssr|vmess|vless|trojan|hysteria2?|tuic)://"),
    ),
    (
        "机场订阅链接",
        re.compile(
            r"(?i)https?://[^\s\"']+(?:"
            r"/api/v\d+/client/subscribe|/subscribe(?:/|\?|$)|"
            r"/sub(?:/|\?|$)|[?&]token=)"
        ),
    ),
    (
        "代理节点配置",
        re.compile(r"(?im)^\s*(?:server|server_port|uuid|cipher)\s*="),
    ),
]


def add_error(errors: list[str], message: str) -> None:
    """Append a consistently formatted validation error."""
    errors.append(message)


def load_toml(errors: list[str]) -> dict[str, Any] | None:
    """Load rules.toml and collect parse errors."""
    try:
        with CONFIG_PATH.open("rb") as file:
            data = tomllib.load(file)
    except FileNotFoundError:
        add_error(errors, "找不到配置文件: config/rules.toml")
        return None
    except tomllib.TOMLDecodeError as exc:
        add_error(errors, f"rules.toml 解析失败: {exc}")
        return None
    except OSError as exc:
        add_error(errors, f"无法读取 rules.toml: {exc}")
        return None
    return data


def resolve_local_path(relative_path: str, errors: list[str], rule_id: str) -> Path | None:
    """Resolve a local rule path while preventing traversal outside the repository."""
    candidate = (ROOT / relative_path).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        add_error(errors, f"规则 {rule_id} 的 path 超出项目目录: {relative_path}")
        return None
    return candidate


def validate_rule_line(path: Path, number: int, line: str, errors: list[str]) -> None:
    """Check one non-comment classical rule for obvious format errors."""
    parts = [part.strip() for part in line.split(",")]
    rule_type = parts[0].upper() if parts else ""

    if rule_type in DOMAIN_RULES:
        if len(parts) != 2 or not parts[1] or re.search(r"\s", parts[1]):
            add_error(errors, f"{path.relative_to(ROOT)}:{number}: 域名规则格式错误: {line}")
        return

    if rule_type in IP_RULES:
        if len(parts) not in {2, 3} or not parts[1]:
            add_error(errors, f"{path.relative_to(ROOT)}:{number}: IP 规则格式错误: {line}")
            return
        if len(parts) == 3 and parts[2] != "no-resolve":
            add_error(
                errors,
                f"{path.relative_to(ROOT)}:{number}: 第三个字段只能是 no-resolve: {line}",
            )
        try:
            network = ipaddress.ip_network(parts[1], strict=False)
        except ValueError:
            add_error(errors, f"{path.relative_to(ROOT)}:{number}: CIDR 无效: {parts[1]}")
            return
        if network.version != IP_RULES[rule_type]:
            add_error(errors, f"{path.relative_to(ROOT)}:{number}: IP 版本与 {rule_type} 不符")
        return

    add_error(
        errors,
        (
            f"{path.relative_to(ROOT)}:{number}: 不支持或明显错误的规则类型 "
            f"{rule_type or '<空>'}"
        ),
    )


def validate_local_file(
    path: Path,
    errors: list[str],
    seen_rules: dict[str, tuple[Path, int]],
) -> None:
    """Validate local rule syntax and exact duplicates across all local files."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        add_error(errors, f"本地规则文件不是 UTF-8: {path.relative_to(ROOT)}")
        return
    except OSError as exc:
        add_error(errors, f"无法读取本地规则文件 {path.relative_to(ROOT)}: {exc}")
        return

    for number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        validate_rule_line(path, number, line, errors)
        previous = seen_rules.get(line)
        if previous is not None:
            previous_path, previous_number = previous
            add_error(
                errors,
                (
                    f"{path.relative_to(ROOT)}:{number}: 本地规则完全重复；"
                    f"首次出现于 {previous_path.relative_to(ROOT)}:{previous_number}: {line}"
                ),
            )
        else:
            seen_rules[line] = (path, number)


def configured_policy_keys(data: dict[str, Any], errors: list[str]) -> set[str]:
    """Return policy keys available to both generated clients."""
    policies = data.get("policies")
    if not isinstance(policies, dict):
        add_error(errors, "缺少 [policies] 配置。")
        return set()

    client_keys: list[set[str]] = []
    for client in ("mihomo", "shadowrocket"):
        client_policies = policies.get(client)
        if not isinstance(client_policies, dict):
            add_error(errors, f"缺少 [policies.{client}] 配置。")
            client_keys.append(set())
            continue
        client_keys.append(set(client_policies) - {"final"})
    return client_keys[0] & client_keys[1]


def validate_rules(data: dict[str, Any], errors: list[str]) -> list[Path]:
    """Validate rule entries and return existing local source paths."""
    raw_rules = data.get("rules")
    if not isinstance(raw_rules, list):
        add_error(errors, "rules.toml 缺少 [[rules]] 数组。")
        return []

    seen_ids: set[str] = set()
    local_paths: list[Path] = []
    seen_local_rules: dict[str, tuple[Path, int]] = {}
    policy_keys = configured_policy_keys(data, errors)

    for index, rule in enumerate(raw_rules, start=1):
        context = f"rules[{index}]"
        if not isinstance(rule, dict):
            add_error(errors, f"{context} 不是有效的规则表。")
            continue

        rule_id = rule.get("id")
        display_id = rule_id if isinstance(rule_id, str) and rule_id else context
        if not isinstance(rule_id, str) or not rule_id.strip():
            add_error(errors, f"{context}.id 必须是非空字符串。")
        elif rule_id in seen_ids:
            add_error(errors, f"规则 ID 重复: {rule_id}")
        else:
            seen_ids.add(rule_id)

        rule_type = rule.get("type")
        if rule_type not in ALLOWED_TYPES:
            add_error(errors, f"规则 {display_id} 的 type 必须是 local 或 quixoticheart。")

        policy = rule.get("policy")
        if not isinstance(policy, str) or policy not in policy_keys:
            add_error(
                errors,
                (
                    f"规则 {display_id} 的 policy 必须同时定义于 "
                    "[policies.mihomo] 和 [policies.shadowrocket]。"
                ),
            )

        if rule_type == "local":
            relative_path = rule.get("path")
            if not isinstance(relative_path, str) or not relative_path.strip():
                add_error(errors, f"本地规则 {display_id} 缺少有效 path。")
                continue
            path = resolve_local_path(relative_path, errors, str(display_id))
            if path is None:
                continue
            if not path.is_file():
                add_error(errors, f"本地规则文件不存在: {relative_path}")
                continue
            local_paths.append(path)
            validate_local_file(path, errors, seen_local_rules)
        elif rule_type == "quixoticheart":
            upstream_name = rule.get("upstream_name")
            if not isinstance(upstream_name, str) or not upstream_name.strip():
                add_error(errors, f"QuixoticHeart 规则 {display_id} 缺少 upstream_name。")

    return local_paths


def check_sensitive_files(paths: list[Path], errors: list[str]) -> None:
    """Scan source configuration and rules for common secret/proxy signatures."""
    for path in paths:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            add_error(errors, f"敏感信息扫描无法读取 {path.relative_to(ROOT)}: {exc}")
            continue
        for label, pattern in SENSITIVE_PATTERNS:
            match = pattern.search(content)
            if match:
                line_number = content.count("\n", 0, match.start()) + 1
                add_error(
                    errors,
                    f"{path.relative_to(ROOT)}:{line_number}: 检测到可能的{label}",
                )


def check_generated_files(data: dict[str, Any], errors: list[str]) -> None:
    """Compare committed outputs with a fresh deterministic in-memory rebuild."""
    try:
        expected_outputs = build.render_outputs(data)
    except build.BuildError as exc:
        add_error(errors, f"配置无法构建: {exc}")
        return

    for path, expected in expected_outputs.items():
        relative_path = path.relative_to(ROOT)
        if not path.is_file():
            add_error(errors, f"生成文件不存在: {relative_path}")
            continue
        try:
            actual = path.read_text(encoding="utf-8")
        except OSError as exc:
            add_error(errors, f"无法读取生成文件 {relative_path}: {exc}")
            continue
        if actual != expected:
            add_error(
                errors,
                f"生成文件不是最新内容: {relative_path}；请运行 python scripts/build.py",
            )


def main() -> int:
    """Run all checks and return a shell-friendly exit status."""
    errors: list[str] = []
    data = load_toml(errors)
    if data is not None:
        local_paths = validate_rules(data, errors)
        check_sensitive_files(
            [CONFIG_PATH, build.SHADOWROCKET_BASE_PATH, *local_paths],
            errors,
        )
        check_generated_files(data, errors)

    if errors:
        print(f"检查失败，共 {len(errors)} 个问题：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("检查通过：配置、规则文件、敏感信息和 dist 生成内容均正常。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
