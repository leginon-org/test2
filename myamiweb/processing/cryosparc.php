<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 *	Simple viewer to view a image using mrcmodule
 */
require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";

processing_header("Appion cryoSPARC", "cryoSPARC");
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST) {
    runProgram();
}
// CREATE FORM PAGE
else {
    if ($_GET['delId']) {
        delete($_GET['delId']);
    }
    elseif ($_GET['id']) {
        display($_GET['id']);
    }
    else {
        createForm();
    }
}

// CREATE FORM PAGE
function createForm($extra=false) {
    if ($extra) {
        echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
    }
    if (privilege('groups') > 3 ){
        echo"<FORM NAME='viewerform' method='POST'>\n";
        echo"<p>Please enter cryoSPARC project and job id for a cryoSPARC 3D refinement job.</p>
        <TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
        <tr>
        <td>";
        echo "<label for='projectId'>Project ID: </label>";
        echo "<input type='text' id='project' name='projectId' size='6'>";
        echo "</td>
        <td>";
        echo "<label for='jobId'>Job ID: </label>";
        echo "<input type='text' id='job' name='jobId' size='6'>";
        echo "</td>
        <td>
        <input type='submit' value='Submit'>
        </td>
    	</tr>
    	</table>
        </form>\n";
    }
    else {
        echo "<p>Administration privileges is needed to add new cryoSPARC job. Please ask an Administrator to add cryoSPARC job, if needed.</p>";
    }
    $particle = new particledata();
    $expId = $_GET['expId'];
    $jobs = $particle->getCryosparcJobs($expId);
    if ($jobs) {
        echo "<h3>Available CryoSPARC Jobs</h3>";
        echo"<TABLE BORDER=1 CLASS=tableborder CELLPADDING=15>
        <tr>
        <th>Project ID</th>
        <th>Job ID</th>
        <th></th>
        <th></th>
        </tr>";
        $phpself = $_SERVER['PHP_SELF'];
        foreach ($jobs as $job){
            $id = $job[id];
            echo "<tr>
            <td>$job[projectId]</td>
            <td>$job[jobId]</td>
            <td><a href='$phpself?expId=$expId&id=$id'>Summary</a></td>
            <td><a href='$phpself?expId=$expId&delId=$id'>Delete</a></td>
            </tr>";
        }
        echo "</table>";
    }
}

// --- parse data and process on submit
function runProgram() {
    
    /* *******************
     PART 1: Get variables
     ******************** */
    $expId = $_GET['expId'];
    $projectId = $_POST['projectId'];
    $jobId = $_POST['jobId'];
    if (!$projectId || !$jobId){
        createForm("Please provide a valid cryoSPARC project and job id");
        exit;
    }
    $manager = new MongoDB\Driver\Manager("mongodb://".CRYOSPARC.":".CRYOSPARC_PORT);
    $query = new MongoDB\Driver\Query(array('project_uid' => "$projectId", 'job_uid' => "$jobId"));
    $cursor = $manager->executeQuery('meteor.events', $query);
    $results = $cursor->toArray();
    if (!$results){
        createForm("Could not find cryoSPARC project '$projectId' with job id '$jobId'");
        exit;
    }
    $particle = new particledata();
    $id = $particle->insetCryosparcJob($expId, $projectId, $jobId);
    display($id);
}

function display($id) {
    $manager = new MongoDB\Driver\Manager("mongodb://".CRYOSPARC.":".CRYOSPARC_PORT);
    $particle = new particledata();
    $job = $particle->getCryosparcJobs($_GET['expId'], $id);
    $query = new MongoDB\Driver\Query(array('project_uid' => $job[0][projectId], 'job_uid' => $job[0][jobId]));
    $cursor = $manager->executeQuery('meteor.events', $query);
    $results = $cursor->toArray();
    $out_text = '';
    $fcs = '';
    foreach ($results as $result){
        if (strpos($result->text, "FSC Iteration") !== false){
            $fcs = $result;
        }
        $out_text .= $result->text.'<br>';
    }
    echo "<table border=1 CLASS=tableborder CELLPADDING=15>
        <tr><td>";

    echo '
    <!-- NGL -->
    <script src="../ngl/js/ngl.js"></script>

    <!-- UI -->
    <script src="../ngl/js/lib/signals.min.js"></script>
    <script src="../ngl/js/lib/tether.min.js"></script>
    <script src="../ngl/js/lib/colorpicker.min.js"></script>
    <script src="../ngl/js/ui/ui.js"></script>
    <script src="../ngl/js/ui/ui.extra.js"></script>
    <script src="../ngl/js/ui/ui.ngl.js"></script>
    <script src="../ngl/js/gui.js"></script>

    <!-- EXTRA -->
    <script src="../ngl/js/plugins.js"></script>

    <script>
        NGL.cssDirectory = "../ngl/css/";
        var stage;
        document.addEventListener( "DOMContentLoaded", function(){
            stage = new NGL.Stage("viewport");
                
            var oReq = new XMLHttpRequest();    
            
            oReq.open("GET", "../proxy.php?csurl=http://'.CRYOSPARC.':39000/download_result_file/'.$job[0][projectId].'/'.$job[0][jobId].'.volume.map", true);
            oReq.responseType = "arraybuffer";            
            oReq.onload = function(oEvent) {
              var blob = new Blob([oReq.response],  { type: "application/octet-binary"} );
              var filename = "'.$job[0][jobId].'";
              stage.loadFile(blob, {ext: "mrc", name: filename}).then(function (component) {
            	  component.addRepresentation("surface");
            	  component.autoView();
            	});
              
            };
            oReq.send();            
            } );            

    </script>
    <div id="viewport" style="width:500px; height:300px;"></div>';
    echo "<p style='text-align:center'><a href='http://".CRYOSPARC.":39000/download_result_file/".$job[0][projectId]."/".$job[0][jobId].".volume.map'>Download Map</a></p>";
    echo "</td><td><img src='http://".CRYOSPARC.":39000/file/".$fcs->imgfiles[0]->fileid."'>";
    echo "</td></tr></table>";
    echo "<h1>CryoSPARC Output</h1>"; 
        echo $out_text;
}

function delete($id) {
    $particle = new particledata();
    $particle->deleteCryosparcJob($_GET['expId'], $id);
    createForm();
}

processing_footer();
?>