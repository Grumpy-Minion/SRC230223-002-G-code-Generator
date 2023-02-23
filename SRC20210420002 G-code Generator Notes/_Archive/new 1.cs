
// C# program to illustrate the String array 
// declaration, initialization and accessing 
// its elements

using System;
	
	class String
	{
		// Main Method
		static void Main()
		{
			
		// Step 1: Array Declaration
        string[] stringarr; 
          
        // Step 2:Array Initialization
        stringarr = new string[3] {"Element 1", "Element 2", "Element 3"}; 
          
        // Step 3:Accessing Array Elements
        Console.WriteLine(stringarr[0]); 
        Console.WriteLine(stringarr[1]); 
        Console.WriteLine(stringarr[2]);
		Console.WriteLine();	// Prints a new line.
			 
		// array initialization and declaration
        string[] stringarr02 = new string[] {"Uno", "Dos", "Tres"}; 
  
        // accessing array elements using a while loop.
		int i=0;
		while (i<=2)
		{
			Console.WriteLine(stringarr02[i]);
			i=i+1;
		}
		Console.WriteLine();	// Prints a new line.
		
		//.GetType() returns the variable type
		Console.WriteLine(stringarr02.GetType());
		Console.WriteLine();	// Prints a new line.
		
		//writes text directly.
		Console.WriteLine("Write text directly"); 
		}
		
	}