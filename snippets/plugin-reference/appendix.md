<!-- Shared source. Use product-neutral language. -->

## Reference: file formats

### `.CTL` — control file

The master simulation-control file. Plain text, key-value blocks. Exported by the plugin; generally not hand-edited.

### `.FED` — mesh + elevation

Binary mesh description with per-cell elevations. Regenerated on every export.

### `.hydrog` — hydrograph

Time-series files for inflow, outflow, rainfall, or other time-varying boundary conditions.

### `.OUT*` — solver output series

Per-variable time-series results. The plugin's Maps and Animation tools consume these directly.

## Reference: coordinate systems

- Projected, metric CRSs only.
- UTM is the default working assumption.
- Reprojection on import is available but not recommended for production work.

## Reference: performance notes

- GPU builds scale roughly linearly with cell count up to ~5M cells on modern cards.
- CPU builds are recommended for domains below 200k cells or when GPU memory is tight.
- Mesh refinement strongly outperforms timestep reduction for accuracy; refine first, reduce Δt only if stability demands it.
