# Interface manager

`Library.InterfaceManager:Create(tab, options)` creates the customizable settings preset.

```lua
local interface = Library.InterfaceManager:Create(settingsTab, {
    Window = Window,
    SettingsFolder = "seized/settings",
    ResetFolder = "seized",

    AutoExecute = {
        URL = "https://raw.githubusercontent.com/OWNER/REPO/main/loader.lua",
        Default = false,
        CarryGlobals = { "seizedExecutions" },
    },

    OnError = function(message)
        console:Warn(message)
    end,
})
```

Replace the example URL with your published script's loader. It must load your script, not just the UI library. No URL is inferred from the library import.

## Included controls

- **show ui on load**: defaults to on. Changes affect the next script launch; toggling it does not hide the current window.
- **auto execute**: defaults to off. Runs the configured loader after teleporting; it does not start with Roblox.
- **notifications**: right or none.
- **ui scale**: 60–140%.
- **ui opacity**: 20–100%.
- **menu bind**: defaults to RightShift.
- **unload**: unloads immediately.
- **reset**: opens a choice panel. **reset interface** restores creation defaults (always disabling auto execute) and saves them without deleting themes or game configs. Changes apply immediately except show-on-load, which applies next launch. **delete everything** is only included when `ResetFolder` names a script-owned root folder. Asks for confirmation, uses the theme danger color, deletes that folder and its memory fallback entries, then unloads. A deletion failure keeps the UI running.

Keybind menu and watermark controls are deferred.

## Settings and customization

Preferences automatically save to `SettingsFolder/interface.json`. The default folder is `Facility/settings`, or the folder supplied through legacy `SetFolder` plus `/settings`. Stored valid preferences override defaults. Invalid saved values are ignored. Without native file functions, the library's memory fallback only lasts for that library instance.

These controls use `Flag = false` by default because interface preferences are independent of game configs. Provide `Flags = { Scale = "uiScale", ... }` only if you also want SaveManager to register those controls. Loading those registered values also updates the interface preferences.

```lua
local interface = Library.InterfaceManager:Create(settingsTab, {
    Title = "interface",
    Column = 1,
    SettingsFolder = "seized/settings",
    Controls = { AutoExecute = false, Reset = false },
    Labels = { ShowOnLoad = "show menu on launch", Unload = "close script" },
    Defaults = {
        ShowOnLoad = true,
        Notifications = "right",
        Scale = 100,
        Opacity = 100,
        MenuBind = "RightShift",
    },
})
```

Control keys are `ShowOnLoad`, `AutoExecute`, `Notifications`, `Scale`, `Opacity`, `MenuBind`, `Unload`, and `Reset` (`HardReset = false` remains accepted). Labels use the same keys, plus `ShowOnLoadHint`, `AutoExecuteHint`, `ResetPrompt`, `ResetConfirm`, `Reset`, `ResetHelp`, `ResetInterface`, and `Cancel`.

Returned handles: `Section`, `Instance`, `Controls`, `Settings`, `SettingsPath`, and `Alive`. Controls retain their ordinary component methods. `ResetInterface()` restores and saves interface defaults; it returns success and storage mode/error. `ResetModal` exposes the reset choice panel. `Save()` returns success and storage mode/error; `Destroy()` removes this section and its listeners. Unloading or destroying its parent cleans up automatically.

## Auto execute

Supply exactly one of `AutoExecute.URL` (HTTPS) or `AutoExecute.Code` (loader source string). The toggle is disabled, with a help hint, when no loader or queue teleport function is available.

```lua
AutoExecute = {
    Code = [[
        -- your loader
    ]],
    Default = false,
}
```

The manager listens for the local player's teleport-start event and queues only if enabled. It queues at most once per instance after a successful queue call, avoiding duplicate submissions. Failed queue calls can retry on a subsequent teleport-start event. Closing the UI does not disable auto execute; destroying the section disconnects future queuing.

A previously queued script cannot be universally removed: executors differ in whether they retain or consume their queue after a failed teleport. When native storage is available, the queued loader checks the saved preference and skips execution if it was subsequently turned off. Real teleport behavior still needs testing in your executor.

`CarryGlobals` optionally copies named, JSON-serializable `getgenv()` values at departure and restores them before the loader. For the template's execution count, use `{ "seizedExecutions" }`. The manager does not increment the count. Keep incrementing once in your script; remove a separate counter-transfer queue when this manager handles auto execution. If you still need count transfer while auto execute is disabled, that separate behavior must be retained.

Errors go to `OnError(message)` when supplied, otherwise `warn`; no extra notifications are created.

## Legacy API

`SetLibrary`, `SetWindow`, `GetWindow`, `SetFolder`, and `BuildInterfaceSection(tab, column)` remain available. The legacy builder retains its old menu-key, 70–130% scale, hotkeys, and unload-confirmation layout. It does not use the new automatic preference storage.

For flash-free setup, create the window with `Visible = false`. InterfaceManager applies the saved scale before showing the window according to show-on-load. Omitting `Visible` preserves the window’s default visible behavior.
