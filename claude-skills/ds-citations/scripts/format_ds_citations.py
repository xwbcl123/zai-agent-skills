#!/usr/bin/env python3
"""
Deep Research Citation Formatter
================================

Convert Deep Research reports (GPT/Gemini) citations to Markdown footnote format.

Usage:
    python format_ds_citations.py <file_or_directory>
    python format_ds_citations.py -n <file>  # Preview mode (dry run)
    python format_ds_citations.py -c <file>  # Check mode (verify format only)
    python format_ds_citations.py -f <file>  # Force re-process converted files

Options:
    -n, --dry-run   Preview changes without writing
    -c, --check     Check file format without processing
    -f, --force     Force re-process even if already converted
    -r, --recursive Process subdirectories recursively
    -v, --verbose   Show detailed output
    -h, --help      Show this help message
"""

import re
import sys
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# =============================================================================
# Configuration
# =============================================================================

GPT_INLINE_PATTERN = re.compile(r'\[\\?\[(\d+)\\?\]\]\([^)]+\)')
GEMINI_INLINE_PATTERN = re.compile(r'(?<=[^\d\[]) ?(\d{1,3})(?=[。，,\s]|$)')
GEMINI_REF_PATTERN = re.compile(
    r'^(\d+)\. (.+?)(?:, 访问时间为[^，]+，)? ?\[?(https?://[^\s\]]+)\]?\(?[^)]*\)?$',
    re.MULTILINE
)
# Pattern to detect already-converted footnote format
CONVERTED_INLINE_PATTERN = re.compile(r'\[\^(\d+)\]')
CONVERTED_REF_PATTERN = re.compile(r'^\[\^(\d+)\]:', re.MULTILINE)

@dataclass
class ProcessResult:
    """Result of processing a file."""
    success: bool
    message: str
    format_type: str = 'unknown'
    citations_before: int = 0
    citations_after: int = 0
    refs_before: int = 0
    refs_after: int = 0

@dataclass
class DirectoryStats:
    """Statistics for directory processing."""
    processed: int = 0
    converted: int = 0  # Already in target format
    skipped: int = 0    # Unknown format
    errors: int = 0

    def total(self) -> int:
        return self.processed + self.converted + self.skipped + self.errors

# =============================================================================
# Format Detection
# =============================================================================

def detect_format(content: str) -> str:
    """
    Detect the report format: 'gpt', 'gemini', 'converted', or 'unknown'

    GPT format: Contains [[n]](URL) pattern in text
    Gemini format: Contains numbered citations like " 1。" and numbered references at end
    Converted format: Already has [^n] inline and [^n]: reference format
    """
    # Check for GPT format (has [[n]](URL) pattern)
    if r'[\[' in content or r'[\\[' in content:
        return 'gpt'

    # Check for Gemini format (has numbered references at end)
    # Look for pattern like "1. Title ... [URL](URL)" at end of document
    if re.search(r'\n\d+\..+访问时间为', content):
        return 'gemini'

    # Fallback: check for Gemini-style inline citations (space + number + punctuation)
    # But NOT if it already has [^n] format
    if re.search(r'\s\d{1,3}[。，]', content) and not CONVERTED_INLINE_PATTERN.search(content):
        return 'gemini'

    # Check for already-converted format
    inline_matches = CONVERTED_INLINE_PATTERN.findall(content)
    ref_matches = CONVERTED_REF_PATTERN.findall(content)
    if inline_matches and ref_matches:
        return 'converted'

    return 'unknown'


def count_citations(content: str, format_type: str) -> Tuple[int, int]:
    """
    Count inline citations and reference definitions in the content.

    Returns:
        (inline_count, ref_count)
    """
    if format_type == 'gpt':
        inline_count = len(GPT_INLINE_PATTERN.findall(content))
        # Count [^n]: patterns for refs
        ref_count = len(re.findall(r'^\[\^(\d+)\]:', content, re.MULTILINE))
        # If no [^n]: refs, count [[n]](URL) patterns in ref section
        if ref_count == 0 and '---' in content:
            ref_section = content.split('---')[-1]
            ref_count = len(set(GPT_INLINE_PATTERN.findall(ref_section)))
    elif format_type == 'gemini':
        inline_count = len(GEMINI_INLINE_PATTERN.findall(content))
        ref_count = len(GEMINI_REF_PATTERN.findall(content))
    elif format_type == 'converted':
        inline_count = len(CONVERTED_INLINE_PATTERN.findall(content))
        ref_count = len(CONVERTED_REF_PATTERN.findall(content))
    else:
        inline_count = 0
        ref_count = 0

    return inline_count, ref_count


def get_unique_citation_numbers(content: str) -> Tuple[set, set]:
    """
    Get unique citation numbers from inline and reference sections.

    Returns:
        (inline_numbers_set, ref_numbers_set)
    """
    inline_nums = set(CONVERTED_INLINE_PATTERN.findall(content))
    ref_nums = set(CONVERTED_REF_PATTERN.findall(content))
    return inline_nums, ref_nums

# =============================================================================
# GPT Format Conversion
# =============================================================================

def convert_gpt_inline(content: str) -> str:
    """Convert GPT inline citations: [[n]](URL) → [^n]"""
    result = GPT_INLINE_PATTERN.sub(r'[^\1]', content)
    return result

def convert_gpt_variant_references(content: str) -> str:
    """
    Handle GPT variant format where references section has:
    [[n]](URL) [[m]](URL) Title
    [URL](URL)

    Convert to:
    [^n]: Title URL
    [^m]: Title URL

    Only processes content after '---' separator.
    """
    # Split at the reference section separator
    if '---' in content:
        main_content, ref_content = content.split('---', 1)
    else:
        # No separator found, return as-is
        return content

    lines = ref_content.split('\n')
    result = []
    i = 0
    skip_next = False

    while i < len(lines):
        line = lines[i]

        # Skip URL lines that follow reference lines
        if skip_next:
            skip_next = False
            i += 1
            continue

        # Check for reference lines in variant format: [[n]](URL) [[m]](URL) Title
        citation_pattern = re.compile(r'\[\\?\[(\d+)\\?\]\]\([^)]+\)')
        citations = citation_pattern.findall(line)

        if len(citations) >= 1:
            # This is a reference line in variant format
            # Remove all [[n]](URL) patterns to get the title
            title = citation_pattern.sub('', line).strip()

            # Check if next line is a raw URL markdown link
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Match [URL](URL) pattern - check for markdown link
                url_link_pattern = re.compile(r'\[https?://[^]]+\]\(https?://[^)]+\)')
                if url_link_pattern.match(next_line):
                    # Extract the URL from the markdown link
                    url_match = re.search(r'\]\((https?://[^)]+)\)', next_line)
                    if url_match:
                        url = url_match.group(1)
                        # Add all citations with this URL and title
                        for num in citations:
                            result.append(f'[^{num}]: {title} {url}')
                        # Mark next line to skip
                        skip_next = True
                        i += 1
                        continue

            # No separate URL line found, use URLs from the inline citations
            urls = re.findall(r'\[\\?\[\d+\\?\]\]\(([^)]+)\)', line)
            for j, num in enumerate(citations):
                url = urls[j] if j < len(urls) else ''
                if url:
                    result.append(f'[^{num}]: {title} {url}')
                else:
                    result.append(f'[^{num}]: {title}')
        else:
            # Skip raw URL markdown lines that stand alone
            url_link_pattern = re.compile(r'^\[https?://[^]]+\]\(https?://[^)]+\)$')
            if not url_link_pattern.match(line.strip()):
                result.append(line)

        i += 1

    # Reconstruct the file with the converted references section
    new_ref_content = '\n'.join(result)
    return main_content + '---\n' + new_ref_content

def convert_gpt_references(content: str) -> str:
    """
    Clean up GPT references section.

    The GPT format already has [^n]: format but with messy [[m]](URL) inline links.
    We need to clean those up and extract proper URLs.
    """
    lines = content.split('\n')
    result = []
    in_references = False
    skip_raw_urls = False

    for line in lines:
        # Detect references section
        if line.strip().startswith('## 参考文献') or line.strip().startswith('## References'):
            in_references = True
            result.append(line)
            continue

        # Detect the start of raw URL list (after ---)
        if in_references and line.strip() == '---':
            skip_raw_urls = True
            continue

        if skip_raw_urls:
            # Skip everything after the raw URL list
            continue

        if in_references:
            # Process reference lines like: [^1]: Title [[140]](URL)[[23]](URL)
            if line.strip().startswith('[^') or line.strip().startswith(r'\[^'):
                # Remove all [[n]](URL) patterns and collect URLs
                urls = re.findall(r'\[\\?\[\d+\\?\]\]\(([^)]+)\)', line)
                title = re.sub(r'\[\\?\[\d+\\?\]\]\([^)]+\)', '', line)
                title = re.sub(r'\s+', ' ', title).strip()

                # Remove escaped backslashes
                title = title.replace(r'\[', '[').replace(r'\]', ']')

                # Reconstruct clean reference
                if title.startswith('[^'):
                    # Extract the number
                    match = re.match(r'\[\^?(\d+)\]?:\s*(.+)', title)
                    if match:
                        num, rest = match.groups()
                        # Clean up any remaining [^n] patterns in the title
                        rest = re.sub(r'\[\^?\d+\]?:?', '', rest).strip()
                        if urls:
                            result.append(f'[^{num}]: {rest} {urls[0]}')
                        else:
                            result.append(f'[^{num}]: {rest}')
                    else:
                        result.append(line)
                else:
                    result.append(line)
            elif line.strip().startswith('**其它来源'):
                # Keep the "other sources" line
                result.append(line)
            else:
                result.append(line)
        else:
            result.append(line)

    return '\n'.join(result)

# =============================================================================
# Gemini Format Conversion
# =============================================================================

def convert_gemini_inline(content: str) -> str:
    """Convert Gemini inline citations: n。 → [^n]

    Skip heading lines (starting with #) to avoid converting heading numbers.
    """
    result = []
    for line in content.split('\n'):
        # Skip heading lines
        if line.strip().startswith('#'):
            result.append(line)
            continue

        # Apply conversion
        converted = GEMINI_INLINE_PATTERN.sub(r' [^\1]', line)
        result.append(converted)

    return '\n'.join(result)

def convert_gemini_references(content: str) -> str:
    """
    Convert Gemini references section.

    From: "1. Title, 访问时间为..., [URL](URL)"
    To: "[^1]: Title URL"
    """
    result = []

    for line in content.split('\n'):
        match = GEMINI_REF_PATTERN.match(line.strip())
        if match:
            num, title, url = match.groups()
            result.append(f'[^{num}]: {title} {url}')
        else:
            result.append(line)

    return '\n'.join(result)

# =============================================================================
# Main Processing
# =============================================================================

def process_file(file_path: Path, dry_run: bool = False, force: bool = False,
                 check_only: bool = False, verbose: bool = False) -> ProcessResult:
    """
    Process a single file.

    Args:
        file_path: Path to the file
        dry_run: If True, preview changes without writing
        force: If True, re-process even if already converted
        check_only: If True, only check format without processing
        verbose: If True, show detailed output

    Returns:
        ProcessResult with success status and details
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return ProcessResult(False, f"Error reading file: {e}")

    format_type = detect_format(content)

    # Count citations before processing
    inline_before, refs_before = count_citations(content, format_type)

    # Check-only mode
    if check_only:
        if format_type == 'converted':
            inline_nums, ref_nums = get_unique_citation_numbers(content)
            missing_refs = inline_nums - ref_nums
            orphan_refs = ref_nums - inline_nums

            msg = f"Format: converted | Inline: {len(inline_nums)} unique | Refs: {len(ref_nums)}"
            if missing_refs:
                msg += f" | ⚠ Missing refs: {sorted(missing_refs)[:5]}"
            if orphan_refs:
                msg += f" | ⚠ Orphan refs: {sorted(orphan_refs)[:5]}"
            return ProcessResult(True, msg, format_type, inline_before, inline_before, refs_before, refs_before)
        elif format_type in ('gpt', 'gemini'):
            return ProcessResult(True, f"Format: {format_type} | Needs conversion | Inline: {inline_before} | Refs: {refs_before}",
                               format_type, inline_before, 0, refs_before, 0)
        else:
            return ProcessResult(False, "Format: unknown | Cannot process", format_type)

    # Handle already-converted files
    if format_type == 'converted':
        if force:
            # With --force, we could re-validate or report stats
            inline_nums, ref_nums = get_unique_citation_numbers(content)
            return ProcessResult(True, f"Already converted (forced check) | {len(inline_nums)} citations, {len(ref_nums)} refs",
                               format_type, inline_before, inline_before, refs_before, refs_before)
        else:
            return ProcessResult(False, "Already converted - use -f to force re-check", format_type)

    if format_type == 'unknown':
        return ProcessResult(False, "Unknown format - skipping", format_type)

    if verbose:
        print(f"  Detected format: {format_type}")
        print(f"  Citations before: {inline_before} inline, {refs_before} refs")

    # Apply conversions based on format
    new_content = content

    if format_type == 'gpt':
        # Check if this is the variant GPT format (has [[n]](URL) in references section)
        ref_section = content.split('---')[-1] if '---' in content else content
        # Check for both escaped and non-escaped versions
        is_variant = r'[[' in ref_section or r'[\[' in ref_section

        # For variant format, do references first, then inline
        if is_variant:
            new_content = convert_gpt_variant_references(new_content)
            new_content = convert_gpt_inline(new_content)
        else:
            new_content = convert_gpt_inline(new_content)
            new_content = convert_gpt_references(new_content)
    elif format_type == 'gemini':
        new_content = convert_gemini_inline(new_content)
        new_content = convert_gemini_references(new_content)

    # Count citations after processing
    inline_after, refs_after = count_citations(new_content, 'converted')

    # Check if anything changed
    if new_content == content:
        return ProcessResult(False, "No changes needed", format_type,
                           inline_before, inline_after, refs_before, refs_after)

    # Validate conversion
    inline_nums, ref_nums = get_unique_citation_numbers(new_content)
    missing_refs = inline_nums - ref_nums

    validation_msg = ""
    if missing_refs and verbose:
        validation_msg = f" | ⚠ {len(missing_refs)} missing refs"

    if dry_run:
        # Show preview of changes
        lines_old = content.split('\n')[:20]
        lines_new = new_content.split('\n')[:20]
        print("\n  === Preview (first 20 lines) ===")
        for i, (old, new) in enumerate(zip(lines_old, lines_new)):
            if old != new:
                print(f"  Line {i+1}:")
                print(f"    - {old[:80]}")
                print(f"    + {new[:80]}")
        return ProcessResult(True, f"Preview complete | {inline_after} citations, {refs_after} refs{validation_msg}",
                           format_type, inline_before, inline_after, refs_before, refs_after)
    else:
        # Backup original file
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        shutil.copy2(file_path, backup_path)

        # Write new content
        file_path.write_text(new_content, encoding='utf-8')
        return ProcessResult(True, f"Converted | {inline_after} citations, {refs_after} refs | backup: {backup_path.name}{validation_msg}",
                           format_type, inline_before, inline_after, refs_before, refs_after)


def process_directory(dir_path: Path, dry_run: bool = False, force: bool = False,
                     check_only: bool = False, recursive: bool = False,
                     verbose: bool = False) -> DirectoryStats:
    """
    Process all .md files in a directory.

    Returns:
        DirectoryStats with counts
    """
    stats = DirectoryStats()

    if recursive:
        md_files = list(dir_path.rglob('*.md'))
    else:
        md_files = list(dir_path.glob('*.md'))

    # Filter out .bak files
    md_files = [f for f in md_files if not f.suffix.endswith('.bak')]

    for md_file in md_files:
        rel_path = md_file.relative_to(dir_path) if recursive else md_file.name
        print(f"\nProcessing: {rel_path}")

        result = process_file(md_file, dry_run, force, check_only, verbose)

        if result.success:
            if result.format_type == 'converted' and not force:
                stats.converted += 1
                print(f"  ◈ {result.message}")
            else:
                stats.processed += 1
                print(f"  ✓ {result.message}")
        else:
            if "Already converted" in result.message:
                stats.converted += 1
                print(f"  ◈ {result.message}")
            elif "Unknown format" in result.message or "No changes" in result.message:
                stats.skipped += 1
                print(f"  ⊘ {result.message}")
            else:
                stats.errors += 1
                print(f"  ✗ {result.message}")

    return stats

# =============================================================================
# CLI Entry Point
# =============================================================================

def parse_args(args: List[str]) -> dict:
    """Parse command line arguments."""
    options = {
        'dry_run': False,
        'check_only': False,
        'force': False,
        'recursive': False,
        'verbose': False,
        'help': False,
        'paths': []
    }

    for arg in args:
        if arg in ('-n', '--dry-run'):
            options['dry_run'] = True
        elif arg in ('-c', '--check'):
            options['check_only'] = True
        elif arg in ('-f', '--force'):
            options['force'] = True
        elif arg in ('-r', '--recursive'):
            options['recursive'] = True
        elif arg in ('-v', '--verbose'):
            options['verbose'] = True
        elif arg in ('-h', '--help'):
            options['help'] = True
        elif not arg.startswith('-'):
            options['paths'].append(arg)

    return options


def main():
    args = sys.argv[1:]
    options = parse_args(args)

    if not args or options['help']:
        print(__doc__)
        print("\nArguments:")
        print("  <file_or_directory>  Path to .md file or directory")
        print("\nOptions:")
        print("  -n, --dry-run   Preview changes without writing")
        print("  -c, --check     Check file format and citation counts")
        print("  -f, --force     Force re-process even if already converted")
        print("  -r, --recursive Process subdirectories recursively")
        print("  -v, --verbose   Show detailed output")
        print("  -h, --help      Show this help message")
        print("\nExamples:")
        print("  python format_ds_citations.py report.md")
        print("  python format_ds_citations.py -n ./deep-research/")
        print("  python format_ds_citations.py -c -r ./sources/")
        sys.exit(0)

    if not options['paths']:
        print("Error: Please specify a file or directory")
        sys.exit(1)

    input_path = Path(options['paths'][0])

    if not input_path.exists():
        print(f"Error: Path not found: {input_path}")
        sys.exit(1)

    print("=" * 60)
    print("Deep Research Citation Formatter")
    print("=" * 60)

    mode_indicators = []
    if options['dry_run']:
        mode_indicators.append("PREVIEW")
    if options['check_only']:
        mode_indicators.append("CHECK")
    if options['force']:
        mode_indicators.append("FORCE")
    if options['recursive']:
        mode_indicators.append("RECURSIVE")
    if options['verbose']:
        mode_indicators.append("VERBOSE")

    if mode_indicators:
        print(f"\n[{' | '.join(mode_indicators)}]")

    if input_path.is_file():
        result = process_file(input_path, options['dry_run'], options['force'],
                            options['check_only'], options['verbose'])
        if result.success:
            print(f"\n✓ {result.message}")
        else:
            print(f"\n✗ {result.message}")
            sys.exit(1)
    elif input_path.is_dir():
        stats = process_directory(input_path, options['dry_run'], options['force'],
                                 options['check_only'], options['recursive'],
                                 options['verbose'])
        print("\n" + "=" * 60)
        print(f"Summary: {stats.processed} processed, {stats.converted} already converted, "
              f"{stats.skipped} skipped, {stats.errors} errors")
        print("=" * 60)
    else:
        print(f"Error: Not a file or directory: {input_path}")
        sys.exit(1)

if __name__ == '__main__':
    main()
