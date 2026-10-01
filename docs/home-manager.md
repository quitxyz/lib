# HomeManager

HomeManager builds the profile, live stats, game information/actions, and executor card used by the Home template. It is loaded on demand.

```lua
local HomeManager = assert(Library:LoadAddon("HomeManager"))
local home = HomeManager:Create(Window)
```

Passing a window creates a `general` tab with a `home` icon. Passing an existing tab or section mounts the cards there:

```lua
local home = HomeManager:Create(homeTab, {
    Profile = { Badge = { Text = "premium", Detail = "lifetime" } },
    Executor = { Title = "my executor", Description = "custom status" },
})
```

## Options

| Option | Default / behavior |
| --- | --- |
| `Title`, `Icon` | `general`, `home`; used when creating a tab |
| `Spacing` | `9` between cards |
| `Order` | `{ "Profile", "Stats", "Game", "Executor" }`; omitted cards are appended |
| `Profile`, `Stats`, `Game`, `Executor` | Card option tables; `false` skips creation entirely |
| `Player` | `Players.LocalPlayer` |
| `SessionStarted` | Time HomeManager was loaded, using `os.clock()` |
| `RunsValue` | `"—"`; supplied by the script; creating Home never records an execution |
| `Getters` | Map of stat IDs to getter functions; `false` disables a built-in updater |
| `Intervals` | Seconds per stat ID; friends defaults to 10, other polled stats to 1 |
| `OnError` | Optional callback for default server-action failures; otherwise uses `warn` |

Card options are passed through to the underlying components. Profile `Badge` and `Privacy` options merge with their defaults. Lists such as `Stats.Items`, `Game.Fields`, and `Game.Actions` replace the default list, so `{}` removes all entries. Input tables are copied and not modified.

`Visible = false` hides a created card; its live updates continue. Setting the entire card option to `false` avoids creating it or starting its work. `Order` controls the initial order of whole cards; afterwards use each card's `SetOrder`.

The default profile uses a neutral `preview` badge with no expiry claim. The executor name is detected when available, but support checks are owned by the script. Supply your description and colors using `Executor`. No premium status, execution count, or compatibility result is inferred.

## Returned handles

`home.Profile`, `home.Stats`, `home.Game`, and `home.Executor` are the native card APIs. Skipped cards have no handle. `home.Cards` contains the same handles by name. `home.Container` accepts additional native controls/cards. `home.Instance` is the cards container; `home.Window` is the containing window. `home.Tab` is available for a newly created or supplied tab.

```lua
home.Profile.Badge:SetText("free")
home.Profile.Badge:SetDetail("no expiry")
home.Profile.Badge:SetStyle({ ContentColor = "Accent", CornerRadius = 6 })
home.Profile:SetVisible(false)
home.Game.Actions.rejoin:SetText("join again")
home.Game.Actions.rejoin:SetCallback(function() print("custom action") end)
home.Game.Actions.copyJoinLink:SetOrder(1)
home.Game.Fields.universe:SetOrder(1)
home.Stats.Items.ping:SetOrder(1)
home.Executor:SetDescription("custom status")
home.Executor:SetIconColor(Color3.fromRGB(110, 200, 140))
home.Game:AddAction({ Id = "extra", Text = "extra", Callback = function() end })
home.Game:RemoveAction("extra")
```

`SetOrder(index)` on an action, field, or stat moves it within that component's list (one-based). Whole-card `SetOrder` sets its layout order. Existing card methods remain available.

## Live stats and game information

Default stats are players, friends in the current server, runs, session, FPS, and ping. Async stats initially display `—`; failed getter calls display `unknown` and retry at the configured interval. FPS uses a half-second frame sample. Friend lookup and game details do not block construction of the Home UI.

```lua
local home = HomeManager:Create(homeTab, {
    Getters = { ping = false }, -- manage this value yourself
    Stats = { Items = {
        { Id = "ping", Label = "ping", Icon = "wifi", Value = "manual" },
        { Id = "score", Label = "score", Value = "—",
          Getter = function() return myScore end, Interval = 2 },
    } },
})
home.Stats:Set("ping", "42ms")
```

An item's `Getter` overrides `Getters[id]`; setting it to `false` disables that item's updater. Removing an item stops its old updater after any pending getter/wait finishes. Re-adding the same ID does not attach the removed item's updater. Destroying the grid cancels all its tasks and disconnects its FPS listener immediately.

Game title and creator share one details request per Home. Explicit initial `Game.Title`/`Subtitle` values are preserved. Updates made through the card setters while the request is pending are preserved when they differ from the initial placeholder.

Default actions match the template: rejoin, server hop, join lowest server, copy join link, copy job ID, and copy universe. Server lookup examines one page of up to 100 public servers; “lowest” means lowest population within those returned results. Replace `Game.Actions` or an action's callback to use your own behavior. Clipboard and teleport failures are reported through `OnError`; no new notification is generated by HomeManager itself. Server availability and teleport acceptance remain outside the addon's control.

## Lifetime

```lua
home:Destroy()
```

Destroys the cards, disconnects listeners, and cancels Home's stat/details tasks. It removes the tab if Home created that tab. A supplied tab or section remains available. Destroying the parent also stops Home's work. Multiple Homes have independent listeners and tasks and share no execution-count side effects.

See [native cards](native-cards.md) for card options and [buttons](elements/buttons.md) for row control handles.
