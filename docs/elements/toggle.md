# Toggle

A checkbox: empty square when off, filled with the accent color when on. The label color never changes.

```lua
local toggle = section:Toggle({
    Text = "enable",
    Flag = "enable",
    Default = false,
    Hint = "starts the main loop",
    Callback = function(state)
        print(state)
    end,
})
```

| Option | Default | Description |
| --- | --- | --- |
| `Text` | `"toggle"` | label |
| `Flag` | `Text` | configuration identifier, `false` to exclude |
| `Default` | `false` | initial state; when `true`, `Callback` runs on construction |
| `Hint` | `nil` | adds a `?` with a tooltip on hover |
| `Callback` | `nil` | `function(state)` |

## Methods

```lua
toggle:Set(true)        -- fires the callback
toggle:Set(true, true)  -- silent
toggle.State            -- current boolean
```

## Attached elements

The three methods below return the toggle, so they chain.

### Keybind

A pill on the right of the row. Left click to listen, left click elsewhere to cancel, right click to clear.

```lua
toggle:Keybind({ Default = "F", Flag = "enable_key", Mode = "hold" })
```

`Mode = "hold"` keeps the toggle on while the key is held. Without a `Flag`, the key is not saved.

### Color picker

One or more swatches on the right, each with its own flag and callback.

```lua
toggle
    :ColorPicker({ Flag = "outline", Default = Color3.fromRGB(232, 161, 168) })
    :ColorPicker({ Flag = "fill", Default = Color3.fromRGB(60, 60, 65), DefaultAlpha = 0.35 })

toggle.Pickers[1]:Get() -- Color3, alpha
```

### Gear

A gear icon opening a floating panel that accepts every element.

```lua
toggle:Gear(function(panel)
    panel:Slider({ Text = "delay", Flag = "delay", Min = 0, Max = 500, Suffix = " ms", Default = 60 })
    panel:Dropdown({ Text = "profile", Flag = "profile", Options = { "default", "custom" } })
end)
```

## Layout order

Color swatches first, then the keybind pill, then the gear. The label width is recomputed automatically so it is never truncated.
