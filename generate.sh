#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

commit_message="${*:-Update proxy rules}"

fail() {
  printf '错误：%s\n' "$1" >&2
  exit 1
}

supports_python_311() {
  "$@" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' \
    >/dev/null 2>&1
}

PYTHON_CMD=()
if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_CMD=("$PYTHON_BIN")
  supports_python_311 "${PYTHON_CMD[@]}" ||
    fail "PYTHON_BIN 指向的 Python 不可用或版本低于 3.11。"
elif command -v python3 >/dev/null 2>&1 &&
  supports_python_311 python3; then
  PYTHON_CMD=(python3)
elif command -v python >/dev/null 2>&1 &&
  supports_python_311 python; then
  PYTHON_CMD=(python)
elif command -v py >/dev/null 2>&1 &&
  supports_python_311 py -3.11; then
  PYTHON_CMD=(py -3.11)
else
  fail "找不到 Python 3.11 或更高版本；也可以通过 PYTHON_BIN 指定解释器。"
fi

git rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
  fail "当前目录不是 Git 仓库。"
git remote get-url origin >/dev/null 2>&1 ||
  fail "没有配置 origin 远程仓库。"

if ! git diff --cached --quiet; then
  fail "暂存区已有改动，请先提交或取消暂存，避免混入本次自动提交。"
fi

printf '使用：'
"${PYTHON_CMD[@]}" --version

printf '\n[1/5] 构建配置\n'
"${PYTHON_CMD[@]}" scripts/build.py

printf '\n[2/5] 检查配置\n'
"${PYTHON_CMD[@]}" scripts/check.py

printf '\n[3/5] 暂存项目文件\n'
PROJECT_PATHS=(
  README.md
  .gitignore
  .gitattributes
  config/rules.toml
  config/shadowrocket-base.conf
  rules/custom-direct.list
  rules/custom-proxy.list
  rules/custom-reject.list
  scripts/build.py
  scripts/check.py
  dist/mihomo-global-script.js
  dist/shadowrocket-rules.conf
  .github/workflows/validate.yml
  generate.sh
)
git add -- "${PROJECT_PATHS[@]}"
git diff --cached --check

printf '\n将要提交的文件：\n'
git diff --cached --name-status

printf '\n[4/5] 提交\n'
if git diff --cached --quiet; then
  printf '没有需要提交的改动，跳过 commit。\n'
else
  git commit -m "$commit_message"
fi

printf '\n[5/5] 推送\n'
git push

printf '\n完成。\n'
