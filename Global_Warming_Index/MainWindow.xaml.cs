using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System;
using System.Diagnostics;      // lets C# run Python
using System.Globalization;    // for parsing "424.61" correctly


namespace Global_Warming_Index
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            try
            {
                double co2 = GetLatestCo2();          // runs backend.py and reads the number it prints
                current.Text = "CO2: "+ co2;
                Debug.WriteLine("Todays Current stats CO2: " + co2);
            }
            catch (Exception ex)
            {
                // Without this catch, any error here crashes the window with a XamlParseException
                current.Text = ex.Message;
                Debug.WriteLine(ex);
            }

        }
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
        private double GetLatestCo2()
        {

            var psi = new ProcessStartInfo("python", "backend.py")
            {
                WorkingDirectory = FindRepoRoot(),  // folder with backend.py
                RedirectStandardOutput = true,   // capture what Python prints
                RedirectStandardError = true,    // capture Python's error messages too
                UseShellExecute = false,         // required for capturing output
                CreateNoWindow = true            // no console window flash
            };

            var p = Process.Start(psi);
            string output = p.StandardOutput.ReadToEnd();   // e.g. "424.61"
            string errors = p.StandardError.ReadToEnd();    // Python's traceback, if it crashed
            p.WaitForExit();

            if (p.ExitCode != 0)
                throw new Exception("Python failed:\n" + errors);

            return double.Parse(output.Trim(), CultureInfo.InvariantCulture);
        }
    }
}
