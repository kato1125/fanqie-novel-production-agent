# 每位使用者的独立配置

## 目录

1. 配置定位
2. 首次设置
3. 字段说明
4. 账号与隐私
5. 分享规则

## 1. 配置定位

每位使用者维护自己的 `番茄小说Agent配置.json`，不要把真实配置打包进插件。按以下优先级定位：

1. 用户在当前请求中明确给出的配置路径
2. 环境变量 `FANQIE_NOVEL_AGENT_CONFIG`
3. 当前工作区根目录的 `番茄小说Agent配置.json`
4. `~/Documents/自动小说/番茄小说Agent配置.json`

找到配置后，必须先运行 `scripts/settings.py validate`。若没有配置，进入设置关卡，一次性收集必需信息并用脚本创建；不得使用插件作者的个人值代替。

## 2. 首次设置

```bash
python3 scripts/settings.py init \
  --config "<配置文件路径>" \
  --author-name "<小说作者名>" \
  --output-root "<小说输出根目录>" \
  --gpts-url "<指定 GPTs 地址>" \
  --gpts-account-hint "<可选：GPTs 账号显示名>" \
  --fanqie-workbench-url "<可选：番茄工作台地址>" \
  --fanqie-account-hint "<可选：番茄账号显示名>" \
  --word-template "<可选：DOCX 模板路径>"

python3 scripts/settings.py validate --config "<配置文件路径>"
```

模板留空时使用稳定的默认 Word 样式。模板存在时必须是非空 DOCX。此工作流始终跳过 Word 图片渲染和视觉检查。

## 3. 字段说明

- `author_name`：写入封面及番茄作品信息的小说作者名
- `output_root`：每本书文件夹、章节 Word、合并文件和断点的根目录
- `gpts.url`：负责全部文学创作和封面的指定 GPTs 地址
- `gpts.account_hint`：用于核对当前 Chrome 登录账号的非敏感显示提示
- `fanqie.workbench_url`：可留空；留空时从当前 Chrome 已登录状态进入工作台
- `fanqie.account_hint`：用于核对当前番茄账号的非敏感显示提示
- `word.template_path`：可选固定 Word 模板

AI 标记固定为“是”，试读比例固定为 30%，分类仍根据平台当时可选项推荐。提交审核和发布默认并强制为关闭。

## 4. 账号与隐私

- 配置只允许保存账号显示提示，不保存密码、Cookie、令牌、密钥或登录凭据。
- GPTs 和番茄都使用每位使用者自己的当前 Chrome 登录会话。
- 若页面显示的账号与配置提示不一致，停止并要求使用者确认；不得自动切换账号。
- 若使用者无权访问指定 GPTs 或番茄工作台，报告阻塞，不尝试绕过权限。

## 5. 分享规则

- 分享插件时只包含 `assets/config.example.json`，不包含任何人的真实配置。
- 接收者首次运行必须创建自己的配置。
- 不复制浏览器配置、登录态、Cookie、密码或番茄草稿标识。
- 已有书籍断点保存其创建时的配置路径和非敏感账号提示，用于断网恢复时核对环境。
