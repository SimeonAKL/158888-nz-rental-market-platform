"""Validate final Phase 5A anomaly outputs."""

from __future__ import annotations

from rmp.anomaly.pipeline import (
    build_anomaly_validation_outputs,
)


def main() -> None:
    """Run final anomaly validation and metadata build."""
    validation, metadata = build_anomaly_validation_outputs()

    print("Phase 5A anomaly validation complete.")
    print()

    print(
        "Validation checks:",
        len(validation),
    )

    print(
        "Passed:",
        int(validation["passed"].sum()),
    )

    print(
        "Failed:",
        int((~validation["passed"]).sum()),
    )

    print()
    print("=== VALIDATION ===")

    print(
        validation[
            [
                "check_name",
                "passed",
                "observed",
                "expected",
            ]
        ].to_string(index=False)
    )

    print()
    print("=== METADATA ===")

    print(metadata.to_string(index=False))


if __name__ == "__main__":
    main()
