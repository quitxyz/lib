# Theme

Every color lives in `Library.Theme`, read when instances are created.

```lua
Library.Theme.Accent = Color3.fromRGB(120, 190, 255)
```

For a runtime change after creation, go through [ThemeManager](theme-manager.md) or call `Library:Repaint()` after editing the palette.

## Keys

| Key | Role |
| --- | --- |
| `Window`, `WindowAlpha`, `WindowBorder` | window and its outline |
| `TopBar` | top bar |
| `Section`, `SectionBorder` | section cards, notifications |
| `Group`, `GroupBorder` | paragraphs |
| `Field`, `FieldHover`, `Border` | dropdowns, buttons, fields, pills |
| `PopupBg`, `PopupBorder` | floating panels |
| `BorderSoft` | separators |
| `Track` | slider rail |
| `Text`, `TextDim`, `TextBright` | three text levels |
| `TextMarked` | yellow used by `warning` styles |
| `TextCode` | green used by `success` styles |
| `Danger` | red used by `danger` styles |
| `Accent`, `AccentSoft`, `AccentDim` | accent color, hover, scrollbars |
| `Font`, `FontMedium`, `TextSize`, `Radius` | typography and corner radius |
| `GearIcon` | asset for the gear icon |

## Example

```lua
local Theme = Library.Theme
Theme.Accent     = Color3.fromRGB(120, 190, 255)
Theme.AccentSoft = Color3.fromRGB(160, 210, 255)
Theme.AccentDim  = Color3.fromRGB(70, 110, 150)

local Window = Library:Window({ Title = "facility" })
```
