# Appendix: QGIS Plugin Layer Attributes Reference

## Layer Attributes Reference
The following tables detail the attribute fields for the default layers created by the New RiverFlow2D Project tool and the New Template Layer Tool.

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

##### **DomainOutline** {#domainoutline .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CellSize | Real | Specifies the default cell size for mesh generation within the domain. |

##### **BoundaryConditions** {#boundaryconditions .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** BCID | String | User-defined identifier for the boundary segment. |
| BCType | Integer | Type code defining the boundary condition (e.g., WSE, Discharge, Rating Curve). |  |  |
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
| CULVERTYPE | Integer | Type defining culvert shape and hydraulic calculation method (e.g., 1=Rectangular, 2=Circular). |  |  |
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

##### **InitialConcentrationPollutants** {#initialconcentrationpollutants .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** POLLUTFILE | String | Path to file defining initial pollutant concentration values for this zone. |

##### **Internal_Rating_Table** {#internal_rating_table .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** IRT_ID | String | Unique identifier for the internal rating table location. |
| IRT_BCType | Integer | Boundary condition type (e.g., 19 for Stage vs Discharge). |  |  |
| IRTFileName | String | Path to the file containing the stage-discharge data. |  |  |
| CellSize | Real | Cell size parameter related to the internal boundary representation. |  |  |

##### **Piers** {#piers .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** PIERID | String | Unique identifier for the pier. |
| ICOMP | Integer | Calculation method (Scour): 1=Complex, 2=HEC-18, 3=Coarse Bed, 4=Cohesive. |  |  |
| ALFA | Real | Angle of attack (flow relative to pier alignment). |  |  |
| ISHAPE | Integer | Pier shape: 1=Square, 2=Round, 3=Cylindrical, 4=Sharp, 5=Group. |  |  |
| PIER_L | Real | Length of the pier parallel to flow. |  |  |
| PIER_A | Real | Width of the pier perpendicular to flow. |  |  |
| IBEDCO | Integer | Bed condition (Scour): 1=Clear-Water, 2=Plane/Antidune, 3=Small Dunes, 4=Medium Dunes, 5=Large Dunes. |  |  |
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
| IABUTMENT | Integer | Abutment type: 1=Spill-through, 2=Vertical wall. |  |  |
| IXSECTION | Integer | Cross-section type: 1=Bridge Section, 2=Upstream Section. |  |  |
| D50 | Real | Median grain size of bed material. |  |  |
| SW | Real | Specific weight of water. |  |  |

##### **ParticleTransport** {#particletransport .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** PARTICLEID | String | Unique identifier for the particle source/site. |
| FILENAME | String | Path to file defining particle release properties (e.g., count, timing, characteristics). |  |  |

##### **InitialBedFractions** {#initialbedfractions .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CONCENTFIL | String | Path to file defining initial bed sediment fraction values for this zone. |

##### **Channels1D** {#channels1d .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CHANID | String | Unique identifier for the 1D channel reach. |
| FILENAME | String | Path to file defining 1D channel geometry (e.g., cross-sections) and properties. |  |  |

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

##### **InitialConcentrationPollutants** {#initialconcentrationpollutants-1 .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** POLLUTID | String | Unique identifier for the pollutant concentration zone. |
| POLLUTFILE | String | Path to file defining initial pollutant concentration values for this zone. |  |  |

##### **ParticleTransport** {#particletransport-1 .unnumbered}

| **Field Name** | **Type** | **Description** |
| --- | --- | --- |
| PARTID | String | Unique identifier for the particle source/site. |
| PARTFILE | String | Path to file defining particle release properties (e.g., hydrograph). |
| CoordX | Real | X-coordinate of the release point (if point source). |
| CoordY | Real | Y-coordinate of the release point (if point source). |
| CoordZ | Real | Z-coordinate (elevation) of the release point (if point source). |
| NParts | Integer | Number of particles released per time step. |
| InitTime | Real | Initial time (hours) when the release starts. |
| Duration | Real | Duration of the release (hours). |
| ReleaseT | Real | Release time step (hours). |
| SettVel | Real | Settling velocity of particles. |
| CritShear | Real | Critical shear stress for deposition/erosion. |
| Density | Real | Density of the particles. |
| Diameter | Real | Diameter of the particles. |

##### **Channels1D** {#channels1d-1 .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** CHANID | String | Unique identifier for the 1D channel reach. |
| CHANFILE | String | Path to file defining 1D channel geometry (e.g., cross-sections) and properties. |  |  |
| ChanType | Integer | Type of 1D channel definition. |  |  |
| NNodes | Integer | Number of nodes defining the channel centerline. |  |  |
| Roughness | Real | Default Manning's roughness for the channel. |  |  |

##### **Landslides** {#landslides .unnumbered}

| **Field Name** | **Type** | **Description** |  |  |
| --- | --- | --- | --- | --- |
| **Field Name** | **Type** | **Description** LANDSLID | String | Unique identifier for the landslide source point. |
| LANDSLFILE | String | Path to file defining landslide hydrograph (volume vs time). |  |  |
| Volume | Real | Total volume of the landslide material. |  |  |
| Duration | Real | Duration of the landslide event. |  |  |
| Delay | Real | Delay time before the landslide starts. |  |  |
| Porosity | Real | Porosity of the landslide material. |  |  |
| SS | Real | Specific gravity of the landslide solids. |  |  |
| D50 | Real | Median grain size of the landslide material. |  |  |

##### **Hazard Event Editor File (HEEF)** {#hazard-event-editor-file-heef .unnumbered}

The HEEF functionality is managed through a dedicated dialog within the plugin (accessed via the HEEF Database tools). It allows users to define and manage different types of hazard events (e.g., Rainfall, Levee Breach, Dam Break) by specifying parameters and linking to relevant data files. It does not create a distinct GIS layer named \"HEEF\" within the project structure with standard attributes. Instead, it facilitates the configuration and application of these events within the simulation setup. Consult the HEEF dialog interface for specific event parameters.
