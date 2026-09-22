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

`Save` and `Load` return `ok, result` — the file name on success, an error message otherwise.

## Autoload

Nothing is loaded at startup until a configuration is marked. `LoadAutoloadConfig` reads `<folder>/settings/autoload.txt` and does nothing when the file is missing.

## Without file support

If the executor exposes no `writefile` / `readfile`, an in-memory store takes over: the buttons keep working, but everything is lost when the session ends.

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
