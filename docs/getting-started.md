# Getting started

## Script layout

Order matters: build the managers **after** every other element, because `BuildConfigSection` captures default values at the moment it runs.

```lua
local Library = loadstring(game:HttpGet("https://raw.githubusercontent.com/FacilityHUB/UI-Facility/refs/heads/main/main.luau"))()

local SaveManager = Library.SaveManager
local InterfaceManager = Library.InterfaceManager
local ThemeManager = Library.ThemeManager

-- 1. window
local Window = Library:Window({ Title = "facility", Suffix = ".app" })

-- 2. tabs
local Main = Window:Tab("main")
local Settings = Window:Tab("settings")

-- 3. sections and elements
local combat = Main:Section("combat", 1)
combat:Toggle({ Text = "enable", Flag = "combat_enable" })

-- 4. managers
SaveManager:SetLibrary(Library)
InterfaceManager:SetLibrary(Library)
InterfaceManager:SetWindow(Window)
ThemeManager:SetLibrary(Library)

SaveManager:IgnoreThemeSettings()
SaveManager:SetIgnoreIndexes({})

InterfaceManager:SetFolder("Facility")
ThemeManager:SetFolder("Facility")
SaveManager:SetFolder("Facility/my-game")

InterfaceManager:BuildInterfaceSection(Settings, 1)
ThemeManager:BuildThemeSection(Settings, 1)
SaveManager:BuildConfigSection(Settings, 2)

-- 5. initial state
Window:SetTab(Main)
Library:Notify("Facility", "script loaded.", 5)
SaveManager:LoadAutoloadConfig()
```

## Flags

Every stateful element takes a `Flag`, a unique identifier used for saving and for `Library.Flags`.

```lua
combat:Slider({ Text = "range", Flag = "combat_range", Min = 0, Max = 100, Default = 25 })

print(Library.Flags.combat_range) --> 25
```

Rules:

* without a `Flag`, the value of `Text` is used — two elements with the same name collide, and a `warn` is emitted;
* `Flag = false` excludes the element from configurations entirely;
* stateless elements (`Label`, `Paragraph`, `Button`, `Divider`) have no flag.

## Toggle key

`RightShift` by default.

```lua
Library:SetToggleKey("RightAlt")      -- key name
Library:SetToggleKey(Enum.KeyCode.F4) -- or a KeyCode
Library:SetToggleKey("MB2")           -- or a mouse button
Library:ToggleUI()                    -- toggle manually
```

## Unloading

```lua
Library:Destroy()
```

Disconnects every tracked connection, destroys the `ScreenGui` instances (window, notifications, mobile button) and clears `Flags` and `Registry`.
