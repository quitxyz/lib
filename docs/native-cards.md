# Native cards

These APIs are implemented in `main.luau`. They render reusable content, not a
hardcoded Home tab. Your script owns player/game data, timers, clipboard access,
and button callbacks. Existing window show/hide animation is unchanged.

## Containers

```lua
local tab = Window:Tab("general", "home")
local cards = tab:Cards({ Spacing = 9 })
local profile = cards:ProfileCard({
    Eyebrow = "Welcome back,",
    Title = "quit",
    Subtitle = "@quit_xyz",
    Image = "rbxthumb://type=AvatarHeadShot&id=1&w=150&h=150",
    Badge = { Text = "Preview", Detail = "Home prototype" },
})
```

Use `tab:Cards()`, **not** `tab:Page()`: `tab.Page` already holds the native
scrolling frame. Each call creates a new full-width, headerless vertical group.
Cards can also be created inside an ordinary section:

```lua
local section = tab:Section("Account", 1)
local profile = section:ProfileCard({ Title = "Account", Privacy = false })
```

All four constructors belong to the shared element API, so other native element
containers can use them too. Cards use the width of their own container.

## Common card handle

`ProfileCard`, `MediaCard`, `StatusCard`, and `StatGrid` return:

| Member | Purpose |
| --- | --- |
| `Instance` | Root frame |
| `SetVisible(boolean)` | Hide/show the entire card |
| `SetOrder(number)` | Change its layout order in the parent |
| `Refresh()` | Recompute layout after intentional raw property edits |
| `Destroy()` | Destroy descendants and disconnect card listeners/repaint hooks |

Profile, media, and status options also support `Order`, `Padding` (14),
`CornerRadius` (7), `Borderless` (false), `BackgroundColor` ("Section"),
and `BorderColor` ("SectionBorder"). Their handles support
`SetCornerRadius(number)`. Cards in a group are ordered by creation by default.
When mixing ordinary elements and cards, assign explicit `LayoutOrder` values
to ordinary elements and use `SetOrder` on cards for precise ordering.

Colors accept a theme key or a Roblox `Color3`. Theme-key colors follow repaint;
custom colors stay custom. Radii, padding, and offsets are unscaled UI pixels.

## ProfileCard(options)

| Option | Default / behavior |
| --- | --- |
| `Title`, `Subtitle`, `Eyebrow` | Optional text; empty/nil hides that line |
| `TitleColor`, `SubtitleColor`, `EyebrowColor` | TextBright, Text, TextDim |
| `Image` | Image URI |
| `AvatarSize` | 64 |
| `AvatarRadius` | 1000 (circle); 0 gives square corners |
| `CompactWidth` | 510; below this width the badge stacks beneath identity |
| `Spacing` | 10 between major rows |
| `HideName`, `HideAvatar` | Initial privacy state, false |
| `Badge` | Options table below, or false to hide |
| `Privacy` | Options table below, or false to hide the controls |

Badge options: `Visible`, `Text` ("Preview"), `Icon` ("sparkles"),
`Detail`, `Width` (128), `CornerRadius` (17), `BackgroundColor` ("Group"),
`BorderColor` ("Accent"), `ContentColor` ("AccentSoft"),
`DetailColor` ("TextDim"), `DetailAlignment` ("Left", "Center", or "Right";
default "Right"), `DetailOffset` (`Vector2.new(0, 0)`).
The detail is below the pill in both layouts. Use alignment before arbitrary
offsets; large offsets can intentionally move text outside the badge bounds.

Privacy options: `Visible` (true), `Alignment` ("Right"),
`CompactAlignment` ("Fill"), `Width` (300).
Alignment values are "Left", "Center", "Right", and "Fill".
Fill uses all available padded width and ignores Width. Privacy controls always
occupy their own row below the identity/badge area.

### Runtime changes

```lua
profile:SetTitle("New name")
profile:SetSubtitle("@new")
profile:SetEyebrow("Good evening,")
profile:SetImage("rbxassetid://123")
profile:SetAvatarRadius(8)
profile:SetAvatarVisible(false) -- removes the avatar's layout space
profile.Eyebrow:SetVisible(false)
profile.Subtitle:SetColor("AccentSoft")

profile.Badge:SetText("Premium")
profile.Badge:SetDetail("Lifetime")
profile.Badge:SetStyle({
    BackgroundColor = "Field",
    BorderColor = Color3.fromRGB(180, 140, 200),
    ContentColor = "TextBright",
    CornerRadius = 8,
    DetailColor = "AccentSoft",
    DetailAlignment = "Left",
    DetailOffset = Vector2.new(0, 0),
})
profile.Badge:SetCornerRadius(12)
profile.Badge:SetVisible(false)
profile.Privacy:SetAlignment("Center", true) -- true selects compact alignment
profile.Privacy:SetVisible(false)
```

`Title`, `Subtitle`, `Eyebrow`, and `Badge.Detail` expose
`Instance`, `SetText(value)` (alias `Set`), `SetColor(value)`, and
`SetVisible(boolean)`. Empty text collapses; SetText with nonempty text shows it.
Use top-level SetTitle/SetSubtitle to preserve the real identity while hidden.

### Privacy controls in another tab

```lua
profile.Privacy:SetVisible(false)
settingsSection:Toggle({
    Text = "Hide name",
    Callback = function(value) profile.HideName:Set(value) end,
})
settingsSection:Toggle({
    Text = "Hide avatar",
    Callback = function(value) profile.HideAvatar:Set(value) end,
})
```

`HideName` and `HideAvatar` each expose `Set(boolean)` and `Get()`.
Hiding the avatar for privacy preserves its space; SetAvatarVisible(false)
removes that space. External toggles control the profile but are not automatically
two-way-bound or saved; use the existing native flag/save system for persistence.

## MediaCard(options)

Optional `Title`, `Subtitle`, `Description`, `Image`, `Icon`, `Fields`,
and `Actions`. Icon takes precedence over Image. `ImageSize` defaults to 64,
`ImageRadius` to 7, `Spacing` to 8, and `CompactWidth` to 570.
On wide containers, actions appear on the right; below the breakpoint they stack
under the information. Fields use two columns and actions use two slots per row.

```lua
local gameCard = cards:MediaCard({
    Title = "Experience",
    Subtitle = "by Creator",
    Description = "Job abc…123",
    Image = "rbxassetid://123",
    Fields = {
        { Id = "place", Label = "Place ID", Value = "123" },
        { Id = "universe", Label = "Universe ID", Value = "456" },
    },
    Actions = {
        { Id = "rejoin", Text = "Rejoin", Callback = function() end },
        { Id = "copy", Text = "Copy ID", Callback = function() end },
        { Id = "lowest", Text = "Join Lowest Server", Span = 2, Callback = function() end },
    },
})
```

Each field/action requires a unique `Id` within its collection. Actions accept
`Enabled` (true), `Span` (1 or 2), and `Callback`. Callbacks go through the
library's SafeCallback; no networking or server actions are built into these cards.

```lua
gameCard:SetTitle("Changed")
gameCard:SetSubtitle("by Another creator")
gameCard:SetDescription("") -- removes the line
gameCard:SetImage("")       -- removes the image
gameCard:SetImageRadius(12)
gameCard:SetField("place", "789")

gameCard:AddField({ Id = "version", Label = "Version", Value = "1.2" })
gameCard:RemoveField("universe")
gameCard:AddAction({ Id = "joinLink", Text = "Copy Join Link", Callback = copyJoinLink })
gameCard.Actions.lowest:SetSpan(1) -- permits a following button alongside it
gameCard:RemoveAction("rejoin")
```

`Fields[id]` exposes `Instance`, `Label`, `Value`, `Set(value)`,
and `SetVisible(boolean)`. Label and Value have the text-handle methods above.
`Actions[id]` exposes `Instance`, `SetText`, `SetEnabled`, `SetVisible`,
and `SetSpan`. Removal is permanent; hiding preserves the handle and collapses
its space. Removed IDs can be reused. Hidden actions/fields are excluded from layout.

## StatusCard(options)

A compact MediaCard wrapper for `Title`, `Description`, optional `Icon`
or `Image`, and common card styling. ImageSize defaults to 32.
Returns the MediaCard handle (including SetTitle, SetDescription, and SetImage).

```lua
local status = cards:StatusCard({
    Title = "Runtime",
    Description = "Ready",
    Icon = "shield-check",
})
status:SetDescription("Connected")
```

## StatGrid(options or items)

```lua
local stats = cards:StatGrid({
    Spacing = 8,
    Items = {
        { Id = "players", Label = "Players", Value = "3/20", Icon = "users" },
        { Id = "fps", Label = "FPS", Value = 60, Icon = "gauge" },
    },
})
stats:Set("fps", 144)
stats:Add({ Id = "ping", Label = "Ping", Value = "30ms", Icon = "wifi" })
stats.Items.ping:SetVisible(false)
stats:Remove("players")
```

A plain array of items is also accepted. Each item requires a unique Id and accepts
Label, Value, Icon, LabelColor, and ValueColor. Grid options:
`Columns` (optional fixed positive count), `Spacing` (8),
`CornerRadius` (7, per cell), `Order`.
Automatic column counts: 2 below 440 px, 3 from 440 to 749 px, 6 from 750 px.
Cells are 76 px tall. An empty grid has zero height.
`Items[id]` exposes Instance, Label, Value, Set(value), SetVisible(boolean).

## Layout and compatibility notes

- Existing components and window animations are unchanged.
- Width-based layout changes are deferred/coalesced and use logical (unscaled)
  container width. Scale-only frames with unchanged logical width are skipped.
- Text sizes are fixed; text is single-line and truncated rather than auto-scaled.
- Hidden profile lines, badge, controls, media lines, fields, and actions reflow.
- Reorder whole cards with SetOrder; reorder fields/actions by removing and re-adding.
- Named layout presets, arbitrary child slots, drag-and-drop ordering, target/HP
  cards, console, and watermark are **not included** in this update.
- This is a native API implementation, not a converted Home showcase. The existing
  test Lua remains unchanged. Confirm rendering and toggle animation in Roblox
  before treating the migration as visually complete.
