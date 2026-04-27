# Water Quality Model: WQ Module

In this chapter, a 2D shallow water flow solver integrated with a water quality model is presented. The interaction between the main water quality constituents included is based on the Water Quality Analysis Simulation Program. The proposed numerical model is evaluated in cases that include the transport and reaction of water quality components over irregular bed topography and dry-wet fronts, verifying that the numerical solution in these situations conserves the required properties (C-property and positivity). The model can operate in any steady or unsteady form allowing an efficient assessment of the environmental impact of water flows.

The configurations of this module follow the structure given in the table :

p4cm p1.8cm p2cm p1.5cm p1.5cm p1.5cm p1.5cm

&**Option**:\
- **&:** 1; 2; 3; 4
- ****State variable**:** **SI Units**; **English Units**
- **Ammonium nitrogen ($\rm{NH_4^+-N}$):** $\rm{gN/m^3}$; $\rm{lbN/ft^3}$; &; &
- **Nitrate Nitrogen ($\rm{NO_3^--N}$):** $\rm{gN/m^3}$; $\rm{lbN/ft^3}$; &; &
- **Inorganic phosphorus ($\rm{IP}$):** $\rm{gP/m^3}$; $\rm{lbP/ft^3}$; &; &
- **Phytoplankton carbon ($\rm{PHYT}$):** $\rm{gC/m^3}$; $\rm{lbC/ft^3}$; &; &
- **ultimate carbonaceous biological oxygen demanad ($\rm{CBOD}$):** $\rm{gO_2/m^3}$; $\rm{lbO_2/ft^3}$; &; &
- **Dissolved oxygen ($\rm{DO}$):** $\rm{gO_2/m^3}$; $\rm{lbO_2/ft^3}$; &; &
- **Organic nitrogen ($\rm{ON}$):** $\rm{gN/m^3}$; $\rm{lbN/ft^3}$; &; &
- **Organic phosphorus ($\rm{OP}$):** $\rm{gP/m^3}$; $\rm{lbP/ft^3}$; &; &
- **Temperature ($\rm{T}$):** $^\circ$C; $^\circ$F; &; &
- **Total coliform bacteria ($\rm{TC}$):** TC/100 mL; TC/100 mL; &; &

#### Dissolved oxygen {#dissolved-oxygen .unnumbered}

The DO ($\phi_6$) is one of the most important parameters of water quality, because it is a basic requirement for a healthy aquatic ecosystem. The DO concentration in a stream can change through an exchange with the atmosphere (coefficient ka) and the growth of algae (photosynthesis).

However, its depletion is due to the oxidation of organic carbon (affected by coefficient $k_d$), nitrification ($k_{12}$), the death of algae (respiration $k_{1R}$) and the sediment oxygen demand (SOD), defined as the rate of DO required for the oxidation of organic matter in benthic sediments. The DO concentration frequently oscillates in the water column, but its oscillation is higher when it arises from the human activity (Gordillo et al. 2020). The complete process that includes all these gains and losses of DO in the water column can be expressed as $R_6$.

#### Carbonaceous BOD {#carbonaceous-bod .unnumbered}

The carbonaceous BOD (CBOD; $\phi_5$) is the concentration of organic material present in the water body. This process ($R_5$) includes the effects of sedimentation, oxidation ($k_d$) and denitrification ($k_{2D}$). The principal sources of CBOD are man-made sources, algal death ($k_{1d}$) and natural runoff. There is a mutual interaction between the CBOD and the DO components, so that, in particular, the DO level will decrease when the injection of CBOD is continuous in time, causing an oxygen deficit (Gordillo et al. 2020).

#### Phytoplankton {#phytoplankton .unnumbered}

The quality of a body of water can be affected by the presence of phytoplankton ($\phi_4$). This population can be accelerated by the addition of nutrients (nitrogen and phosphorus), either by human activities or natural processes. The excess of nutrients provides more population growth. This uncontrolled growth is commonly referred to as eutrophication. When this population becomes large, it may cause diurnal variations in DO that can be fatal to fish life. Also, the presence of phytoplankton can cause water taste and odor problems.

The model considers two of the three primary dependent systems: the phytoplankton population and the nutrient system. The external environment variables that affect those systems are temperature, advective flow and solar radiation. The classical approach is to assume that these effects are multiplicative. Thereby, the increase of phytoplankton in rivers and streams is due to the availability of nutrients and solar energy, while its reduction occurs primarily through respiration (Gordillo et al. 2020). A simplified representation of this process is given by $R_4$.

#### Nitrogenous BOD (NBOD) {#nitrogenous-bod-nbod .unnumbered}

Nitrogen can be found in five major forms in aquatic environments: organic nitrogen (ON), ammonia (NH$_3$), nitrite (NO$^-_2$), nitrate (NO$^-_3$) and dissolved nitrogen gas (N$_2$). The sequential processes of nitrogen compounds transforming ON to NH$_3$, NO$^-_2$ and finally to NO$^-_3$ (Gordillo et al. 2020).

The ON ($\phi_7$) originally present in water is partially transformed into NH$_3$ and partially settles on the bottom; meanwhile, the increase of ON is due to phytoplankton death. The ON kinetic equation describing these processes is expressed as $R_7$, involving ($k_{71}$).

NH$_3$ ($\phi_1$) is one of the intermediate compounds formed during biological metabolism and, together with ON, is considered as an indicator of recent pollution. The ammonia concentration is increased by the change of ON to NH$_3$ due to mineralization and the production of nitrogen due to phytoplankton death and respiration. At the same time, its concentration is reduced by the uptake for phytoplankton growth and the change of NH$_3$ to NO$^-_3$ due to nitrification. The corresponding kinetic process for this state variable is $R_1$.

NO$^-_3$ ($\phi_2$), the end product of nitrification, represents the sum of NO$^-_2$ and NO$^-_3$ (the amount of NO$^-_2$ present in natural waters is usually very small). Its reduction is due to the growth of phytoplankton and the denitrification process ($k_{2D}$); meanwhile, its rise is generated by the nitrification process ($k_{12}$). Therefore, the total nitrate concentration can be expressed as $R_2$.

#### Phosphorus (OP, PO$_3$) {#phosphorus-op-po_3 .unnumbered}

To model the phosphorus cycle, two single kinetic equations are taken into account: organic phosphorus (OP) ($\phi_8$) and inorganic phosphorus PO$^-_3$ 3 ($\phi_3$) (Gordillo et al. 2020).

The production of OP is caused by phytoplankton death and respiration. Conversely, the loss of OP is due to mineralization and the settling process ($R_8$). The kinetics of PO$^-_3$ is affected by the uptake for phytoplankton growth. However, the production of phosphorus is caused by phytoplankton death, respiration and mineralization. Hence, the mathematical equation for PO$^-_3$ can be expressed as $R_3$.

All the kinetic equations that describe the increase or decrease of state variables in time as well as all the coefficients controlling the rate of the processes are summarized in Tables , and.

#### Temperature {#temperature .unnumbered}

The integrity of all the processes can be largely affected by the river temperature. High or low water temperatures generate a potential risk for aquatic biota, biological and chemical reactions. Also, the rate coefficients of most reactions in natural waters are affected by the temperature (Gordillo et al. 2020). In the present work, some of the kb biodegradation process coefficients have been made dependent on the temperature with reference to the rate at 20 $^\circ$C (Ji, 2017) as follows:

$$k_b(T) = k_b(20) \theta{^(T-20)_R}$$

where $T$ is the temperature in degrees Celsius, $k_b$ is the biodegradation rate and $\theta_R$ is a temperature correction factor for every process. According to Chapra (2008), the correction factor is bounded by $1.01 < \theta_R < 1.1$ for most steady processes.

- **In this study, following Edinger et al. (1968), a temperature transport model has been included assuming it as a scalar variable whose evolution can be formulated following also an advection--reaction equation. The total heat budget for a water body includes the effects of water depth, velocity and atmospheric conditions. For that purpose, it is useful to estimate the daily average stream temperature based on climate conditions (Gu:** Li 2002; Herb; Stefan 2011).

## Hydrodynamic and Water Quality State Variable Equations

The flow of water with a free surface can be described by using equations that conserve mass and momentum:

$$\begin{aligned}
\begin{aligned}
\frac{\partial \textbf{U}}{\partial t}+\frac{\partial \textbf{F}(\textbf{U})}{\partial x}+\frac{\partial \textbf{G}(\textbf{U})}{\partial y}=\textbf{H}(\textbf{U})
\end{aligned} 
\end{aligned}$$

with:

$$\begin{aligned}
\begin{aligned}
&\textbf{U}=(h,q_x,q_y)^T\\[3ex]
&\textbf{F}=\left(q_x,\frac{q^2x}{h}+\frac{1}{2}gh^2,\frac{q_xq_y}{h}\right)^T\\[3ex]
&\textbf{G}=\left(q_y,\frac{q_xq_y}{h},\frac{q^2y}{h}+\frac{1}{2}gh^2\right)^T\\[3ex]
&\textbf{H}=\left(0,gh(S_{0x}-S_{fx}),gh(S_{0y}-S_{fy})\right)^T\\[3ex]
\end{aligned} 
\end{aligned}$$

$$\begin{split}
    &q_x=uh\\
    &q_y=vh\\
    &(u,v)=\text{Average components of velocity vector \textbf{u} along the x and y}\\
    &h=\text{depth}\\
    \nonumber
    \end{split}$$

The transport equation is written as:

$$\begin{aligned}
&\frac{\partial (h\phi_i)}{\partial t}+\frac{\partial(hu \phi_i)}{\partial x}+\frac{\partial(hv \phi_i)}{\partial y}=E\frac{\partial}{\partial x}\left( h\frac{\partial \phi_i}{\partial x}\right) +E\frac{\partial}{\partial y}\left( h\frac{\partial \phi_i}{\partial y}\right) \pm hR_i \pm f_i\\
\end{aligned}$$

where $\phi_i$ is the average concentration of each state variable, $E$ is the dispersion coefficient, $f_i$ point and non-point sources, y $R_i$ represents the formation or consumption of each constituent.

The term $R_i$ is established according to the Petersen matrix. The matrix is composed of processes (rows) and state variables (columns), with elements within the matrix that include stoichiometric coefficients that establish the relationships between the components in the individual processes. The general matrix to simulate the options in table , it will be defined according to the tables , , and

90
