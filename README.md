# agent-skills

> English | [简体中文](README.zh.md)

## Overview
This repository collects agent skill examples and related resources to help you study, experiment, or integrate them into your own projects.

## Skills Collection

### Claude Code Skills (`claude-skills/`)

Skills designed for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI tool.

| Skill | Description |
|-------|-------------|
| [`ds-citations`](claude-skills/ds-citations/) | Deep Research Citation Formatter - Convert GPT/Gemini Deep Research citations to Markdown footnotes |

### GLM Skills (`glm-skills/`)

Skills for GLM (ChatGLM) models.

### OpenAI Skills (`openai-skills/`)

Skills for OpenAI models.

## Recommended official repositories
- [anthropics/skills](https://github.com/anthropics/skills): Anthropic skill examples illustrating prompt patterns, tool use, and safety considerations.
- [openai/skills](https://github.com/openai/skills): Official OpenAI skill examples covering diverse scenarios and best practices for comparison or reuse.

## Usage

### Claude Code Skills

Copy the skill folder to your project's `.claude/skills/` directory:

```bash
cp -r claude-skills/ds-citations /path/to/your/project/.claude/skills/
```

Then use the skill via command line:

```bash
python .claude/skills/ds-citations/scripts/format_ds_citations.py -c <file>
```

## Contributing

Feel free to submit pull requests with new skills or improvements to existing ones.

## License

Each skill may have its own license. Check the individual skill folders for details.
