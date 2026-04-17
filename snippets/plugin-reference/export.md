<!-- Shared source. Use product-neutral language. -->

## Overview

The **Export** toolbar group writes the project's current scene to the solver's native file format: the `.CTL` control file, the `.FED` mesh/elevation file, hydrograph files, and all supporting tables.

## Dialog window

![Export dialog](img/export-dialog.png)

## Dialog controls

| Control | Purpose |
| --- | --- |
| *Simulation duration* | End time of the simulation, in seconds or hours. |
| *Output interval* | Time step at which result snapshots are written. |
| *Solver mode* | CPU / GPU / FE variant selector. |
| *Advanced flags* | Per-solver toggles (e.g. dry-bed tolerance, Manning override). |

## Workflow

1. Finalize the scene — mesh generated, boundary conditions assigned, DEM-sampled.
2. Open **Export**.
3. Set duration, output interval, solver.
4. Click **Export** — files are written under `Scene<N>/export/`.
5. Launch the solver externally or via the included runner.

## Requirements

- A valid TriMesh layer for the active scene.
- At least one boundary-condition feature (inflow, outflow, or initial condition).
- Valid elevations on all mesh cells.

## Technical details

Export is order-dependent: mesh → elevations → boundary conditions → controls. The plugin validates each stage before writing and raises descriptive errors when something is missing or inconsistent.

## Tips

- Run a short (60-second) export first to verify the solver starts cleanly before committing to a long run.
- Keep Manning tables and storm-drain files under version control — they're the inputs most likely to drift across scenarios.
