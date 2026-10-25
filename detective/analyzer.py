"""Failed Build Detective - CI Pipeline Failure Analyzer.

Analyzes CI build logs, extracts root causes, categorizes failure types
(Dependency Issue, Build Error, Test Error), and produces structured
Markdown summaries for GitHub Actions workflow summaries.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# ==============================================================================
# Failure Category Definitions and Data Structures
# ==============================================================================

CATEGORY_DEPENDENCY = "Dependency Issue"
CATEGORY_BUILD = "Build Error"
CATEGORY_TEST = "Test Error"
CATEGORY_UNKNOWN = "Unknown Pipeline Error"
CATEGORY_SUCCESS = "Success"


@dataclass
class AnalysisResult:
    """Represents the categorized analysis result of a build log."""

    category: str
    icon: str
    headline: str
    error_message: str
    error_snippet: str
    suggested_fixes: List[str]
    is_failure: bool


# ==============================================================================
# Regular Expressions for Categorization
# ==============================================================================

# Regex to strip ANSI escape codes (colors, cursor movements) from log streams
ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# 1. Dependency Issue Patterns
DEPENDENCY_PATTERNS = [
    re.compile(r"(ModuleNotFoundError:\s*[^\n]+)", re.IGNORECASE),
    re.compile(r"(ImportError:\s*[^\n]+)", re.IGNORECASE),
    re.compile(
        r"(ERROR:\s*Could not find a version that satisfies the requirement[^\n]+)",
        re.IGNORECASE,
    ),
    re.compile(r"(ERROR:\s*No matching distribution found for[^\n]+)", re.IGNORECASE),
    re.compile(r"(pip._vendor.resolvelib.resolvers.ResolutionError:[^\n]+)", re.IGNORECASE),
]

# 2. Build Error Patterns (Docker build & Python syntax/indentation)
BUILD_PATTERNS = [
    re.compile(r"(SyntaxError:\s*[^\n]+)", re.IGNORECASE),
    re.compile(r"(IndentationError:\s*[^\n]+)", re.IGNORECASE),
    re.compile(r"(TabError:\s*[^\n]+)", re.IGNORECASE),
    re.compile(r"(failed to solve:?\s*[^\n]+)", re.IGNORECASE),
    re.compile(r"(The command '[^']+' returned a non-zero code:\s*\d+)", re.IGNORECASE),
    re.compile(r"(returned a non-zero code:\s*\d+)", re.IGNORECASE),
    re.compile(r"(executor failed running\s*\[[^\]]+\]:\s*exit code:\s*\d+)", re.IGNORECASE),
    re.compile(r"(docker:\s*Error response from daemon:[^\n]+)", re.IGNORECASE),
]

# 3. Test Error Patterns (Pytest assertion failures & test status)
TEST_PATTERNS = [
    re.compile(r"(FAILED\s+tests/[^\n]+)", re.IGNORECASE),
    re.compile(r"(AssertionError:\s*[^\n]+)", re.IGNORECASE),
    re.compile(r"(AssertionError)", re.IGNORECASE),
    re.compile(r"(=+\s*\d+\s+failed[^\n]*=+)", re.IGNORECASE),
]


def strip_ansi(text: str) -> str:
    """Remove ANSI color and formatting escape sequences from text."""
    return ANSI_ESCAPE_RE.sub("", text)


# ==============================================================================
# Log Parsing & Extraction Utilities
# ==============================================================================

def extract_surrounding_block(
    lines: List[str], match_index: int, window_before: int = 10, window_after: int = 6
) -> str:
    """Extract a contextual code or traceback block surrounding a match line.

    Scans backwards to locate logical section headers (traceback starts,
    pytest failure markers, Docker build steps) and forwards to capture
    the conclusion of the failure block.
    """
    start_idx = max(0, match_index - window_before)
    end_idx = min(len(lines), match_index + window_after + 1)

    # Search backwards for a cleaner block start if available
    for i in range(match_index, max(0, match_index - 20), -1):
        line = lines[i]
        if "Traceback (most recent call last):" in line or line.startswith("___") or "failed to solve" in line or line.startswith("#") and "RUN" in line:
            start_idx = i
            break

    # Search forwards for pytest summary if close
    for j in range(match_index, min(len(lines), match_index + 12)):
        if "=== short test summary info ===" in lines[j] or "=== 1 failed" in lines[j]:
            end_idx = min(len(lines), j + 4)
            break

    snippet = "\n".join(lines[start_idx:end_idx]).strip()
    return snippet


def locate_pattern(
    patterns: List[re.Pattern], lines: List[str]
) -> Optional[Tuple[re.Match, int, str]]:
    """Search for the first matching pattern across log lines.

    Returns:
        Tuple of (regex match object, line index, matched string) or None.
    """
    for pattern in patterns:
        for idx, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                return match, idx, line.strip()
    return None


# ==============================================================================
# Analyzer Engine
# ==============================================================================

class BuildLogAnalyzer:
    """Intelligent analyzer for CI build logs."""

    def __init__(self, log_content: str) -> None:
        """Initialize analyzer with raw log content."""
        self.raw_content = log_content
        self.clean_content = strip_ansi(log_content)
        self.lines = self.clean_content.splitlines()

    def analyze(self) -> AnalysisResult:
        """Categorize the log and return a structured diagnostic report."""
        # 1. Check for Dependency Issue
        dep_match = locate_pattern(DEPENDENCY_PATTERNS, self.lines)
        if dep_match:
            match_obj, line_idx, raw_line = dep_match
            err_msg = match_obj.group(1).strip() if match_obj.groups() else raw_line
            snippet = extract_surrounding_block(self.lines, line_idx)
            return AnalysisResult(
                category=CATEGORY_DEPENDENCY,
                icon="📦",
                headline="A required Python package or module could not be imported or resolved.",
                error_message=err_msg,
                error_snippet=snippet,
                suggested_fixes=[
                    "Check `app/requirements.txt` to verify the missing module is declared with a valid package name and version.",
                    "Verify spelling in `import` statements against the official PyPI distribution name.",
                    "Ensure `PYTHONPATH` includes your application root (e.g., `ENV PYTHONPATH=/app` in Dockerfile).",
                    "Verify network access and proxy settings if package download timed out during `pip install`.",
                ],
                is_failure=True,
            )

        # 2. Check for Build Error
        build_match = locate_pattern(BUILD_PATTERNS, self.lines)
        if build_match:
            match_obj, line_idx, raw_line = build_match
            err_msg = match_obj.group(1).strip() if match_obj.groups() else raw_line
            snippet = extract_surrounding_block(self.lines, line_idx)
            return AnalysisResult(
                category=CATEGORY_BUILD,
                icon="🔨",
                headline="A compilation, syntax, or container build instruction encountered a critical failure.",
                error_message=err_msg,
                error_snippet=snippet,
                suggested_fixes=[
                    "Inspect the file and line number referenced in the traceback for invalid syntax, missing colons, or improper indentation.",
                    "Run syntax verification locally: `python -m py_compile <file>` or execute a linter such as `ruff check .`.",
                    "For Docker build errors, verify Dockerfile instructions, base image architecture, and file paths passed to `COPY`.",
                    "Check file permissions and line endings (ensure Linux LF line endings for shell scripts in containers).",
                ],
                is_failure=True,
            )

        # 3. Check for Test Error
        test_match = locate_pattern(TEST_PATTERNS, self.lines)
        if test_match:
            match_obj, line_idx, raw_line = test_match
            err_msg = match_obj.group(1).strip() if match_obj.groups() else raw_line
            snippet = extract_surrounding_block(self.lines, line_idx)
            return AnalysisResult(
                category=CATEGORY_TEST,
                icon="🧪",
                headline="One or more automated unit tests failed during pytest suite execution.",
                error_message=err_msg,
                error_snippet=snippet,
                suggested_fixes=[
                    "Review the failed assertion and test output above to identify why the actual output differed from expectations.",
                    "Check recent application logic changes in `app/main.py` that may have broken unit test assumptions.",
                    "Reproduce locally by running `pytest tests/ -vv` or inside the container: `docker run --rm <image> pytest tests/ -v`.",
                    "If `SIMULATE_FAILURE=test` was passed, this failure was intentionally simulated.",
                ],
                is_failure=True,
            )

        # 4. Check for General Pipeline Failure (if log indicates failure without matching specific categories)
        exit_code_pattern = re.search(r"exit code:\s*([1-9]\d*)", self.clean_content)
        error_word_pattern = re.search(r"(FATAL|CRITICAL|ERROR:)\s*([^\n]+)", self.clean_content)
        if exit_code_pattern or error_word_pattern:
            err_msg = (
                error_word_pattern.group(0).strip()
                if error_word_pattern
                else (exit_code_pattern.group(0).strip() if exit_code_pattern else "Non-zero exit code detected.")
            )
            # Take last 15 lines as context
            snippet = "\n".join(self.lines[-15:]).strip() if self.lines else "No log output available."
            return AnalysisResult(
                category=CATEGORY_UNKNOWN,
                icon="⚠️",
                headline="Pipeline execution failed with an unclassified non-zero exit status or error.",
                error_message=err_msg,
                error_snippet=snippet,
                suggested_fixes=[
                    "Review the full CI pipeline logs for earlier failure symptoms or system issues.",
                    "Verify container resource limits (memory, CPU) and Docker daemon health.",
                    "Check if the command was killed by SIGKILL / OOM killer.",
                ],
                is_failure=True,
            )

        # 5. Success State
        return AnalysisResult(
            category=CATEGORY_SUCCESS,
            icon="✅",
            headline="All pipeline checks, Docker build steps, and automated tests passed successfully.",
            error_message="None (All checks passed)",
            error_snippet="No failure detected in execution log.",
            suggested_fixes=[
                "Pipeline is healthy. No action required.",
            ],
            is_failure=False,
        )


# ==============================================================================
# Markdown Report Generator
# ==============================================================================

def format_markdown_report(result: AnalysisResult, log_filename: str) -> str:
    """Format the diagnostic analysis result into GitHub-flavored Markdown."""
    lines: List[str] = []

    if result.is_failure:
        lines.append(f"# 🚨 Failure Category: {result.category}")
        lines.append("")
        lines.append(f"> **Root Cause Summary:** {result.icon} {result.headline}")
        lines.append("")
        lines.append("### ⚠️ Exact Error Message")
        lines.append("```text")
        lines.append(result.error_message)
        lines.append("```")
        lines.append("")
        lines.append("### 📋 Extracted Error Log Block")
        lines.append("```text")
        lines.append(result.error_snippet)
        lines.append("```")
        lines.append("")
        lines.append("### 💡 Suggested Fix & Remediation")
        for fix in result.suggested_fixes:
            lines.append(f"- {fix}")
        lines.append("")
        lines.append(f"*(Analyzed from `{log_filename}` by Failed Build Detective)*")
    else:
        lines.append("# ✅ Pipeline Status: All Checks Passed")
        lines.append("")
        lines.append(f"> {result.icon} {result.headline}")
        lines.append("")
        lines.append("- **Status:** Clean execution")
        lines.append(f"- **Log File:** `{log_filename}`")
        lines.append("- **Failures Detected:** 0")
        lines.append("")
        lines.append("*(Report generated by Failed Build Detective)*")

    return "\n".join(lines)


# ==============================================================================
# CLI Entry Point
# ==============================================================================

def main() -> int:
    """CLI execution entrypoint for log analysis."""
    # Ensure stdout and stderr handle UTF-8 cleanly across all operating systems
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Failed Build Detective - CI/CD Log Analyzer and Categorizer"
    )
    parser.add_argument(
        "logfile",
        type=str,
        help="Path to the build log file to analyze (use '-' to read from stdin)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Optional destination file for Markdown report (defaults to stdout)",
    )

    args = parser.parse_args()

    # Read log content
    if args.logfile == "-":
        log_content = sys.stdin.read()
        log_filename = "stdin"
    else:
        log_path = Path(args.logfile)
        if not log_path.exists():
            error_md = (
                f"# 🚨 Failure Category: {CATEGORY_UNKNOWN}\n\n"
                f"**Error:** Log file not found at path: `{args.logfile}`\n\n"
                "### 💡 Suggested Fix\n"
                "- Verify that Step 2 successfully redirected output to `build.log`.\n"
            )
            print(error_md)
            return 0  # Allow Step 3 to finish and let Step 4 enforce failure

        try:
            log_content = log_path.read_text(encoding="utf-8", errors="replace")
            log_filename = log_path.name
        except Exception as exc:
            error_md = (
                f"# 🚨 Failure Category: {CATEGORY_UNKNOWN}\n\n"
                f"**Error reading log file:** `{exc}`\n"
            )
            print(error_md)
            return 0

    # Perform analysis
    analyzer = BuildLogAnalyzer(log_content)
    result = analyzer.analyze()
    report_md = format_markdown_report(result, log_filename)

    # Output report
    if args.output:
        Path(args.output).write_text(report_md, encoding="utf-8")

    # Print to stdout (which is redirected to $GITHUB_STEP_SUMMARY in CI)
    print(report_md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
