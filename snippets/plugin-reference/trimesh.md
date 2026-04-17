<!-- Shared source. Use product-neutral language. -->

## Overview

The **TriMesh** toolbar group generates an unstructured triangular mesh covering the simulation domain. The mesher is [Gmsh](https://gmsh.info), called through a PyQGIS wrapper that feeds it the domain polygon, break-lines, and DEM elevations.

## Dialog window

![TriMesh Generation dialog](img/trimesh-dialog.png)

## Dialog controls

| Control | Purpose |
| --- | --- |
| *Domain layer* | Polygon layer defining the outer boundary of the mesh. |
| *Break-lines layer* | Optional line layer constraining element edges (levees, roads, ridges). |
| *Target element size* | Nominal edge length, in CRS units. |
| *Size gradation* | Ratio by which element size is allowed to grow per step. |
| *DEM for elevation* | Raster used to assign cell-centroid elevation. |

## Workflow

1. Prepare the domain polygon and any break-line layers.
2. Open the **Generate TriMesh** dialog.
3. Select domain, break-lines, element size, and DEM.
4. Run — the mesher produces a cell layer and a node layer with elevations attached.

## Requirements

- Domain must be a single, simple polygon in the project CRS.
- Break-lines must be entirely inside the domain and non-self-intersecting.
- DEM extent must cover the domain.

## Technical details

Internally the plugin writes a `.geo` script, invokes Gmsh, parses the `.msh` output, and projects each node's elevation from the DEM. Mesh quality is reported (minimum angle, max skewness) after generation.

## Tips

- Start with a coarse mesh, inspect, then refine. Iteration is faster than a perfect first pass.
- Use break-lines on hydraulic control features — levees and ridgelines especially benefit from mesh-aware alignment.
