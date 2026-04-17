<!--
Shared source — included by every product's "New Project" page.
Use `![](img/<asset>.png)` for figures; each product wrapper provides its own
`img/` directory so the same text renders with the correct branded screenshots.
Do NOT use product-specific names like "RiverFlow2D" here. Use "the plugin".
-->

## Overview

The **New Project / New Scene** toolbar group creates a fresh plugin project or adds a new scene to an existing one, with full control over coordinate reference system (CRS), project folder layout, and initial layers.

## Dialog window

![New Project dialog](img/new-project-dialog.png)

## Dialog controls

| Control | Purpose |
| --- | --- |
| *Project name* | Name used for the project folder and scene files. |
| *Project folder* | Parent directory where the project tree will be created. |
| *CRS* | Coordinate reference system (projected, metric preferred). |
| *Create default layers* | Populates the project with the standard layer set. |

## Workflow

1. Open the **New Project** dialog from the toolbar.
2. Set project name, destination folder, and CRS.
3. Optionally enable default layer creation.
4. Click **Create** — the plugin generates the project tree and loads the base layers.

## Requirements

- QGIS 3.40 LTR or later.
- Writable destination folder.
- A valid projected CRS (geographic CRS is not supported).

## Technical details

The project folder contains scene subfolders (`Scene1/`, `Scene2/`, …). Each scene carries its own geopackage, exported control files, and simulation outputs. The first scene is created automatically; additional scenes are added with **New Scene**.

## Scenes: new, delete, import

- **New Scene** duplicates the current scene's layer templates into a new subfolder without copying results.
- **Delete Scene** removes a scene and its files after confirmation.
- **Import Project** pulls an existing scene from another project on disk.

## Tips

- Keep project paths short on Windows — long-path issues still bite when exporting to the solver.
- Commit scene folders to git if you want scenario history; outputs are usually `.gitignore`d.
