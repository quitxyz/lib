# Keybind

A standalone element, not to be confused with the pill attached to a toggle.

```lua
section:Keybind({
    Text = "hold to inspect",
    Flag = "inspect_key",
    Default = "E",
    Mode = "hold",
    Callback = function(down) print(down) end,
})
```

| Option | Default | Description |
| --- | --- | --- |
| `Text` | `"keybind"` | label |
| `Flag` | `Text` | configuration identifier |
| `Default` | `nil` | initial key, as a name (`"E"`, `"MB2"`) |
| `Mode` | `"press"` | `"hold"` calls `Callback(true)` on press and `Callback(false)` on release |
| `Callback` | `nil` | `function(key)` in press mode, `function(down)` in hold mode |
| `OnChanged` | `nil` | `function(key)` on every assignment, clearing included |

## Interaction

* left click on the pill: listen for the next key;
* left click elsewhere while listening: cancel without changing anything;
* right click: clear the key;
* `Escape`: clear the key.

Mouse buttons supported: `MB1`, `MB2`, `MB3`. While listening, the interface toggle key is suppressed so it does not fire.

## Methods

```lua
keybind:Set("R")
keybind:Get() -- "R", or "" when no key is set
```

## Driving the menu key

```lua
section:Keybind({
    Text = "menu key",
    Default = "RightShift",
    OnChanged = function(key)
        Library:SetToggleKey(key)
    end,
})
```

This is exactly what the `InterfaceManager` does.
