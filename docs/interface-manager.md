# Interface manager

`Library.InterfaceManager` builds the settings section for the interface itself.

```lua
local InterfaceManager = Library.InterfaceManager

InterfaceManager:SetLibrary(Library)
InterfaceManager:SetWindow(Window)
InterfaceManager:SetFolder("Facility")
InterfaceManager:BuildInterfaceSection(Settings, 1)
```

## Section contents

| Element | Effect |
| --- | --- |
| `menu key` | toggle key, applied immediately |
| `ui scale` | scale from 70% to 130% |
| `unload` | `Library:Destroy()` |

## Persistence

None. These settings live in memory for the session and nothing is written to disk, so nothing applies itself on the next launch.

## Separation from configurations

The flags of this section (`interface_menu_key`, `interface_scale`) are listed in `InterfaceManager.Flags`. `SaveManager:IgnoreThemeSettings()` adds them to the ignore list: they are never saved, never overwritten when a configuration loads, and never raise the unsaved changes indicator.
