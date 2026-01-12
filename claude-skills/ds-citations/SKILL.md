---
name: ds-citations
description: "Deep Research Citation Formatter - Convert GPT/Gemini Deep Research reports citations to Markdown footnote format. Use when processing AI-generated research reports with messy citation formats."
---

# Deep Research Citation Formatter

Convert citations from GPT-4o Deep Research and Gemini 2.0 Deep Research reports into clean Markdown footnote format.

## When to Use This Skill

- Processing Deep Research reports from GPT or Gemini
- Converting `[[n]](URL)` (GPT) or ` n。` (Gemini) citations to `[^n]` format
- Validating citation integrity (checking for missing/orphan references)
- Batch processing multiple research reports

## Supported Formats

| Source | Inline Format | Reference Format |
|--------|---------------|------------------|
| **GPT Deep Research** | `[[n]](URL)` or `[\[n\]](URL)` | Various mixed formats |
| **Gemini Deep Research** | ` n。` (space + number + punctuation) | `1. Title, 访问时间为..., [URL](URL)` |

## Target Format

```markdown
Inline: [^n]
Reference: [^n]: Title URL
```

## Usage

### Basic Commands

```bash
# Convert a single file
python .claude/skills/ds-citations/scripts/format_ds_citations.py report.md

# Preview changes without writing (dry run)
python .claude/skills/ds-citations/scripts/format_ds_citations.py -n report.md

# Check format and citation counts
python .claude/skills/ds-citations/scripts/format_ds_citations.py -c report.md

# Process a directory
python .claude/skills/ds-citations/scripts/format_ds_citations.py ./deep-research/

# Recursive directory processing
python .claude/skills/ds-citations/scripts/format_ds_citations.py -r ./sources/
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `-n, --dry-run` | Preview changes without writing |
| `-c, --check` | Check format and citation counts only |
| `-f, --force` | Force re-process already converted files |
| `-r, --recursive` | Process subdirectories recursively |
| `-v, --verbose` | Show detailed output |
| `-h, --help` | Show help message |

## Output Symbols

| Symbol | Meaning |
|--------|---------|
| ✓ | Successfully processed/converted |
| ◈ | Already in target format (no processing needed) |
| ⊘ | Skipped (unknown format or no changes) |
| ✗ | Error |
| ⚠ | Warning (e.g., missing references) |

## Workflow Example

### Step 1: Check Current State

```bash
python .claude/skills/ds-citations/scripts/format_ds_citations.py -c ./deep-research/
```

Output:
```
Processing: [DS-GPT]report.md
  ✓ Format: gpt | Needs conversion | Inline: 45 | Refs: 40

Processing: [DS-Gemini]report.md
  ◈ Format: converted | Inline: 70 unique | Refs: 70
```

### Step 2: Preview Changes

```bash
python .claude/skills/ds-citations/scripts/format_ds_citations.py -n report.md
```

### Step 3: Convert

```bash
python .claude/skills/ds-citations/scripts/format_ds_citations.py report.md
```

### Step 4: Verify

```bash
python .claude/skills/ds-citations/scripts/format_ds_citations.py -c report.md
```

## Features

### Format Detection
- Automatically detects GPT, Gemini, or already-converted formats
- Distinguishes between "unknown format" and "already converted"

### Citation Counting
- Counts inline citations and reference definitions
- Reports unique citation numbers
- Detects missing references (inline without definition)
- Detects orphan references (definition without inline usage)

### Safety
- Automatic backup (`.bak` files) before any modification
- Preview mode for safe testing
- No changes made in check-only mode

## Troubleshooting

### "Unknown format - skipping"
The file doesn't match known GPT or Gemini patterns. It may be:
- A non-research document
- Already manually formatted
- Using a different AI tool's format

### "Missing refs" Warning
Some inline citations don't have corresponding reference definitions. This usually indicates:
- Incomplete conversion
- Errors in the original document
- References accidentally deleted

### "Already converted"
The file is already in `[^n]` footnote format. Use `-f` flag to force re-check.

## File Locations

| File | Location |
|------|----------|
| Main Script | `.claude/skills/ds-citations/scripts/format_ds_citations.py` |
| This Documentation | `.claude/skills/ds-citations/SKILL.md` |

## Version History

- **v2.0** (2026-01-12): Added check mode, force mode, citation counting, improved format detection
- **v1.0** (2026-01-12): Initial version with GPT/Gemini conversion
