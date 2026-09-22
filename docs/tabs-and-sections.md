# Tabs and sections

## Tabs

```lua
local General = Window:Tab("general")
local Settings = Window:Tab("settings")

Window:SetTab(General)
Window:SetTab("settings") -- by name
```

The tab bar scrolls horizontally when tabs exceed the available width: nothing spills out of the window, even after a resize.

## Columns

Every tab has two columns of equal width. The second argument of `Section` picks the column (`1` by default).

```lua
local left  = General:Section("global", 1)
local right = General:Section("settings", 2)
```

Explicit equivalent:

```lua
local column = General:Column(2)
local section = column:Section("settings")
```

## Sections

A section is a card with a clickable title: clicking collapses or expands its contents with an animation.

```lua
local section = General:Section("global", 1)

section.Open      -- current state
section.Frame     -- the instance
section.Container -- the element container
```

Every element method is called on a section:

```lua
section:Toggle({ ... })
section:Dropdown({ ... })
section:Slider({ ... })
section:Keybind({ ... })
section:ColorPicker({ ... })
section:Input({ ... })
section:Search({ ... })
section:Button({ ... })
section:ButtonRow({ ... })
section:Label("text")
section:Paragraph({ ... })
section:Divider()
```

Gear popups expose exactly the same methods, so any element can be nested inside one.
