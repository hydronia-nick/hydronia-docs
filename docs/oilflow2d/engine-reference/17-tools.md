# OilFlow2D Tools

## Automated Batch Execution of Model Simulations

You can perform multiple OilFlow2D runs using batch scripts. When controlling model runs through batch scripts, it is recommended to enable the *Automatic Close of Model Windows* output option in the DIP interface to ensure uninterrupted execution.

There are two available methods for performing multiple runs using batch scripts:

- Using a MS-DOS script in a file.
- Using a script written in the Python computer programming language.

!!! note

    Note: The script files described in this chapter can be downloaded using the following link:

    [BarchRun-RF2D-OF2D.zip](https://www.dropbox.com/scl/fi/nmy8pcai4w5a1g2v6zola/BarchRun-RF2D-OF2D.zip?rlkey=luo9ezqtmndbn9f635ovynrea&dl=0)

### Using a MS-DOS script to perform multiple batch runs


        C:
        cd "C:\Program Files\Hydronia\OilFlow2D"
        OilFlow2Dm5 "D:\OilFlow2D\Projects\ProjectA\Scenario1\Run1" > "D:\OilFlow2D\Projects\ProjectA\Scenario1\Run1_batch.log"
        OilFlow2Dm5 "D:\OilFlow2D\Projects\ProjectA\Scenario2\Run2" > "D:\OilFlow2D\Projects\ProjectA\Scenario2\Run2_batch.log"


!!! warning

    The redirect log filename must not match `<projectname>.log`. The OilFlow2D engine writes its own log file using that exact name, and redirecting to the same path locks the file for the duration of the command, preventing the OilFlow2D Plus viewer from launching. Use a different suffix such as `_batch.log` (as shown above) or omit the redirect entirely.

    Comment lines in MS-DOS batch files must start with `REM` or `::`. The `%` character begins variable expansion, so any line that starts with `%` will be parsed and executed as a command rather than ignored as a comment.


### Using a Python script within QGIS to perform multiple batch runs

This script runs within the QGIS Python Console, but has the disadvantage that blocks QGIS while running models.


    # -*- coding: utf-8 -*-
    from subprocess import call

    oilflow2d_path = r"C:\Program Files\Hydronia\OilFlow2D\OilFlow2Dm5 "

    dat_paths = [ 
               r"C:\Users\hydronia\Documents\OilFlow2D_QGIS\ExampleProjects\OilSpillLandTutorial\OilSpillLand_Run",
               r"C:\Users\hydronia\Documents\OilFlow2D_QGIS\ExampleProjects\OilSpillWaterTutorial\OilSpillWater_Run"
                ]

    for path in dat_paths:
        prjPath = oilflow2d_path + path 
        call(prjPath)


### Using a Python script through a batch file to perform multiple runs

This Python script also runs from within QGIS, but creates a .BAT file that does not block QGIS while the models are executing.


    # -*- coding: utf-8 -*-
    import tempfile
    import subprocess
    tmpdir = tempfile.mkdtemp(prefix='of2qgis')
    temp = os.path.join(tmpdir, "temp.bat")

    dat_paths = [
               r"C:\Users\hydronia\Documents\OilFlow2D_QGIS\ExampleProjects\OilSpillLandTutorial\OilSpillLand_Run",
               r"C:\Users\hydronia\Documents\OilFlow2D_QGIS\ExampleProjects\OilSpillWaterTutorial\OilSpillWater_Run"
                ]

    with open(temp, "w") as f:
      f.write("C:\n")
      f.write('cd "C:\Program Files\Hydronia\OilFlow2D"\n')
      for path in dat_paths:
          f.write('OilFlow2Dm5 "' + path + '" > "' + QFileInfo(path).absolutePath +
           '/Run.log" \n')

    subprocess.Popen(temp, shell=True)
