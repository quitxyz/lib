# PrivacyManager

This first version masks the local player's username and display name in presentation text. It does not change Player.Name, Player.DisplayName, Player.UserId, character references, dropdown selection values, or gameplay targets.

## Setup

Load once after importing the library, preferably before building the window:

```lua
local PrivacyManager = assert(Library:LoadAddon("PrivacyManager"))

-- After creating settingsTab:
local privacy = PrivacyManager:BuildPrivacySection(settingsTab, 1)
```

The section contains **user identity**, with a gear for:
- hide username
- hide display name
- affect facility
- affect game ui

Defaults: identity masking off, both name fields selected, Facility selected, game UI off. Controls are unflagged and session-only in this version. Turning the master toggle off restores text. Changing any gear option refreshes affected text automatically.

Alternatively:

```lua
local privacy = PrivacyManager:BuildPrivacyTab(Window)
```

Both builders return a panel with Section, Instance, Controls, Alive, and Destroy(). BuildPrivacyTab also returns Tab on that panel. Multiple panels reflect the same manager options. Destroying a panel removes its controls; call Restore or Destroy on the manager to stop masking.

## Resolver

```lua
PrivacyManager:SetOptions({
    Enabled = true,
    HideUsername = true,
    HideDisplayName = true,
    AffectFacility = true,
    AffectGame = false,
})

local identity = PrivacyManager:GetIdentity() -- local player by default
local shownName = PrivacyManager:GetName(player)
local shownDisplayName = PrivacyManager:GetDisplayName(player)
local text = PrivacyManager:ResolveText("teleport to RealName", "facility", false)

PrivacyManager:Refresh()
PrivacyManager:Restore() -- disable masking and restore text
PrivacyManager:Destroy() -- restore, disconnect, remove owned panels
```

The local replacement is always `player 001`. GetIdentity returns a new table containing Name, DisplayName, and the unchanged UserId. Name getters reflect field toggles and the master switch; ResolveText additionally respects the requested scope (facility/game). Other players are unchanged in this first version. Never use a masked name as a gameplay identifier.

SetLibrary(Library) is accepted for consistency; a loaded manager belongs to its creating library and cannot be moved to another instance. Library:LoadAddon caches it. Destroy releases that cached instance so it may be loaded again.

## Facility integration

The library registers its GUI roots automatically, including windows, floating panels, notifications, and later-created GUI roots. One shared watcher applies the resolver to TextLabel and TextButton text. Dropdown callbacks and stored selections continue using the real option values.

Console display uses this same watcher. Console copy/save and forwarded native script messages use the same resolver; there are no separate privacy toggles for these outputs. Console history remains original, so GetEntries returns original messages. Turning privacy off reveals originals again; exported files and already-forwarded native messages cannot be retrospectively changed.

The generic resolver uses literal, case-sensitive, whole-name matches, handles longer overlapping names first, and never reprocesses generated replacements. RichText tag attributes are preserved. A name split across multiple RichText tags is not matched. Identical usernames/display names in generic text cannot be distinguished by meaning; either enabled matching field can mask them.

## Game UI coverage

When enabled for the first time, the manager scans PlayerGui, accessible CoreGui, and Workspace once, watches new descendants, and listens for text changes. This covers ordinary labels/buttons, including those inside billboards and SurfaceGuis. It does not scan every frame.

Each text element retains its latest original text plus its last rendered replacement. External updates replace that original; toggling privacy off restores it. Editable TextBoxes are intentionally excluded to preserve input and command values. Other scripts that continually rewrite the same label may conflict with masking. If a game uses visible label text itself as gameplay input, it needs an adapter before enabling that coverage.

This is best-effort text coverage, not universal identity protection: native humanoid name tags, inaccessible platform UI, images, thumbnails, and avatar appearance are not handled yet. There are no player-property assignments or chat callback overrides.

## Customization

```lua
PrivacyManager:BuildPrivacySection(settingsTab, 1, {
    Title = "privacy",
    Labels = {
        Enabled = "hide my identity",
        HideUsername = "hide username",
        HideDisplayName = "hide display name",
        AffectFacility = "affect facility",
        AffectGame = "affect game ui",
    },
})
```

BuildPrivacyTab also accepts Title and Icon. Avatar/ID masking, other players, server information, custom/random identities, adapters, and character appearance are later steps.
