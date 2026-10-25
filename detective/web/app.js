/**
 * Failed Build Detective - Frontend Application Logic
 */

// ==============================================================================
// Simulation Presets (Mirrors exact CI execution outputs)
// ==============================================================================
const PRESETS = {
  dependency: `=== Step 2A: Building Docker Image ===
Sending build context to Docker daemon  24.58kB
Step 1/6 : FROM python:3.10-slim
 ---> 9c968f8b0304
Step 2/6 : WORKDIR /app
 ---> Using cache
Step 3/6 : COPY app/requirements.txt ./app/requirements.txt
 ---> Using cache
Step 4/6 : RUN pip install --no-cache-dir -r app/requirements.txt
 ---> Using cache
Step 5/6 : COPY app/ ./app/
Step 6/6 : COPY tests/ ./tests/
Successfully built failed-build-detective:latest

=== Step 2B: Running Automated Tests Inside Container ===
============================= test session starts ==============================
platform linux -- Python 3.10.16, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
collecting ... 
Traceback (most recent call last):
  File "/app/tests/test_main.py", line 12, in <module>
    from app.main import (
  File "/app/app/main.py", line 27, in <module>
    import dummy_non_existent_pkg  # type: ignore # noqa: F401
ModuleNotFoundError: No module named 'dummy_non_existent_pkg'
=========================== short test summary info ============================
ERROR tests/test_main.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.09s ===============================`,

  build: `=== Step 2A: Building Docker Image ===
Sending build context to Docker daemon  24.58kB
Step 1/6 : FROM python:3.10-slim
 ---> 9c968f8b0304
Step 2/6 : WORKDIR /app
 ---> Using cache
Step 3/6 : COPY app/requirements.txt ./app/requirements.txt
 ---> Using cache
Step 4/6 : RUN pip install --no-cache-dir -r app/requirements.txt
 ---> Using cache
Step 5/6 : COPY app/ ./app/
Step 6/6 : COPY tests/ ./tests/
Successfully built failed-build-detective:latest

=== Step 2B: Running Automated Tests Inside Container ===
============================= test session starts ==============================
platform linux -- Python 3.10.16, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
collecting ... 
Traceback (most recent call last):
  File "/app/tests/test_main.py", line 12, in <module>
    from app.main import (
  File "/app/app/main.py", line 30, in <module>
    exec("def invalid_syntax_trigger(:\\n    pass")
  File "<string>", line 1
    def invalid_syntax_trigger(:
                               ^
SyntaxError: invalid syntax
=========================== short test summary info ============================
ERROR tests/test_main.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.08s ===============================`,

  test: `=== Step 2A: Building Docker Image ===
Step 1/6 : FROM python:3.10-slim
 ---> Using cache
Successfully built failed-build-detective:latest

=== Step 2B: Running Automated Tests Inside Container ===
============================= test session starts ==============================
platform linux -- Python 3.10.16, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
collected 10 items

tests/test_main.py F.........                                            [100%]

=================================== FAILURES ===================================
_____________________ test_intentional_failure_simulation ______________________

    def test_intentional_failure_simulation() -> None:
        simulate_mode = os.getenv("SIMULATE_FAILURE", "").strip().lower()
        if simulate_mode == "test":
>           assert 1 == 2, (
                "Simulated pipeline test failure triggered via SIMULATE_FAILURE=test environment variable."
            )
E           AssertionError: Simulated pipeline test failure triggered via SIMULATE_FAILURE=test environment variable.
E           assert 1 == 2

tests/test_main.py:34: AssertionError
=========================== short test summary info ============================
FAILED tests/test_main.py::test_intentional_failure_simulation - AssertionError: Simulated pipeline test failure triggered via SIMULATE_FAILURE=test environment variable.
========================= 1 failed, 9 passed in 0.08s ==========================`,

  pass: `=== Step 2A: Building Docker Image ===
Step 1/6 : FROM python:3.10-slim
 ---> Using cache
Successfully built failed-build-detective:latest

=== Step 2B: Running Automated Tests Inside Container ===
============================= test session starts ==============================
platform linux -- Python 3.10.16, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
collected 10 items

tests/test_main.py::test_intentional_failure_simulation PASSED           [ 10%]
tests/test_main.py::test_calculate_statistics_nominal PASSED             [ 20%]
tests/test_main.py::test_calculate_statistics_single_element PASSED      [ 30%]
tests/test_main.py::test_calculate_statistics_empty_raises PASSED        [ 40%]
tests/test_main.py::test_compute_factorial_valid PASSED                  [ 50%]
tests/test_main.py::test_compute_factorial_negative_raises PASSED        [ 60%]
tests/test_main.py::test_is_palindrome_simple PASSED                     [ 70%]
tests/test_main.py::test_is_palindrome_mixed_case_and_punctuation PASSED [ 80%]
tests/test_main.py::test_reverse_words_standard PASSED                   [ 90%]
tests/test_main.py::test_count_vowels PASSED                             [100%]

============================== 10 passed in 0.07s ==============================
Pipeline completed successfully with zero defects.`
};

// ==============================================================================
// Client-Side Detective Analyzer (Exact Regex Logic as analyzer.py)
// ==============================================================================
function stripAnsi(text) {
  return text.replace(/\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])/g, '');
}

function analyzeLogClient(rawLog) {
  const cleanLog = stripAnsi(rawLog);
  const lines = cleanLog.split(/\r?\n/);

  // 1. Dependency Issue Check
  const depPatterns = [
    /ModuleNotFoundError:\s*([^\n]+)/i,
    /ImportError:\s*([^\n]+)/i,
    /ERROR:\s*(Could not find a version that satisfies the requirement[^\n]+)/i,
    /ERROR:\s*(No matching distribution found for[^\n]+)/i,
  ];

  for (const pat of depPatterns) {
    for (let idx = 0; idx < lines.length; idx++) {
      const match = lines[idx].match(pat);
      if (match) {
        const errorMsg = match[1] || match[0];
        const snippet = extractSnippet(lines, idx);
        return {
          category: 'Dependency Issue',
          icon: '📦',
          classSuffix: 'cat-dependency',
          severity: 'HIGH PRIORITY',
          headline: 'A required Python package or module could not be imported or resolved.',
          errorMessage: errorMsg,
          snippet: snippet,
          fixes: [
            'Verify that <code>app/requirements.txt</code> declares the missing module with a valid PyPI package name.',
            'Confirm spelling in your <code>import</code> statement matches the installed package namespace.',
            'Ensure <code>PYTHONPATH=/app</code> is set in the Docker container so local modules resolve correctly.',
            'Test installation locally in an isolated virtualenv: <code>pip install -r app/requirements.txt</code>.'
          ],
          isFailure: true
        };
      }
    }
  }

  // 2. Build Error Check
  const buildPatterns = [
    /SyntaxError:\s*([^\n]+)/i,
    /IndentationError:\s*([^\n]+)/i,
    /TabError:\s*([^\n]+)/i,
    /failed to solve:?\s*([^\n]+)/i,
    /The command '[^']+' returned a non-zero code:\s*(\d+)/i,
    /returned a non-zero code:\s*(\d+)/i,
  ];

  for (const pat of buildPatterns) {
    for (let idx = 0; idx < lines.length; idx++) {
      const match = lines[idx].match(pat);
      if (match) {
        const errorMsg = match[1] || match[0];
        const snippet = extractSnippet(lines, idx);
        return {
          category: 'Build Error',
          icon: '🔨',
          classSuffix: 'cat-build',
          severity: 'CRITICAL FAILURE',
          headline: 'A syntax compilation or container build instruction encountered a critical failure.',
          errorMessage: errorMsg,
          snippet: snippet,
          fixes: [
            'Inspect the exact file and line number shown in the traceback for invalid syntax or missing colons.',
            'Run static syntax checks locally: <code>python -m py_compile app/main.py</code> or <code>ruff check .</code>.',
            'If Docker build failed, inspect Dockerfile instructions, base image architecture, and file paths passed to <code>COPY</code>.',
            'Verify file permissions and ensure Linux LF line endings are preserved.'
          ],
          isFailure: true
        };
      }
    }
  }

  // 3. Test Error Check
  const testPatterns = [
    /FAILED\s+(tests\/[^\n]+)/i,
    /AssertionError:\s*([^\n]+)/i,
    /AssertionError/i,
    /=+\s*\d+\s+failed[^\n]*=+/i,
  ];

  for (const pat of testPatterns) {
    for (let idx = 0; idx < lines.length; idx++) {
      const match = lines[idx].match(pat);
      if (match) {
        const errorMsg = match[1] || match[0];
        const snippet = extractSnippet(lines, idx);
        return {
          category: 'Test Error',
          icon: '🧪',
          classSuffix: 'cat-test',
          severity: 'DEFECT DETECTED',
          headline: 'One or more automated unit tests failed during pytest suite execution.',
          errorMessage: errorMsg,
          snippet: snippet,
          fixes: [
            'Review the failed assertion above to understand why the actual output differed from expectations.',
            'Check recent commits in <code>app/main.py</code> that may have broken unit test assumptions.',
            'Reproduce locally by running <code>pytest tests/ -vv</code>.',
            'If <code>SIMULATE_FAILURE=test</code> was used, this failure was intentionally triggered.'
          ],
          isFailure: true
        };
      }
    }
  }

  // 4. Clean Success Check
  return {
    category: 'All Checks Passed',
    icon: '✅',
    classSuffix: 'cat-success',
    severity: 'CLEAN PIPELINE',
    headline: 'All pipeline checks, Docker build steps, and automated tests passed successfully with zero defects.',
    errorMessage: 'None (Clean run)',
    snippet: cleanLog.trim() || 'No failure detected in execution log.',
    fixes: [
      'The pipeline is healthy and ready for deployment.',
      'No remediation or bug fixes required.'
    ],
    isFailure: false
  };
}

function extractSnippet(lines, matchIdx) {
  let start = Math.max(0, matchIdx - 10);
  let end = Math.min(lines.length, matchIdx + 8);

  for (let i = matchIdx; i >= Math.max(0, matchIdx - 20); i--) {
    if (lines[i].includes('Traceback (most recent call last):') || lines[i].startsWith('___') || lines[i].includes('failed to solve')) {
      start = i;
      break;
    }
  }

  for (let j = matchIdx; j < Math.min(lines.length, matchIdx + 12); j++) {
    if (lines[j].includes('=== short test summary info ===') || lines[j].includes('=== 1 failed')) {
      end = Math.min(lines.length, j + 4);
      break;
    }
  }

  return lines.slice(start, end).join('\n').trim();
}

// ==============================================================================
// DOM Element Binding and Event Handlers
// ==============================================================================
document.addEventListener('DOMContentLoaded', () => {
  const logInput = document.getElementById('logInput');
  const lineCount = document.getElementById('lineCount');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const emptyState = document.getElementById('emptyState');
  const diagnosticResult = document.getElementById('diagnosticResult');
  const reportActions = document.getElementById('reportActions');
  const logFileInput = document.getElementById('logFileInput');

  // Category elements
  const categoryCard = document.getElementById('categoryCard');
  const catIcon = document.getElementById('catIcon');
  const catName = document.getElementById('catName');
  const severityBadge = document.getElementById('severityBadge');
  const catHeadline = document.getElementById('catHeadline');
  const errorMessageText = document.getElementById('errorMessageText');
  const errorSnippetText = document.getElementById('errorSnippetText');
  const remediationList = document.getElementById('remediationList');

  // Action buttons
  const copyMarkdownBtn = document.getElementById('copyMarkdownBtn');
  const downloadReportBtn = document.getElementById('downloadReportBtn');
  const copyErrorMsgBtn = document.getElementById('copyErrorMsgBtn');

  let currentAnalysis = null;

  // Update line count
  function updateLineCount() {
    const lines = logInput.value ? logInput.value.split('\n').length : 0;
    lineCount.textContent = `${lines} ${lines === 1 ? 'line' : 'lines'}`;
  }

  logInput.addEventListener('input', updateLineCount);

  // Preset buttons
  document.querySelectorAll('.preset-btn[data-preset]').forEach(btn => {
    btn.addEventListener('click', () => {
      const presetKey = btn.getAttribute('data-preset');
      if (PRESETS[presetKey]) {
        logInput.value = PRESETS[presetKey];
        updateLineCount();
        runAnalysis();
      }
    });
  });

  document.getElementById('presetClear').addEventListener('click', () => {
    logInput.value = '';
    updateLineCount();
    emptyState.style.display = 'flex';
    diagnosticResult.style.display = 'none';
    reportActions.style.display = 'none';
  });

  // File Upload
  logFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        logInput.value = evt.target.result;
        updateLineCount();
        runAnalysis();
      };
      reader.readAsText(file);
    }
  });

  // Analyze Action
  analyzeBtn.addEventListener('click', runAnalysis);

  async function runAnalysis() {
    const rawContent = logInput.value.trim();
    if (!rawContent) {
      alert('Please enter or paste a build log first, or choose one of the quick presets.');
      return;
    }

    // Attempt to query local backend if running via ui.py, otherwise fallback to client engine
    let result = null;
    try {
      const resp = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ log: rawContent })
      });
      if (resp.ok) {
        result = await resp.json();
      }
    } catch {
      // Offline / standalone mode: run client-side engine
    }

    if (!result) {
      result = analyzeLogClient(rawContent);
    }

    currentAnalysis = result;
    renderAnalysis(result);
  }

  function renderAnalysis(result) {
    emptyState.style.display = 'none';
    diagnosticResult.style.display = 'flex';
    reportActions.style.display = 'flex';

    // Reset card classes
    categoryCard.className = `category-card ${result.classSuffix || ''}`;
    catIcon.textContent = result.icon;
    catName.textContent = result.category;
    severityBadge.textContent = result.severity;
    catHeadline.textContent = result.headline;

    errorMessageText.textContent = result.errorMessage;
    errorSnippetText.textContent = result.snippet;

    // Populate remediation
    remediationList.innerHTML = '';
    result.fixes.forEach(fix => {
      const li = document.createElement('li');
      li.innerHTML = fix;
      remediationList.appendChild(li);
    });
  }

  // Copy Markdown
  copyMarkdownBtn.addEventListener('click', () => {
    if (!currentAnalysis) return;
    const md = generateMarkdown(currentAnalysis);
    navigator.clipboard.writeText(md).then(() => {
      const orig = copyMarkdownBtn.textContent;
      copyMarkdownBtn.textContent = '✅ Copied!';
      setTimeout(() => copyMarkdownBtn.textContent = orig, 2000);
    });
  });

  // Download Report
  downloadReportBtn.addEventListener('click', () => {
    if (!currentAnalysis) return;
    const md = generateMarkdown(currentAnalysis);
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `failed-build-detective-report-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // Copy Error Message
  copyErrorMsgBtn.addEventListener('click', () => {
    if (!currentAnalysis) return;
    navigator.clipboard.writeText(currentAnalysis.errorMessage).then(() => {
      copyErrorMsgBtn.textContent = 'Copied!';
      setTimeout(() => copyErrorMsgBtn.textContent = 'Copy', 1500);
    });
  });

  function generateMarkdown(res) {
    if (!res.isFailure) {
      return `# ✅ Pipeline Status: All Checks Passed\n\n> ${res.icon} ${res.headline}\n\n- **Status:** Clean execution\n- **Failures Detected:** 0\n\n*(Report generated by Failed Build Detective)*`;
    }
    const fixes = res.fixes.map(f => `- ${f.replace(/<[^>]*>/g, '')}`).join('\n');
    return `# 🚨 Failure Category: ${res.category}\n\n> **Root Cause Summary:** ${res.icon} ${res.headline}\n\n### ⚠️ Exact Error Message\n\`\`\`text\n${res.errorMessage}\n\`\`\`\n\n### 📋 Extracted Error Log Block\n\`\`\`text\n${res.snippet}\n\`\`\`\n\n### 💡 Suggested Fix & Remediation\n${fixes}\n\n*(Report generated by Failed Build Detective)*`;
  }

  // Pre-load Dependency preset on first view to give an instant preview!
  logInput.value = PRESETS.dependency;
  updateLineCount();
  runAnalysis();
});
