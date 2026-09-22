# Window

```lua
local Window = Library:Window({
    Title  = "facility",
    Suffix = ".app",
    Width  = 620,
    Height = 620,
})
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `Title` | `"demoui"` | bright part of the top bar title |
| `Suffix` | `".app"` | rest of the title, drawn in grey |
| `Width` / `Height` | `620` / `560` | starting size in pixels |
| `MinWidth` / `MinHeight` | `460` / `320` | lower bounds when resizing |
| `Position` | centered | `UDim2`, anchored at the window center |
| `Footer` | `true` | `false` removes the bottom bar |
| `Name` | `"Facility"` | name of the `ScreenGui` |
| `MobileButton` | auto | `true` forces the floating button, `false` disables it; created by default on touch devices |
| `MobileButtonOptions` | `nil` | same keys as `CreateMobileButton`: `{ Size = 44, Position = UDim2… }` |

## Behaviour

**Dragging**: grab the top bar.

**Resizing**: handle in the bottom-right corner. Size is clamped by `MinWidth`/`MinHeight` and by the viewport. Everything follows automatically — columns, sections, footer.

**Responsive scaling**: a `UIScale` shrinks the window down to `0.55` when the screen is too small, never above `1` (multiplied by the user scale).

## Methods

```lua
Window:Tab(name)                 -- create a tab
Window:SetTab(tabOrName)         -- switch tab
Window:Action(text, callback)    -- text button in the footer
Window:SetVisible(bool)
Window:SetSize(width, height)
Window:SetUserScale(1.15)        -- 0.6 to 1.4
Window:SetOpacity(0.9)           -- 0.2 to 1
Window:CloseFloating()           -- close open dropdowns and popups
```

## Fields

`Window.Tabs`, `Window.ActiveTab`, `Window.Main`, `Window.Gui`, `Window.Width`, `Window.Height`, `Window.Visible`.

## Mobile button

A floating button living in its own `ScreenGui`, so it stays visible even when the interface is hidden. Draggable with a finger; a press that moves less than 6 pixels toggles the interface.

It is only created automatically on touch devices. On PC, force it with `MobileButton = true` or `Library:CreateMobileButton()` to test it.

```lua
Library:CreateMobileButton({ Size = 50, Position = UDim2.new(1, -70, 0, 90) })
Library:SetMobileButtonVisible(false)
```

| Option | Default | Description |
| --- | --- | --- |
| `Size` | `44` | square side in pixels |
| `Position` | `UDim2.new(0, 18, 0.5, -22)` | starting position |
