# Configurations

SaveManager saves registered control flags automatically. There is no list of included flags to maintain: use a unique `Flag = "featureEnabled"` on a game control, or `Flag = false` to exclude it.

## Create the preset

Create game controls before the panel so autoload can find their flags.

```lua
local configs = SaveManager:Create(settingsTab, {
    Window = Window,
    Column = 2,
    ConfigFolder = "seized/configs/game1",
    OnError = function(message)
        console:Warn(message)
    end,
})
```

This builds the template's layout: config name and create, saved-config list, save/overwrite and load, delete and refresh, copy/import sharing, autoload list and set/remove buttons, current-autoload label, unsaved-changes label, and operation status.

Creating a config refuses existing names; overwrite uses the selected saved config. Delete asks for confirmation. Lists refresh after panel operations; refresh also discovers external file changes. Copy exports the selected saved file as readable JSON. Import accepts clipboard text when available or manual multiline paste, saves under the name entered in the panel, and does not apply the settings until Load is pressed.

The panel automatically ignores ThemeManager's and legacy InterfaceManager's listed flags. The new InterfaceManager uses unflagged controls and its separate preference file by default. If you deliberately supply custom interface flags, exclude those yourself with `SetIgnoreIndexes`.

## Customize

```lua
local configs = SaveManager:Create(settingsTab, {
    Title = "profiles",
    Column = 2,
    Autoload = false,
    JsonHeight = 180,
    Controls = { Sharing = false, Delete = false },
    Labels = { Create = "new profile", Clean = "all changes saved" },
})
```

Options:

| Option | Default |
| --- | --- |
| `Window` | Tab's window, then first library window |
| `Title`, `Column` | `configs`, `2` |
| `ConfigFolder` | Existing manager folder; supplying one calls SetConfigFolder |
| `Autoload` | `true`; load selected autoload config after building the panel |
| `ImportWidth`, `ImportHeight`, `JsonHeight` | `420`, `360`, `130` |
| `OnError` | Optional error callback; panel always displays errors when Status is visible |

Set entries in `Controls` to false to omit them. Keys: `Name`, `Create`, `Saved`, `Save`, `Load`, `Delete`, `Refresh`, `Sharing`, `Copy`, `Import`, `Autoload`, `SetAutoload`, `RemoveAutoload`, `AutoloadStatus`, `Dirty`, `Status`. Hidden Name/Saved/Autoload inputs retain API handles because operations use their values. Hiding Sharing omits the entire sharing group. Omitted row buttons reflow.

`Labels` accepts action keys plus `SavedList`, `NamePlaceholder`, `Empty`, `AutoloadPrefix`, `None`, `Unsaved`, `Clean`, `MemoryOnly`, `Saved` (save-success message), `LoadedPrefix`, `DeletedPrefix`, `CopiedPrefix`, `ImportedPrefix`, `Refreshed`, `AutoloadRemoved`, `DeleteTitle`, `DeletePrompt` (one %s placeholder), `Cancel`, `ImportHelp`, `Json`, `JsonPlaceholder`, `ImportConfirm`. Validation errors remain diagnostic messages.

Returned handles: `Section`, `Instance`, `Controls`, `Alive`, and, when enabled, `ImportModal` and `JsonInput`.

```lua
configs.Controls.Create:SetText("create profile")
configs.Controls.Name:Set("new profile")
configs:Refresh()
configs:Destroy()
```

Destroy removes this panel and its owned subscriptions and import modal. It does not delete files or game controls. Dirty labels use independent subscriptions, preserving `Library.OnDirty` and other panels. Dirty means a flagged control changed since the last successful save/load; it is not a value-by-value comparison. Building a panel does not clear an existing dirty state.

## Folders and methods

`SetFolder("Facility/my-game")` uses its configs/settings subfolders. `SetConfigFolder("seized/configs/game1")` sets an exact config directory, with autoload.txt inside it. `SetSettingsFolder(path)` optionally changes only the autoload-marker directory. Folder setters return success and storage/error. The manager has one active folder shared by its panels.

```lua
SaveManager:Save("default")          -- ok, filename/error, storage
SaveManager:Load("default.json")     -- ok, filename/error
SaveManager:Delete("default.json")   -- ok, filename/error
SaveManager:List()
SaveManager:SetAutoload("default")   -- ok, storage/error
SaveManager:GetAutoload()
SaveManager:ClearAutoload()          -- ok, storage/error
SaveManager:Export("default")        -- ok, readable JSON/error
SaveManager:Import("shared", json)   -- ok, filename/error, storage
SaveManager:Decode(json)             -- ok, filtered and validated data/error
```

Names allow 1–64 letters, numbers, spaces, underscores and hyphens, with optional .json suffix. Import refuses overwrites. Unknown and ignored flags are omitted on load/import/export. Known values are type-checked before setters run. Empty configs are valid, including when no game controls are registered yet. Setter failures can leave earlier settings applied; loading is not transactional. Callback failures use the library's normal callback reporting.

Without native file support, storage lasts only for that library instance and the panel reports memory-only saves. Native IO failures return errors instead of silently falling back to memory.

`BuildConfigSection(tab, column)` now builds this same layout but returns the Section for compatibility, exposing the panel as `section.ConfigPanel`. That legacy call does not autoload; use `LoadAutoloadConfig()` afterward if needed. The latter retains its legacy notification behavior. The new Create preset uses its status label and optional OnError callback.

## JSON example

```json
{
    "featureEnabled": true,
    "range": 25,
    "target": "nearest"
}
```
