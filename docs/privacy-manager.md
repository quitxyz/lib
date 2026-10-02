# PrivacyManager

This version masks the local player's username, display name, and recognizable avatar thumbnails. It does not change Player.Name, Player.DisplayName, Player.UserId, character references, dropdown selection values, or gameplay targets.

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
- hide avatar
- affect facility
- affect game

Defaults: identity masking off, both name fields and avatar masking selected, Facility selected, game UI off. Controls are unflagged and session-only in this version. Turning the master toggle off restores text. Changing any gear option refreshes affected text automatically.

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
    HideAvatar = true,
    AffectFacility = true,
    AffectGame = false,
})

local identity = PrivacyManager:GetIdentity() -- local player by default
local shownName = PrivacyManager:GetName(player)
local shownDisplayName = PrivacyManager:GetDisplayName(player)
local shownAvatar = PrivacyManager:GetAvatar(player)
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

This is best-effort text coverage, not universal identity protection: native humanoid name tags and inaccessible platform UI are not handled yet. Avatar images and local character masking are described below. There are no player-property assignments or chat callback overrides.

## Customization

```lua
PrivacyManager:BuildPrivacySection(settingsTab, 1, {
    Title = "privacy",
    Labels = {
        Enabled = "hide my identity",
        HideUsername = "hide username",
        HideDisplayName = "hide display name",
        HideAvatar = "hide avatar",
        AffectFacility = "affect facility",
        AffectGame = "affect game",
    },
})
```

BuildPrivacyTab also accepts Title and Icon. ID masking, other players, server information, custom/random identities, adapters, and replacement character identities are later steps.

## Avatar thumbnails

`hide avatar` replaces local-player `rbxthumb://` images of type AvatarHeadShot, AvatarBust, or Avatar with Roblox's neutral GUI image placeholder. The watcher handles ImageLabel and ImageButton instances, existing and newly created, using the same Facility/game switches as text. It preserves the latest original Image and restores it when disabled or unloaded. Other players, game icons, and unrelated images are unchanged. ViewportFrame models are not modified. Local character appearance is covered below.

`GetAvatar(player)` returns an avatar headshot URI, or the placeholder for the local player when Enabled and HideAvatar are true. Like the name getters, it does not apply scope switches. `ResolveImage(image, scope)` applies those switches and is used automatically by the watcher.

Opaque asset/CDN URLs (including resolved thumbnail URLs without a player ID), and custom avatar renderers cannot be reliably identified by this first image resolver and are left unchanged. The automatic coverage currently recognizes rbxthumb URIs only.

## Local character appearance

The same `hide avatar` toggle now covers the local character when `Enabled`, `HideAvatar`, and `AffectGame` are all true. The visible option is named **affect game**; its API key remains `AffectGame`, so existing calls still work.

The temporary anonymous appearance uses gray body colors, clears ordinary MeshPart/SpecialMesh body textures and classic clothing, hides body decals (including the face), and hides accessory parts and their particle/trail/beam effects. Accessories use LocalTransparencyModifier, which applies locally. No character, accessory, clothing, or mesh instances are replaced, destroyed, or reparented. Rig geometry, joints, Humanoid, animation objects, tools, movement, and targeting references remain intact.

Original visual property values are tracked per instance. External updates become the latest originals while masking is active. Turning off identity privacy, hide avatar, or affect game restores those values; unload does the same and disconnects listeners. The manager follows CharacterAdded/CharacterRemoving, restores the old character, and watches new descendants on each respawn. Facility-only privacy does not mask the character.

This is a neutral visual treatment, not a complete generic avatar replacement. Body silhouettes remain recognizable. SurfaceAppearance/PBR textures, custom character renderers, and ViewportFrame models may retain visual details and are not covered by this version. Predefined anonymous characters, chosen custom appearances, and random identity appearances are later work. Changes are made on the local client and do not change what other players see.
