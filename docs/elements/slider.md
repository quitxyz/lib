# Slider

```lua
local slider = section:Slider({
    Text = "radius",
    Flag = "radius",
    Min = 0,
    Max = 200,
    Default = 50,
    Suffix = " m",
    Callback = function(value) print(value) end,
})
```

| Option | Default | Description |
| --- | --- | --- |
| `Text` | `"slider"` | label |
| `Flag` | `Text` | configuration identifier |
| `Min` / `Max` | `0` / `100` | bounds |
| `Default` | `Min` | initial value |
| `Step` | `nil` | rounding increment |
| `Decimals` | `0` | decimals displayed and kept |
| `Suffix` | `nil` | text appended to the value |
| `ZeroText` | `nil` | replacement text when the value equals `Min` |
| `Callback` | `nil` | `function(value)` |

## Examples

```lua
section:Slider({ Text = "strength", Flag = "strength", Min = 0, Max = 1, Decimals = 2, Default = 0.35 })
section:Slider({ Text = "max distance", Flag = "distance", Min = 0, Max = 5000, Default = 0, ZeroText = "0 - unlimited" })
section:Slider({ Text = "steps", Flag = "steps", Min = 0, Max = 100, Step = 5, Default = 25 })
```

## Methods

```lua
slider:Set(120)
slider:Set(120, true) -- silent
slider.Value
```

The hit area extends a few pixels above the rail, so it stays usable with a mouse and with a finger.
