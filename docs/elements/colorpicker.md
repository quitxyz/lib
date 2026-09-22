# Color picker

A row with a swatch on the right; clicking it opens a floating panel: saturation and value square, hue bar, alpha bar, hexadecimal field and `copy` / `paste` links.

```lua
local picker = section:ColorPicker({
    Text = "highlight",
    Flag = "highlight_color",
    Default = Color3.fromRGB(232, 161, 168),
    DefaultAlpha = 1,
    Callback = function(color, alpha)
        print(color, alpha)
    end,
})
```

| Option | Default | Description |
| --- | --- | --- |
| `Text` | `"color"` | label (ignored for a swatch attached to a toggle) |
| `Flag` | `Text` | configuration identifier |
| `Default` | white | initial `Color3` |
| `DefaultAlpha` | `1` | initial alpha, `0` to `1` |
| `Alpha` | `true` | `false` removes the alpha bar |
| `Callback` | `nil` | `function(color, alpha)` |

## Methods

```lua
picker:Get()                                  -- Color3, alpha
picker:Set(Color3.fromRGB(255, 0, 0))
picker:Set("#FF0000AA")                       -- hex, alpha included
picker:Set(Color3.new(1, 0, 0), 0.5, true)    -- silent
picker.Color
picker.Alpha
```

## Storage format

The saved value is a `#RRGGBBAA` string. `Set` accepts either a `Color3` or a 6 or 8 character hex string, with or without the `#`.

## Several pickers on one option

```lua
section:Toggle({ Text = "radius circle", Flag = "radius" })
    :ColorPicker({ Flag = "radius_outline", Default = Color3.fromRGB(232, 161, 168) })
    :ColorPicker({ Flag = "radius_fill", Default = Color3.fromRGB(60, 60, 65), DefaultAlpha = 0.35 })
```

Alpha is rendered on the swatch itself, which makes an opaque outline instantly distinguishable from a translucent fill.
