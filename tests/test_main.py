"""Comprehensive unit tests for the target application module.

Validates mathematical operations, string utilities, and the intentional
failure simulation mechanism used for pipeline diagnostic testing.
"""

from __future__ import annotations

import os
import pytest

from app.main import (
    calculate_statistics,
    compute_factorial,
    count_vowels,
    is_palindrome,
    reverse_words,
)


# ==============================================================================
# Intentional Failure Simulation Test Case
# ==============================================================================

def test_intentional_failure_simulation() -> None:
    """Validate deliberate failure trigger when SIMULATE_FAILURE=test.

    When SIMULATE_FAILURE=test, an explicit assertion failure is triggered
    to test the Failed Build Detective analyzer. Under normal conditions
    (SIMULATE_FAILURE=none or unset), this test passes cleanly.
    """
    simulate_mode = os.getenv("SIMULATE_FAILURE", "").strip().lower()
    if simulate_mode == "test":
        assert 1 == 2, (
            "Simulated pipeline test failure triggered via SIMULATE_FAILURE=test environment variable."
        )


# ==============================================================================
# Mathematical Operations Tests
# ==============================================================================

def test_calculate_statistics_nominal() -> None:
    """Validate statistics calculation on standard numeric input."""
    data = [10, 20, 30, 40, 50]
    stats = calculate_statistics(data)
    assert stats["count"] == 5.0
    assert stats["sum"] == 150.0
    assert stats["mean"] == 30.0
    assert stats["median"] == 30.0
    assert stats["min"] == 10.0
    assert stats["max"] == 50.0


def test_calculate_statistics_single_element() -> None:
    """Validate statistics calculation on a single-element list."""
    stats = calculate_statistics([42])
    assert stats["count"] == 1.0
    assert stats["sum"] == 42.0
    assert stats["mean"] == 42.0
    assert stats["median"] == 42.0
    assert stats["min"] == 42.0
    assert stats["max"] == 42.0


def test_calculate_statistics_empty_raises() -> None:
    """Ensure ValueError is raised when input sequence is empty."""
    with pytest.raises(ValueError, match="Cannot calculate statistics for an empty sequence"):
        calculate_statistics([])


def test_compute_factorial_valid() -> None:
    """Validate factorial computation for non-negative integers."""
    assert compute_factorial(0) == 1
    assert compute_factorial(1) == 1
    assert compute_factorial(5) == 120
    assert compute_factorial(6) == 720


def test_compute_factorial_negative_raises() -> None:
    """Ensure ValueError is raised when factorial input is negative."""
    with pytest.raises(ValueError, match="Factorial is not defined for negative numbers"):
        compute_factorial(-5)


# ==============================================================================
# String Operations Tests
# ==============================================================================

def test_is_palindrome_simple() -> None:
    """Validate palindrome detection on standard words."""
    assert is_palindrome("radar") is True
    assert is_palindrome("python") is False


def test_is_palindrome_mixed_case_and_punctuation() -> None:
    """Validate palindrome detection ignoring casing, spacing, and punctuation."""
    assert is_palindrome("A man, a plan, a canal: Panama!") is True
    assert is_palindrome("Was it a car or a cat I saw?") is True
    assert is_palindrome("No 'x' in Nixon") is True


def test_reverse_words_standard() -> None:
    """Validate word reversal in a multi-word sentence."""
    assert reverse_words("DevOps and Docker CI Pipeline") == "Pipeline CI Docker and DevOps"
    assert reverse_words("  hello   world  ") == "world hello"


def test_count_vowels() -> None:
    """Validate vowel counting across mixed case strings."""
    assert count_vowels("Automated CI Pipeline") == 10
    assert count_vowels("rhythm") == 0
    assert count_vowels("AEIOU aeiou") == 10
