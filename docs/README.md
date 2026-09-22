# Facility

Luau UI library for Roblox: resizable window, tabs, collapsible sections, modern elements, configuration system and notifications.

## Loading

```lua
local Library = loadstring(game:HttpGet("https://raw.githubusercontent.com/FacilityHUB/UI-Facility/refs/heads/main/main.luau"))()
```

## Minimal example

```lua
local Window = Library:Window({ Title = "facility", Suffix = ".app" })

local General = Window:Tab("general")
local section = General:Section("global", 1)

section:Toggle({
    Text = "enable",
    Flag = "enable",
    Callback = function(state)
        print("enable", state)
    end,
})

section:Slider({ Text = "radius", Flag = "radius", Min = 0, Max = 200, Default = 50 })

Window:Action("Connect", function()
    Library:Notify("facility", "session started.", 3)
end)
```

## What the library covers

| Area | Contents |
| --- | --- |
| Window | dragging, resizing, responsive scaling, keybind, mobile button |
| Structure | scrollable tabs, two columns, collapsible sections |
| Elements | toggle, dropdown, slider, keybind, color picker, input, search, buttons, labels, paragraphs |
| Data | flag registry, configuration saving and loading, autoload |
| Feedback | notifications with styles and Lucide icons |

## Structure

```
main.luau                      library core
addons/Icons.lua               Lucide icons, local copy
addons/SaveManager.luau        configurations
addons/InterfaceManager.luau   interface settings
addons/ThemeManager.luau       colors
```

`main.luau` loads its own addons. See [Architecture](architecture.md).

## Compatibility

Roblox client only. File functions (`writefile`, `readfile`, `listfiles`, `delfile`) are detected at runtime: without them, configurations stay in memory for the session. `setclipboard` and `getclipboard` are optional (copy and paste buttons).
# Native component update — 2026.09.22

The new [native cards reference](native-cards.md) documents the implemented
card APIs. Existing documentation below was carried forward from the supplied
documentation archive; it has not been comprehensively re-audited in this update.
The existing Home test and showcase have not been migrated yet.
