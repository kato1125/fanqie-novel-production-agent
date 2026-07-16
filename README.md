# 番茄小说 Agent 插件市场

这是一个可安装的 Codex 插件市场，目前包含：

- `fanqie-short-novel-gpts-agent`：新版番茄短篇 GPTs 一次直出 Agent
- `fanqie-novel-production-agent`：原版番茄小说自动生产 Agent

## 安装

```bash
codex plugin marketplace add kato1125/fanqie-novel-production-agent
```

重启 ChatGPT/Codex 桌面端，在插件目录中选择“番茄小说 Agent”。

推荐安装“番茄短篇 GPTs 一次直出 Agent”。也可以在终端直接安装：

```bash
codex plugin add fanqie-short-novel-gpts-agent@fanqie-novel-agent-marketplace
```

新建任务后调用：

```text
$fanqie-short-novel-gpts-agent
```

新版流程固定为：

- 工程包在当前对话上传
- GPTs 生成全部选题，由用户亲自选择
- GPTs 完成策划和各章正文
- 每章正文只生成一次
- 不进行全书文学复核
- 本地只机械保存章节 Word
- 最终合并版 Word 由同一个 GPTs 生成
- 合并版作为番茄正文唯一来源
- 默认只保存草稿，不提交审核或发布

首次运行会要求创建使用者自己的 `番茄小说Agent配置.json`，包括作者名、输出目录、
GPTs 地址、非敏感账号提示和可选 Word 模板。指定 GPTs 若不是公开 GPT，还需要由
GPT 创建者单独授予使用权限。

本仓库不包含任何人的密码、Cookie、Token、浏览器登录状态、番茄草稿或真实个人配置。
