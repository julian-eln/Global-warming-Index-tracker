# C# desktop app

Not generated on purpose — creating it yourself is 5 minutes and teaches you how .NET projects fit together.

## 1. Pick a UI framework (decide in the first 10 minutes)

| | **WPF** | **Avalonia** |
|---|---|---|
| Runs on | Windows only | Windows, macOS, Linux |
| Tutorials / Stack Overflow answers | Tons | Fewer, but WPF knowledge mostly transfers |
| Visual designer | Yes, in Visual Studio | Previewer, less mature |
| Pick it if | Everyone demoing is on Windows | Anyone on the team uses a Mac |

Default for a learner on Windows: **WPF**. Both use XAML + MVVM, so the concepts are the same.

## 2. Create the project (from the repo root)

```bash
# needs the .NET 8 (or newer) SDK: dotnet --version
dotnet new sln -n ClimateTracker -o csharp
dotnet new wpf -n ClimateTracker.App -o csharp/ClimateTracker.App
dotnet sln csharp/ClimateTracker.sln add csharp/ClimateTracker.App

cd csharp/ClimateTracker.App
dotnet add package CommunityToolkit.Mvvm        # removes MVVM boilerplate
dotnet add package LiveChartsCore.SkiaSharpView.WPF --prerelease   # charts (or: ScottPlot.WPF)
dotnet run
```
(Avalonia: `dotnet new install Avalonia.Templates`, then `dotnet new avalonia.mvvm` instead of `wpf`.)

## 3. Suggested structure

```
ClimateTracker.App/
├── Models/          # plain classes mirroring Data/SCHEMA.md
├── Services/        # DashboardDataService: reads + deserializes the JSON
├── ViewModels/      # MainViewModel: exposes properties the UI binds to
└── Views/           # XAML windows / user controls
```

## Pointers (in the order you'll hit them)

1. **Models first.** Write `DashboardData`, `Indicator`, `Threshold`, etc. as C# `record`s matching the schema. Use `double?` (nullable) for values — the schema allows `null`.
2. **Deserializing:**
   ```csharp
   var options = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower };
   var data = JsonSerializer.Deserialize<DashboardData>(File.ReadAllText(path), options);
   ```
   `SnakeCaseLower` maps `as_of` → `AsOf` automatically (.NET 8+).
3. **Finding the JSON file:** the app runs from `bin/Debug/net8.0-windows/`, not the repo root. Either walk up from `AppContext.BaseDirectory` until you find `Data/`, or copy it on build with `<None Include="..\..\Data\dashboard_data.json" CopyToOutputDirectory="PreserveNewest" />` in the `.csproj`.
4. **Learn data binding before anything else.** `{Binding PropertyName}` in XAML + `[ObservableProperty]` from CommunityToolkit.Mvvm. If you find yourself writing `textBlock.Text = ...` in code-behind, stop — that's the habit MVVM replaces.
5. **The countdown:** a `DispatcherTimer` ticking every 100 ms that recomputes `remaining = budget - ratePerSecond * secondsElapsed`. Compute from elapsed time, don't subtract per tick (ticks drift).
6. **Auto-refresh:** `FileSystemWatcher` on `Data/` reloads when Python rewrites the file. Its events fire on a background thread — marshal back with `Application.Current.Dispatcher.Invoke(...)` or you'll get a cross-thread exception.
7. **Refresh button that runs Python:** `Process.Start` with `python build_dashboard.py` and `WorkingDirectory` set to `python/`. Run it async (`await process.WaitForExitAsync()`) so the UI doesn't freeze.
8. **Show `as_of` next to every number** and grey out cards whose value is `null`.
