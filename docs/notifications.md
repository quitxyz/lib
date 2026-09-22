# Notifications

Cards stacked in the bottom-right corner, in their own `ScreenGui`: they stay visible while the interface is hidden.

## Calls

```lua
Library:Notify("Facility", "script loaded.", 5)

Library:Notify({
    Title = "Facility",
    Text = "script loaded.",
    Duration = 5,
})

Library:Notify({ Title = "Facility", Content = "Fluent style alias" })
```

`Text`, `Content` and `Description` are interchangeable.

| Option | Default | Description |
| --- | --- | --- |
| `Title` | `"notice"` | title |
| `Text` | `nil` | body, wraps automatically |
| `Duration` | `3.5` | display time in seconds |
| `Style` | `nil` | `warning`, `danger`, `success`, `accent`… |
| `Color` | `nil` | explicit tint, takes priority over `Style` |
| `Icon` | auto | icon in front of the title |

## Shortcuts

```lua
Library:Warn("careful", "experimental option.", 4)
Library:Error("risky", "this cannot be undone.", 4)
Library:Success("done", "config applied.", 4)
```

The style drives the accent bar on the left, the title color and the default icon (`alert-triangle`, `x-circle`, `check-circle`). Without a style: pink bar, bright title, no icon.

## Muting notifications

```lua
Library.NotificationsEnabled = false
```

`Library:Notify` returns immediately without drawing anything.
