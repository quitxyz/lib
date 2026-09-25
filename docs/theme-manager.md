# Theme manager

`Library.ThemeManager` recolors the interface at runtime, with no reload.

```lua
local ThemeManager = Library.ThemeManager

ThemeManager:SetLibrary(Library)
ThemeManager:SetSettingsFolder("seized/settings")
ThemeManager:Load() -- optional, before mounting
ThemeManager:Mount(Window)
```

## Presets

`facility` (default), `darker`, `typewriter`, `aqua`, `amethyst`, `rose`, `contrast`, `light`.

```lua
ThemeManager:Apply("aqua")
ThemeManager:Names() -- list of presets
```

## Custom accent

```lua
ThemeManager:SetAccent(Color3.fromRGB(120, 190, 255))
ThemeManager:SetAccent("#78BEF0")
```

`AccentSoft` (hover) and `AccentDim` (scrollbars) are derived automatically in HSV: only one color to pick.

## Generated section

`Mount` adds a footer paintbrush that opens a modal with a preset dropdown,
individual theme color pickers and a reset button. Closing after edits prompts
to save or discard. Its `theme_preset` flag is excluded from configurations by
`SaveManager:IgnoreThemeSettings()`.

## Persistence

Call `Load` explicitly to restore saved colors. Saving is available from the
modal's save/discard prompt; `AutoSave` enables saving during editing.

```lua
ThemeManager.AutoSave = true
ThemeManager:Save()
ThemeManager:Load()           -- call it explicitly, before building elements
```

`SetSettingsFolder("seized/settings")` writes directly to
`seized/settings/theme.json`. Legacy `SetFolder("seized")` produces the same
path and clears the explicit override. `Save` returns `ok, storageOrError`,
where successful storage is `"disk"` or `"memory"`.

## How it works

As each instance is created, any `Color3` matching a palette entry is recorded along with its property. `Library:Repaint()` reapplies the current palette over that registry, which recolors the existing interface.

```lua
Library.Theme.Accent = Color3.fromRGB(255, 120, 80)
Library:Repaint()
```

Limitation: two palette keys holding the exact same RGB value may be indexed under
a single key. Components registered through this value-based mapping may then
follow that key when colors change.
