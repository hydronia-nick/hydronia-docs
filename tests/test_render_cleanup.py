from __future__ import annotations

from pathlib import Path

from scripts.render_cleanup import cleanup_markdown


def test_cleanup_markdown_converts_shader_block_to_admonition() -> None:
    text = "\n".join(
        [
            "1. Run the installation.",
            "",
            "    ::: shader",
            "    Reboot will be required. Please reboot before proceeding to the next section.",
            "    :::",
            "",
        ]
    )

    result = cleanup_markdown(text)

    assert "::: shader" not in result
    assert "!!! note" in result
    assert "Reboot will be required." in result


def test_cleanup_markdown_removes_pdf_table_carryover_lines() -> None:
    text = "\n".join(
        [
            "p2.9cmp3.8cmp3.9cm",
            "",
            "\\",
            "",
            "& &",
            "",
            "Table -- continued from previous page\\",
            "",
            "& &",
            "",
            "\\",
            "",
            "Real content.",
        ]
    )

    result = cleanup_markdown(text)

    assert "p2.9cmp3.8cmp3.9cm" not in result
    assert "continued from previous page" not in result
    assert "\n& &\n" not in result
    assert "Real content." in result


def test_cleanup_markdown_converts_simple_tabular_rows_to_bullets() -> None:
    text = "\n".join(
        [
            "Metric & Select this option to work in metric units.\\",
            "English & Select this option to work in English units.\\",
        ]
    )

    result = cleanup_markdown(text)

    assert "- **Metric:** Select this option to work in metric units." in result
    assert "- **English:** Select this option to work in English units." in result


def test_cleanup_markdown_drops_generic_directive_wrappers() -> None:
    text = "\n".join(
        [
            "::: tabular p4cm p1.8cm",
            "Metric & Select this option to work in metric units.\\",
            ":::",
            "",
            "::: turn 90 :::",
        ]
    )

    result = cleanup_markdown(text)

    assert "::: tabular" not in result
    assert "::: turn 90 :::" not in result
    assert "- **Metric:** Select this option to work in metric units." in result


def test_cleanup_markdown_handles_leading_ampersand_rows() -> None:
    text = "\n".join(
        [
            "& Q & Qs\\",
            "& h. & Output time interval for reporting results.\\",
        ]
    )

    result = cleanup_markdown(text)

    assert "- **Q:** Qs" in result
    assert "- **h.:** Output time interval for reporting results." in result


def test_cleanup_markdown_converts_rows_with_escaped_text() -> None:
    text = (
        "CFL & Courant-Friederich-Lewy condition (CFL). Set this number to a value in the (0,1\\] "
        "interval. By default CFL is set to 1.0.\\"
    )

    result = cleanup_markdown(text)

    assert "- **CFL:** Courant-Friederich-Lewy condition (CFL)." in result


def test_cleanup_markdown_converts_multi_cell_rows_with_leading_empty_cell() -> None:
    text = "& m/ft & The model will report the inundation arrival time.\\"

    result = cleanup_markdown(text)

    assert "- **m/ft:** The model will report the inundation arrival time." in result


def test_engine_reference_markdown_has_no_known_rendering_artifacts() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "docs" / "oilflow2d" / "engine-reference" / "02-installing-activating.md",
        repo_root / "docs" / "oilflow2d" / "engine-reference" / "05-hydrodynamic-model.md",
        repo_root / "docs" / "oilflow2d" / "engine-reference" / "11-bridge-scour.md",
        repo_root / "docs" / "oilflow2d" / "engine-reference" / "13-hydraulic-hydrologic-components.md",
        repo_root / "docs" / "hydrobid-flood" / "engine-reference" / "02-installing-activating.md",
        repo_root / "docs" / "hydrobid-flood" / "engine-reference" / "11-bridge-scour.md",
        repo_root / "docs" / "hydrobid-flood" / "engine-reference" / "13-hydraulic-hydrologic-components.md",
    ]
    bad_tokens = [
        "ï¿½",
        "north wild",
        "layerï¿½s",
        "polygonsï¿½one",
        "culvertï¿½s entrance and exit",
    ]

    for target in targets:
        text = target.read_text(encoding="utf-8")
        for token in bad_tokens:
            assert token not in text, f"{token!r} still present in {target}"
