# Appendix: QGIS Plugin Layer Attributes Reference

## Layer Attributes Reference
The following tables detail the attribute fields for the default layers created by the New OilFlow2D Project tool and the New Template Layer Tool.

##### **MeshDensityLine** {#meshdensityline .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CellSize | Real | Target mesh element size along this line. |

##### **MeshDensityPolygon** {#meshdensitypolygon .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CellSize | Real | Target mesh element size within this area. |

##### **MeshBreakLine** {#meshbreakline .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CellSize | Real | Target mesh element size along this enforced breakline. |

##### **MultipleDemBoundaries** {#multipledemboundaries .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** dem_layer | String | Identifier or path for the DEM layer associated with this boundary. |

##### **Domain_Outline** {#domain_outline .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CellSize | Real | Specifies the default cell size for mesh generation within the domain. |

##### **BoundaryConditions** {#boundaryconditions .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** BCID | String | User-defined identifier for the boundary segment. |
| BCType | Integer | Type: 1=WSE vs Time (Free), 6=Discharge vs Time, 9=Rating Curve, 12=Normal Depth (Outflow), etc. See plugin UI for full list. |  |  |
| BCFileName | String | Path/Name of the associated data file (e.g., hydrograph, rating curve). |  |  |

##### **Manning N** {#manning-n .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** ManningN | Real | Isotropic Manning's roughness coefficient for this area. |

##### **Manning_Nz** {#manning_nz .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** MANNNFILE | String | Path to the file defining anisotropic Manning's values (n, nx, ny, angle). |

##### **Initial_WSE** {#initial_wse .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** InitialWSE | Real | Initial water surface elevation value for this zone. |

##### **MaximumErosionDepth** {#maximumerosiondepth .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** MAXERODEPT | Real | Maximum allowable erosion depth in this zone. |

##### **Infiltration** {#infiltration .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** INFILFILE | String | Path to the file defining infiltration parameters for this zone. |

##### **RainEvap** {#rainevap .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** RAINEVFILE | String | Path to the file defining rainfall/evaporation rates for this zone. |

##### **Wind** {#wind .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CD | Real | Wind drag coefficient. |
| AIRDENSITY | Real | Air density. |  |  |
| WINDFILE | String | Path to the file containing wind speed and direction time series. |  |  |

##### **Bridges** {#bridges .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** BRIDGEID | String | Unique identifier for the bridge. |
| LELEM | Integer | Number of elements spanned by the bridge representation. |  |  |
| BRIDGEFILE | String | Path to the file defining bridge geometry/properties. |  |  |
| ZUPPER | Real | Elevation of the bridge deck soffit (underside). |  |  |
| DECK | Real | Thickness of the bridge deck. |  |  |

##### **Gates** {#gates .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** GATEID | String | Unique identifier for the gate. |
| LELEM | Integer | Number of elements spanned by the gate representation. |  |  |
| GATEFILE | String | Path to the file defining gate operation rules (time vs opening). |  |  |
| CRESTELEV | Real | Elevation of the gate sill/crest. |  |  |
| GHEIGHT | Real | Height of the gate opening when fully open. |  |  |
| GATECD | Real | Discharge coefficient for the gate. |  |  |

##### **Culverts** {#culverts .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CULVERTID | String | Unique identifier for the culvert. |
| CULVERTYPE | Integer | Type defining culvert shape and hydraulic calculation method (e.g., 1=Rectangular, 2=Circular). See plugin UI for full list. |  |  |
| CULVERTFIL | String | Path to rating curve file (if CULVERTYPE=0). |  |  |
| Nb | Integer | Number of identical barrels. |  |  |
| Ke | Real | Entrance loss coefficient. |  |  |
| nc | Real | Manningś n for the culvert barrel. |  |  |
| KP | Real | Coefficient used in FHWA equation. |  |  |
| M | Real | Coefficient used in FHWA equation. |  |  |
| Cp | Real | Coefficient used in FHWA equation. |  |  |
| Y | Real | Coefficient used in FHWA equation. |  |  |
| m1 | Real | Coefficient used in FHWA equation (0.7 or -0.5). |  |  |
| Hb | Real | Height of box culvert. |  |  |
| Base | Real | Base width of box culvert. |  |  |
| Dc | Real | Diameter of circular culvert. |  |  |
| INVERT_Z1 | Real | Invert elevation at the upstream end. |  |  |
| INVERT_Z2 | Real | Invert elevation at the downstream end. |  |  |

##### **Weirs** {#weirs .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** WEIR_ID | String | Unique identifier for the weir. |
| WEIRCD | Real | Discharge coefficient for the weir. |  |  |
| WCRESTELEV | String | Path to the file defining weir crest elevation profile or a constant value. |  |  |
| LELEM | Real | Number of elements spanned by the weir representation. |  |  |

##### **DamBreach** {#dambreach .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** DAMID | String | Unique identifier for the dam/breach segment. |
| DAMFILE | String | Path to file defining prescribed breach parameters (if iFailure=1). |  |  |
| L_CENTER | Real | Location of breach center along the dam line. |  |  |
| Z_CREST | Real | Initial elevation of the dam crest. |  |  |
| BREACHANG | Real | Angle of the breach side slopes. |  |  |
| BREACHCD | Real | Discharge coefficient for the breach flow. |  |  |
| LELEM | Real | Number of elements spanned by the dam representation. |  |  |
| iFailure | Integer | Failure mode: 1=Prescribed, 2=Overtopping, 3=Piping. |  |  |
| D50 | Real | Median grain size of dam material (for erosion modes). |  |  |
| Tau_c | Real | Critical shear stress (for erosion modes). |  |  |
| K_sm | Real | Coefficient (for erosion modes). |  |  |
| T_initial | Real | Time of breach initiation (for erosion modes). |  |  |
| GS | Real | Specific gravity of dam material (for erosion modes). |  |  |
| Porosity | Real | Porosity of dam material (for erosion modes). |  |  |
| kd | Real | Erodibility coefficient (for erosion modes). |  |  |
| Zb0 | Real | Initial breach bottom elevation (for erosion modes). |  |  |
| C | Real | Coefficient (for erosion modes). |  |  |
| cWidth | Real | Crest width of the dam. |  |  |
| uSlope | Real | Upstream slope of the dam. |  |  |
| dSlope | Real | Downstream slope of the dam. |  |  |

##### **Sources_Sinks** {#sources_sinks .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** SOURCEID | String | Unique identifier for the source/sink. |
| SOURCETYPE | Integer | Type: 1=Discharge vs Time, 2=Rating Curve (Depth vs Q). |  |  |
| FILENAME | String | Path to the associated data file (hydrograph or rating curve). |  |  |

##### **InitialConcentrations** {#initialconcentrations .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CONCENTFIL | String | Path to file defining initial concentration values for this zone. |

##### **Internal_Rating_Table** {#internal_rating_table .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** IRT_ID | String | Unique identifier for the internal rating table location. |
| IRT_BCType | Integer | Boundary condition type (typically 19 for Stage vs Discharge). |  |  |
| IRTFileName | String | Path to the file containing the stage-discharge data. |  |  |
| CellSize | Real | Cell size parameter related to the internal boundary representation. |  |  |

##### **Piers** {#piers .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** PIERID | String | Unique identifier for the pier. |
| ICOMP | Integer | Calculation method: 1=Complex piers, 2=HEC-18, 3=Coarse Bed, 4=Cohesive Materials. |  |  |
| ALFA | Real | Angle of attack (flow relative to pier alignment). |  |  |
| ISHAPE | Integer | Pier shape: 1=Square Nose, 2=Round Nose, 3=Cylindrical, 4=Sharp Nose, 5=Group of Cylinders. |  |  |
| PIER_L | Real | Length of the pier parallel to flow. |  |  |
| PIER_A | Real | Width of the pier perpendicular to flow. |  |  |
| IBEDCO | Integer | Bed condition: 1=Clear-Water Scour, 2=Plane bed and Antidune flow, 3=Small Dunes, 4=Medium Dunes, 5=Large Dunes. |  |  |
| D50 | Real | Median grain size of bed material. |  |  |
| D84 | Real | Grain size for which 84 |  |  |
| SS | Real | Specific gravity of sediment. |  |  |
| SW | Real | Specific weight of water. |  |  |
| THETA | Real | Critical Shields parameter. |  |  |
| VC | Real | Critical velocity for initiation of motion. |  |  |
| CD | Real | Drag coefficient for the pier. |  |  |

##### **Abutments** {#abutments .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** ABUTID | String | Unique identifier for the abutment. |
| IABUTMENT | Integer | Abutment type: 1=Spill-through, 2=Vertical wall with wind walls. |  |  |
| IXSECTION | Integer | Cross-section type: 1=Bridge Section, 2=Upstream Section. |  |  |
| D50 | Real | Median grain size of bed material. |  |  |
| SW | Real | Specific weight of water. |  |  |

##### **OilSpills** {#oilspills .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** IDSPILLSTE | String | Unique identifier for the spill source/site. |
| WDENSITY | Real | Density of the water. |  |  |
| COORD_X | Real | X-coordinate of the spill location. |  |  |
| COORD_Y | Real | Y-coordinate of the spill location. |  |  |
| COORD_Z | Real | Z-coordinate (elevation) of the spill location. |  |  |
| NPARCELS | Integer | Number of parcels released per time step for this spill. |  |  |
| OILDENSITY | Real | Density of the spilled oil. |  |  |
| OILVISCOS | Real | Viscosity of the spilled oil. |  |  |
| INITIALST | Real | Initial time (hours) when the spill starts. |  |  |
| DISP_L | Real | Longitudinal dispersion coefficient. |  |  |
| DISP_T | Real | Transverse dispersion coefficient. |  |  |
| DISP_V | Real | Vertical dispersion coefficient. |  |  |
| HYDROGFILE | String | Path to the file defining the spill hydrograph (volume vs time). |  |  |
| s_bottom | Boolean | Flag to activate interaction with the bottom. |  |  |
| s_shore | Boolean | Flag to activate interaction with the shoreline. |  |  |
| s_dispapp | Boolean | Flag related to dispersant application effects. |  |  |
| s_vegtrapp | Boolean | Flag to activate trapping by vegetation. |  |  |

##### **Shorelines** {#shorelines .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** IDTYPE | Integer | Type of shoreline (e.g., 1=Rocky cliffs, 2=Sand beaches, etc. See plugin UI for full list). |

##### **InitialBedFractions** {#initialbedfractions .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CONCENTFIL | String | Path to file defining initial bed sediment fraction values for this zone. |

##### **SpillBooms** {#spillbooms .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** BOOMID | String | Unique identifier for the spill boom. |
| BOOMTYPE | Integer | Type of boom (e.g., 1=Curtain, 2=Fence, 3=Sorbent, 4=Bubble). See plugin UI for full list. |  |  |
| SKIRTHEIGH | Real | Skirt height of the boom. |  |  |
| POILLOSS | Real | Percentage of oil loss through the boom. |  |  |
| VU | Real | Boom velocity component in U direction. |  |  |
| VV | Real | Boom velocity component in V direction. |  |  |

##### **SpillPaths** {#spillpaths .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** IDSPILLSTE | String | Unique identifier for the spill source/site associated with this path. |
| WDENSITY | Real | Density of the water. |  |  |
| NPARCELS | Integer | Number of parcels released per time step along this path. |  |  |
| OILDENSITY | Real | Density of the spilled oil. |  |  |
| OILVISCOS | Real | Viscosity of the spilled oil. |  |  |
| INITIALST | Real | Initial time (hours) when the spill starts. |  |  |
| DISP_L | Real | Longitudinal dispersion coefficient. |  |  |
| DISP_T | Real | Transverse dispersion coefficient. |  |  |
| DISP_V | Real | Vertical dispersion coefficient. |  |  |
| HYDROGFILE | String | Path to the file defining the spill hydrograph (volume vs time). |  |  |

##### **OilPipelines** {#oilpipelines .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** OPLID | String | Unique identifier for the pipeline segment. |
| OPLFILE | String | Path to file containing detailed pipeline properties or data. |  |  |

##### **OilPipeLineBoundCond** {#oilpipelineboundcond .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** OPLBCID | String | Unique identifier for the pipeline boundary condition point. |
| OPLBCTYPE | Integer | Type of boundary condition (e.g., leak rate, pressure). |  |  |
| OPLBCFILE | String | Path to file containing time series data for the boundary condition. |  |  |

##### **OilRetDepth** {#oilretdepth .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** RETDEPFIL | String | Path to file defining oil retention depth parameters for this zone. |

##### **VegTrapp** {#vegtrapp .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** VEGTRAPFIL | String | Path to file defining vegetation trapping parameters for this zone. |

##### **CrossSections** {#crosssections .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** XSECID | String | Unique identifier for the cross-section line. |
| ND_CS | Integer | Number of discretization points along the cross-section for output. |  |  |

##### **Profiles** {#profiles .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** PROFILEID | String | Unique identifier for the profile line. |
| ND_PR | Integer | Number of discretization points along the profile line for output. |  |  |

##### **ObservationPoints** {#observationpoints .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** ObsID | String | Unique identifier for the observation point. |
