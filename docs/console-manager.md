# ConsoleManager

ConsoleManager provides the template's console as an optional addon. It does not replace global `print`, `warn`, or `error` functions. Use its logger methods for script messages.

```lua
local ConsoleManager = assert(Library:LoadAddon("ConsoleManager"))
local console = ConsoleManager:Create(Window, {
    MaxVisibleRows = 100,
    UIOutput = true,
    RobloxOutput = false,
    Folder = "seized/logs",
    Prefix = "seized",
})
console:Print("script loaded.")
console:Warn("something needs attention")
console:Error('status: <font color="#E66464">failed</font>')
```

Passing a window creates a reusable modal and a footer icon next to the theme action. Passing an existing tab or section mounts the controls and output inline instead:

```lua
local console = ConsoleManager:Create(consoleTab)
-- Also supported: ConsoleManager:Create(settingsTab:Section("console", 1))
```

## Options

| Option | Default / behavior |
| --- | --- |
| `Title`, `Width`, `Height` | Modal title `console`, width `460`, height `0.85` |
| `MaxVisibleRows` | `100` newest matching entries; positive finite number, rounded down |
| `UIOutput`, `RobloxOutput` | Independent script destinations; default `true`, `false` |
| `Output` | Compatibility shorthand: `console`, `roblox`, `both`, or `none`; explicit destination booleans take precedence |
| `Target` | `Both`; display/export source filter: `Script`, `Roblox`, `Both`; displayed as lowercase under “source” |
| `Filters` | `{ Print = true, Warn = true, Error = true }`; visibility/export filters |
| `CaptureRoblox` | `true`; listen for future `LogService.MessageOut` events |
| `RichText` | `true` for script messages; Roblox messages are literal text |
| `TextSize`, `OutputHeight` | `12`, `190` |
| `Folder` | `Facility/logs`; destination for saved session logs |
| `Prefix` | `Facility`; native messages include this prefix and a unique instance ID |
| `MountButton`, `Icon`, `ButtonOrder` | `true`, `square-terminal`, `2`; modal only |
| `Spacing` | `9`; inline cards container only |
| `Controls` | Set `UIOutput`, `RobloxOutput`, `Target`, `Filters`, `Copy`, `Save`, or `Clear` to `false` to omit those controls; `Output = false` hides both destination toggles |
| `Labels` | Override `UIOutput`, `RobloxOutput`, `UIOutputHint`, `RobloxOutputHint`, `Target`, `Print`, `Warn`, `Error`, `Copy`, `Save`, `Clear`, `Empty`, `Saved`, `CopyFailed`, or `SaveFailed` text |
| `Colors` | Per-level Color3 values or theme tokens; defaults: Print=`Text`, Warn=`TextMarked`, Error=`Danger` |

Both output toggles include a small help marker using the library’s existing toggle hints. Customize their explanations through `Labels.UIOutputHint` and `Labels.RobloxOutputHint`.

The “ui console” and “roblox console” toggles independently route new script Print/Warn/Error calls. Both may be off. They do not change Roblox’s own logging, remove existing history, or stop capture of unrelated Roblox messages. Closing the panel only hides it.

Omitted controls do not disable the corresponding API methods. Controls use `Flag = false`; they do not enter saved game configs. Output routing and capture are distinct: choosing `roblox` forwards new script messages there, while unrelated Roblox messages can still be captured in the panel. Existing entries remain stored when routing changes.

```lua
local console = ConsoleManager:Create(Window, {
    Controls = { Save = false },
    Labels = { Copy = "copy logs", Empty = "nothing yet" },
    Colors = { Warn = "Accent", Error = "Danger" },
})
```

Set the modal title through the top-level `Title` option, not `Labels`.

## Methods and handles

```lua
console:SetMaxVisibleRows(50)
console:SetUIOutput(true)
console:SetRobloxOutput(true)
console:SetOutput("both") -- shorthand for enabling both
console:SetTarget("Script")
console:SetFilter("Warn", false)
console:SetCaptureRoblox(false)
console:SetOpen(true)
console:Toggle()
```

Setters keep the corresponding controls synchronized. Filters select the newest matching entries first, then display those entries chronologically. The row limit counts entries, not physical text lines; wrapped entries can occupy several lines.

Returned handles are `Controls.UIOutput`, `Controls.RobloxOutput`, `Controls.Target`, `Controls.Print`, `Controls.Warn`, `Controls.Error`, `Controls.Copy`, `Controls.Save`, and `Controls.Clear` when those controls were created. Other handles include `Content`, `LogArea`, `Root`/`Instance`, `Window`, and `ActionRow`. `Modal` and `Button` exist only for a modal and its optional footer button.

```lua
console.Controls.Copy:SetText("copy visible history")
console.Controls.Save:SetEnabled(false)
console.Controls.Clear:SetCallback(function() console:Clear() end)
```

For an inline console, `SetOpen`/`Toggle` show or hide the root. Hiding either form keeps capture and history active.

## History and exporting

```lua
local text = console:Export(true)
local entries = console:GetEntries()
local copied, copyError = console:Copy()
local saved, filenameOrError = console:Save()
console:Clear()
```

`Clear` hides all existing entries. It does not delete session history. `Export(false)` and `Copy` include matching entries since the last clear, including those older than the visible row limit. `Export(true)` and `Save` include all matching session entries, including cleared entries. Export text retains the message strings, including RichText tags.

`GetEntries` returns copies of all stored entries, unaffected by filters or clear. Each entry has `source`, `level`, `time`, and `message`. History remains in memory for the lifetime of the console; the visible limit does not cap stored history. `Save` requires `writefile`, creates the configured directory, and returns the saved path. Direct `Copy`/`Save` calls return success/error without creating status messages; their default UI buttons log the result.

Forwarded native messages are tagged so the same console ignores their delayed echoes. Repeated messages with identical text remain separate entries. RichText tags are removed from native output. Native errors use `LogService:Log` when available; otherwise they use `warn` with an Error label so logging never deliberately throws an exception in the caller.

Capture begins at creation and only includes messages exposed by Roblox's `MessageOut`; it cannot retrieve private executor-console messages or reconstruct earlier errors.

## Cleanup

```lua
console:Destroy()
```

Disconnects capture and control listeners, cancels pending render work, removes owned repaint hooks, dropdown floating panels, and the footer button, then destroys the console UI and clears history. A supplied tab/section remains available. Destroying the parent or unloading the library performs the same cleanup. Multiple consoles maintain independent histories and filters.
