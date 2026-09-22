# Theme manager

`Library.ThemeManager` recolors the interface at runtime, with no reload.

```lua
local ThemeManager = Library.ThemeManager

ThemeManager:SetLibrary(Library)
ThemeManager:SetFolder("Facility")
ThemeManager:BuildThemeSection(Settings, 1)
```

## Presets

`rose` (default), `blue`, `green`, `amber`, `violet`, `mono`.

```lua
ThemeManager:Apply("blue")
ThemeManager:Names() -- list of presets
```

## Custom accent

```lua
ThemeManager:SetAccent(Color3.fromRGB(120, 190, 255))
ThemeManager:SetAccent("#78BEF0")
```

`AccentSoft` (hover) and `AccentDim` (scrollbars) are derived automatically in HSV: only one color to pick.

## Generated section

`BuildThemeSection` adds a preset dropdown, an accent color picker and a reset button. Its flags `theme_preset` and `theme_accent` are excluded from configurations by `SaveManager:IgnoreThemeSettings()`.

## Persistence

Nothing is written or read back automatically.

```lua
ThemeManager.AutoSave = true  -- writes <folder>/settings/theme.json on every change
ThemeManager:Save()
ThemeManager:Load()           -- call it explicitly, before building elements
```

## How it works

As each instance is created, any `Color3` matching a palette entry is recorded along with its property. `Library:Repaint()` reapplies the current palette over that registry, which recolors the existing interface.

```lua
Library.Theme.Accent = Color3.fromRGB(255, 120, 80)
Library:Repaint()
```

Limitation: two palette keys holding the exact same RGB value are indexed under a single one. `BorderSoft` and `SectionBorder` are both `46, 46, 50` — changing one without the other will not recolor everything. Harmless as long as you only change the accent.
