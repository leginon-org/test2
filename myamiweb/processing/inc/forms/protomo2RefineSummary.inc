<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc";
require_once "inc/leginon.inc";

session_start();
$tiltseries=$_SESSION['tiltseries'];
$sessionname=$_SESSION['sessionname'];
$outdir=$_SESSION['outdir'];
$runname=$_SESSION['runname'];
$iters=$_SESSION['iters'];
$imageinfo=$_SESSION['imageinfo'];

class Protomo2RefineSummary extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML )
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		
		// Set the publications to be references on the web pages
		$pubList = array('protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Refinement Summary' );
		$this->setHeading( 'Protomo Refinement Summary' );
		$this->setExeFile( '' );
		$this->setGuideURL( "http://www.electrontomography.org/?page_id=317" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
	}
	
	// Display plots and videos
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		global $outdir;
		global $runname;
		global $tiltseries;
		
		$corrpeak_gif_files = glob("$outdir/$runname/media/correlations/s*.gif");
		$corrpeak_vid_files = glob("$outdir/$runname/media/correlations/s*.{mp4,ogv,webm}",GLOB_BRACE);
		$qa_gif_file = "$outdir/$runname/media/quality_assessment/series".sprintf('%04d',$tiltseries)."_quality_assessment.gif";
		$azimuth_gif_file = "$outdir/$runname/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_azimuth.gif";
		$theta_gif_file = "$outdir/$runname/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_theta.gif";
		
		$qa_gif = "loadimg.php?rawgif=1&filename=".$qa_gif_file;
		$azimuth_gif = "loadimg.php?rawgif=1&filename=".$azimuth_gif_file;
		$theta_gif = "loadimg.php?rawgif=1&filename=".$theta_gif_file;
		
		//foreach(array_keys($initial_tilt_vid_files) as $paramName)
		//	echo $paramName . "<br>";
		//	echo $initial_tilt_vid_files["$paramName"] . "<br>";
		
		// Quality assessment for each iteration
		$html .= "
	<hr />
	<center><H4><b>Quality Assessment ".docpop('quality_assessment', '(Info)')."</b></H4></center>
	<hr />";
		$html .= '<table id="" class="display" cellspacing="0" border="0" width="100%">';
		$html .= '<tr><td rowspan="2">';
		$html .= '<center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$qa_gif.'" alt="qa" width="666" />'."</a></center>";
		$html .= '<center>'.docpop('quality_assessment2', 'CCMS Info').'</center><br></td>';
		$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$azimuth_gif.'" alt="azimuth" width="400" />'."</a></center></td></tr>";
		$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$theta_gif.'" alt="theta" width="400" />'."</a></center></td></tr>";
		$html .= '</tr></td></table>';
		
		// Table of all of the correlation peaks for easy identification of bad alignment iterations
		$html .= "
	<hr />
	<center><H4><b>Correlation Peaks for Each Iteration ".docpop('corrimageinfo_refine', '(Info)')."</b></H4></center>
	<hr />";
		
		$i = 0;
		$j = -1;
		$numcolumns=5;
		$html .= '<table id="" class="display" cellspacing="0" border="1" align="center">';
		$html .= "<tr>";
		if (count($corrpeak_gif_files) > 0)
		{
			do {
				foreach ($corrpeak_gif_files as $corr)
				{
					$ite=$i+1;
					if ($ite <= count($corrpeak_gif_files) AND $ite > 0) {
						$html .= '<th><a href="protomo2RefineIterationSummary.php?iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank">Iteration #'.$ite.'</a></th>';
					}
					if ($ite % $numcolumns == 0 OR $ite < 1) {
						$html .= "</tr><tr>";
						$j++;
						break;
					}
					$i++;
				}
				$i = 0 + $numcolumns*$j;
				foreach ($corrpeak_gif_files as $corr)
				{
					$ite=$i+1;
					if ($ite <= count($corrpeak_gif_files) AND $ite > 0) {
						$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_gif_files[$i];
						$html .= '<td><center><a href="protomo2RefineIterationSummary.php?iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$corrpeak_gif.'"/></a></center></td>';
					}
					if ($ite % $numcolumns == 0 OR $ite < 1) {
						$html .= "</tr><tr>";
						$i++;
						break;
					}
					$i++;
				}
			} while ($i < count($corrpeak_gif_files));
		}
		elseif (count($corrpeak_vid_files) > 0)
		{
			do {
				foreach ($corrpeak_vid_files as $corr)
				{
					$ite=$i+1;
					if ($ite <= count($corrpeak_vid_files)/3 AND $ite > 0) {
						$html .= '<th><a href="protomo2RefineIterationSummary.php?iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank">Iteration #'.$ite.'</a></th>';
					}
					if ($ite % $numcolumns == 0 OR $ite < 1) {
						$html .= "</tr><tr>";
						$j++;
						break;
					}
					$i++;
				}
				$i = 0 + $numcolumns*$j;
				foreach ($corrpeak_vid_files as $corr)
				{
					$ite=$i+1;
					if ($ite <= count($corrpeak_vid_files)/3 AND $ite > 0) {
						$corrpeak_vid_mp4 = "loadvid.php?filename=".$corrpeak_vid_files[$i];
						$html .= '<td><center><a href="protomo2RefineIterationSummary.php?iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank">
							 <video id="corrpeakVideos" autoplay loop>
							 <source src="'.$corrpeak_vid_mp4.'" type="video/mp4" loop>
							 </video></a></center></td>';
					}
					if ($ite % $numcolumns == 0 OR $ite < 1) {
						$html .= "</tr><tr>";
						$i++;
						break;
					}
					$i++;
				}
			} while ($i < count($corrpeak_vid_files)/3);
		}
		$html .= '</tr><tr></table><br>';
		
		// Display Refinement Summary for each iteration (disabled because it overloads the browser=[)
		//$html.='<script type="text/javascript">
		//function toggleMe(a){
		//var e=document.getElementById(a);
		//if(!e)return true;
		//if(e.style.display=="none"){
		//e.style.display="block"
		//}
		//else{
		//e.style.display="none"
		//}
		//return true;
		//}
		//</script>
		//
		//<center><input type="button" style="width:150px;height:30px;" onclick="return toggleMe(\'para1\')" value="View All Iterations"></center><br>
		//<div id="para1" style="display:none">';
		//
		//for ($j = 0; $j < max(count($corrpeak_gif_files),count($rec_files)); $j++)
		//{
		//	$ite=$j+1;
		//	$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_gif_files[$j];
		//	$rec_gif = "loadimg.php?rawgif=1&filename=".$rec_files[$j];
		//	
		//	$html .= "
		//<hr />
		//<center><H3><b>Refinement Iteration #$ite</b></H3></center>
		//<hr />";
		//	$html .= "
		//<br />
		//<center><H4>Tilt-Series Correlation Peaks</H4></center>
		//<br />";
		//	if (isset($corrpeak_gif_files[$j])) {
		//		$html .= '<center><img src="'.$corrpeak_gif.'" alt="correlations" />'."<br /><br /><hr /></center>";
		//	} else {
		//		$html .= "<b>Depiction Correlation Peak Gif for Iteration $ite either failed to generate or is still processing</b>";
		//	}
		//	$html .= "
		//<br />
		//<center><H4>Tilt-Series Preliminary Reconstruction After Refinement</H4></center>
		//<br />";
		//	if (isset($rec_files[$j])) {
		//		$html .= '<center><img src="'.$rec_gif.'" alt="reconstruction" /></center>'."<br /><br />";
		//	} else {
		//		$html .= "<center><b>Depiction Reconstruction Gif for Iteration $ite either failed to generate or is still processing</b></center>";
		//	}
		//	if ($i == $j+1)
		//	{
		//		$html .= '</div>';
		//	}
		//}
		
		// Only display link to next step in tomo processing if at least one iteration is complete
		if (max(count($corrpeak_gif_files),count($corrpeak_vid_files)) < 1)
		{
			$html .= "<br></br>
			<b><center>[Refresh this page after at least one Refinement iteration completes]</center><br></b>";
		} else {
			$html .= "<br><hr /><br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2ReconstructionForm'><b><center>[Click here to continue onto <font size='4'>Reconstruction</font> if protomo2aligner.py has finished <br>and you're happy with the alignment of at least one iteration] <font size='5'>→</font></center></b></a>";
			$html .= "<br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center><font size='5'>←</font> [Click here to go back to <font size='4'>Refinement</font>]</center></b></a><br>";
		}
			
		return $html;
	}	
	
	// Override the default ShowReference function because the user needs to be re-directed
	// to the next step of the Protomo workflow.
	public function showReference( $postArray )
	{
		$html = parent::showReference( $postArray );
		
		global $tiltseries;
		global $sessionname;
		global $runname;
		global $outdir;
		global $iters;
		global $imageinfo;

		$_SESSION['tiltseries'] = $tiltseries;
		$_SESSION['runname'] = $runname;
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['outdir'] = $outdir;
		$_SESSION['iters'] = $iters;
		$_SESSION['imageinfo'] = $imageinfo;
		$_SESSION['erase_refine'] = 1;
		$_SESSION['restart_cycle'] = $iters;
		
		$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2ReconstructionForm'><b><center>[Click here to continue onto <font size='4'>Reconstruction</font> if protomo2aligner.py has finished <br>and you're happy with the alignment of at least one iteration] <font size='5'>→</font></center></b></a>";
		$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center><font size='5'>←</font> [Click here to go back to <font size='4'>Refinement</font>]</center></b></a><br>";

		return $html;
	}
}
?>