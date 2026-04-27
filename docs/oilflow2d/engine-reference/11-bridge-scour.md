# Bridge Scour

The bridge scour calculations implemented in RiverFlow2D are based on the methods developed by the U.S. Department of Transportation and described in depth in the Hydraulic Engineering Circular No. 18. RiverFlow2D includes tools to calculate pier and abutment scour using DIP.

## HEC-18 Method for Pier Scour

The equation used to compute pier scour in this method is:

$$y_s = y_1 2.0 K_1 K_2 K_3 ({a \over y_1})^{0.65} Fr^{0.43}$$

where:

$y_s$=Scour depth, ft or m,

$y_1$=Flow depth directly upstream of the pier, ft or m,

$K_1$=Correction factor for pier nose shape.

$$K_2 =(\cos{\alpha}+ max(L/a,12.) \sin{\alpha)}^{0.65}$$

$\alpha$ is the angle of attack in radians,

$K_3$=Correction factor for bed condition,

$a$=Pier width,ft or m,

$L$ =Length of pier, ft or m,

$Fr$=Froude Number directly upstream of the pier $Fr = V_1/\sqrt{g y_1}$,

$V_1$=Mean velocity of flow directly upstream of the pier, ft/s or m/s,

$g$=Acceleration of gravity, 32.2 ft/s$^2$ in English units and 9.81 m/s$^2$ in SI.

## Pier scour in Coarse Bed material

The equation is only applicable to clear-water flow conditions and to coarse bed materials with $D50 = 20$ mm and $\sigma \ge 1.5$.

$$y_s = 1.1 K_1 K_2 a^{0.62} y_1^{0.38} \tanh{{FrD^2 \over 1.97 \sigma^{1.5}}}$$

where:

$y_s, K1, K2, a, y_1, and V_1$ are defined as beforehand:

$FrD$= Densimetric particle Froude Number $= V_1 / \sqrt{g (Sg-1) D50}$,

$Sg$ = Sediment specific gravity,

$D50$ = Median bed material size, ft or m,

$D84$ = D84 sediment size, ft or m,

$\sigma$ = Sediment gradation coefficient = $D84/D50$.

## Pier scour in Cohesive Materials

$$y_s = 2.2 K_1 K_2 a^{0.65} \left(\frac{2.6 V_1 - V_c}{\sqrt{g}}\right)^{0.7}$$

where $y_s, K_1, K_2, a, and V_1$ are defined before and:

$V_c$ = Critical velocity for initiation of erosion of the material, ft/s or m/s.

## Top and bottom width of pier scour holes

To calculate the top width of pier scour holes we use the following equation:

$$W = y_s (K + \cot{\theta})$$

$$W_{bottom} = K y_s$$

where:

$W$ is the scour hole topwidth,

$W_{bottom}$ = scour hole bottom width,

$K$ = bottom width of the scour hole related to the depth of scour,

$\theta$ = angle of repose of the bed material.

## Abutment Scour

These are the equations used to calculate abutment scour.

$$Y_{max}LB = \alpha_a YcLB$$

$$Y_{max}CW = \alpha_b YcCW$$

$$YsA = Max(Y_{max}LB, Y_{max}CW) - Y_1$$

$$YcLB = Y_1 (q2c/q_1)^{6/7}$$

$$YcCW1 = (q2c/(K_4 D50^{1/3})^{6/7}$$

$$YcCW2 = (\gamma_w / \tau_c)(n \ q2c/K_5)^{6/7}$$

where:

$K_4$ = 11.17 for English units and 6.19 for SI units,

$\gamma_w$ = 62.4 Sw for English units,

$\gamma_w$ = 9800 Sw for SI units,

Sw is the water specific weight,

$V = q_1/y_1$,

$V_c$ = Critical velocity for initiation of erosion of the material, ft/s or m/s,

$V_c = K_u  y_1^{1/6}  D50^{1/3}$,

Where $K_u$ is 11.17 for English units and 6.19 for SI units,

If $V \ge V_c$ then use live-bed conditions,

If $V < V_c$ then use clear-water conditions.

### Scour amplification factor for spill-through abutments and live-bed conditions

To determine the amplification factor for spill-through abutments and live-bed conditions the following regressions are used.

$x = q2c/q_1$

$y = \alpha_a = Y_{max}/Yc$

For $x \in [1., 1.23]$

$y(x)  = -20172x^6 + 139961x^5 - 404430 x^4 + 622994x^3  - 539598x^2 + 249172x - 47926$

For $x \in (1.23, 1.60]$

$y(x)  = -1968.9x^6 + 16589x^5 - 58072x^4 + 108127x^3  - 112948x^2 + 62766x - 14497$

For $x \in (1.60, 3]$

$y(x) = 0.076x^6 - 1.136x^5+ 7.1218x^4 - 24.031x^3 + 46.166x^2 - 48.086x + 22.476$

For $x>3$, $y = y(3)$. $x < 1$ is not allowed.

### Scour amplification factor for wingwall abutments and live-bed conditions 

To determine the amplification factor for wingwall abutments and live-bed conditions the following regressions are used.

$x = q2c/q_1$

$y = \alpha_a = Y_{max}/Yc$

For $x \in [1., 1.24]$,

$y = 1085.1 x^5- 6379.4x^4 + 15009x^3 - 17670x^2 + 10414x - 2457.2$

For $x \in (1.24, 1.60]$

$y = -449.86x^6 + 3796.2 x^5 - 13319x^4 + 24872x^3 - 26082x^2 + 14567x - 3384.9$

For $x \in (1.60, 3]$

$y = 0.1371x^4 - 1.469x^3 + 6.0171x^2- 11.221x + 9.1721$

For $x>3$, $y = y(3)$. $x < 1$ is not allowed.

### Scour amplification factor for spill-through abutments and clear-water conditions

To determine the amplification factor for spill-through abutments and clear-water conditions the following regressions are used.

$x = q2c/q1$

$y = \alpha_b = Y_{max}/Yc$

For $x \in [1., 1.45]$

$y = 443.57x^5 - 2769.4x^4 + 6913.2x^3 - 8630.8x^2+ 5393.6x - 1349.2$

For $x \in (1.45, 5]$

$y = 0.0061x^5- 0.1193x^4 + 0.9027x^3 - 3.1887x^2 + 4.7646x - 0.2761$

For $x>5$, $y = y(5)$. $x < 1$ is not allowed.

### Scour amplification factor for wingwall abutments and clear-water conditions

To determine the amplification factor for wingwall abutments and clear-water conditions the following regressions are used.

$x = q2c/q1$

$y = \alpha_b = Y_{max}/Yc$

For $x \in [1., 1.18]$

$y = -331011x^6 + 2 10^6 x^5 - 6 10^6 x^4 + 9 10^6 x^3 - 8 10^6 x^2 + 1000000x - 632819$

For $x \in (1.18, 5]$

$y = -0.0033x^6 + 0.0639x^5 - 0.5041x^4 + 2.0151x^3 - 4.1113x^2+ 3.2197x + 2.0841$

For $x>5$, $y = y(5)$. $x < 1$ is not allowed.
