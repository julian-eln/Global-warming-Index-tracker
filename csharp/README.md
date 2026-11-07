# C# desktop app

Your project lives in `Global_Warming_Index/` (WPF). This file is your pointer list for it.

## First: your project targets .NET Framework 4.7.2 — decide now whether to keep that

You created it with the **"WPF App (.NET Framework)"** template. That's the old, Windows-only framework that's in maintenance mode. The newer **"WPF Application"** template targets modern .NET (8+). It's the same WPF and XAML, but newer C# features and libraries.

| | Keep .NET Framework 4.7.2 | Switch to .NET 8 |
|---|---|---|
| Effort now | None | ~5 min: the project is still nearly empty, so recreate it and paste your `MainWindow` code back in |
| C# version | 7.3 by default (no `record`, no `init`, no nullable reference types) | C# 12 |
| JSON | Add **Newtonsoft.Json** NuGet package | `System.Text.Json` built in |
| Tutorials you'll find | Older | Most current ones |
| IDE | Works in VS 2019 | Needs **VS 2022** (17.8+). Your `.vs/.../v16` folder means it was opened in VS 2019. |

**Recommendation:** switch to .NET 8 now if you can use VS 2022. It only gets more expensive later. If you're stuck on VS 2019, staying on 4.7.2 is fine for a hackathon. The notes below cover both.

## Suggested structure inside `Global_Warming_Index/`

```
Models/       # plain classes mirroring Data/SCHEMA.md
Services/     # DashboardDataService: reads + deserializes the JSON
ViewModels/   # MainViewModel: properties the UI binds to
Views/        # extra windows / user controls (MainWindow can stay at root)
```

Useful NuGet packages (right-click project → Manage NuGet Packages):
- **CommunityToolkit.Mvvm**: `[ObservableProperty]` / `[RelayCommand]`, removes MVVM boilerplate. It supports .NET Framework too, but its source generators need a newer C# version. On 4.7.2, add `<LangVersion>latest</LangVersion>` to the `.csproj`.
- **Charts:** LiveCharts2 (`LiveChartsCore.SkiaSharpView.WPF`, prerelease) or **ScottPlot.WPF**. ScottPlot is simpler to get working.
- **Newtonsoft.Json** (only if you stay on .NET Framework).

## Pointers, in the order you'll hit them

1. **Models first.** One class per schema shape (`DashboardData`, `Indicator`, `Threshold`...). Use `double?` (nullable) for values, because the schema allows `null`. On .NET 8 you can use `record`s.

2. **Deserializing.** The JSON is `snake_case` and C# properties are `PascalCase`. Let the library map them rather than renaming everything:
   ```csharp
   // .NET 8 (System.Text.Json)
   var options = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };
   var data = JsonSerializer.Deserialize<DashboardData>(File.ReadAllText(path), options);

   // .NET Framework (Newtonsoft.Json)
   var settings = new JsonSerializerSettings {
       ContractResolver = new DefaultContractResolver { NamingStrategy = new SnakeCaseNamingStrategy() }
   };
   var data = JsonConvert.DeserializeObject<DashboardData>(File.ReadAllText(path), settings);
   ```

3. **Finding the JSON file.** The app runs from `Global_Warming_Index/bin/Debug/`, not the repo root. Walk up from `AppDomain.CurrentDomain.BaseDirectory` until you find a folder containing `Data/dashboard_data.json`. That's more robust than a hard-coded `..\..\..\` path.

4. **Learn data binding before anything else.** `{Binding PropertyName}` in XAML, `DataContext = new MainViewModel()` in `MainWindow`, and `INotifyPropertyChanged` (or `[ObservableProperty]`). If you're writing `myTextBlock.Text = ...` in code-behind, stop: that's the habit MVVM replaces.

5. **The carbon-budget countdown.** Use a `DispatcherTimer` ticking every 100 ms that recomputes `remaining = budgetAtStart - ratePerSecond * (DateTime.UtcNow - start).TotalSeconds`. Recompute from elapsed time; don't subtract a fixed amount per tick, because ticks drift.

6. **Auto-refresh.** A `FileSystemWatcher` on `Data/` reloads when Python rewrites the file. Its events fire on a background thread, so marshal back with `Application.Current.Dispatcher.Invoke(...)` or you'll get a cross-thread exception.

7. **Refresh button that runs the Python side.** Use `Process.Start` with `FileName = "python"`, `Arguments = "build_dashboard.py"`, and `WorkingDirectory` set to the repo's `python/` folder. Don't block the UI thread waiting for it: use `await Task.Run(() => p.WaitForExit())` on 4.7.2, or `await p.WaitForExitAsync()` on .NET 8.

8. **Show `as_of` next to every number,** and grey out cards whose value is `null`.

## Don't commit build output
`bin/`, `obj/` and `.vs/` are covered by the repo's `.gitignore` on GitHub. Make sure you've pulled it **before** your first `git add`, or you'll commit hundreds of build files.
