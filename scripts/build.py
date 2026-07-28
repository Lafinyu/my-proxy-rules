#!/usr/bin/env python3
"""Build Mihomo and Shadowrocket configurations from project sources."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "rules.toml"
SHADOWROCKET_BASE_PATH = ROOT / "config" / "shadowrocket-base.conf"
DIST_DIR = ROOT / "dist"
ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
BASE_POLICY_KEYS = {"direct", "proxy", "reject"}
RULE_TYPES = {"local", "quixoticheart"}
SHADOWROCKET_RULES_PLACEHOLDER = "{{GENERATED_RULES}}"


class BuildError(ValueError):
    """Raised when the source configuration cannot be rendered safely."""


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load a TOML configuration file."""
    try:
        with path.open("rb") as file:
            data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise BuildError(f"无法读取配置 {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BuildError("rules.toml 顶层必须是 TOML 表。")
    return data


def require_string(table: dict[str, Any], key: str, context: str) -> str:
    """Return a required non-empty string."""
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BuildError(f"{context}.{key} 必须是非空字符串。")
    return value.strip()


def enabled_rules(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate and return enabled rules without changing their TOML order."""
    raw_rules = data.get("rules")
    if not isinstance(raw_rules, list):
        raise BuildError("rules.toml 必须包含一个或多个 [[rules]]。")

    result: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_rule in enumerate(raw_rules, start=1):
        context = f"rules[{index}]"
        if not isinstance(raw_rule, dict):
            raise BuildError(f"{context} 必须是 TOML 表。")

        rule_id = require_string(raw_rule, "id", context)
        if not ID_PATTERN.fullmatch(rule_id):
            raise BuildError(f"{context}.id 只能包含字母、数字、点、下划线和连字符。")
        if rule_id in seen_ids:
            raise BuildError(f"规则 ID 重复: {rule_id}")
        seen_ids.add(rule_id)

        rule_type = require_string(raw_rule, "type", context)
        if rule_type not in RULE_TYPES:
            raise BuildError(f"{context}.type 不支持: {rule_type}")

        policy = require_string(raw_rule, "policy", context)

        enabled = raw_rule.get("enabled", True)
        if not isinstance(enabled, bool):
            raise BuildError(f"{context}.enabled 必须是布尔值。")

        if rule_type == "local":
            require_string(raw_rule, "path", context)
        else:
            upstream_name = require_string(raw_rule, "upstream_name", context)
            if not ID_PATTERN.fullmatch(upstream_name):
                raise BuildError(
                    f"{context}.upstream_name 只能包含字母、数字、点、下划线和连字符。"
                )

        if enabled:
            result.append(raw_rule)

    return result


def get_repository(data: dict[str, Any]) -> tuple[str, str, str]:
    """Return repository coordinates used by local-rule Raw URLs."""
    repository = data.get("repository")
    if not isinstance(repository, dict):
        raise BuildError("缺少 [repository] 配置。")
    return (
        require_string(repository, "owner", "repository"),
        require_string(repository, "name", "repository"),
        require_string(repository, "branch", "repository"),
    )


def get_policies(data: dict[str, Any], client: str) -> dict[str, str]:
    """Return a client's logical-policy mapping."""
    policies = data.get("policies")
    if not isinstance(policies, dict):
        raise BuildError("缺少 [policies] 配置。")
    client_policies = policies.get(client)
    if not isinstance(client_policies, dict):
        raise BuildError(f"缺少 [policies.{client}] 配置。")

    result: dict[str, str] = {}
    for key, value in client_policies.items():
        if key == "final":
            continue
        if not isinstance(key, str) or not key:
            raise BuildError(f"policies.{client} 包含无效策略键。")
        if not isinstance(value, str) or not value.strip():
            raise BuildError(f"policies.{client}.{key} 必须是非空字符串。")
        result[key] = value.strip()

    missing = BASE_POLICY_KEYS - result.keys()
    if missing:
        missing_text = "、".join(sorted(missing))
        raise BuildError(f"policies.{client} 缺少基础策略: {missing_text}")
    return result


def get_final_policy(data: dict[str, Any], client: str) -> str:
    """Return a client's final unmatched-traffic policy."""
    policies = data.get("policies")
    if not isinstance(policies, dict):
        raise BuildError("缺少 [policies] 配置。")
    client_policies = policies.get(client)
    if not isinstance(client_policies, dict):
        raise BuildError(f"缺少 [policies.{client}] 配置。")
    return require_string(client_policies, "final", f"policies.{client}")


def get_mihomo_groups(
    data: dict[str, Any],
    policies: dict[str, str],
) -> list[dict[str, Any]]:
    """Return dynamic Mihomo proxy groups in TOML order."""
    raw_groups = data.get("mihomo_groups")
    if not isinstance(raw_groups, dict):
        raise BuildError("缺少 [mihomo_groups] 配置。")

    groups: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for policy_key, raw_group in raw_groups.items():
        context = f"mihomo_groups.{policy_key}"
        if policy_key not in policies:
            raise BuildError(f"{context} 未在 policies.mihomo 中定义。")
        if not isinstance(raw_group, dict):
            raise BuildError(f"{context} 必须是 TOML 表。")

        group_type = require_string(raw_group, "type", context)
        if group_type not in {"select", "url-test"}:
            raise BuildError(f"{context}.type 必须是 select 或 url-test。")

        raw_keywords = raw_group.get("keywords")
        if not isinstance(raw_keywords, list) or not raw_keywords:
            raise BuildError(f"{context}.keywords 必须是非空字符串数组。")
        keywords: list[str] = []
        for index, keyword in enumerate(raw_keywords, start=1):
            if not isinstance(keyword, str) or not keyword.strip():
                raise BuildError(
                    f"{context}.keywords[{index}] 必须是非空字符串。"
                )
            keywords.append(keyword.strip())

        group_name = policies[policy_key]
        if group_name in seen_names:
            raise BuildError(f"Mihomo 动态策略组名称重复: {group_name}")
        seen_names.add(group_name)
        group: dict[str, Any] = {
            "policy_key": policy_key,
            "name": group_name,
            "type": group_type,
            "keywords": keywords,
        }
        if group_type == "url-test":
            group["url"] = require_string(raw_group, "url", context)
            interval = raw_group.get("interval")
            if not isinstance(interval, int) or isinstance(interval, bool) or interval <= 0:
                raise BuildError(f"{context}.interval 必须是正整数。")
            group["interval"] = interval
        groups.append(group)
    return groups


def local_rule_url(owner: str, name: str, branch: str, path: str) -> str:
    """Build the GitHub Raw URL for a repository-owned rule file."""
    normalized_path = path.replace("\\", "/").lstrip("/")
    return (
        f"https://raw.githubusercontent.com/{owner}/{name}/refs/heads/"
        f"{branch}/{normalized_path}"
    )


def rule_url(
    rule: dict[str, Any],
    client: str,
    repository: tuple[str, str, str],
) -> str:
    """Build the client-specific remote URL for one rule."""
    if rule["type"] == "local":
        owner, name, branch = repository
        return local_rule_url(owner, name, branch, str(rule["path"]))

    upstream_name = str(rule["upstream_name"])
    target = "meta" if client == "mihomo" else "shadowrocket"
    return (
        "https://raw.githubusercontent.com/QuixoticHeart/rule-set/"
        f"refs/heads/ruleset/{target}/{upstream_name}.list"
    )


def load_shadowrocket_base(path: Path = SHADOWROCKET_BASE_PATH) -> str:
    """Load and validate the non-rule Shadowrocket configuration template."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"无法读取 Shadowrocket 基础配置 {path}: {exc}") from exc

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    placeholder_count = content.count(SHADOWROCKET_RULES_PLACEHOLDER)
    if placeholder_count != 1:
        raise BuildError(
            "config/shadowrocket-base.conf 必须且只能包含一个 "
            f"{SHADOWROCKET_RULES_PLACEHOLDER} 占位符。"
        )

    rule_section = re.search(
        r"(?ms)^\[Rule\]\s*\n(.*?)(?=^\[[^\]]+\]\s*$|\Z)",
        content,
    )
    if rule_section is None:
        raise BuildError("config/shadowrocket-base.conf 缺少 [Rule] 区段。")

    rule_body_lines = [
        line.strip()
        for line in rule_section.group(1).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if rule_body_lines != [SHADOWROCKET_RULES_PLACEHOLDER]:
        raise BuildError(
            "config/shadowrocket-base.conf 的 [Rule] 区段只能包含生成占位符。"
        )
    return content


def render_mihomo_script(data: dict[str, Any]) -> str:
    """Render a Clash Verge Rev global extension script."""
    repository = get_repository(data)
    policies = get_policies(data, "mihomo")
    final_policy = get_final_policy(data, "mihomo")
    proxy_groups = get_mihomo_groups(data, policies)
    dynamic_policy_keys = {
        str(group["policy_key"])
        for group in proxy_groups
    }
    rules = enabled_rules(data)

    providers: dict[str, dict[str, Any]] = {}
    rule_entries: list[dict[str, str | None]] = []
    for rule in rules:
        rule_id = str(rule["id"])
        provider_id = f"my-proxy-rules-{rule_id}"
        policy_key = str(rule["policy"])
        if policy_key not in policies:
            raise BuildError(
                f"规则 {rule['id']} 的 policy 未在 policies.mihomo 中定义: "
                f"{policy_key}"
            )
        providers[provider_id] = {
            "type": "http",
            "behavior": "classical",
            "format": "text",
            "url": rule_url(rule, "mihomo", repository),
            "path": f"./ruleset/my-proxy-rules/{rule_id}.list",
            "interval": 86400,
        }
        rule_entries.append(
            {
                "rule": f"RULE-SET,{provider_id},{policies[policy_key]}",
                "required_group": (
                    policies[policy_key]
                    if policy_key in dynamic_policy_keys
                    else None
                ),
            }
        )

    providers_json = json.dumps(providers, ensure_ascii=False, indent=2)
    groups_json = json.dumps(proxy_groups, ensure_ascii=False, indent=2)
    entries_json = json.dumps(rule_entries, ensure_ascii=False, indent=2)
    final_rule_json = json.dumps(f"MATCH,{final_policy}", ensure_ascii=False)
    return (
        "// 此文件由 scripts/build.py 自动生成。\n"
        "// 请勿直接编辑；请修改 config/rules.toml 或 rules/ 后重新构建。\n\n"
        f"const RULE_PROVIDERS = {providers_json};\n\n"
        f"const PROXY_GROUPS = {groups_json};\n\n"
        f"const RULE_ENTRIES = {entries_json};\n\n"
        "function createProxyGroups(config) {\n"
        "  const ownedNames = new Set(PROXY_GROUPS.map(group => group.name));\n"
        "  const originalGroups = (config[\"proxy-groups\"] || []).filter(group => {\n"
        "    return !ownedNames.has(group.name);\n"
        "  });\n"
        "  const proxyNames = (config.proxies || [])\n"
        "    .map(proxy => proxy.name)\n"
        "    .filter(Boolean);\n"
        "  const generatedGroups = [];\n"
        "  const activeGroupNames = new Set();\n\n"
        "  for (const group of PROXY_GROUPS) {\n"
        "    const keywords = group.keywords.map(keyword => keyword.toLowerCase());\n"
        "    const matchedNames = [...new Set(proxyNames.filter(name => {\n"
        "      const normalizedName = String(name).toLowerCase();\n"
        "      return keywords.some(keyword => normalizedName.includes(keyword));\n"
        "    }))];\n\n"
        "    if (matchedNames.length === 0) {\n"
        "      continue;\n"
        "    }\n"
        "    const generatedGroup = {\n"
        "      name: group.name,\n"
        "      type: group.type,\n"
        "      proxies: matchedNames\n"
        "    };\n"
        "    if (group.type === \"url-test\") {\n"
        "      generatedGroup.url = group.url;\n"
        "      generatedGroup.interval = group.interval;\n"
        "    }\n"
        "    generatedGroups.push(generatedGroup);\n"
        "    activeGroupNames.add(group.name);\n"
        "  }\n\n"
        "  config[\"proxy-groups\"] = [...generatedGroups, ...originalGroups];\n"
        "  return activeGroupNames;\n"
        "}\n\n"
        "function main(config) {\n"
        '  config["rule-providers"] = {\n'
        '    ...(config["rule-providers"] || {}),\n'
        "    ...RULE_PROVIDERS\n"
        "  };\n\n"
        "  const activeGroupNames = createProxyGroups(config);\n"
        "  const rules = RULE_ENTRIES\n"
        "    .filter(entry => {\n"
        "      return !entry.required_group || activeGroupNames.has(entry.required_group);\n"
        "    })\n"
        "    .map(entry => entry.rule);\n\n"
        "  // 本项目采用白名单代理模式，未匹配流量直接连接。\n"
        f"  config.rules = [...rules, {final_rule_json}];\n"
        "  return config;\n"
        "}\n"
    )


def render_shadowrocket(data: dict[str, Any]) -> str:
    """Render a complete Shadowrocket configuration."""
    repository = get_repository(data)
    policies = get_policies(data, "shadowrocket")
    final_policy = get_final_policy(data, "shadowrocket")

    rule_lines: list[str] = []
    for rule in enabled_rules(data):
        policy_key = str(rule["policy"])
        if policy_key not in policies:
            raise BuildError(
                f"规则 {rule['id']} 的 policy 未在 policies.shadowrocket 中定义: "
                f"{policy_key}"
            )
        url = rule_url(rule, "shadowrocket", repository)
        policy = policies[policy_key]
        rule_lines.append(f"RULE-SET,{url},{policy}")
    rule_lines.append(f"FINAL,{final_policy}")

    base = load_shadowrocket_base().strip()
    rendered = base.replace(
        SHADOWROCKET_RULES_PLACEHOLDER,
        "\n".join(rule_lines),
    )
    return (
        "# 此文件由 scripts/build.py 自动生成。\n"
        "# 请勿直接编辑。\n"
        "# 规则请修改 config/rules.toml 或 rules/；其余配置请修改 "
        "config/shadowrocket-base.conf。\n\n"
        f"{rendered}\n"
    )


def render_outputs(data: dict[str, Any]) -> dict[Path, str]:
    """Return every generated path and its deterministic content."""
    return {
        DIST_DIR / "mihomo-global-script.js": render_mihomo_script(data),
        DIST_DIR / "shadowrocket-rules.conf": render_shadowrocket(data),
    }


def main() -> int:
    """Build all distribution files."""
    try:
        outputs = render_outputs(load_config())
    except BuildError as exc:
        print(f"构建失败: {exc}")
        return 1

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"已生成: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
