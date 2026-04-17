<!-- Shared source. Use product-neutral language. -->

## Overview

The **Maps** toolbar group turns raw solver output into styled QGIS layers: element time maps, max-value cell maps, time-to-depth maps, hazard intensity maps, velocity-field maps, and HEEF (Hydro-Economic Evaluation of Flood) maps.

## Dialog windows

The Maps menu exposes one dialog per map type; they share a common structure.

![Element Time Maps dialog](img/maps-element-t.png)

## Common controls

| Control | Purpose |
| --- | --- |
| *Result file* | The `.OUT`-series file to visualize. |
| *Variable* | Depth, water-surface elevation, velocity, or derived quantity. |
| *Time step* | Snapshot selector (where applicable). |
| *Symbology preset* | Ready-made color ramps tuned per variable. |

## Map types

- **Element time maps** — per-cell value at a chosen timestep.
- **Max value cell maps** — maximum over the full simulation per cell.
- **Time-to-depth maps** — how long until a threshold depth is reached per cell.
- **Hazard intensity maps** — combined depth-velocity hazard classification.
- **Velocity-field maps** — vector arrows sampled on a regular grid.
- **HEEF maps** — economic damage estimates per building footprint.

## Workflow

1. Pick a map type from the **Maps** toolbar dropdown.
2. Select result file and variable.
3. Apply — the plugin creates a styled raster or vector layer in the current QGIS project.

## Tips

- Use max-value maps for reports and executive summaries; time-series maps for hydraulic diagnostics.
- Save styles as `.qml` alongside the result file so colleagues see the same symbology.
