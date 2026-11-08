using System;
using System.Collections.Generic;
using System.Diagnostics;      // lets C# run Python
using System.Globalization;    // for parsing "424.61" correctly
using System.Linq;             // for .Select(...) and .ToArray()
using System.Windows;

namespace Global_Warming_Index
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();   // builds the controls from the XAML; must come first

            try
            {
                // 1. Latest values -> text at the top (each call runs backend.py once)
                double co2   = GetLatest("co2_ppm");
                double temp  = GetLatest("temperature");
                double trees = GetLatest("trees");
                double waste = GetLatest("waste");
                current.Text = $"CO2: {co2} ppm   Temp anomaly: +{temp} °C   " +
                               $"Trees planted: {trees:N0}   Waste collected: {waste:N0} lbs";

                // 2. Every year -> chart
                var co2History = GetHistory("co2_ppm");

                // A chart needs two arrays: x values (years) and y values (ppm)
                double[] years  = co2History.Select(pt => (double)pt.Year).ToArray();
                double[] values = co2History.Select(pt => pt.Value).ToArray();

                co2Chart.Plot.Add.Scatter(years, values);   // the CO2 curve
                co2Chart.Plot.Add.HorizontalLine(350);      // the 350 ppm "safe level" line
                co2Chart.Plot.Title("Atmospheric CO2 (Mauna Loa)");
                co2Chart.Plot.XLabel("Year");
                co2Chart.Plot.YLabel("ppm");
                co2Chart.Refresh();                          // required: redraws with the new data
            }
            catch (Exception ex)
            {
                // Without this catch, any error here crashes the window with a XamlParseException
                current.FontSize = 12;
                current.Text = ex.Message;
                Debug.WriteLine(ex);
            }
        }

        // Finds the repo folder on any PC by walking up from bin\Debug until backend.py appears
        private static string FindRepoRoot()
        {
            var dir = new System.IO.DirectoryInfo(AppDomain.CurrentDomain.BaseDirectory);
            while (dir != null)
            {
                if (System.IO.File.Exists(System.IO.Path.Combine(dir.FullName, "backend.py")))
                    return dir.FullName;
                dir = dir.Parent;   // go up one level
            }
            throw new Exception("Couldn't find backend.py in any folder above " + AppDomain.CurrentDomain.BaseDirectory);
        }

        // Runs "python backend.py <arguments>" and returns everything it printed
        private static string RunPython(string arguments)
        {
            var psi = new ProcessStartInfo("python", "backend.py " + arguments)   // note the space after .py
            {
                WorkingDirectory = FindRepoRoot(),
                RedirectStandardOutput = true,   // capture what Python prints
                RedirectStandardError = true,    // capture Python's error messages too
                UseShellExecute = false,         // required for capturing output
                CreateNoWindow = true            // no console window flash
            };

            using (var p = Process.Start(psi))
            {
                string output = p.StandardOutput.ReadToEnd();
                string errors = p.StandardError.ReadToEnd();
                p.WaitForExit();

                if (p.ExitCode != 0)
                    throw new Exception("Python failed:\n" + errors);
                return output;
            }
        }

        // "python backend.py co2_ppm" prints one number, e.g. "424.61"
        // Works for "co2_ppm", "temperature", "trees" and "waste"
        private double GetLatest(string source)
        {
            return double.Parse(RunPython(source).Trim(), CultureInfo.InvariantCulture);
        }

        // "python backend.py history co2_ppm" prints one "year,value" line per year
        private List<(int Year, double Value)> GetHistory(string source)
        {
            string output = RunPython("history " + source);

            var points = new List<(int Year, double Value)>();
            foreach (string line in output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
            {
                string[] parts = line.Split(',');     // "1959,315.98" -> ["1959", "315.98"]
                points.Add((int.Parse(parts[0]), double.Parse(parts[1], CultureInfo.InvariantCulture)));
            }
            return points;
        }
    }
}
