# my-proxy-rules

`my-proxy-rules` 用一份按顺序维护的规则清单，同时生成 Clash Verge Rev 全局扩展脚本和可直接选用的完整 Shadowrocket 配置。项目只保存自己的补充规则；第三方规则通过远程 URL 引用，不复制、不重新发布。

## 设计逻辑

- `config/rules.toml` 是规则分类、策略和顺序的唯一配置来源。
- `config/shadowrocket-base.conf` 保存 Shadowrocket 的非规则配置。
- `rules/` 保存本项目自己的补充规则。
- `scripts/build.py` 按 TOML 中从上到下的顺序生成两个客户端的配置。
- `scripts/check.py` 检查配置、规则格式、敏感信息和生成文件一致性。
- `dist/` 保存生成结果，并应提交到 Git，方便客户端通过固定 URL 读取。

所有规则均采用“从上到下、首次匹配生效”。调整规则顺序时只修改 `config/rules.toml` 中 `[[rules]]` 的排列，构建脚本不会自动排序。

当前默认采用“白名单代理”模式：Mihomo 中的 AI 流量走动态生成的 `AI代理` 组，其他 `proxy` 规则走动态生成的 `其他代理` 组；没有命中规则的流量最终全部 `DIRECT`。Shadowrocket 使用自身已有的对应策略。因此通常不需要维护直连分类。

## 目录结构

```text
my-proxy-rules/
├── README.md
├── .gitignore
├── config/
│   ├── rules.toml
│   └── shadowrocket-base.conf
├── rules/
│   ├── custom-direct.list
│   ├── custom-proxy.list
│   └── custom-reject.list
├── scripts/
│   ├── build.py
│   └── check.py
├── dist/
│   ├── mihomo-global-script.js
│   └── shadowrocket-rules.conf
└── .github/
    └── workflows/
        └── validate.yml
```

## 修改统一配置

仓库地址和分支位于：

```toml
[repository]
owner = "Lafinyu"
name = "my-proxy-rules"
branch = "main"
```

公开到 GitHub 前，应确认 `owner`、`name` 和 `branch` 与实际仓库一致。本地规则会据此生成 Raw URL：

```text
https://raw.githubusercontent.com/{owner}/{name}/refs/heads/{branch}/{path}
```

两个客户端的策略名称分别在以下配置中维护：

```toml
[policies.mihomo]
proxy = "其他代理"
ai_proxy = "AI代理"
direct = "DIRECT"
reject = "REJECT"
final = "DIRECT"

[mihomo_groups.ai_proxy]
type = "select"
keywords = ["美国", "日本", "新加坡", "英国", "加拿大", "德国"]

[mihomo_groups.proxy]
type = "url-test"
keywords = ["台湾", "香港"]
url = "https://www.gstatic.com/generate_204"
interval = 300
tolerance = 100

[policies.shadowrocket]
proxy = "PROXY"
ai_proxy = "🇺🇸/美国/02/"
direct = "DIRECT"
reject = "REJECT"
final = "DIRECT"
```

`final` 控制未匹配流量的最终策略。Mihomo 生成 `MATCH,DIRECT`，Shadowrocket 生成 `FINAL,DIRECT`。

Mihomo 全局脚本从每个订阅的 `config.proxies` 中按关键词筛选节点。`AI代理` 是手动选择的 `select` 组，`其他代理` 是每 300 秒测速的 `url-test` 组，并设置 `tolerance = 100`，只有候选节点至少快 100 毫秒时才切换，减少延迟小幅波动造成的来回切换。某组没有匹配节点时，脚本不创建该组，也不添加指向它的规则，相应流量最终走 `DIRECT`。Shadowrocket 的 AI 规则使用指定策略，其他代理规则使用内置 `PROXY`，随首页当前选中的节点切换。

Shadowrocket 的 `[General]`、`[Host]` 和 `[URL Rewrite]` 位于 `config/shadowrocket-base.conf`。其中 `[Rule]` 必须保留唯一的 `{{GENERATED_RULES}}` 占位符，构建时会用 `rules.toml` 生成的规则和 `FINAL` 替换它。不要在基础配置的 `[Rule]` 中手工添加其他规则；需要补充规则时使用 `rules/` 和 `rules.toml`。

每个 `[[rules]]` 表示一项规则：

- `id`：项目内唯一标识，也用于 Mihomo 的 rule provider 名称。
- `type`：`local` 或 `quixoticheart`。
- `policy`：逻辑策略键，必须同时存在于 `[policies.mihomo]` 和 `[policies.shadowrocket]`。当前 AI 使用 `ai_proxy`，其他代理规则使用 `proxy`。
- `enabled`：是否参与生成。
- `path`：本地规则相对于项目根目录的路径，仅用于 `local`。
- `upstream_name`：QuixoticHeart 上游规则文件名，不含 `.list`，仅用于 `quixoticheart`。

## 添加自定义规则

在对应文件中添加一行一条的 classical 规则：

- `rules/custom-direct.list`：显式直连例外，默认禁用。
- `rules/custom-proxy.list`：优先代理。
- `rules/custom-reject.list`：显式拒绝例外，默认禁用。

支持的常用格式：

```text
DOMAIN,example.com
DOMAIN-SUFFIX,example.com
DOMAIN-KEYWORD,example
IP-CIDR,192.0.2.0/24,no-resolve
IP-CIDR6,2001:db8::/32,no-resolve
```

空行和以 `#` 开头的注释会被忽略。添加后运行构建和检查。

由于最终策略已经是 `DIRECT`，一般不需要向 `custom-direct.list` 添加规则。只有某个地址会先被较宽泛的代理规则命中、但你希望它例外直连时，才需要启用 `custom-direct` 并把它排在对应代理规则之前。

## 引用新的 QuixoticHeart 分类

在 `config/rules.toml` 的目标位置增加：

```toml
[[rules]]
id = "example-service"
type = "quixoticheart"
upstream_name = "example-service"
policy = "proxy"
enabled = true
```

普通第三方代理分类使用 `policy = "proxy"`；需要使用 AI 策略的分类写 `policy = "ai_proxy"`。Mihomo 会分别指向动态生成的 `其他代理` 和 `AI代理`；Shadowrocket 的普通代理走当前选中节点，AI 则走指定策略。不需要代理的第三方分类通常不要加入或设为 `enabled = false`，未匹配流量会由最终规则直接连接。

构建时会分别引用：

```text
# Mihomo
https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/{upstream_name}.list

# Shadowrocket
https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/shadowrocket/{upstream_name}.list
```

请先确认上游存在对应文件。第三方规则归 [QuixoticHeart/rule-set](https://github.com/QuixoticHeart/rule-set) 原项目维护者所有，本项目仅进行远程引用。

## 构建和检查

需要 Python 3.11 或更高版本，不需要安装第三方包：

```bash
python scripts/build.py
python scripts/check.py
```

构建会覆盖 `dist/mihomo-global-script.js` 和 `dist/shadowrocket-rules.conf`。后者是由 Shadowrocket 基础配置与统一规则合成的完整配置。检查脚本不会修改文件，而是重新在内存中生成预期内容并与 `dist/` 比较；如果不一致，会提示先重新构建。

在 Git Bash 中也可以用 `generate.sh` 一次完成构建、检查、暂存、提交和推送。只调整具体规则时不传提交说明，脚本会 amend 当前提交并使用 `--force-with-lease` 安全覆盖远端最新版本，不增加提交数量：

```bash
./generate.sh
```

调整项目功能或特性时传入提交说明，脚本才会创建并正常推送一个新提交：

```bash
./generate.sh "Add a new feature"
```

脚本要求暂存区在运行前为空，避免把已有暂存内容混入自动提交。如果 Python 不在常规命令路径中，可以指定解释器：

```bash
PYTHON_BIN="/path/to/python" ./generate.sh
```

## Clash Verge Rev 使用方法

`dist/mihomo-global-script.js` 是全局扩展脚本，不包含节点或订阅。它执行三项操作：

- 将项目生成的远程 `rule-providers` 合并到订阅已有 provider 中。
- 根据 `[mihomo_groups]` 关键词创建 `AI代理` 和 `其他代理`。
- 按 `rules.toml` 顺序设置规则，并以 `MATCH,DIRECT` 收尾。

在 Clash Verge Rev 中打开“全局扩展脚本”，用生成文件内容替换原脚本，保存后刷新或重新启用当前订阅。脚本会替换自己管理的同名策略组，不需要各订阅预先提供统一策略名称。

脚本会用项目生成的规则替换订阅原有规则；最后一条 `MATCH,DIRECT` 保证没有命中本项目代理或拒绝规则的流量直接连接。如果某个订阅没有符合一组关键词的节点，对应策略组和规则会被跳过。

以后增加规则分类时，只需在 `config/rules.toml` 末尾或目标优先级位置添加新的 `[[rules]]`，选择 `policy = "proxy"` 或 `policy = "ai_proxy"`，然后重新构建并把新的全局扩展脚本应用到 Clash Verge Rev。

## Shadowrocket 使用方法

`dist/shadowrocket-rules.conf` 是可直接选用的完整配置，包含 `[General]`、生成的 `[Rule]`、`[Host]` 和 `[URL Rewrite]`。AI 规则引用现有的 `🇺🇸/美国/02/` 策略，其他代理规则使用 Shadowrocket 内置 `PROXY`，跟随首页当前选中的节点。

在 Shadowrocket 中通过以下 GitHub Raw URL 下载配置，然后将它设为当前配置：

```text
https://raw.githubusercontent.com/{owner}/{name}/refs/heads/{branch}/dist/shadowrocket-rules.conf
```

配置不包含代理服务器、订阅地址或访问凭据，节点继续由 Shadowrocket 应用管理。请确认应用中存在名称完全一致的 AI 策略。仓库更新并重新构建、提交和推送后，在 Shadowrocket 中更新这份远程配置即可同步；生成内容只包含一条 `FINAL,DIRECT`。

## 安全与维护

- 公开仓库中不得提交机场订阅地址、代理节点、GitHub Token、密码、内部域名或敏感 IP。
- `dist/` 是生成文件，但应提交到 Git；修改源配置后必须重新构建并一并提交。
- 不要直接编辑 `dist/`，否则下次构建会覆盖手工修改。
- GitHub Actions 只执行构建、检查和差异验证，不会自动提交或推送。
