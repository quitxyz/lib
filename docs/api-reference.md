# API reference

## Library

| Method | Description |
| --- | --- |
| `Library:Window(opts)` | creates a window |
| `Library:Notify(opts \| title, text, duration)` | notification |
| `Library:Warn / :Error / :Success(title, text, duration)` | styled notifications |
| `Library:SetToggleKey(key)` | toggle key: key name, `KeyCode` or `MB1`–`MB3` |
| `Library:ToggleUI(state)` | toggles or forces visibility |
| `Library:CreateMobileButton(opts)` | floating touch button |
| `Library:SetMobileButtonVisible(bool)` | shows or hides that button |
| `Library:PreloadIcons()` | loads the icon table |
| `Library:LoadAddon(name)` | loads an addon, locally or over HTTP |
| `Library:Repaint()` | reapplies the palette to existing instances |
| `Library:BuildFolders(folder)` | creates `<folder>/configs` and `<folder>/settings` |
| `Library:GetConfig(ignore)` | `flag = value` table |
| `Library:LoadConfig(data, ignore)` | applies a table of values |
| `Library:CaptureDefaults()` | snapshot of current values |
| `Library:ResetDefaults(ignore)` | restores that snapshot |
| `Library:Register(flag, entry)` | manual registration |
| `Library:MarkDirty(flag)` / `:ClearDirty()` | unsaved changes indicator |
| `Library:Destroy()` | full unload |

### Fields

| Field | Contents |
| --- | --- |
| `Library.Flags` | raw values indexed by flag |
| `Library.Registry` | `{ Type, Get, Set }` per flag |
| `Library.Defaults` | snapshot of default values |
| `Library.Theme` | palette |
| `Library.ToggleKey` / `ToggleInput` | current toggle key |
| `Library.NotificationsEnabled` | enables or mutes notifications |
| `Library.Open` | interface visible |
| `Library.Windows` | created windows |
| `Library.SaveManager` / `InterfaceManager` / `ThemeManager` | managers |
| `Library.BaseUrl` | root for remote addons |
| `Library.AddonPaths` | addon name to file path |
| `Library.Addons` | already loaded addons |
| `Library.FileSystem` | file reading and writing |

## Registry types

| Type | Stored value |
| --- | --- |
| `Toggle` | boolean |
| `Dropdown` | string |
| `MultiDropdown` | table of strings |
| `Slider` | number |
| `Keybind` | string, `""` when no key |
| `Input` | string |
| `ColorPicker` | `#RRGGBBAA` string |

## Registering a value by hand

```lua
Library:Register("my_flag", {
    Type = "Toggle",
    Get = function() return myState end,
    Set = function(value) myState = value end,
})
```

Useful for saving state that does not come from a UI element.

## Executor functions used

| Function | Purpose | Missing? |
| --- | --- | --- |
| `writefile`, `readfile`, `isfile` | configurations | in-memory fallback |
| `listfiles`, `delfile` | listing and deletion | in-memory fallback |
| `makefolder`, `isfolder` | folder tree | ignored |
| `setclipboard`, `getclipboard` | copy and paste | buttons inactive |
| `gethui`, `syn.protect_gui` | GUI parenting | falls back to `CoreGui` then `PlayerGui` |
| `game:HttpGet` | addon loading | addons unavailable |
# Native card extension

See [Native cards](native-cards.md) for `Tab:Cards`, `ProfileCard`, `MediaCard`,
`StatusCard`, and `StatGrid`, including all implemented options and setters.
`tab.Page` remains the native scrolling-frame property; it is not a constructor.
