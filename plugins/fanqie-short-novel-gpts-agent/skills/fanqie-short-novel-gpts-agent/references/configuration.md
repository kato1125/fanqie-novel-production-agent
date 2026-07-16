# 每位用户的独立配置

## 配置定位

按以下优先级查找 `番茄小说Agent配置.json`：

1. 用户在当前请求中明确给出的路径
2. 环境变量 `FANQIE_NOVEL_AGENT_CONFIG`
3. 当前工作区根目录
4. `~/Documents/自动小说/番茄小说Agent配置.json`

找到后运行：

```bash
python3 scripts/settings.py validate --config "<配置路径>"
```

新 Agent 兼容原番茄小说 Agent 的独立配置，不要求用户重复填写。

## 首次设置

配置不存在时执行：

```bash
python3 scripts/settings.py init \
  --config "<配置路径>" \
  --author-name "<作者名>" \
  --output-root "<输出根目录>" \
  --gpts-url "<指定 GPTs 地址>" \
  --gpts-account-hint "<可选：GPTs账号显示提示>" \
  --fanqie-workbench-url "<可选：番茄工作台地址>" \
  --fanqie-account-hint "<可选：番茄账号显示提示>" \
  --word-template "<可选：章节DOCX模板>"
```

## 字段用途

- `author_name`：封面及番茄作品作者名
- `output_root`：工程包、章节 Word、GPTs 合并版和断点的保存根目录
- `gpts.url`：负责选题、策划、正文和最终合并 DOCX 的指定 GPTs
- `gpts.account_hint`：核对 Chrome 登录账号的非敏感显示提示
- `fanqie.workbench_url`：番茄工作台地址，可留空
- `fanqie.account_hint`：番茄账号的非敏感显示提示
- `word.template_path`：可选章节 Word 模板，仅用于机械排版

AI 标记固定为“是”，试读比例固定为 30%。提交审核和发布默认关闭。

## 隐私与账号

- 配置不得保存密码、Cookie、令牌、密钥或其他登录凭据。
- GPTs 和番茄均使用用户当前 Chrome 登录会话。
- 页面账号与配置提示不一致时暂停确认，不自动切换账号。
- 不复制或分享任何用户的真实配置和登录状态。
