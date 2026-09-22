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

Returns `{ Instance, Buttons }`, where `Buttons` holds the `TextButton` instances in the order given.

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
