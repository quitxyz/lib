# PrivacyManager

This version masks the local player's username, display name, user ID, and recognizable avatar thumbnails. It does not change Player.Name, Player.DisplayName, Player.UserId, character references, dropdown selection values, or gameplay targets.

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
- hide user ids
- affect facility
- affect game

Defaults: identity masking off, both name fields, avatar masking, and user ID masking selected, Facility selected, game UI off. Controls are unflagged and session-only in this version. Turning the master toggle off restores text. Changing any gear option refreshes affected text automatically.

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
    HideUserIds = true,
    AffectFacility = true,
    AffectGame = false,
})

local identity = PrivacyManager:GetIdentity() -- local player by default
local shownName = PrivacyManager:GetName(player)
local shownDisplayName = PrivacyManager:GetDisplayName(player)
local shownAvatar = PrivacyManager:GetAvatar(player)
local shownId = PrivacyManager:GetUserId(player)
local text = PrivacyManager:ResolveText("teleport to RealName", "facility", false)

PrivacyManager:Refresh()
PrivacyManager:Restore() -- disable masking and restore text
PrivacyManager:Destroy() -- restore, disconnect, remove owned panels
```

The local anonymous replacement defaults to `seized.cc/1`. SetAnonymous can change the prefix (for example `player ` produces `player 1`). GetIdentity returns a new table containing Name, DisplayName, and a display UserId (0 when local ID masking is enabled). Name getters reflect field toggles and the master switch; ResolveText additionally respects the requested scope (facility/game). Other players are unchanged in this first version. Never use a masked name as a gameplay identifier.

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
        HideUserIds = "hide user ids",
        AffectFacility = "affect facility",
        AffectGame = "affect game",
    },
})
```

BuildPrivacyTab also accepts Title and Icon. Other players, server information, account-backed/random identities and a general adapter registry are later steps. Explicit preview registration is available below.

## Avatar thumbnails

`hide avatar` recognizes local-player `rbxthumb://` images of type AvatarHeadShot, AvatarBust, or Avatar. It hides that image and adds an owned ViewportFrame containing a white classic character with the Smile face. Headshot, bust, and full-avatar requests get different camera framing. Headshots use a close crop centered on the face; both the portrait and character use a classic head mesh scale of 1.25. This covers the recognized thumbnails in Facility and accessible Roblox/game menus, without replacing them with a flat face texture. Existing image backgrounds remain untouched; corner styling is copied when the preview is built. The original image returns and the preview is destroyed on disable/unload. Other players, game icons, and unrelated images remain unchanged.

`GetAvatar(player)` returns an avatar headshot URI, or the classic face texture for the local player when Enabled and HideAvatar are true. Like the name getters, it does not apply scope switches. `ResolveImage(image, scope)` applies those switches. The automatic watcher uses this to recognize masking, then renders the 3D preview; these low-level getters still return the face texture URI, not a generated thumbnail URL.

Opaque asset/CDN URLs (including resolved thumbnail URLs without a player ID), and custom avatar renderers cannot be reliably identified by this first image resolver and are left unchanged. The automatic coverage currently recognizes rbxthumb URIs only.

## Local character appearance

The same `hide avatar` toggle now covers the local character when `Enabled`, `HideAvatar`, and `AffectGame` are all true. The visible option is named **affect game**; its API key remains `AffectGame`, so existing calls still work.

The anonymous appearance uses white body colors, clears ordinary MeshPart/SpecialMesh body textures and classic clothing, hides original body decals and the original Head, then renders an owned classic head in its place, and hides accessory parts and their particle/trail/beam effects. Accessories use LocalTransparencyModifier, which applies locally. No existing character, accessory, clothing, or mesh instances are replaced, destroyed, or reparented. The addon destroys only its own visual head and preview objects when masking stops. The visual head has no collision, touch, or query behavior; it follows the real Head each rendered frame, including its camera transparency. The original Head and its joints remain intact. Rig geometry, joints, Humanoid, animation objects, tools, movement, and targeting references remain intact.

Original visual property values are tracked per instance. External updates become the latest originals while masking is active. Turning off identity privacy, hide avatar, or affect game restores those values; unload does the same and disconnects listeners. The manager follows CharacterAdded/CharacterRemoving, restores the old character, and watches new descendants on each respawn. Facility-only privacy does not mask the character.

This is a neutral visual treatment, not a complete generic avatar replacement. Body silhouettes remain recognizable. SurfaceAppearance/PBR textures, custom character renderers, and unidentifiable ViewportFrame models may retain visual details. Recognized previews are covered as described below. Chosen custom appearances and random identity appearances are later work. R15 rigs keep their current geometry; this does not convert them to R6. Changes are made on the local client and do not change what other players see.

## Gear height

```lua
PrivacyManager:BuildPrivacySection(settingsTab, 1, { GearMaxHeight = 160 })
```

GearMaxHeight is optional and also works with BuildPrivacyTab. It caps the popup's total height and enables vertical wheel/touch scrolling when needed. Omit it for the previous natural-height behavior. The popup continues opening downward.

## Displayed user IDs

`HideUserIds` replaces the local player's decimal UserId with `0` in presentation text, using the same Facility/game scope switches and RichText handling as names. It is selected by default; the master privacy switch remains off by default. `GetUserId(player)` returns the display ID as a number and does not apply scope switches, matching the identity getters. GetIdentity also returns this display ID. Always use the real Player.UserId for gameplay, thumbnail lookup, and identity targeting.

The generic matcher changes complete tokens only: `user id: 123` becomes `user id: 0`, while `1234`, `x123`, and `123_x` remain unchanged. RichText attributes, editable TextBoxes, registered selection values, and underlying game data are untouched. Existing console display, exports, and newly forwarded script logs use the shared resolver automatically. Originals are restored on disable/unload. A matching unrelated standalone number cannot be distinguished from a user ID in generic text and will also be masked. This option does not hide place, universe, or job IDs.

## Anonymous identity

The first completed identity preset uses `seized.cc/1` for both names, displayed ID `0`, and a white appearance with the classic black face. Recognized profile images render a matching classic head/body in a ViewportFrame. The original thumbnail Image is restored when masking stops.

```lua
PrivacyManager:SetAnonymous({ Prefix = "player " }) -- player 1
local identity = PrivacyManager:GetAnonymousIdentity()
-- Name, DisplayName, UserId, Avatar, Appearance.BodyColor, Appearance.Face
```

The returned identity is a fresh table, including a fresh Appearance table. Changing it does not modify the manager. Prefix accepts plain text up to 64 bytes (no control characters or angle brackets), and updates existing masked text immediately. The local identity reserves number 1; masking/numbering other players is a later step. This is a display label, so punctuation such as `seized.cc/` does not need to be a valid Roblox username.

For automatic 3D portraits, keep the real avatar thumbnail URI in the ImageLabel/ImageButton and let the watcher resolve it. GetAvatar returns a texture URI only. Manual custom identities are supported below. Badge application and randomised identities are not implemented yet.

The face uses image texture 144080495, verified from Roblox's Smile face asset (144075659). The catalog face asset contains a Decal; its texture ID is the image used for both GUI images and character decals. The addon applies the face to its own classic head with Transparency 0. This avoids depending on the bundled `rbxasset://textures/face.png` path. The texture still requires Roblox asset loading; no automated mock test can verify its rendering on a particular device.

### Native avatar inspection

Recognized thumbnail images in the player-list popup use the replacement preview. The full native **Examine Avatar** viewer can independently load an account's HumanoidDescription or create a separate 3D model. This version does not intercept that viewer's data requests or rewrite arbitrary native ViewportFrame models. It therefore cannot guarantee masking inside the full inspection viewer. It does not modify the account's actual avatar.


## Character previews in game and Facility UI

Existing and newly created Models inside watched ViewportFrames share the character appearance controller. Automatic recognition requires a direct Humanoid plus either a `UserId`, `PlayerUserId`, or `OwnerUserId` attribute matching the local player's ID, or an exact model name matching the real username or numeric user ID. An explicit ID attribute takes precedence over the name. Display names alone are not used because they are not unique. Models belonging to other players and unrelated units are left alone.

The existing `Enabled`, `HideAvatar`, `AffectGame`, and `AffectFacility` switches control previews too. Toggles refresh open previews; new accessories, clothing, and heads are watched. Preview accessory parts use `Transparency`, while world accessories retain `LocalTransparencyModifier`. The model's pose, animation objects, camera, and real identity metadata are preserved. The latest captured visual properties are restored on disable, scope changes, or unload. A model already cloned from a masked character has masked source properties: restoring it cannot recover clothing data that was absent before the watcher saw it; the game must rebuild that preview from the original appearance.

For unnamed previews, a game adapter can explicitly bind the model:

```lua
PrivacyManager:WatchRoot(LocalPlayer.PlayerGui, "game")
local unregister = PrivacyManager:RegisterPreview(previewModel, LocalPlayer)
-- Call RegisterPreview again for each replacement model created by the menu.
-- Optional: remove this explicit binding (automatic recognition still applies).
unregister()
```

Registration handles only local-player models for now. Destroying a registered model releases its watchers. This API does not guess UI paths or intercept avatar-loading requests. Native inspection models are covered only if accessible and identifiable, or explicitly registered. Anonymous portraits generated by PrivacyManager are excluded from this watcher.


## Custom identity editor

Select **custom**, open **edit custom identity**, enter a username, display name and numeric user ID, then press **apply identity**. User identity must be enabled; existing hide and scope toggles still control each replacement. Changes are presentation-only and do not alter the real player or account.

Appearance supports **anonymous** (the white classic appearance) and **keep mine** (restore the real thumbnails and character appearance while retaining text privacy). Switching back to anonymous restores the anonymous identity. Disabling privacy restores the original visuals.

Draft edits only apply after pressing the button. Closing and reopening keeps the draft during the panel lifetime; this editor does not persist it to disk. Account loading is available as described below. Badge choices are preview-only and do not apply badges to game or Facility visuals yet.

The manual API accepts partial updates:

```lua
PrivacyManager:SetCustom({
    Name = "example",
    DisplayName = "example display",
    UserId = 123,
    Appearance = "keep mine", -- or "anonymous"
})
PrivacyManager:SetMethod("custom")
PrivacyManager:SetOptions({ Enabled = true })

local identity = PrivacyManager:GetCustom() -- defensive copy
```

SetCustom validates all supplied fields before applying any changes. Names must be nonblank plain text up to 64 bytes; IDs must be non-negative integers within the safe numeric range. Setting custom values does not automatically enable privacy or switch the method.

Generic text containing identical real username/display-name tokens uses the username replacement because their meaning cannot be distinguished from text alone. Typed identity getters preserve the distinction.

BuildPrivacySection accepts EditorWidth (default 420) and EditorHeight (default 0.86). Its panel exposes CustomEditor, EditorControls and Draft. The editor itself is excluded from privacy replacement so its labels and draft preview remain readable. Destroying the panel destroys its editor.

The gear retains hide and scope toggles. Capped gear popups and dropdowns open downward and shrink to available screen height, with scrolling for overflow.

## Load a custom Roblox account

Enter a username (optionally beginning with @) or numeric user ID, then press **load account**. The editor fills in the account username, display name and ID, and selects **loaded account** appearance. Loading only updates the draft. Edit any fields and press **apply identity** to activate the selected custom identity.

The selected appearance stays linked to the loaded account even if you override the displayed user ID. Anonymous and keep mine remain available. Lookup or asset-loading failures appear in the editor and retain the current applied identity.

API usage:

```lua
local identity = PrivacyManager:LoadAccount("seized_cc") -- yields; may error
PrivacyManager:SetCustom(identity)
PrivacyManager:SetMethod("custom")
```

LoadAccount returns Name, DisplayName, UserId, AccountId and Appearance. AccountId selects the loaded appearance independently of the displayed UserId. R6 and R15 appearance templates are loaded once per chosen account and released when the manager is destroyed.

Recognised thumbnails preserve their original thumbnail type and resolution while switching the account ID. Live characters and recognised/registered game preview rigs receive a separate local visual model. Its body parts follow the original rig and accessories follow their attachment body parts. Original character references, joints and physics remain intact; disabling masking removes the visual model and restores the tracked properties.

Matching R6/R15 body parts are required. Custom rigs, unusual accessory attachments and differences in body proportions can require a game adapter. Native avatar inspection that independently fetches account data remains subject to the existing accessible/identifiable preview coverage.
