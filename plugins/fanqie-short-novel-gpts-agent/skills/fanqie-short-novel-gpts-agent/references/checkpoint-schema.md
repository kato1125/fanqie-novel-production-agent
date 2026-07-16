# 断点状态与恢复规则

## 状态文件

每本书目录保存：

- `生产状态.json`：机器可读的唯一状态源
- `生产日志.md`：只追加的事件记录

使用 `scripts/checkpoint.py` 原子写入，正常流程不手工修改。

## 固定策略

断点必须保存以下不可变策略：

- `topic_selection_policy`: `user_only`
- `chapter_generation_policy`: `once`
- `literary_review`: `false`
- `merged_docx_provider`: `gpts`
- `local_merge_allowed`: `false`

## 章节阶段

章节只允许单调推进：

`pending → generating → generated → text_saved → word_saved → finalized`

首次进入 `generating` 时将 `generation_count` 设为 1。脚本拒绝第二次进入正文生成。
恢复时先检查同一 GPTs 对话和本地文件，不得因为线程重启重复请求章节。

## 主要状态

断点记录：

- 配置路径、工程包、书名、作者和输出目录
- GPTs 对话 URL、番茄草稿 URL 与草稿 ID
- GPTs 原始选题、用户选题和确认状态
- 冻结策划、章节总数和各章阶段
- 各章纯文本与本地章节 Word 路径
- GPTs 最终合并版 DOCX 与番茄唯一上传源
- 封面、AI 标记、分类、试读比例和草稿状态
- 发布授权、提交审核和发布状态

不设置全书复核报告、复核完成或本地合并文件状态。

## 恢复顺序

1. 验证独立配置和账号提示。
2. 运行 `resume` 与 `verify`。
3. 打开断点登记的同一个 GPTs 对话。
4. 已有完整 GPTs 章节输出时只完成机械保存，不重新生成。
5. 已有章节 Word 时直接跳过该章。
6. 最终合并版存在时不得再次要求 GPTs 生成。
7. 番茄草稿存在时恢复原草稿，不新建重复草稿。
8. 从 `next_action` 继续。

## 发布保护

- `publish_authorized`、`submitted_for_review` 和 `published` 默认均为 `false`。
- 没有用户新消息中的明确授权证据，脚本拒绝记录提交或发布。
- 自动执行许可、选题选择和上传正文都不等于发布授权。
