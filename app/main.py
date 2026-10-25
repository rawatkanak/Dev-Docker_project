"""Target Application Module.

Provides mathematical and string manipulation utility functions alongside an
intentional failure simulation mechanism designed for CI/CD pipeline diagnostics.
"""

from __future__ import annotations

import os
import re
import statistics
from typing import Sequence

# ==============================================================================
# Intentional Failure Simulation Trigger (CI/CD Diagnostic Mechanism)
# ==============================================================================
# Reads the SIMULATE_FAILURE environment variable to trigger specific pipeline failure modes:
# - 'dependency': Attempts to import a non-existent package, raising ModuleNotFoundError.
# - 'build': Injects a deliberate Python SyntaxError before code execution.
# - 'test': Triggers an assertion failure in tests/test_main.py.
# - 'none' (or unset): Executes normally with all tests passing.
# ==============================================================================
SIMULATE_FAILURE: str = os.getenv("SIMULATE_FAILURE", "").strip().lower()

if SIMULATE_FAILURE == "dependency":
    # Deliberately attempt to import a non-existent package
    import dummy_non_existent_pkg  # type: ignore # noqa: F401
elif SIMULATE_FAILURE == "build":
    # Deliberately inject a Python SyntaxError into execution context
    exec("def invalid_syntax_trigger(:\n    pass")


# ==============================================================================
# Mathematical Operations
# ==============================================================================

def calculate_statistics(numbers: Sequence[float | int]) -> dict[str, float]:
    """Calculate summary statistics for a sequence of numbers.

    Args:
        numbers: A sequence of numeric values (floats or integers).

    Returns:
        A dictionary containing count, sum, mean, median, min, and max.

    Raises:
        ValueError: If the input sequence is empty.
    """
    if not numbers:
        raise ValueError("Cannot calculate statistics for an empty sequence.")

    num_list = [float(x) for x in numbers]
    return {
        "count": float(len(num_list)),
        "sum": float(sum(num_list)),
        "mean": float(statistics.mean(num_list)),
        "median": float(statistics.median(num_list)),
        "min": float(min(num_list)),
        "max": float(max(num_list)),
    }


def compute_factorial(n: int) -> int:
    """Compute the factorial of a non-negative integer.

    Args:
        n: A non-negative integer.

    Returns:
        The factorial of n.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError(f"Factorial is not defined for negative numbers: {n}")
    if n in (0, 1):
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


# ==============================================================================
# String Manipulation Operations
# ==============================================================================

def is_palindrome(text: str) -> bool:
    """Check if a given string is a palindrome, ignoring case and non-alphanumeric chars.

    Args:
        text: The string to test.

    Returns:
        True if the normalized string is a palindrome, False otherwise.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", text).lower()
    return cleaned == cleaned[::-1]


def reverse_words(sentence: str) -> str:
    """Reverse the order of words in a sentence while normalizing whitespace.

    Args:
        sentence: The input sentence string.

    Returns:
        The sentence with words reversed in order.
    """
    words = sentence.strip().split()
    return " ".join(reversed(words))


def count_vowels(text: str) -> int:
    """Count the total number of vowels (A, E, I, O, U) in a string.

    Args:
        text: The input string.

    Returns:
        The total vowel count.
    """
    vowels = set("aeiouAEIOU")
    return sum(1 for char in text if char in vowels)


if __name__ == "__main__":
    print("Failed Build Detective Target Application loaded successfully.")
    sample_nums = [10.0, 20.0, 30.0, 40.0, 50.0]
    print(f"Sample Statistics: {calculate_statistics(sample_nums)}")
    print(f"Palindrome Check ('Racecar'): {is_palindrome('Racecar')}")
