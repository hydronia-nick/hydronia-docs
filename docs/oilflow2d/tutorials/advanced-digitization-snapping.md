# Advanced digitization/snapping

In many cases the drawing of polygons that share borders (contiguous) is required. Trying to do this manually usually produces polygon overlap errors, or it may generate gaps as illustrated in the following figure:

![Areas with overlap and empty spaces in manual digitization of adjacent polygons.](img/13-1.png){ width=80% }

This tutorial illustrates how to use the QGIS Snapping tool to facilitate the scanning of adjacent polygons. The procedure includes the following steps:

1.  Open an existing RiverFlow2D  project.

2.  Activate the *Snapping* tool.

3.  Configure the *Snapping* tool

4.  Draw contiguous or adjacent polygons using the *Snapping* tool.

::: shaded
The files required to follow this tutorial can be extracted from the 'ExampleProjects' zip file under the 'SnappingTutorial' folder. This zip file is downloaded separately from your installation materials.
:::

## Open an existing project

1.  Open QGIS

2.  In the main menu go to *Project* $\rightarrow$ *Open...* browse to the existing project: 'SnappingTutorial.qgz'.

This project contains the basic templates of a RiverFlow2D  project and a raster with 4 areas with different Manning's n coefficients derived from land cover and land use maps. From this raster, the polygons of the *Manning N* layer will be drawn. When the project is opened, a project image will be loaded in QGIS as shown in Figure 18.2.

![Project screen loaded in QGIS.](img/13-2.png){ width=90% }

## Activate and configure the Snapping tool

To use the Snapping tool, you must activate it beforehand:

1.  Open the configuration options window: In Project menu $\rightarrow$ Snapping Options...

    ![Project Snapping Settings window.](img/13-18.png){ width=100% }

2.  In the *Project Snapping Settings* window, click on the *Enable Snapping* button.

    ![](img/snappingbutton.png){ width=1cm }

3.  Next to the *Enable Snapping* button the dropdown menu for *All Layers* is activated. Click on the dropdown and select *Advanced Configuration*.

4.  In the list of layers, make sure only *Manning N* layer is selected.

5.  Select the checkbox to *Avoid Overlap* on the *Manning N* layer.

The configuration window of the Snapping tool should be as shown in the following Figure:

![Snapping configuration panel.](img/13-5.png){ width=90% }

## Draw contiguous or adjacent polygons using the Snapping tool

To draw the polygons with the information of the Manning's n coefficients we proceed as follows:

1.  Edit the *Manning N* layer: In the layers panel, select the *Manning N* layer

2.  In the digitalization toolbar click on the *Toggle Editing* button

    ![](img/button7.png){ width=1cm }

    A pencil icon will appear in the *Manning N* layer indicating that the layer is in edit mode:

    ![](img/button32.png){ width=3.6cm }

3.  Draw the polygon that demarcates the Manning's n area: Using the *Add Toggle Editing* button in the digitalization toolbar

    ![](img/button15.png){ width=1cm }

    proceed to draw the polygons. Start by drawing the polygon in the bottom of the watershed shown in gray which corresponds to n = 0.02. After completing the drawing you should have an image similar to the one shown in the following figure:

    ![The first polygon sketch.](img/13-6.png){ width=80% }

4.  Proceed to draw the second polygon. This will be the small yellow polygon to which corresponds to n = 0.30. To draw the polygon, follow the boundary with the green polygon as indicated by the raster, but in the boundary with the polygon already drawn (the gray) an overlap will be made so that the snapping tool takes the edge that already exists and completes the polygon. Try to make a path as shown in the figure below:

    ![Drawn of the second polygon.](img/13-7.png){ width=75% }

5.  Right-click to finish the drawing.

6.  Enter the Manning coefficient, n = 0.30 and you will have an image like the one shown below where you can see how the final drawing of the second polygon took the vertices of the first adjacent polygon:

    ![Final draw of the second polygon.](img/13-8.png){ width=75% }

7.  The third polygon to be drawn will be the large yellow polygon. Just as in the previous case, the contour of the polygon according to the raster is faithfully followed, but in the adjacent polygons it is already drawn overlapped. The figure below shows the initial drawing, with an approach in the area where the overlap is made with the existing polygon:

    ![Preliminary draw of the third polygon.](img/13-9.png){ width=90% }

8.  After finishing the drawing and assigning the *Manning N* umber to the polygon, the final drawing of the third polygon will be shown as shown below:

    ![Final draw of the third polygon.](img/13-10.png){ width=90% }

9.  The fourth polygon to draw will be the green polygon which corresponds to n = 0.45. To do it will follow the outer boundary of the same and the boundary with the brown polygon. Then a thick overlap will be made within the polygon already drawn, the yellows and the gray, as shown in the figure below:

    ![Preliminary draw of the fourth polygon.](img/13-11.png){ width=78% }

10. After finishing the drawing and assigning the Manning's n value to the polygon, you will have the final layout of the third polygon as shown below:

    ![Final draw of the fourth polygon.](img/13-12.png){ width=78% }

11. To finish, draw the fifth polygon of brown color, which corresponds to n = 0.03. For this the outer limit is drawn following the contour of the raster and for the shared limits an overlap is made inside the neighboring polygons as shown in the figure below:

    ![Preliminary draw of the fifth polygon.](img/13-13.png){ width=60% }

12. After finishing the drawing and inputting the Manning coefficient to the polygon, you will have the final drawing of the third polygon as shown below:

    ![Final draw of the fifth polygon.](img/13-14.png){ width=73% }

13. To finish, click on the *Toggle Editing* button

    ![](img/button7.png){ width=1cm }

    changes are accepted and saved. Then the layer of the raster Manning_Map_n is deactivated, and the *Manning N* vectorized layer can be observed as shown in the Figure below:

    ![Final draw of the Manning N layer.](img/13-15.png){ width=90% }

## Delete a polygon

Suppose you want to delete the last polygon created because you are not satisfied with the result. In that case you can proceed doing as follows:

1.  The *Manning N* layer is edited using the *Toggle Editing* button

    ![](img/button7.png){ width=1cm }

    ![](img/button32.png){ width=3.6cm }

2.  Then the polygon to be eliminated is selected using the *Select Feature* button

    ![](img/button33.png){ width=1cm }

3.  With the active select Feature tool, click on the polygon to be deleted and it will be highlighted in yellow to indicate that it is selected (Figure 18.15).

    ![Polygon to be deleted selected.](img/13-16.png){ width=65% }

4.  Then the polygon is deleted either with the Delete key on the keyboard or with the *Delete selected* button

    ![](img/button34.png){ width=1cm }

    ![Manning N layer with the polygon removed.](img/13-17.png){ width=65% }

5.  Finally, the changes are saved and the editing mode of the layer is deactivated by clicking on the *Toggle Editing* button.

    ![](img/button7.png){ width=1cm }

This concludes the Snapping tutorial.
