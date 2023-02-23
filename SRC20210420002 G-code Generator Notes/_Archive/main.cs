using System;

class Program
{
    static void Main()
    {

        string[] lines =
      {
        "akwlnaoiwv"
    };

        // WriteAllLines creates a file, writes a collection of strings to the file,
        // and then closes the file.  You do NOT need to call Flush() or Close().
        System.IO.File.WriteAllLines(@"C:\Sandbox\01.txt", lines);


        //===Input Variables===
        double Start_depth = 0.000;
        double Depth_of_cut = -0.400;
        double Safe_Z = 1.000;
        double Width_of_Slot = 1.500;
        double start_X = 0;
        double start_Y = 0;
        double end_X = 10;
        double end_Y = 10;
        double Cut_Feed = 162.1;
        double Plunge_Feed = 22.4;
        double Diameter_of_cutter = 0.750;
        double Stepover_width = 0.1;

        //(---Sub-Intialize Variables: Start---)
        double X_Vector = end_X - start_X;   //#302 = #106-#104				(X Vector Length of Slot)
        double Y_Vector = end_Y - start_Y;   //#303 = #107-#105				(Y Vector Length of Slot)
        double Length_of_Slot = Math.Sqrt(Math.Pow(X_Vector, 2) + Math.Pow(Y_Vector, 2));    //#301 = SQRT[#302^2+#303^2]		(Length of Slot)
        double Number_of_Cuts_Raw = Length_of_Slot / Stepover_width;    //#304 = #301/#204				(number of cuts-raw)
        double Number_of_Cuts = Math.Floor(Number_of_Cuts_Raw);  //#305 = [#301-#307]/#204		(number of cuts rounded down)
        double Remainder = Number_of_Cuts_Raw - Number_of_Cuts;    //#307 = #301%#204				(calculate remainder)
                                                                   //#308 = 0						(Clear Leftover Cycle Flag)
                                                                   //#308 = #307/#307				(set Left over cycle flag 0=no 1=yes)
        double Diameter_of_Cut_Arc = Width_of_Slot - Diameter_of_cutter;  //#311 = #108-#203				(Diameter of Cut Arc)
        double Radius_of_Cut_Arc = Diameter_of_Cut_Arc / 2;   //#312 = #311/2					(Radius of Cut Arc)
                                                              //#313 = 1						(Set First Cut Flag)

        //Calculate Vectors and Angles
        double angle = Math.Asin(Y_Vector / Length_of_Slot) * 360 / (2 * Math.PI);

        //Calculate Absolute Angles
        double abs_angle = 0;

        if (X_Vector < 0)
        {
            abs_angle = 180 - angle;
            if (Y_Vector < 0)
            {
                abs_angle = 180 - angle;
            }
        }
        if (X_Vector >= 0)
        {
            abs_angle = angle;
            if (Y_Vector < 0)
            {
                abs_angle = 360 + angle;
            }
        }
//write to console		
Console.WriteLine("test2");

        // Example #1: Write an array of strings to a file.
        // Create a string array that consists of three lines.
        

        // WriteAllLines creates a file, writes a collection of strings to the file,
        // and then closes the file.  You do NOT need to call Flush() or Close().
		
 string lines3 = "akwlnaoiwv";
 lines3 = "akwlnaoisfsfsdwv";
		
        System.IO.File.WriteAllLines(@"C:\Sandbox\01.txt", lines);

        // Example #4: Append new text to an existing file.
        // The using statement automatically flushes AND CLOSES the stream and calls
        // IDisposable.Dispose on the stream object.
        using (System.IO.StreamWriter file = new System.IO.StreamWriter(@"C:\Sandbox\01.txt", true))
        {
            file.WriteLine("\r\n" + "=================" + "\r\n");
        }
        // Example #4: Append new text to an existing file.
        // The using statement automatically flushes AND CLOSES the stream and calls
        // IDisposable.Dispose on the stream object.
        using (System.IO.StreamWriter file = new System.IO.StreamWriter(@"C:\Sandbox\01.txt", true))
        {
            file.WriteLine(Length_of_Slot);
            file.WriteLine(Number_of_Cuts_Raw);
            file.WriteLine(Number_of_Cuts);
            file.WriteLine(Remainder);
            file.WriteLine(Diameter_of_Cut_Arc);
            file.WriteLine("X_Vector = " + X_Vector + "\r\n" + "Y_Vector = " + Y_Vector + "\r\n" + "Length_of_Slot = " + Length_of_Slot);
            file.WriteLine("angle = " + angle + "\r\n" + "abs_angle = " + abs_angle);
        }
    }
}

//===============================