# Dropdown

```lua
local dropdown = section:Dropdown({
    Text = "anchor",
    Flag = "anchor",
    Options = { "head", "torso", "origin" },
    Default = "head",
    Callback = function(value) print(value) end,
})
```

| Option | Default | Description |
| --- | --- | --- |
| `Text` | `nil` | caption above the field |
| `Flag` | `Text` | configuration identifier |
| `Options` | `{}` | list of values |
| `Default` | first option | initial value, a table when `Multi` |
| `Multi` | `false` | multiple selection |
| `Empty` | `"none"` | text shown when nothing is selected |
| `Search` | auto | search field; shown past 8 options, `true` forces it, `false` removes it |
| `MaxHeight` | `154` | maximum list height in pixels |
| `Callback` | `nil` | `function(value)` — a string, or a table when `Multi` |

## Multiple selection

```lua
section:Dropdown({
    Text = "ignore",
    Flag = "ignore",
    Options = { "friends", "hidden", "inactive" },
    Multi = true,
    Default = { "friends" },
})
```

The field shows values separated by commas; the list stays open between choices.

## Methods

```lua
dropdown:Get()
dropdown:Set("torso")
dropdown:Set("torso", true)   -- silent
dropdown:SetOptions({ "a", "b", "c" })
```

`SetOptions` rebuilds the list; if the current value disappears, the first option is selected.

## Search

The field filters on substring, case insensitive, and the list height adjusts to the number of results. It is cleared every time the dropdown opens.
