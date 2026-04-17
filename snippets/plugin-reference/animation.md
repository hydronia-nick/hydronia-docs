<!-- Shared source. Use product-neutral language. -->

## Overview

The **Animation** toolbar button opens the animation composer: an interactive, QGIS-integrated tool for scrubbing through simulation time and exporting video, KMZ, or image sequences.

## Dialog window

![Animation dialog](img/animation-dialog.png)

## Dialog controls

| Control | Purpose |
| --- | --- |
| *Result file* | The `.OUT` file to animate. |
| *Variable* | Depth, velocity, WSE, or concentration. |
| *Time slider* | Scrubs through simulation timesteps. |
| *Playback controls* | Play / pause / loop. |
| *Export target* | Video file, KMZ, or PNG sequence. |

## Workflow

1. Load a result file into the animator.
2. Choose the variable and color ramp.
3. Scrub to find the range of interest.
4. Export: video for stakeholder reviews, KMZ for Google Earth, PNG sequence for external editors.

## Requirements

- Result files from a completed solver run.
- FFmpeg on `PATH` for video export.

## Technical details

Animation uses the WSE (water-surface elevation) from the result layer — not the DEM — so flooded cells render at the correct water height. KMZ export drapes the animated surface over the terrain with per-frame time markers.

## Tips

- For reports, export as PNG sequence and compose externally; you'll get finer control over titles and legends.
- KMZ files over 50 MB often choke Google Earth — sample the output interval down before export.
