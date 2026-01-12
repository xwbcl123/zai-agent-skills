# agent-skills

> [English](README.md) | 简体中文

## 简介
本仓库用于收集和整理各类 Agent 技能示例与资源，便于在本地学习、试验或整合到自己的项目中。

## 技能合集

### Claude Code 技能 (`claude-skills/`)

为 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI 工具设计的技能。

| 技能 | 描述 |
|------|------|
| [`ds-citations`](claude-skills/ds-citations/) | Deep Research 引用格式转换器 - 将 GPT/Gemini 深度研究报告的引用转换为 Markdown 脚注格式 |

### GLM 技能 (`glm-skills/`)

适用于 GLM (ChatGLM) 模型的技能。

### OpenAI 技能 (`openai-skills/`)

适用于 OpenAI 模型的技能。

## 推荐官方资源库
- [anthropics/skills](https://github.com/anthropics/skills)：Anthropic 发布的技能示例，可参考提示工程、工具调用与安全相关范式。
- [openai/skills](https://github.com/openai/skills)：OpenAI 官方技能示例，涵盖多种使用场景和最佳实践，适合对照学习或复用。

## 使用方法

### Claude Code 技能

将技能文件夹复制到项目的 `.claude/skills/` 目录：

```bash
cp -r claude-skills/ds-citations /path/to/your/project/.claude/skills/
```

然后通过命令行使用：

```bash
python .claude/skills/ds-citations/scripts/format_ds_citations.py -c <文件>
```

## 贡献

欢迎提交 Pull Request 来添加新技能或改进现有技能。

## 许可证

每个技能可能有自己的许可证，请查看各技能文件夹中的详细说明。
