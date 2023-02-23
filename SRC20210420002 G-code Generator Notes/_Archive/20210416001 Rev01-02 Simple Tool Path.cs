using System;

class Program
{
    static void Main()
    {
//---------------------------------------Variable Block--------------------------------------------------
        double Start_depth = 0.000;
        double Depth_of_cut = -0.400;
        double Safe_Z = 1.000;
        double Width_of_Slot = 1.500;
        double start_X = 000;
        double start_Y = 000;
        double end_X = 10;
        double end_Y = 10;
        double Cut_Feed = 162.1;
        double Plunge_Feed = 22.4;
        double Diameter_of_cutter = 0.750;
        double Stepover_width = 0.1;
		double Spindle_Speed = 2900;
		
		string file = @"C:\Sandbox\"+DateTime.Now.ToString("yyyyMMdd-HHmmss")+".txt";
		
		string[] varblock =
		{
			"",
			"(===Input Variables===)",
			"(Start_depth = "+Start_depth.ToString("F3")+")",
			"(Depth_of_cut = "+Depth_of_cut.ToString("F3")+")",
			"(Safe_Z = "+Safe_Z.ToString("F3")+")",
			"(Width_of_Slot = "+Width_of_Slot.ToString("F3")+")",
			"(start_X = "+start_X.ToString("F3")+")",
			"(start_Y = "+start_Y.ToString("F3")+")",
			"(end_X = "+end_X.ToString("F3")+")",
			"(end_Y = "+end_Y.ToString("F3")+")",
			"(Cut_Feed = "+Cut_Feed.ToString("F0")+")",
			"(Plunge_Feed = "+Plunge_Feed.ToString("F0")+")",
			"(Diameter_of_cutter = "+Diameter_of_cutter.ToString("F1")+")",
			"(Stepover_width = "+Stepover_width.ToString("F3")+")",
			"(Spindle_Speed = "+Spindle_Speed.ToString("F0")+")",
			"",
		};
		System.IO.File.WriteAllLines(file,varblock);
		//------------------------------------------------------------------------------------------------------
		
		//---------------------------------------Starting Block--------------------------------------------------
		string[] startblock =
		{
		"(===Main Start===)",
		"G90			(Absolute XYZ)",
		"G21G64G17		(mm, Best Speed Path, XY Plane)",
		"M3 S"+Spindle_Speed.ToString("F0")+"		(Spindle Speed)",
		"G0 Z"+Safe_Z.ToString("F3")+"		(Go to safe height)",
		"G0 X"+start_X.ToString("F3")+" Y"+start_Y.ToString("F3")+"	(Rapid to start point)"
		};
		System.IO.File.AppendAllLines(file,startblock);
		//------------------------------------------------------------------------------------------------------
		
		string[] toolpath =
		{
		"",
		"F " + Plunge_Feed + "		(Plunge Feed)",
		"G1 Z " + Depth_of_cut + "		(Plunge to depth)",
		"F " + Cut_Feed + "		(Cut Feed)",
		"G1 X 10.000	(To go X10)",
		"G1 Y 10.000	(To go Y10)",
		"G0 Z " + Safe_Z + "		(Safe_Z)",
		};
		System.IO.File.AppendAllLines(file,toolpath);
		
		//---------------------------------------Ending Block--------------------------------------------------
		string[] endblock =
		{
		"",
		"G0 Z " + Safe_Z + "		(Safe_Z)",
		"M5		(Spindle Stop)",
		"M30		(End & Rewind)",
		"(===Main End===)"
		};
		System.IO.File.AppendAllLines(file,endblock);
		//------------------------------------------------------------------------------------------------------
    }
}