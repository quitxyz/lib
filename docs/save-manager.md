# Configurations

`Library.SaveManager` serialises every flagged element to JSON.

## Setup

```lua
local SaveManager = Library.SaveManager

SaveManager:SetLibrary(Library)
SaveManager:IgnoreThemeSettings()      -- excludes InterfaceManager and ThemeManager flags
SaveManager:SetIgnoreIndexes({ "flag_a", "flag_b" })
SaveManager:SetFolder("Facility/my-game")
SaveManager:BuildConfigSection(Settings, 2)
SaveManager:LoadAutoloadConfig()
```

`SetFolder` creates the tree: `<folder>/configs` and `<folder>/settings`.

For exact paths, use `SetConfigFolder` instead:

```lua
local ok, err = SaveManager:SetConfigFolder("seized/configs/game1")
assert(ok, err)
-- Saves: seized/configs/game1/default.json
-- Autoload: seized/configs/game1/autoload.txt

ThemeManager:SetSettingsFolder("seized/settings")
-- Theme: seized/settings/theme.json
```

`SaveManager:SetSettingsFolder(path)` optionally overrides the folder containing
`autoload.txt`. If omitted, an explicit config folder keeps its own autoload
selection. `SetFolder` resets both overrides and retains the legacy layout.
Folder setters return `ok, storageOrError`; nested relative paths are supported.
An absolute path or a `.`/`..` segment is rejected.

Every registered control is saved automatically unless its flag is ignored.
There is no required list of included flags. Use a unique `Flag = "uiScale"`
on a saved control and `Flag = false` on an unsaved control. Setting folders
does not automatically divide UI flags from game flags; exclusions determine
the contents of each saved config.

`BuildConfigSection` must run **after** every element has been created: that is when it captures the default values used by `reset defaults`.

## Generated section

A `name` field, a `saved` list, then the actions: `save`, `load`, `delete`, `refresh`, `set autoload`, `clear autoload`, `copy`, `paste`, `reset defaults`. Two status labels show the autoloaded configuration and whether unsaved changes exist.

## API

```lua
SaveManager:Save("default")        -- writes <folder>/configs/default.json
SaveManager:Load("default.json")
SaveManager:Delete("default.json")
SaveManager:List()                 -- table of file names
SaveManager:SetAutoload("default.json")
SaveManager:GetAutoload()
SaveManager:ClearAutoload()
SaveManager:LoadAutoloadConfig()
```

`Save` returns `ok, fileOrError, storage`, with `storage` equal to `"disk"` or
`"memory"` on success. `Load` and `Delete` return `ok, fileOrError`.
`SetAutoload` and `ClearAutoload` return `ok, storageOrError`.
`SetAutoload` requires an existing config. `List` includes only `.json` files.
Config names allow 1–64 letters, digits, spaces, underscores and hyphens, with
an optional `.json` suffix. Names cannot contain directory separators.

Load reports setter failures and may already have applied preceding settings;
it is not a transactional rollback. Callback errors continue to use the
library's callback error reporting.

## Autoload

Nothing is loaded at startup until a configuration is marked. `LoadAutoloadConfig` reads `<folder>/settings/autoload.txt` and does nothing when the file is missing.

## Without file support

If either `writefile` or `readfile` is unavailable, an in-memory store takes over:
the buttons keep working, but everything is lost with that library instance.
The built-in panel labels memory-only saves. When native file functions exist
but a write or delete fails, the operation returns an error rather than silently
falling back to memory. Custom panels must check the returned result before
showing success or clearing their own change indicators.

## Configuration contents

```json
{
  "combat_enable": true,
  "combat_range": 25,
  "anchor": "head",
  "ignore": ["friends"],
  "inspect_key": "E",
  "highlight_color": "#E8A1A8FF"
}
```
