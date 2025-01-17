<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";
$defaultId= 1445;
$sessionId= ($_GET['Id']) ? $_GET['Id'] : $defaultId;
$maxrate = (is_numeric($_POST['maxr'])) ? $_POST['maxr'] 
		: (is_numeric($_GET['maxr']) ? $_GET['maxr'] : false);
#$slow=($_POST['slow']) ? int ($_POST['slow']) : 0;
#$sloo=($_GET['slow']);
#$slow = (is_numeric($_POST['slow'])) ? $_POST['slow'] 
#		: (is_numeric($_GET['slow']) ? $_GET['slow'] : 0);

$data = array();
if ($driftdata = $leginondata->getDriftDataFromSessionId($sessionId)) {
foreach ($driftdata[0] as $drift) {
	$id = (int) $drift[0]['imageId'];
	$data[$id] = $drift;
}
}
// --- Set  experimentId
// $lastId = $leginondata->getLastSessionId();
// $sessionId = (empty($_GET[Id])) ? $lastId : $_GET[sessionId];
$sessioninfo = $leginondata->getSessionInfo($sessionId);
$title = $sessioninfo['Name'];

function getFrameDriftGraphs($expId) {
	global $leginondata;
	$align_source_presets = $leginondata->getFrameSavedPresets($expId);
	if (!empty($align_source_presets)) {
		foreach($align_source_presets as $preset) {
			if ( strstr($preset['name'],'-') != false ) continue;
			$html .= "<tr><td colspan='3'>";
			$html .= divtitle("Frame Movement of Movies Acquire by ".$preset['name']." Preset ");
			$html .= "</td></tr>";
			$html .= "<tr>";
			$graph_prefix = 'dddriftstatsgraph.php?expId='.$expId.'&preset='.$preset['name'];
			$html .= "<td>";
			$html .= "<a href='".$graph_prefix."&vdata=1'>[data]</a>";
			$html .= "</td>\n";
			$html .= "</tr>\n";
			$html .= "<tr>";
			$html .= "<td>";
			$html .= "<a href='".$graph_prefix."'>";
			$html .= "<img border='0' src='".$graph_prefix."'";
			$html .= "</a>\n";
			$html .= "</td>\n";
			$html .= "</tr>\n";
			#$html .= "<tr>";
			#$html .= "<td>";
			#$html .= "<a href='".$graph_prefix."&hg=1'>";
			#$html .= "<img border='0' src='".$graph_prefix."&hg=1&w=512'>";
			#$html .= "</a>\n";
			#$html .= "</td>\n";
			#$html .= "</tr>\n";
		}
	} else $html .= "no Frame Movement information available";
		$html .= "</td>";
	return $html;
}

?>
<html>
<head>
<title><?php echo $title; ?> drift report</title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>

<body>
<table border=0 cellpadding=10>
<tr>
 <td>
  <a class="header" HREF="index.php">&lt;index&gt;</a>
 </td>
 <td>
  <a class="header" HREF="3wviewer.php?sessionId=<?php echo $sessionId; ?>">&lt;view <?php echo $title; ?>&gt;</a>
 </td>
</tr>
</table>
<table border="0" cellpadding=10>
<tr valign="top">
	<td colspan="2">
	<?php echo divtitle("Drift Report $title Experiment"); ?>
	</td>
</tr>
<?php
echo getFrameDriftGraphs($sessionId);
?>
<?php
echo "<tr>";
echo "<td colspan='2'>";
echo divtitle("Avg. drift rate at end of measurement cycle");
echo "<br>";
?>
<form method="POST" action="<?php echo $_SERVER['REQUEST_URI']; ?>">
	max rate:<input class="field" name="maxr" type="text" size="5" value="<?php echo $maxrate; ?>">
</form>
<?php
$urlrate = ($maxrate) ? "&maxr=$maxrate" : "";
echo "<a href='avgdriftgraph.php?vd=1&Id=$sessionId'>[data]</a>";
echo "<a href='avgdriftgraph.php?vs=1&Id=$sessionId'>[sql]</a><br>";
echo "<img src='avgdriftgraph.php?Id=$sessionId$urlrate'>";
echo "<br>";
echo "<br>";
echo "<img src='avgdriftgraph.php?hg=1&Id=$sessionId$urlrate'>";
echo "</td>\n";
?>
</tr>
<tr>
<td>
<?php echo divtitle("Total time spent drifting"); ?>
</td>
</tr>
<tr>
<td>
<a href="drifttimegraph.php?vd=1&Id=<?php echo $sessionId; ?>">[data]</a>
<a href="drifttimegraph.php?vs=1&Id=<?php echo $sessionId; ?>">[sql]</a><br>
<img src="drifttimegraph.php?Id=<?php echo $sessionId; ?>">
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>
