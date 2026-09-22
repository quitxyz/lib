# Architecture

The library is split into a core and four addons.

```
main.luau                      window, elements, notifications, file system, addon loader
addons/Icons.lua               Lucide 48px icon table, local copy
addons/SaveManager.luau        JSON configurations
addons/InterfaceManager.luau   toggle key, scale, unload
addons/ThemeManager.luau       color presets and custom accent
```

## Loader

`main.luau` fetches each addon with `loadstring(game:HttpGet(Library.BaseUrl .. path))()`. Change `Library.BaseUrl` if you host the files somewhere else.

```lua
Library.BaseUrl = "https://raw.githubusercontent.com/FacilityHUB/UI-Facility/refs/heads/main/"
Library.AddonPaths = {
    Icons = "addons/Icons.lua",
    SaveManager = "addons/SaveManager.luau",
    InterfaceManager = "addons/InterfaceManager.luau",
    ThemeManager = "addons/ThemeManager.luau",
}
```

`SaveManager`, `InterfaceManager` and `ThemeManager` are loaded at the end of `main.luau`. `Icons` is deferred until the first icon is used: no reason to download 145 KB if you never place one.

When an addon cannot be found, a `warn` is emitted and the matching entry is `nil` — the error only surfaces on the first call in your script.

## Writing an addon

An addon returns either a table, or a function receiving the library:

```lua
return function(Library)
    local MyAddon = {}

    function MyAddon:BuildSection(tab, column)
        local section = tab:Section("my addon", column or 1)
        section:Button({ Text = "hello", Callback = function() Library:Notify("hello") end })
        return section
    end

    return MyAddon
end
```

Declare its path, then load it:

```lua
Library.AddonPaths.MyAddon = "addons/MyAddon.luau"
local MyAddon = Library:LoadAddon("MyAddon")
```

What the core exposes to addons: `Library.Theme`, `Library.FileSystem`, `Library:BuildFolders(folder)`, `Library:Repaint()`, `Library:Notify`, and every tab and section method.

## Hosting

Every file must sit at the exact path declared in `AddonPaths`, relative to `Library.BaseUrl`:

```
main.luau
addons/Icons.lua
addons/SaveManager.luau
addons/InterfaceManager.luau
addons/ThemeManager.luau
```

Open the full URL of one addon in a browser to confirm it serves raw code before shipping. A wrong base URL is silent: the library still loads, but `Library.SaveManager` is `nil` and only fails on first use.
