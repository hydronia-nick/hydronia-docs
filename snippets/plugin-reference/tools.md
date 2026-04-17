<!-- Shared source. Use product-neutral language. -->

## Overview

The **Tools** toolbar group bundles auxiliary utilities: template-layer creation, EPA-SWMM integration, hydro-economic evaluation (HEEF), and project comparison.

## Subgroups

### Template layers

Adds an empty layer with the correct schema for a given feature type — boundary conditions, inflow hydrographs, storm-drain nodes, and so on. Use this when you want to author data from scratch rather than importing.

### EPA-SWMM integration

- **Import SWMM** — pulls a `.INP` file into the project, mapping conduits and nodes to the plugin's storm-drain schema.
- **Create SDP** — builds a simplified drainage polygon from catchment geometry.
- **Create SWMM** — writes the active scene's storm-drain system out as an EPA-SWMM input file.

### Hydro-Economic Evaluation of Flood (HEEF)

Couples flood maps with a building / land-use exposure layer to estimate damages. Requires a depth-damage function table (`.heef`) and a building footprint layer with use-class attributes.

### Compare

Side-by-side comparison of two scenarios — useful for before/after mitigation analyses.

## Tips

- Always inspect imported SWMM networks before re-exporting; automated conversion rarely preserves every manhole attribute verbatim.
- HEEF is only as good as its depth-damage table. Keep one curated table per study and commit it to version control.
