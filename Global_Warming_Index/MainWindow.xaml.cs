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
                double co2 = GetLatest("co2_ppm");
                double temp = GetLatest("temperature");
                double trees = GetLatest("trees");
                double waste = GetLatest("waste");
                double investment = GetLatest("money_total");   // one number in $ billions
                double evsales = GetEVSales();
              
                current.Text = $"CO2: {co2} ppm   Temp anomaly: +{temp} °C   " +
                               $"Trees planted: {trees:N0}   Waste collected: {waste:N0} lbs   " +
                               $"Renewable investment: ${investment:N1}B (2019)"+$" EV`s Sold: {evsales:N1} (as of 2019)";

                // 2. Every year -> line chart
                var co2History = GetHistory("co2_ppm");

                // A chart needs two arrays: x values (years) and y values (ppm)
                double[] years = co2History.Select(pt => (double)pt.Year).ToArray();
                double[] values = co2History.Select(pt => pt.Value).ToArray();

                co2Chart.Plot.Add.Scatter(years, values);   // the CO2 curve
                co2Chart.Plot.Add.HorizontalLine(350);      // the 350 ppm "safe level" line
                co2Chart.Plot.Title("Atmospheric CO2 (Mauna Loa)");
                co2Chart.Plot.XLabel("Year");
                co2Chart.Plot.YLabel("ppm");
                co2Chart.Refresh();                          // required: redraws with the new data

                // 3. Top emitting countries -> bar chart
                DrawTopCountries("total", 15);               // or "per_capita"
                DrawHorizontalBars(investChart, GetInvestmentByTech(),
                   "Renewable investment by technology (2019)", "$ billions");
                DrawEVAdoptionPie();

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
        // Works for "co2_ppm", "temperature", "trees", "waste" and "money_total"
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

        // "python backend.py top total 15" prints one "Country|value" line per country, largest first
        private List<(string Country, double Value)> GetTopCountries(string metric, int count = 20)
        {
            string output = RunPython($"top {metric} {count}");
            var points = new List<(string Country, double Value)>();

            foreach (string line in output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
            {
                string[] parts = line.Trim().Split('|');   // "China|11903.0" -> ["China", "11903.0"]
                points.Add((parts[0], double.Parse(parts[1], CultureInfo.InvariantCulture)));
            }
            return points;
        }

        // Draws the top countries as horizontal bars in topChart
        private void DrawTopCountries(string metric, int count = 20)
        {
            var points = GetTopCountries(metric, count);
            int n = points.Count;

            double[] values = points.Select(p => p.Value).ToArray();
            string[] names = points.Select(p => p.Country).ToArray();
            double[] positions = Enumerable.Range(0, n).Select(i => (double)(n - 1 - i)).ToArray();  // largest at top

            var plot = topChart.Plot;
            plot.Clear();
            var bars = plot.Add.Bars(positions, values);
            bars.Horizontal = true;
            plot.Axes.Left.SetTicks(positions, names);    // country names down the side
            plot.Axes.Margins(left: 0);                   // bars start at the axis
            bool total = metric == "total";
            plot.Title(total ? "Top CO2 emitters" : "Top CO2 emitters per person");
            plot.XLabel(total ? "Million tonnes CO2 per year" : "Tonnes CO2 per person");
            topChart.Refresh();
        }
        private List<(string Label, double Value)> GetInvestmentByTech()
        {
            string output = RunPython("money_bars");
            var points = new List<(string Label, double Value)>();
            foreach (string line in output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
            {
                string[] parts = line.Trim().Split('|');   // "Wind Energy|142.7" -> ["Wind Energy", "142.7"]
                points.Add((parts[0], double.Parse(parts[1], CultureInfo.InvariantCulture)));
            }
            return points;

        }
        private double GetEVSales() 
        {
            string output = RunPython("evsales");
            var points = new List<(string Label, double Value)>();
            double sales = 0;
            foreach (string line in output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
            {
                string[] parts = line.Trim().Split('|');   
                points.Add((parts[0], double.Parse(parts[1], CultureInfo.InvariantCulture)));
            }
            for (int i = 0; i < points.Count; i++)
            {
                sales = points[i].Value + sales;
            }
            return sales;

        }
        // Draws any list of (label, value) as horizontal bars, first item at the top
        private void DrawHorizontalBars(ScottPlot.WPF.WpfPlot chart,
                                        List<(string Label, double Value)> points,
                                        string title, string xLabel)
        {
            int n = points.Count;
            double[] values = points.Select(p => p.Value).ToArray();
            string[] labels = points.Select(p => p.Label).ToArray();
            double[] positions = Enumerable.Range(0, n).Select(i => (double)(n - 1 - i)).ToArray();

            var plot = chart.Plot;
            plot.Clear();
            var bars = plot.Add.Bars(positions, values);
            bars.Horizontal = true;
            plot.Axes.Left.SetTicks(positions, labels);
            plot.Axes.Margins(left: 0);
            plot.Title(title);
            plot.XLabel(xLabel);
            chart.Refresh();
        }
        // Runs any command that prints "label|value" lines and returns them as a list
        private List<(string Label, double Value)> GetLabeledValues(string command)
        {
            string output = RunPython(command);
            var points = new List<(string Label, double Value)>();
            foreach (string line in output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
            {
                string[] parts = line.Trim().Split('|');
                points.Add((parts[0], double.Parse(parts[1], CultureInfo.InvariantCulture)));
            }
            return points;
        }
        private void DrawEVAdoptionPie()
        {
            var points = GetLabeledValues("evadoption");   // "Electric (2025)|25.0", "Not electric|75.0"

            var colors = new[] { ScottPlot.Colors.Green, ScottPlot.Colors.Gray };
            var slices = new List<ScottPlot.PieSlice>();
            for (int i = 0; i < points.Count; i++)
            {
                slices.Add(new ScottPlot.PieSlice
                {
                    Value = points[i].Value,
                    Label = $"{points[i].Label}\n{points[i].Value:0}%",   // "Electric (2025)\n25%"
                    FillColor = colors[i],
                });
            }

            var plot = pieChart.Plot;
            plot.Clear();
            var pie = plot.Add.Pie(slices);
            pie.SliceLabelDistance = 0.6;
            plot.Axes.Frameless();
            plot.HideGrid();
            plot.Title("Share of new cars sold that are electric (World)");
            pieChart.Refresh();
        }
    }
}