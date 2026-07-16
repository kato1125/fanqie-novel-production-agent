---
name: fanqie-short-novel-gpts-agent
description: Automate Fanqie short-novel production from an engineering-package DOCX uploaded in the current Codex conversation. Use one persistent custom-GPTs conversation for topic proposals, user-confirmed topic planning, and one-time chapter prose generation; mechanically save local chapter DOCX files, require the GPTs to generate the final merged DOCX, and configure a Fanqie draft without literary review or publication. Use when the user asks to start, resume, standardize, or inspect this simplified 番茄短篇 workflow.
---

# 番茄短篇 GPTs 一次直出 Agent

## 工作约定

开始或恢复生产前，完整读取 [references/workflow.md](references/workflow.md) 和
[references/configuration.md](references/configuration.md)。创建或恢复断点时，再读取
[references/checkpoint-schema.md](references/checkpoint-schema.md)。

以下规则不可擅自改变：

1. 工程包由用户上传到当前 Codex 对话；将附件机械保存到书籍目录后再交给 GPTs。
2. 所有创意工作都由配置中的同一个 GPTs、同一个持续对话完成。
3. GPTs 只生成选题列表；必须把全部选题原样交给用户并暂停，禁止代选。
4. 只有用户明确选择选题后，才能让 GPTs继续策划和正文。
5. 每章正文只请求和生成一次；首次输出即视为该章最终正文。
6. 不进行全书文学复核、二次润色、章节重写或本地文学修改。
7. 本地只机械保存每章正文及章节 DOCX，不改变措辞、标点、段落或顺序。
8. 全部章节完成后，必须由同一个 GPTs 生成可下载的最终合并版 DOCX；本地不得合并。
9. GPTs 合并时只能汇总已完成章节，不得润色、删改或重新生成正文。
10. 番茄正文只能来自 GPTs 生成的最终合并版 DOCX。
11. 默认只保存番茄草稿。没有新的明确授权，不提交审核、不发布、不签约。
12. 每完成一个转换步骤，先更新断点，再开始下一步。

## 工具路由

- 使用 `scripts/settings.py` 定位、创建和验证每位用户自己的配置。
- 使用 `chrome:control-chrome` 操作已登录的 GPTs 和番茄工作台。
- 使用本地文档能力机械创建章节 DOCX；禁止借此改写正文。
- 最终合并版必须下载自 GPTs，不调用本地 Word 合并程序作为替代。
- 使用 `scripts/checkpoint.py` 写入生产状态，正常流程不手工编辑状态 JSON。
- 若 GPTs 无法生成可下载的最终 DOCX，停止并报告阻塞，不在本地代做合并版。

## 断点命令

开始前验证配置：

```bash
python3 scripts/settings.py validate --config "<番茄小说Agent配置.json>"
```

初始化新书：

```bash
python3 scripts/checkpoint.py init \
  --settings-file "<番茄小说Agent配置.json>" \
  --book-dir "<output_root>/<待定书名-时间或正式书名>" \
  --title "<待定书名或正式书名>" \
  --engineering-package "<已保存的工程包.docx>"
```

恢复生产：

```bash
python3 scripts/checkpoint.py resume --book-dir "<书籍目录>"
python3 scripts/checkpoint.py verify --book-dir "<书籍目录>"
```

使用 `python3 scripts/checkpoint.py --help` 查看推进步骤、确认选题、章节、文件、
浏览器和番茄草稿等子命令。

## 人工关卡

只在以下节点暂停：

- **设置关卡**：没有有效独立配置时，收集非敏感配置并验证。
- **选题关卡**：原样展示全部 GPTs 选题，等待用户亲自选择。
- **异常关卡**：GPTs 章节输出不完整、重复生成风险、无法生成最终合并 DOCX，或账号不一致。
- **发布关卡**：番茄草稿保存完成后停止；发布必须获得新的明确授权。

自动发送常规提示的权限不包括代选选题、重写章节、全书复核或发布。

## 完成汇报

汇报正式书名、用户选择的选题、章节总数、章节 Word 文件夹、GPTs 最终合并版
DOCX 路径、封面路径（若生成）、番茄草稿状态、AI 标记、分类、试读比例和断点的
下一动作。明确说明是否进行过文学复核、提交审核或发布。
