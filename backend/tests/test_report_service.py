"""Unit tests for ReportService, results compilation, metrics verification, and chart generation."""

import json
from pathlib import Path
import pytest

from backend.app.core.config import RESULTS_DIR
from backend.app.core.constants import ALL_LABELS, HELD_OUT_QUERY_COUNT, TUNING_QUERY_COUNT
from backend.app.services.report_service import ReportService, report_service

@pytest.fixture
def test_report_service(tmp_path):
    """Initializes ReportService configured with isolated tmp directories."""
    return ReportService(
        results_dir=RESULTS_DIR,
        docs_dir=tmp_path / "docs",
    )

def test_final_results_compilation_and_loading(test_report_service):
    """Verify that final_results.json compiles successfully and loads valid structured data."""
    data = test_report_service.compile_final_results()

    assert "metadata" in data
    assert "accuracy_summary" in data
    assert "query_transition_counts" in data
    assert "held_out_query_details" in data
    assert "per_tool_metrics" in data
    assert "confusion_matrices" in data
    assert "tool_description_diffs" in data

    meta = data["metadata"]
    assert meta["model"] == "qwen2.5:3b"
    assert meta["temperature"] == 0.0
    assert meta["runs_per_query"] == 1
    assert meta["tuning_queries"] == TUNING_QUERY_COUNT
    assert meta["held_out_queries"] == HELD_OUT_QUERY_COUNT

def test_accuracy_and_improvement_calculations(test_report_service):
    """Verify accuracy numbers and absolute/relative improvement values derived from artifacts."""
    data = test_report_service.compile_final_results()
    acc = data["accuracy_summary"]

    # Tuning verification
    tuning = acc["tuning"]
    assert tuning["baseline"]["correct"] == 28
    assert tuning["baseline"]["total"] == 35
    assert tuning["baseline"]["accuracy"] == 0.8
    assert tuning["optimized"]["correct"] == 30
    assert tuning["optimized"]["total"] == 35
    assert tuning["optimized"]["accuracy"] == 0.8571
    assert tuning["absolute_improvement_pp"] == 5.71
    assert tuning["relative_improvement_pct"] == 7.14

    # Held-out verification
    held_out = acc["held_out"]
    assert held_out["baseline"]["correct"] == 11
    assert held_out["baseline"]["total"] == 15
    assert held_out["baseline"]["accuracy"] == 0.7333
    assert held_out["optimized"]["correct"] == 12
    assert held_out["optimized"]["total"] == 15
    assert held_out["optimized"]["accuracy"] == 0.8
    assert held_out["absolute_improvement_pp"] == 6.67
    assert held_out["relative_improvement_pct"] == 9.09
    assert held_out["error_reduction_pct"] == 25.0

def test_query_transition_counts_and_identities(test_report_service):
    """Verify query transition classifications and specific query IDs."""
    data = test_report_service.compile_final_results()
    counts = data["query_transition_counts"]

    assert counts["remained_correct"] == 11
    assert counts["became_correct"] == 1
    assert counts["became_incorrect"] == 0
    assert counts["remained_incorrect"] == 3

    assert counts["became_correct_ids"] == ["Q014"]
    assert counts["remained_incorrect_ids"] == ["Q009", "Q018", "Q049"]
    assert len(counts["remained_correct_ids"]) == 11
    assert counts["became_incorrect_ids"] == []

    # Total queries must equal 15
    total_transitions = (
        counts["remained_correct"]
        + counts["became_correct"]
        + counts["became_incorrect"]
        + counts["remained_incorrect"]
    )
    assert total_transitions == HELD_OUT_QUERY_COUNT

def test_baseline_and_optimized_contain_identical_held_out_ids(test_report_service):
    """Verify baseline and optimized result artifacts contain the exact same 15 held-out IDs."""
    base_path = RESULTS_DIR / "evaluation_held_out_baseline.json"
    opt_path = RESULTS_DIR / "evaluation_held_out_optimized.json"

    base_data = test_report_service.load_json_artifact(base_path)
    opt_data = test_report_service.load_json_artifact(opt_path)

    base_ids = [q["query_id"] for q in base_data["queries"]]
    opt_ids = [q["query_id"] for q in opt_data["queries"]]

    assert len(base_ids) == HELD_OUT_QUERY_COUNT
    assert len(opt_ids) == HELD_OUT_QUERY_COUNT
    assert base_ids == opt_ids, "Held-out query IDs must match in sequence across conditions"

def test_chart_generation_from_artifacts(tmp_path, test_report_service):
    """Verify chart generation produces all 8 charts in PNG and SVG formats."""
    chart_dir = tmp_path / "charts"
    generated = test_report_service.generate_all_charts(output_dir=chart_dir)

    expected_stems = [
        "chart_1_accuracy_comparison",
        "chart_2_held_out_comparison",
        "chart_3_error_count_comparison",
        "chart_4_per_tool_f1_comparison",
        "chart_5_query_transitions",
        "chart_6_confusion_matrix_baseline",
        "chart_7_confusion_matrix_optimized",
        "chart_8_optimization_journey",
    ]

    assert len(generated) == 16  # 8 PNG + 8 SVG
    for stem in expected_stems:
        png_path = chart_dir / f"{stem}.png"
        svg_path = chart_dir / f"{stem}.svg"
        assert png_path.exists(), f"Missing PNG chart: {png_path}"
        assert svg_path.exists(), f"Missing SVG chart: {svg_path}"
        assert png_path.stat().st_size > 1000
        assert svg_path.stat().st_size > 1000

def test_markdown_report_generation(tmp_path, test_report_service):
    """Verify markdown research report is generated with all 12 required sections."""
    doc_path = tmp_path / "final_results_report.md"
    report_file = test_report_service.generate_markdown_report(output_file=doc_path)

    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")

    # Verify presence of all 12 formal sections
    required_sections = [
        "1. Executive Summary",
        "2. Research Question",
        "3. Experimental Design",
        "4. Optimization Process",
        "5. Controlled Held-Out Evaluation",
        "6. Experimental Results",
        "7. Per-Tool Performance Metrics",
        "8. Error Analysis & Routing Transitions",
        "9. Tool Description Modifications",
        "10. Threats to Validity & Limitations",
        "11. Scientific Conclusion",
        "12. Reproducibility & Provenance",
    ]

    for section in required_sections:
        assert section in content, f"Report missing section: {section}"

    # Verify key factual metrics appear in the report
    assert "80.00%" in content
    assert "85.71%" in content
    assert "73.33%" in content
    assert "+6.67 percentage points" in content
    assert "+9.09%" in content
    assert "Q014" in content
    assert "qwen2.5:3b" in content
