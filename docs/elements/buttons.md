# Buttons

## Button

```lua
section:Button({
    Text = "reload scripts",
    Callback = function()
        print("click")
    end,
})
```

Full width, 26 pixels tall.

## ButtonRow

Two or three buttons of equal width on one line.

```lua
section:ButtonRow({
    { Text = "save", Callback = function() end },
    { Text = "load", Callback = function() end },
})
```

Returns `{ Instance, Buttons, Controls }`. `Buttons` retains the raw `TextButton` instances for compatibility. `Controls` contains the corresponding APIs with `SetEnabled`, `SetDisabled`, `SetText`, `SetCallback`, and `SetVisible`, also available on standalone buttons.

```lua
row.Controls[1]:SetEnabled(false)
row.Controls[2]:SetText("load selected")
row.Controls[2]:SetCallback(function() end)
```

Disabled buttons ignore activation and hover feedback. Hiding a row button retains its original allocated width; it does not redistribute the other buttons.

## Footer action

```lua
Window:Action("Connect", function()
    Library:Notify("facility", "connected.", 3)
end)
```

An accent colored text button, right aligned in the bottom bar. Repeated calls stack actions from right to left.

## Divider

```lua
section:Divider()
```

A one pixel separator line.

None of these elements hold state, so none of them are ever saved into configurations.
