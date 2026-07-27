// 此文件由 scripts/build.py 自动生成。
// 请勿直接编辑；请修改 config/rules.toml 或 rules/ 后重新构建。

const RULE_PROVIDERS = {
  "my-proxy-rules-custom-proxy": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/Lafinyu/my-proxy-rules/refs/heads/main/rules/custom-proxy.list",
    "path": "./ruleset/my-proxy-rules/custom-proxy.list",
    "interval": 86400
  },
  "my-proxy-rules-cn": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/cn.list",
    "path": "./ruleset/my-proxy-rules/cn.list",
    "interval": 86400
  },
  "my-proxy-rules-cncidr": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/cncidr.list",
    "path": "./ruleset/my-proxy-rules/cncidr.list",
    "interval": 86400
  },
  "my-proxy-rules-apple-cn": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/apple-cn.list",
    "path": "./ruleset/my-proxy-rules/apple-cn.list",
    "interval": 86400
  },
  "my-proxy-rules-apple-proxy": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/apple-proxy.list",
    "path": "./ruleset/my-proxy-rules/apple-proxy.list",
    "interval": 86400
  },
  "my-proxy-rules-ai": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/ai.list",
    "path": "./ruleset/my-proxy-rules/ai.list",
    "interval": 86400
  },
  "my-proxy-rules-gits": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/gits.list",
    "path": "./ruleset/my-proxy-rules/gits.list",
    "interval": 86400
  },
  "my-proxy-rules-google": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/google.list",
    "path": "./ruleset/my-proxy-rules/google.list",
    "interval": 86400
  },
  "my-proxy-rules-netflix": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/netflix.list",
    "path": "./ruleset/my-proxy-rules/netflix.list",
    "interval": 86400
  },
  "my-proxy-rules-proxy": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/proxy.list",
    "path": "./ruleset/my-proxy-rules/proxy.list",
    "interval": 86400
  },
  "my-proxy-rules-spotify": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/spotify.list",
    "path": "./ruleset/my-proxy-rules/spotify.list",
    "interval": 86400
  },
  "my-proxy-rules-tld-proxy": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/tld-proxy.list",
    "path": "./ruleset/my-proxy-rules/tld-proxy.list",
    "interval": 86400
  },
  "my-proxy-rules-twitch": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/twitch.list",
    "path": "./ruleset/my-proxy-rules/twitch.list",
    "interval": 86400
  },
  "my-proxy-rules-youtube": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "url": "https://raw.githubusercontent.com/QuixoticHeart/rule-set/refs/heads/ruleset/meta/youtube.list",
    "path": "./ruleset/my-proxy-rules/youtube.list",
    "interval": 86400
  }
};

const PROXY_GROUPS = [
  {
    "policy_key": "ai_proxy",
    "name": "AI代理",
    "type": "select",
    "keywords": [
      "美国",
      "日本",
      "新加坡",
      "英国",
      "加拿大",
      "德国"
    ]
  },
  {
    "policy_key": "proxy",
    "name": "其他代理",
    "type": "url-test",
    "keywords": [
      "台湾",
      "香港"
    ],
    "url": "https://www.gstatic.com/generate_204",
    "interval": 300
  }
];

const RULE_ENTRIES = [
  {
    "rule": "RULE-SET,my-proxy-rules-custom-proxy,其他代理",
    "required_group": "其他代理"
  },
  {
    "rule": "RULE-SET,my-proxy-rules-cn,DIRECT",
    "required_group": null
  },
  {
    "rule": "RULE-SET,my-proxy-rules-cncidr,DIRECT",
    "required_group": null
  },
  {
    "rule": "RULE-SET,my-proxy-rules-apple-cn,DIRECT",
    "required_group": null
  },
  {
    "rule": "RULE-SET,my-proxy-rules-apple-proxy,其他代理",
    "required_group": "其他代理"
  },
  {
    "rule": "RULE-SET,my-proxy-rules-ai,AI代理",
    "required_group": "AI代理"
  },
  {
    "rule": "RULE-SET,my-proxy-rules-gits,其他代理",
    "required_group": "其他代理"
  },
  {
    "rule": "RULE-SET,my-proxy-rules-google,其他代理",
    "required_group": "其他代理"
  },
  {
    "rule": "RULE-SET,my-proxy-rules-netflix,其他代理",
    "required_group": "其他代理"
  },
  {
    "rule": "RULE-SET,my-proxy-rules-proxy,其他代理",
    "required_group": "其他代理"
  },
  {
    "rule": "RULE-SET,my-proxy-rules-spotify,其他代理",
    "required_group": "其他代理"
  },
  {
    "rule": "RULE-SET,my-proxy-rules-tld-proxy,其他代理",
    "required_group": "其他代理"
  },
  {
    "rule": "RULE-SET,my-proxy-rules-twitch,其他代理",
    "required_group": "其他代理"
  },
  {
    "rule": "RULE-SET,my-proxy-rules-youtube,其他代理",
    "required_group": "其他代理"
  }
];

function createProxyGroups(config) {
  const ownedNames = new Set(PROXY_GROUPS.map(group => group.name));
  const originalGroups = (config["proxy-groups"] || []).filter(group => {
    return !ownedNames.has(group.name);
  });
  const proxyNames = (config.proxies || [])
    .map(proxy => proxy.name)
    .filter(Boolean);
  const generatedGroups = [];
  const activeGroupNames = new Set();

  for (const group of PROXY_GROUPS) {
    const keywords = group.keywords.map(keyword => keyword.toLowerCase());
    const matchedNames = [...new Set(proxyNames.filter(name => {
      const normalizedName = String(name).toLowerCase();
      return keywords.some(keyword => normalizedName.includes(keyword));
    }))];

    if (matchedNames.length === 0) {
      continue;
    }
    const generatedGroup = {
      name: group.name,
      type: group.type,
      proxies: matchedNames
    };
    if (group.type === "url-test") {
      generatedGroup.url = group.url;
      generatedGroup.interval = group.interval;
    }
    generatedGroups.push(generatedGroup);
    activeGroupNames.add(group.name);
  }

  config["proxy-groups"] = [...generatedGroups, ...originalGroups];
  return activeGroupNames;
}

function main(config) {
  config["rule-providers"] = {
    ...(config["rule-providers"] || {}),
    ...RULE_PROVIDERS
  };

  const activeGroupNames = createProxyGroups(config);
  const rules = RULE_ENTRIES
    .filter(entry => {
      return !entry.required_group || activeGroupNames.has(entry.required_group);
    })
    .map(entry => entry.rule);

  // 本项目采用白名单代理模式，未匹配流量直接连接。
  config.rules = [...rules, "MATCH,DIRECT"];
  return config;
}
