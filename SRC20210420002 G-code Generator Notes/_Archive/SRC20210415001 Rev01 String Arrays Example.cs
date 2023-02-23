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
        stringarr = new string[3] {"Uno", "Dos", "Tres"}; 
          
        // Step 3:Accessing Array Elements
        Console.WriteLine(stringarr[0]); 
        Console.WriteLine(stringarr[1]); 
        Console.WriteLine(stringarr[2]);
		
		// Prints a new line.
		Console.WriteLine();
		
		// array initialization and declaration
        string[] stringarr02 = new string[] {"Quatro", "Cinco", "Seis"}; 
  
        // accessing array elements using a while loop.
		int i=0;
		while (i<=2)
		{
			Console.WriteLine(stringarr02[i]);
			i=i+1;
		}
		
		// Prints a new line.
		Console.WriteLine();
		
		//.GetType() returns the variable type
		Console.WriteLine(stringarr02.GetType());

		// Prints a new line.
		Console.WriteLine();
		
		//writes text directly.
		Console.WriteLine("Write text directly"); 
		}
		
	}