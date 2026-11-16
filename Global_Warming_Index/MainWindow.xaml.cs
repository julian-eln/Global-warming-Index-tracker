using System;
using System.Collections.Generic;
using System.Diagnostics;          // lets C# run Python
using System.Globalization;        // for parsing "424.61" correctly
using System.Linq;                 // for .Select(...), .Sum(...), .Last()
using System.Threading.Tasks;      // for Task.Run and async/await
using System.Windows;
using System.Windows.Threading;    // for DispatcherTimer

namespace Global_Warming_Index
{
    public partial class MainWindow : Window
    {
        // How often the numbers in the text line are reloaded from Python
        private static readonly TimeSpan RefreshInterval = TimeSpan.FromMinutes(10);

        private bool refreshing = false;    // stops two refreshes running at the same time

        public MainWindow()
        {
            InitializeComponent();   // builds the controls from the XAML; must come first

            // Charts: loaded once, right here, the same way as before
            try
            {
                DrawCo2Chart(GetHistory("co2_ppm"));
                DrawHorizontalBars(topChart, GetLabeledValues("top total 15"), "Top CO2 emitters", "Million tonnes CO2 per year");
                DrawHorizontalBars(investChart, GetLabeledValues("money_bars"), "Renewable investment by technology (2019)", "$ billions");
                DrawEVAdoptionPie(GetLabeledValues("evadoption"));
            }
            catch (Exception ex)
            {
                ShowError(ex);
            }

            // Timer: reload just the numbers every RefreshInterval
            var refreshTimer = new DispatcherTimer { Interval = RefreshInterval };
            refreshTimer.Tick += async (s, e) => await RefreshNumbersAsync();
            refreshTimer.Start();

            // Numbers: first load as soon as the window is on screen, then every RefreshInterval
            Loaded += async (s, e) => await RefreshNumbersAsync();
        }

        // Re-runs only the commands behind the numbers in the text line (the doubles)
        private async Task RefreshNumbersAsync()
        {
            if (refreshing) return;   // the previous refresh is still running; skip this one
            refreshing = true;

            try
            {
                // 1. BACKGROUND: run Python. Task.Run moves this work off the UI thread,
                //    so the window doesn't freeze while Python is working.
                var d = await Task.Run(() => new
                {
                    co2 = GetLatest("co2_ppm"),
                    temp = GetLatest("temperature"),
                    trees = GetLatest("trees"),
                    waste = GetLatest("waste"),
                    investment = GetLatest("money_total"),   // $ billions, 2019
                    raised = GetLatest("Stock"),         // $ billions, last 12 months
                    capex = GetLatest("capex"),         // $ billions, last 12 months
                    ev = GetLabeledValues("evsales"),
                });

                // 2. UI THREAD: "await" brings us back here, where it's safe to change the screen
                double evsales = d.ev.Sum(p => p.Value);                  // total since 2010

                current.FontSize = 20;
                double investment = d.investment + d.capex;               // 2019 total + company capex (last 12 mo)
                current.Text = $"CO2: {d.co2} ppm  Temp anomaly: +{d.temp} °C " +
                               $"Trees planted:{d.trees:N0} Waste collected: {d.waste:N0}kg" + 
                               $"\nRenewable investment: ${investment:N1} (2019(public institution grants) Capex(This Year)" +  $" \n EV`s Sold: {evsales:N1} (as of 2019)" + $" Clean-energy companies, last 12 mo: raised :${d.raised:N1}";
            }
            catch (Exception ex)
            {
                ShowError(ex);
            }
            finally
            {
                refreshing = false;   // always runs, even after an error, so the next refresh can happen
            }
        }

        // Any Python or parsing error shows in the text line instead of crashing the window
        private void ShowError(Exception ex)
        {
            current.FontSize = 12;
            current.Text = ex.Message;
            Debug.WriteLine(ex);
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
                    throw new Exception($"Python failed ({arguments}):\n" + errors);
                return output;
            }
        }

        // For commands that print one number, e.g. "424.61"
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

        // For commands that print "label|value" lines (top, money_bars, evsales, evadoption)
        private List<(string Label, double Value)> GetLabeledValues(string command)
        {
            string output = RunPython(command);
            var points = new List<(string Label, double Value)>();
            foreach (string line in output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
            {
                string[] parts = line.Trim().Split('|');   // "China|11903.0" -> ["China", "11903.0"]
                points.Add((parts[0], double.Parse(parts[1], CultureInfo.InvariantCulture)));
            }
            return points;
        }

        // CO2 line chart with the 350 ppm "safe level" line
        private void DrawCo2Chart(List<(int Year, double Value)> history)
        {
            double[] years = history.Select(pt => (double)pt.Year).ToArray();
            double[] values = history.Select(pt => pt.Value).ToArray();

            var plot = co2Chart.Plot;
            plot.Clear();                         // needed now: without it, every refresh adds another line
            plot.Add.Scatter(years, values);
            plot.Add.HorizontalLine(350);
            plot.Title("Atmospheric CO2 (Mauna Loa)");
            plot.XLabel("Year");
            plot.YLabel("ppm");
            plot.Axes.AutoScale();                // fit the axes to the data (see note in DrawHorizontalBars)
            co2Chart.Refresh();
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
            // Fit the axes to the data. Needed when a chart is drawn AFTER it has already appeared on screen:
            // ScottPlot fixes the axis range at the first render, so without this the data can be off-screen.
            plot.Axes.AutoScale();
            chart.Refresh();
        }

        // Pie of "Electric (2025)" vs "Not electric"
        private void DrawEVAdoptionPie(List<(string Label, double Value)> points)
        {
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
            plot.Axes.AutoScale();
            pieChart.Refresh();
        }
    }
}