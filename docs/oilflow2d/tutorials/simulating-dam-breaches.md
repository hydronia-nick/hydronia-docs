# Simulating dam breaches

This tutorial illustrates how to incorporate dam breach simulation into an existing RiverFlow2D  project using the QGIS  interface. The exercise consists of modeling the a dam break flood. The dam is approximately 1575 feet long, the breach center is 550 feet from the right margin of the dam, the opening of the breach has the final dimensions shown in the following Figure, a top width of 160 feet, and at the bottom width of 100 feet, the final breach height is 30 feet.

**Final dimensions of the dam breach.**

For this exercise, a file with the time evolution of the breaching dimensions is required, this file can be prepared before setting the model or it can be created when entering the input the parameters. The procedure to model the dam break involves the following steps:

1.  Open an existing RiverFlow2D  project.

2.  Create a *DamBreach* layer and to draw a line that represent the transverse axis of the dam.

3.  Generate the mesh.

4.  Run the model.

5.  Review the output files.

::: shaded
The files required to follow this tutorial can be extracted from the 'ExampleProjects' zip file under the 'DamBreachTutorial' folder. This zip file is downloaded separately from your installation materials.
:::

## Open an existing project

1.  Open QGIS

2.  On the *Project* menu click *Open...* and browse to the existing project: .

This project contains the *Domain Outline* layer, the digital elevation model DEM of in raster format, outflow conditions are set to free outflow in the lower left, and an initial condition of water surface elevation behind the dam. Figure [7.2](#11-2) shows the project in QGIS.

**Project loaded in QGIS.**

## Create the DamBreach layer and draw the line that defines the dam

Creating the dam involves the following steps:

1.  Create the template for the *DamBreach* layer: in the RiverFlow2D  toolbar click on the *New Template Layer* button

    <figure>
    <span class="image placeholder" data-original-image-src="img/button16.png" data-original-image-title="" width="1cm"></span>
    </figure>

2.  In the dialog select *DamBreach*, as shown in the figure below:

    

**Dialog to add a new layers.**

3.  Edit the *DamBreach* layer: In the layers panel, select the *DamBreach* layer.

4.  In the digitalization toolbar we click on the *Toggle Editting* button

    <figure>
    <span class="image placeholder" data-original-image-src="img/button7.png" data-original-image-title="" width="1cm"></span>
    </figure>

    A pencil icon will appear in the *DamBreach* layer, indicating that the layer is in edit mode:

    <figure>
    <span class="image placeholder" data-original-image-src="img/button29.png" data-original-image-title="" width="3.6cm"></span>
    </figure>

5.  Draw the line that defines the axis of the dam: Using the *Add Feature* tool of the digitalization toolbar

    <figure>
    <span class="image placeholder" data-original-image-src="img/button8.png" data-original-image-title="" width="1cm"></span>
    </figure>

6.  Draw the line that defines the dam axis. Keep in mind that the breach centroid is measured from the first vertex of the dam line. In this example it occurs 550 feet from the left margin of the dam (Figure [7.1](#11-1)). The dam axis is drawn from the top of the channel (point v0) to the bottom (point v1) along one side of the polygon that defines the initial water surface elevation, as illustrated in the image below.

    

**Dam axis.**

7.  Once finished drawing the dam axis, the window to input the parameters of the *DamBreach* appears.

8.  Input the information as seen below in the figure and click the *Check Fields* button:

    

**Dialog to input the dam breach parameters.**

9.  Click the *Temporal evolution* tab and click on the *Import Dam Breach File* button. Select the 'DAMBREACH_1.txt' file in the scenario folder. Click *OK* to close.

10. The temporal evolution of the 'DAMBREACH_1.TXT' file is shown in the *Temporal evolution* tab below:

    

**Evolution of the breach of the dam.**

    

**Dam axis.**

## Generate the mesh

The mesh is generated using the *Generate TriMesh* tool

<figure>
<span class="image placeholder" data-original-image-src="img/button6.png" data-original-image-title="" width="1cm"></span>
</figure>

Figure [7.8](#11-8) shows the resulting mesh of almost 11,000 cells

**The resulting dam breach mesh. Detail show mesh along the dam axis.**

## Exporting files to RiverFlow2D  

1.  Click on the *Export RiverFlow2D  * button.

    <figure>
    <span class="image placeholder" data-original-image-src="img/button9.png" data-original-image-title="" width="1cm"></span>
    </figure>

2.  Select the raster layer that contains the Digital Elevation Model (DEM) and the name of the project.

    

**Export dialog.**

3.  Once finished, click on the OK button and the export process will begin. Once it is finished, RiverFlow2D  will be loaded with the 'base.DAT' file.

## Running the model

After exporting the files, Hydronia Data Input Program is loaded with the project file of the 'base.DAT' example and shows the *Control Data* panel as illustrated in Figure [7.10](#11-10).

**Hydronia Data Input Program.**

It can be seen that the *Dam Breach* component is selected as well as the initial condition that indicates that the initial elevation of the water surface of the '.FED' file will be read. Selecting from the list on the left panel the *Dam Breach* component will show the panel where you can see the parameters of the dam breach as shown in the figure below:

**Dam Breach component.**

1.  Before running the model, set the simulation time to 4 hours.

2.  Leave all other parameters at their default values.

3.  To run the model, click on the Run RiverFlow2D button in the lower section of Hydronia Data Input Program.

4.  Save the changes with the same name as the 'DamBreach.DAT' file.

A window will appear indicating that the model has started running. The window that RiverFlow2D  presents while running the model shows simulation time information, volume conservation error, the total input and output discharge as well as other parameters as execution progresses (Figure [7.12](#11-12)).

**RiverFlow2D output graphics.**

## Review the output files

RiverFlow2D  output the dam breach hydrograph in a file with extension '.dambreachh'. Figure [7.13](#11-13) shows a section of that file for this exercise.

**Extract of the ‘DamBreach.dambreachh‘ file**

This concludes the *Simulating dam breaches* tutorial.
