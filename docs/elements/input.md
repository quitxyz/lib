# Input and Search

## Input

A text field with a caption above it.

```lua
local input = section:Input({
    Text = "name",
    Flag = "config_name",
    Default = "default",
    Placeholder = "config name",
    Callback = function(text, enterPressed) print(text) end,
})

input:Get()
input:Set("value")
```

| Option | Default | Description |
| --- | --- | --- |
| `Text` | `nil` | caption |
| `Flag` | `Text` | configuration identifier |
| `Default` | `""` | initial text |
| `Placeholder` | `""` | greyed out text |
| `Callback` | `nil` | `function(text, enterPressed)` on focus lost |

## Search

A field followed by a label on the right, meant for filtering a list.

```lua
section:Search({
    Label = "search",
    Placeholder = "",
    Live = true,
    Flag = nil,
    Callback = function(text) print(text) end,
})
```

| Option | Default | Description |
| --- | --- | --- |
| `Label` | `"search"` | label to the right of the field |
| `Placeholder` | `""` | greyed out text |
| `Default` | `""` | initial text |
| `Live` | `false` | fires the callback on every keystroke instead of on focus lost |
| `Flag` | `nil` | not saved unless explicitly provided |
| `Callback` | `nil` | `function(text, enterPressed)` |

Unlike other elements, `Search` does not fall back to `Text` for its flag: without a `Flag`, it stays out of configurations.
