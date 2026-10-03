-- Facility addon | PrivacyManager
-- Presentation-only player identity masking. Real player references stay untouched.
return function(Library)
    if Library.PrivacyManager and Library.PrivacyManager.Alive then return Library.PrivacyManager end
    local Players = game:GetService("Players")
    local RunService = game:GetService("RunService")
    local LocalPlayer = Players.LocalPlayer
    assert(LocalPlayer, "PrivacyManager requires a local player")
    local manager = { Alive = true, Options = {
        Enabled = false, HideUsername = true, HideDisplayName = true, HideAvatar = true, HideUserIds = true,
        AffectFacility = true, AffectGame = false, Method = "anonymous",
    } }
    manager.PlayerOptions = {
        Enabled = false, HideUsername = true, HideDisplayName = true, HideAvatar = true, HideUserIds = true,
        AffectFacility = true, AffectGame = false, Method = "anonymous",
    }
    Library.PrivacyManager = manager
    local watched, roots, connections, panels = {}, {}, {}, {}
    local anonymousPrefix = "seized.cc/"
    local anonymousName = anonymousPrefix .. "1"
    local anonymousAvatar = "rbxassetid://144080495"
    local anonymousColor = Color3.fromRGB(255, 255, 255)

    local identityList, identitiesById, activePlayers, activeById = {}, {}, {}, {}
    local textRules = {}
    local nextIdentity = 2
    local function isLocal(player) return not player or player.UserId == LocalPlayer.UserId end
    local function optionsFor(player) return isLocal(player) and manager.Options or manager.PlayerOptions end
    local function scopeEnabled(options, scope)
        return options.Enabled and (scope == "game" and options.AffectGame
            or scope ~= "game" and options.AffectFacility)
    end
    local function rememberIdentity(player)
        local record = identitiesById[player.UserId]
        if not record then
            record = { UserId = player.UserId, Index = isLocal(player) and 1 or nextIdentity }
            if not isLocal(player) then nextIdentity = nextIdentity + 1 end
            identitiesById[player.UserId] = record
            table.insert(identityList, record)
        end
        if record.Name ~= player.Name or record.DisplayName ~= player.DisplayName then
            record.Name, record.DisplayName = player.Name, player.DisplayName
            textRules = {}
        end
        return record
    end

    local imageNodes = {}
    local custom = { Name = "seized", DisplayName = "seized", UserId = 0, Appearance = "anonymous" }
    local editorRoots = {}
    local accounts = {}
    local loadingAccount = false
    local randomOptions = { MinUserId = 120000000, MaxUserId = 11000000000, Attempts = 5 }
    local randomGenerator = Random.new()
    local randomIdentity, pendingIdentity
    local randomState = "idle"

    function manager:SetRandomOptions(options)
        assert(self.Alive and type(options) == "table", "random options must be a table")
        assert(randomState == "idle", "set random options before selecting randomised")
        local nextOptions = {}
        for key, value in pairs(randomOptions) do nextOptions[key] = value end
        for key, value in pairs(options) do
            assert(nextOptions[key] ~= nil, "unknown random option: " .. tostring(key))
            assert(type(value) == "number" and value >= 1 and value <= 9007199254740991
                and value == math.floor(value), key .. " must be a positive whole number")
            nextOptions[key] = value
        end
        assert(nextOptions.MinUserId <= nextOptions.MaxUserId, "minimum user id exceeds maximum")
        assert(nextOptions.Attempts <= 20, "Attempts must be between 1 and 20")
        randomOptions = nextOptions
    end

    function manager:GetRandomStatus() return randomState end

    local function isServerIdentity(id)
        if id == LocalPlayer.UserId then return true end
        for _, player in ipairs(Players:GetPlayers()) do
            if player.UserId == id then return true end
        end
        return false
    end

    -- Loading returns draft data; it does not activate privacy or replace the current identity.
    function manager:LoadAccount(account)
        assert(self.Alive, "PrivacyManager is destroyed")
        assert(not loadingAccount, "an account is already loading")
        local query = tostring(account):match("^%s*(.-)%s*$")
        assert(query ~= "", "enter a username or user id")
        loadingAccount = true
        local temporary = {}
        local ok, result = pcall(function()
            local id = query:match("^%d+$") and tonumber(query)
                or Players:GetUserIdFromNameAsync(query:gsub("^@", ""))
            assert(id and id > 0 and id <= 9007199254740991 and id == math.floor(id), "invalid user id")
            local info = game:GetService("UserService"):GetUserInfosByUserIdsAsync({ id })[1]
            assert(self.Alive, "PrivacyManager was destroyed while loading")
            assert(info and info.Username and info.DisplayName, "account details unavailable")
            if not accounts[id] then
                local description = Players:GetHumanoidDescriptionFromUserIdAsync(id)
                table.insert(temporary, description)
                assert(self.Alive, "PrivacyManager was destroyed while loading")
                local rigs = {}
                for _, kind in ipairs({ Enum.HumanoidRigType.R6, Enum.HumanoidRigType.R15 }) do
                    local rig = Players:CreateHumanoidModelFromDescriptionAsync(description, kind)
                    table.insert(temporary, rig)
                    assert(self.Alive, "PrivacyManager was destroyed while loading")
                    rigs[kind] = rig
                end
                assert(self.Alive, "PrivacyManager was destroyed while loading")
                accounts[id] = rigs
                temporary = { description }
            end
            assert(self.Alive, "PrivacyManager was destroyed while loading")
            return { Name = info.Username, DisplayName = info.DisplayName, UserId = id,
                AccountId = id, Appearance = "loaded account" }
        end)
        for _, item in ipairs(temporary) do item:Destroy() end
        loadingAccount = false
        if not ok then error(result, 2) end
        return result
    end
    local function replacementIdentity(player)
        if not isLocal(player) then
            local name = anonymousPrefix .. rememberIdentity(player).Index
            return { Name = name, DisplayName = name, UserId = 0, Appearance = "anonymous" }
        end
        if manager.Options.Method == "custom" then return custom end
        if manager.Options.Method == "randomised" then
            if randomIdentity then return randomIdentity end
            if randomState == "loading" and pendingIdentity then return pendingIdentity end
        end
        return { Name = anonymousName, DisplayName = anonymousName, UserId = 0, Appearance = "anonymous" }
    end
    local function startRandom()
        if randomState ~= "idle" then return end
        randomState = "loading"
        task.defer(function()
            local attempted = {}
            for attempt = 1, randomOptions.Attempts do
                -- A custom account lookup shares the loader; wait without consuming attempts.
                while manager.Alive and loadingAccount do task.wait(0.1) end
                if not manager.Alive then return end
                local span = randomOptions.MaxUserId - randomOptions.MinUserId + 1
                -- Scale a fractional draw: the default IDs exceed 32-bit integer bounds.
                local id = math.min(randomOptions.MaxUserId,
                    randomOptions.MinUserId + math.floor(randomGenerator:NextNumber() * span))
                if not attempted[id] and not isServerIdentity(id) then
                    attempted[id] = true
                    local wasCached = accounts[id] ~= nil
                    local ok, identity = pcall(manager.LoadAccount, manager, ("%.0f"):format(id))
                    if not manager.Alive then return end
                    -- A player may have joined while the account/appearance request yielded.
                    if ok and not isServerIdentity(id) then
                        randomIdentity = identity
                        break
                    elseif not wasCached and accounts[id] and custom.AccountId ~= id then
                        for _, rig in pairs(accounts[id]) do rig:Destroy() end
                        accounts[id] = nil
                    end
                end
                if attempt < randomOptions.Attempts then task.wait(0.25) end
            end
            if not manager.Alive then return end
            randomState = randomIdentity and "ready" or "fallback"
            pendingIdentity = nil
            if manager.Options.Method == "randomised" then manager:Refresh() end
        end)
    end

    local function hideAppearance(player)
        return optionsFor(player).HideAvatar and replacementIdentity(player).Appearance ~= "keep mine"
    end
    function manager:GetCustom()
        return { Name = custom.Name, DisplayName = custom.DisplayName, UserId = custom.UserId, Appearance = custom.Appearance, AccountId = custom.AccountId }
    end
    function manager:SetCustom(values)
        assert(self.Alive and type(values) == "table", "custom identity must be a table")
        local nextIdentity = self:GetCustom()
        for key, value in pairs(values) do
            assert(key == "AccountId" or nextIdentity[key] ~= nil, "unknown custom identity field: " .. tostring(key))
            if key == "Name" or key == "DisplayName" then
                assert(type(value) == "string" and #value <= 64 and value:find("%S")
                    and not value:find("[%c<>]"), key .. " must be plain text, 1–64 bytes")
            elseif key == "UserId" then
                assert(type(value) == "number" and value >= 0 and value <= 9007199254740991
                    and value == math.floor(value), "user id must be a non-negative whole number")
            elseif key == "AccountId" then
                assert(type(value) == "number" and accounts[value], "load this account before selecting its appearance")
            elseif key == "Appearance" then
                assert(value == "anonymous" or value == "keep mine" or value == "loaded account", "invalid appearance")
            end
            nextIdentity[key] = value
        end
        assert(nextIdentity.Appearance ~= "loaded account" or accounts[nextIdentity.AccountId], "load an account first")
        custom = nextIdentity
        self:Refresh()
    end
    function manager:SetMethod(method)
        self:SetOptions({ Method = method })
    end

    function manager:GetAnonymousIdentity(player)
        local name = isLocal(player) and anonymousName or anonymousPrefix .. rememberIdentity(player).Index
        return {
            Name = name, DisplayName = name, UserId = 0,
            Avatar = anonymousAvatar,
            Appearance = { BodyColor = anonymousColor, Face = anonymousAvatar },
        }
    end

    function manager:SetAnonymous(options)
        assert(type(options) == "table", "anonymous options must be a table")
        for key in pairs(options) do assert(key == "Prefix", "unknown anonymous option: " .. tostring(key)) end
        if options.Prefix ~= nil then
            assert(type(options.Prefix) == "string" and #options.Prefix <= 64
                and not options.Prefix:find("[%c<>]"), "anonymous Prefix must be plain text up to 64 bytes")
            anonymousPrefix = options.Prefix
            anonymousName = anonymousPrefix .. "1"
        end
        self:Refresh()
    end

    local function wordByte(value)
        return value ~= "" and (value:match("[%w_]") ~= nil or value:byte() >= 128)
    end

    -- Match literal identity tokens with boundaries; never reprocess replacements.
    local function replaceTokens(source, names, replacements)
        local out, position = {}, 1
        while position <= #source do
            local first, last, replacement
            for _, name in ipairs(names) do
                local search = position
                while search <= #source do
                    local a, b = source:find(name, search, true)
                    if not a then break end
                    local before, after = source:sub(a - 1, a - 1), source:sub(b + 1, b + 1)
                    if not wordByte(before) and not wordByte(after) then
                        if not first or a < first or (a == first and b > last) then
                            first, last = a, b
                            replacement = replacements[name] or anonymousName
                        end
                        break
                    end
                    search = b + 1
                end
            end
            if not first then table.insert(out, source:sub(position)); break end
            table.insert(out, source:sub(position, first - 1))
            table.insert(out, replacement)
            position = last + 1
        end
        return table.concat(out)
    end

    function manager:GetIdentity(player)
        player = player or LocalPlayer
        local options = optionsFor(player)
        local enabled = self.Alive and options.Enabled
        local identity = enabled and replacementIdentity(player)
        return {
            Name = enabled and options.HideUsername and identity.Name or player.Name,
            DisplayName = enabled and options.HideDisplayName and identity.DisplayName or player.DisplayName,
            UserId = enabled and options.HideUserIds and identity.UserId or player.UserId,
        }
    end
    function manager:GetName(player) return self:GetIdentity(player).Name end
    function manager:GetDisplayName(player) return self:GetIdentity(player).DisplayName end
    function manager:GetUserId(player) return self:GetIdentity(player).UserId end

    local function rulesFor(scope, richText)
        local key = (scope == "game" and "game" or "facility") .. (richText and "rich" or "plain")
        if textRules[key] then return textRules[key] end
        local rules = { names = {}, replacements = {} }
        local priorities = {}
        local function add(real, replacement, priority)
            if real == "" then return end
            if richText then replacement = replacement:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;") end
            local oldPriority = priorities[real]
            if not oldPriority then table.insert(rules.names, real) end
            if not oldPriority or priority > oldPriority then
                rules.replacements[real], priorities[real] = replacement, priority
            elseif priority == oldPriority and rules.replacements[real] ~= replacement then
                -- Shared display names cannot identify a player in arbitrary text.
                rules.replacements[real] = "player"
            end
        end
        for _, record in ipairs(identityList) do
            local options = optionsFor(record)
            if scopeEnabled(options, scope) then
                local identity = replacementIdentity(record)
                if options.HideDisplayName then add(record.DisplayName, identity.DisplayName, 1) end
                if options.HideUsername then add(record.Name, identity.Name, 2) end
                if options.HideUserIds then add(("%.0f"):format(record.UserId), ("%.0f"):format(identity.UserId), 3) end
            end
        end
        textRules[key] = rules
        return rules
    end

    function manager:ResolveText(value, scope, richText)
        if type(value) ~= "string" or not self.Alive then return value end
        if not scopeEnabled(self.Options, scope) and not scopeEnabled(self.PlayerOptions, scope) then return value end
        local rules = rulesFor(scope, richText)
        local names, replacements = rules.names, rules.replacements
        if #names == 0 then return value end
        if not richText then return replaceTokens(value, names, replacements) end
        -- Preserve markup attributes; only replace visible text between tags.
        local out, position = {}, 1
        while position <= #value do
            local a, b = value:find("<[^>]*>", position)
            if not a then table.insert(out, replaceTokens(value:sub(position), names, replacements)); break end
            table.insert(out, replaceTokens(value:sub(position, a - 1), names, replacements))
            table.insert(out, value:sub(a, b))
            position = b + 1
        end
        return table.concat(out)
    end


    function manager:ResolveImage(value, scope)
        if type(value) ~= "string" or not self.Alive then return value end
        local query = value:match("^rbxthumb://(.+)$")
        if not query then return value end
        local params = {}
        for key, item in query:gmatch("([^&=?]+)=([^&]+)") do params[key:lower()] = item end
        local kind = (params.type or ""):lower()
        local record = identitiesById[tonumber(params.id)]
        if record and scopeEnabled(optionsFor(record), scope) and hideAppearance(record)
            and (kind == "avatarheadshot" or kind == "avatarbust" or kind == "avatar") then
            local identity = replacementIdentity(record)
            if identity.Appearance == "loaded account" then
                return value:gsub("([&?/]id=)%d+", function(prefix) return prefix .. ("%.0f"):format(identity.AccountId) end)
            end
            return anonymousAvatar
        end
        return value
    end

    function manager:GetAvatar(player)
        player = player or LocalPlayer
        if self.Alive and optionsFor(player).Enabled and hideAppearance(player) then
            local identity = replacementIdentity(player)
            if identity.Appearance == "loaded account" then
                return "rbxthumb://type=AvatarHeadShot&id=" .. ("%.0f"):format(identity.AccountId) .. "&w=150&h=150"
            end
            return anonymousAvatar
        end
        return "rbxthumb://type=AvatarHeadShot&id=" .. player.UserId .. "&w=150&h=150"
    end

    local function scopeOf(node)
        local current = node
        local gameScope = false
        while current do
            if editorRoots[current] then return nil end
            if Library.GuiRoots and Library.GuiRoots[current] then return "facility" end
            if roots[current] and roots[current].scope == "game" then gameScope = true end
            current = current.Parent
        end
        return gameScope and "game" or nil
    end

    local ownedVisuals = {}
    local function classicPart(parent, name, size, position)
        local part = Instance.new("Part")
        part.Name = name
        part.Size = size
        part.CFrame = CFrame.new(position)
        part.Color = anonymousColor
        part.Material = Enum.Material.SmoothPlastic
        part.Anchored = true
        part.CanCollide, part.CanTouch, part.CanQuery = false, false, false
        part.CastShadow = false
        part.Parent = parent
        return part
    end

    local function classicHead(parent)
        local head = classicPart(parent, "FacilityAnonymousHead", Vector3.new(2, 1, 1), Vector3.zero)
        local mesh = Instance.new("SpecialMesh")
        mesh.MeshType = Enum.MeshType.Head
        mesh.Scale = Vector3.new(1.25, 1.25, 1.25)
        mesh.Parent = head
        local face = Instance.new("Decal")
        face.Name = "FacilityAnonymousFace"
        face.Face = Enum.NormalId.Front
        face.Texture = anonymousAvatar
        face.Transparency = 0
        face.Parent = head
        return head
    end

    local function clearPreview(record)
        if record.preview then
            ownedVisuals[record.preview] = nil
            record.preview:Destroy()
            record.preview = nil
        end
    end

    local function showPreview(node, record)
        if record.preview and record.previewSource ~= record.original then clearPreview(record) end
        if record.preview then
            record.preview.ZIndex = node.ZIndex
            record.preview.ImageTransparency = node.ImageTransparency
            return
        end
        local viewport = Instance.new("ViewportFrame")
        viewport.Name = "FacilityAnonymousPortrait"
        viewport.Size = UDim2.fromScale(1, 1)
        viewport.BackgroundTransparency = 1
        viewport.Active = false
        viewport.ZIndex = node.ZIndex
        viewport.Ambient = Color3.fromRGB(200, 200, 200)
        viewport.LightColor = anonymousColor
        viewport.LightDirection = Vector3.new(-1, -1, -1)
        ownedVisuals[viewport] = true
        record.preview = viewport
        record.previewSource = record.original
        viewport.ImageTransparency = node.ImageTransparency
        for _, child in ipairs(node:GetChildren()) do
            if child:IsA("UICorner") then child:Clone().Parent = viewport end
        end
        local world = Instance.new("WorldModel")
        world.Parent = viewport
        local head = classicHead(world)
        head.CFrame = CFrame.new(0, 2.5, 0)
        classicPart(world, "Torso", Vector3.new(2, 2, 1), Vector3.new(0, 1, 0))
        classicPart(world, "LeftArm", Vector3.new(1, 2, 1), Vector3.new(-1.5, 1, 0))
        classicPart(world, "RightArm", Vector3.new(1, 2, 1), Vector3.new(1.5, 1, 0))
        classicPart(world, "LeftLeg", Vector3.new(1, 2, 1), Vector3.new(-0.5, -1, 0))
        classicPart(world, "RightLeg", Vector3.new(1, 2, 1), Vector3.new(0.5, -1, 0))
        local camera = Instance.new("Camera")
        camera.FieldOfView = 35
        local kind = (record.original:match("[?&/]type=([^&]+)") or "AvatarHeadShot"):lower()
        if kind == "avatar" then
            camera.CFrame = CFrame.lookAt(Vector3.new(0, 1, -11), Vector3.new(0, 0.5, 0))
        elseif kind == "avatarbust" then
            camera.CFrame = CFrame.lookAt(Vector3.new(0, 2, -7), Vector3.new(0, 1.6, 0))
        else
            camera.CFrame = CFrame.lookAt(Vector3.new(0, 2.6, -3.1), Vector3.new(0, 2.5, 0))
        end
        camera.Parent = viewport
        viewport.CurrentCamera = camera
        viewport.Parent = node
    end

    local function apply(node, record)
        if record.writing then return end
        local scope = scopeOf(node)
        local value = record.original
        if scope then
            if record.property == "Image" then
                value = manager:ResolveImage(value, scope)
            else
                value = manager:ResolveText(value, scope, node.RichText)
            end
        end
        if record.property == "Image" then
            if value ~= record.original and value == anonymousAvatar then
                showPreview(node, record)
                value = ""
            else
                clearPreview(record)
            end
        end
        record.rendered = value
        if node[record.property] ~= value then
            record.writing = true
            node[record.property] = value
            record.writing = false
        end
    end

    local function forget(node, restore)
        local record = watched[node]
        if not record then return end
        watched[node], imageNodes[node] = nil, nil
        clearPreview(record)
        for _, connection in ipairs(record.connections) do connection:Disconnect() end
        if restore then
            pcall(function() node[record.property] = record.original end)
        end
    end

    local watchPreview
    local function watch(node)
        if watchPreview then watchPreview(node) end
        if not manager.Alive or watched[node] then return end
        local property
        if node:IsA("TextLabel") or node:IsA("TextButton") then property = "Text"
        elseif node:IsA("ImageLabel") or node:IsA("ImageButton") then property = "Image"
        else return end
        local record = { property = property, original = node[property], rendered = node[property], connections = {} }
        watched[node] = record
        if property == "Image" then imageNodes[node] = record end
        table.insert(record.connections, node:GetPropertyChangedSignal(property):Connect(function()
            if record.writing or node[property] == record.rendered then return end
            record.original = node[property]
            apply(node, record)
        end))
        if property == "Image" then
            for _, key in ipairs({ "ZIndex", "ImageTransparency" }) do
                table.insert(record.connections, node:GetPropertyChangedSignal(key):Connect(function() apply(node, record) end))
            end
        end
        if property == "Text" then
            table.insert(record.connections, node:GetPropertyChangedSignal("RichText"):Connect(function() apply(node, record) end))
        end
        table.insert(record.connections, node.AncestryChanged:Connect(function() apply(node, record) end))
        table.insert(record.connections, node.Destroying:Connect(function() forget(node, false) end))
        apply(node, record)
    end

    function manager:WatchRoot(root, scope)
        if not self.Alive or roots[root] then return end
        local record = { scope = scope or "facility", connections = {} }
        roots[root] = record
        table.insert(record.connections, root.DescendantAdded:Connect(watch))
        table.insert(record.connections, root.Destroying:Connect(function()
            for _, connection in ipairs(record.connections) do connection:Disconnect() end
            roots[root] = nil
        end))
        watch(root)
        for _, node in ipairs(root:GetDescendants()) do watch(node) end
    end

    -- One reversible appearance controller for live characters and UI copies.
    local function createAppearance(model, isPreview, enabled, player)
        local inheritedHead = false
        if isPreview then
            for _, child in ipairs(model:GetChildren()) do
                if child:IsA("BasePart") and child.Name == "FacilityAnonymousHead" then inheritedHead = true end
            end
        end
        local character, characterConnections = nil, {}
        local characterVisuals = {}
        local neutralColor = anonymousColor
        local ownedHeads = {}
        local accountVisual, accountKey, accountParts
        local function clearAccountVisual()
            if accountVisual then
                ownedVisuals[accountVisual] = nil
                accountVisual:Destroy()
            end
            accountVisual, accountKey, accountParts = nil, nil, nil
        end
        local function loadedAppearance()
            return replacementIdentity(player).Appearance == "loaded account"
        end

        local function clearFaces()
            clearAccountVisual()
            for head, visual in pairs(ownedHeads) do
                ownedHeads[head] = nil
                visual:Destroy()
                ownedVisuals[visual] = nil
            end
        end

        local function characterEnabled()
            return manager.Alive and optionsFor(player).Enabled and hideAppearance(player) and enabled()
        end

        local function syncHeads()
            if accountParts and character then
                for _, record in ipairs(accountParts) do
                    local target = character:FindFirstChild(record.name)
                    if target and target:IsA("BasePart") then
                        record.part.Anchored = true
                        record.part.CanCollide, record.part.CanTouch, record.part.CanQuery = false, false, false
                        record.part.CFrame = target.CFrame * record.offset
                        record.part.LocalTransparencyModifier = isPreview and 0 or target.LocalTransparencyModifier
                    end
                end
                -- A sibling visual model keeps its Humanoid and parts out of the
                -- real character hierarchy. Preview models remain in their WorldModel.
                accountVisual.Parent = character.Parent
            end
            for head, visual in pairs(ownedHeads) do
                if head.Parent == character then
                    visual.CFrame = head.CFrame
                    visual.LocalTransparencyModifier = isPreview and 0 or head.LocalTransparencyModifier
                    local records = characterVisuals[head]
                    local transparency = records and records.properties.Transparency
                    local original = transparency and transparency.original or 0
                    -- Copies made during masking inherit an invisible original Head.
                    visual.Transparency = inheritedHead and original == 1 and 0 or original
                end
            end
        end

        local function refreshFaces()
            if not characterEnabled() or not character then clearFaces(); return end
            if loadedAppearance() then
                for head, visual in pairs(ownedHeads) do
                    ownedHeads[head] = nil; ownedVisuals[visual] = nil; visual:Destroy()
                end
                local humanoid = character:FindFirstChildOfClass("Humanoid")
                local kind = humanoid and humanoid.RigType or Enum.HumanoidRigType.R6
                local identity = replacementIdentity(player)
                local template = accounts[identity.AccountId] and accounts[identity.AccountId][kind]
                local key = tostring(identity.AccountId) .. tostring(kind)
                if accountKey ~= key then clearAccountVisual() end
                if template and not accountVisual then
                    accountVisual = template:Clone()
                    accountVisual.Name = "FacilityCustomAppearance"
                    ownedVisuals[accountVisual] = true
                    accountKey, accountParts = key, {}
                    for _, node in ipairs(accountVisual:GetDescendants()) do
                        if node:IsA("BasePart") then
                            local anchor, offset = node, CFrame.new()
                            if node.Parent:IsA("Accessory") then
                                anchor, offset = nil, nil
                                local weld = node:FindFirstChild("AccessoryWeld")
                                if weld and weld:IsA("JointInstance") then
                                    -- Part0 * C0 = Part1 * C1. Generated handle world
                                    -- positions may still be unassembled; use joint offsets.
                                    if weld.Part0 == node then
                                        anchor, offset = weld.Part1, weld.C1 * weld.C0:Inverse()
                                    elseif weld.Part1 == node then
                                        anchor, offset = weld.Part0, weld.C0 * weld.C1:Inverse()
                                    end
                                end
                                if not anchor or not anchor:IsA("BasePart") or anchor.Parent ~= accountVisual then
                                    anchor, offset = nil, nil
                                    for _, attachment in ipairs(node:GetChildren()) do
                                        if attachment:IsA("Attachment") then
                                            for _, part in ipairs(accountVisual:GetChildren()) do
                                                local target = part:IsA("BasePart") and part:FindFirstChild(attachment.Name)
                                                if target and target:IsA("Attachment") then
                                                    anchor, offset = part, target.CFrame * attachment.CFrame:Inverse()
                                                    break
                                                end
                                            end
                                            if anchor then break end
                                        end
                                    end
                                end
                            end
                            if anchor and offset then
                                table.insert(accountParts, { part = node, name = anchor.Name, offset = offset })
                            end
                            node.Anchored = true
                            node.CanCollide, node.CanTouch, node.CanQuery = false, false, false
                            if node.Name == "HumanoidRootPart" then node.Transparency = 1 end
                        elseif node:IsA("Script") or node:IsA("LocalScript") then node:Destroy()
                        elseif node:IsA("Humanoid") then
                            -- Keep avatar rendering, but prevent this visual rig from enabling
                            -- collisions or applying Humanoid forces after it enters Workspace.
                            node.EvaluateStateMachine = false
                            node.AutoRotate = false
                            node.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
                        end
                    end
                    -- Part transforms are followed explicitly; cloned joints must not
                    -- pull independently anchored visual parts into an assembly.
                    for _, node in ipairs(accountVisual:GetDescendants()) do
                        if node:IsA("JointInstance") or node:IsA("Constraint") then node:Destroy() end
                    end
                end
                syncHeads()
                return
            end
            clearAccountVisual()
            for head, visual in pairs(ownedHeads) do
                if head.Parent ~= character or visual.Parent ~= character then
                    ownedHeads[head] = nil
                    visual:Destroy()
                    ownedVisuals[visual] = nil
                end
            end
            for _, head in ipairs(character:GetChildren()) do
                if head:IsA("BasePart") and head.Name == "Head" and not ownedHeads[head] then
                    local visual = classicHead(nil)
                    ownedHeads[head], ownedVisuals[visual] = visual, true
                    visual.CFrame = head.CFrame
                    visual.Parent = character
                end
            end
            syncHeads()
        end

        local function applyVisual(node, property, record)
            if record.writing then return end
            local value = record.original
            if characterEnabled() then
                value = type(record.masked) == "function" and record.masked() or record.masked
            end
            record.rendered = value
            if node[property] ~= value then
                record.writing = true
                local success = pcall(function() node[property] = value end)
                record.writing = false
                if not success then record.rendered = node[property] end
            end
        end

        local function forgetVisual(node)
            local records = characterVisuals[node]
            if not records then return end
            characterVisuals[node] = nil
            local visual = ownedHeads[node]
            if visual then
                ownedHeads[node] = nil
                visual:Destroy()
                ownedVisuals[visual] = nil
            end
            for property, record in pairs(records.properties) do
                record.connection:Disconnect()
                pcall(function() node[property] = record.original end)
            end
            for _, connection in ipairs(records.connections) do connection:Disconnect() end
        end

        local function maskProperty(node, property, masked)
            local success, original = pcall(function() return node[property] end)
            if not success then return end
            local records = characterVisuals[node]
            if not records then
                records = { properties = {}, connections = {} }
                characterVisuals[node] = records
                table.insert(records.connections, node.Destroying:Connect(function() forgetVisual(node) end))
                table.insert(records.connections, node.AncestryChanged:Connect(function()
                    if not character or not node:IsDescendantOf(character) then forgetVisual(node) end
                end))
            end
            if records.properties[property] then return end
            local record = { original = original, rendered = original, masked = masked }
            records.properties[property] = record
            record.connection = node:GetPropertyChangedSignal(property):Connect(function()
                if record.writing or node[property] == record.rendered then return end
                record.original = node[property]
                applyVisual(node, property, record)
            end)
            applyVisual(node, property, record)
        end

        local function watchCharacterVisual(node)
            if ownedVisuals[node] or not character or not node:IsDescendantOf(character) then return end
            -- A menu may clone the world character while its owned head is present.
            if node.Parent == character and node:IsA("BasePart") and node.Name == "FacilityAnonymousHead" then
                maskProperty(node, "Transparency", 1)
                return
            end
            local ancestor, accessory, body = node, false, nil
            while ancestor and ancestor ~= character do
                if ownedVisuals[ancestor] or ancestor:IsA("Tool") then return end
                if ancestor:IsA("Accessory") then accessory = true end
                if ancestor:IsA("BasePart") and ancestor.Parent == character
                    and ancestor.Name ~= "HumanoidRootPart" then body = ancestor end
                ancestor = ancestor.Parent
            end
            if accessory then
                if node:IsA("BasePart") then maskProperty(node, isPreview and "Transparency" or "LocalTransparencyModifier", 1)
                elseif node:IsA("ParticleEmitter") or node:IsA("Trail") or node:IsA("Beam") then
                    maskProperty(node, "Enabled", false)
                end
            elseif body then
                if node == body then
                    maskProperty(node, "Color", neutralColor)
                    if node.Name ~= "Head" then
                        maskProperty(node, "Transparency", function()
                            return loadedAppearance() and 1 or characterVisuals[node].properties.Transparency.original
                        end)
                    end
                    if node:IsA("MeshPart") then maskProperty(node, "TextureID", "") end
                    if node.Name == "Head" then
                        maskProperty(node, "Transparency", 1)
                        refreshFaces()
                    end
                elseif node:IsA("Decal") or node:IsA("Texture") then
                    maskProperty(node, "Transparency", 1)
                elseif node:IsA("SpecialMesh") then maskProperty(node, "TextureId", "") end
            elseif node.Parent == character then
                if node:IsA("Shirt") then maskProperty(node, "ShirtTemplate", "")
                elseif node:IsA("Pants") then maskProperty(node, "PantsTemplate", "")
                elseif node:IsA("ShirtGraphic") then maskProperty(node, "Graphic", "") end
            end
        end

        local function detachCharacter()
            clearFaces()
            for _, connection in ipairs(characterConnections) do connection:Disconnect() end
            table.clear(characterConnections)
            for node in pairs(characterVisuals) do forgetVisual(node) end
            character = nil
        end

        local function attachCharacter(nextCharacter)
            if character == nextCharacter then return end
            detachCharacter()
            character = nextCharacter
            if not character then return end
            table.insert(characterConnections, character.DescendantAdded:Connect(watchCharacterVisual))
            table.insert(characterConnections, character.Destroying:Connect(detachCharacter))
            for _, node in ipairs(character:GetDescendants()) do watchCharacterVisual(node) end
        end

        attachCharacter(model)
        return {
            Refresh = function()
                for node, records in pairs(characterVisuals) do
                    for property, record in pairs(records.properties) do applyVisual(node, property, record) end
                end
                refreshFaces()
            end,
            Sync = syncHeads,
            Destroy = detachCharacter,
        }
    end

    local function detachCharacter(record)
        if record.mask then record.mask.Destroy() end
        record.model, record.mask = nil, nil
    end
    local function refreshCharacter(player, record)
        local options = optionsFor(player)
        if not record.mask and record.model and options.Enabled and options.AffectGame and hideAppearance(player) then
            record.mask = createAppearance(record.model, false, function()
                return activePlayers[player] == record and optionsFor(player).AffectGame
            end, player)
        end
        if record.mask then record.mask.Refresh() end
    end
    local function attachCharacter(player, record, model)
        if record.model == model then return end
        detachCharacter(record)
        record.model = model
        refreshCharacter(player, record)
    end

    local previewModels = {}
    local function previewScope(model)
        local node, viewport = model, false
        while node do
            if ownedVisuals[node] then return nil end
            if node:IsA("ViewportFrame") then viewport = true end
            node = node.Parent
        end
        return viewport and scopeOf(model) or nil
    end
    local function previewOwner(model, record)
        if record.player then return activePlayers[record.player] and record.player or nil end
        -- Explicit ownership wins over names. Never infer from a display name alone.
        for _, key in ipairs({ "UserId", "PlayerUserId", "OwnerUserId" }) do
            local value = model:GetAttribute(key)
            if value ~= nil then return activeById[tonumber(value)] end
        end
        for player in pairs(activePlayers) do
            if model.Name == player.Name or model.Name == tostring(player.UserId) then return player end
        end
    end
    local function refreshPreview(model, record)
        if record.refreshing then return end
        record.refreshing = true
        local scope = previewScope(model)
        local owner = scope and previewOwner(model, record)
        local eligible = owner and model:FindFirstChildOfClass("Humanoid")
        if record.mask and (not eligible or record.owner ~= owner) then
            record.mask.Destroy()
            record.mask, record.owner = nil, nil
        end
        if eligible and not record.mask and scopeEnabled(optionsFor(owner), scope) and hideAppearance(owner) then
            record.owner = owner
            record.mask = createAppearance(model, true, function()
                local currentScope = previewScope(model)
                return currentScope and previewOwner(model, record) == owner
                    and scopeEnabled(optionsFor(owner), currentScope)
            end, owner)
        end
        if record.mask then record.mask.Refresh() end
        record.refreshing = false
    end
    local function forgetPreview(model)
        local record = previewModels[model]
        if not record then return end
        previewModels[model] = nil
        for _, connection in ipairs(record.connections) do connection:Disconnect() end
        if record.mask then record.mask.Destroy() end
    end
    watchPreview = function(model)
        if not manager.Alive or not model:IsA("Model") or previewModels[model] or not previewScope(model) then return end
        local record = { connections = {} }
        previewModels[model] = record
        local function refresh() refreshPreview(model, record) end
        table.insert(record.connections, model:GetPropertyChangedSignal("Name"):Connect(refresh))
        for _, key in ipairs({ "UserId", "PlayerUserId", "OwnerUserId" }) do
            table.insert(record.connections, model:GetAttributeChangedSignal(key):Connect(refresh))
        end
        table.insert(record.connections, model.ChildAdded:Connect(refresh))
        table.insert(record.connections, model.AncestryChanged:Connect(refresh))
        table.insert(record.connections, model.Destroying:Connect(function() forgetPreview(model) end))
        refresh()
    end

    -- Game adapters can explicitly identify an otherwise anonymous preview model.
    -- Call for each newly created model; the returned function removes that binding.
    function manager:RegisterPreview(model, player)
        assert(self.Alive and model:IsA("Model") and previewScope(model), "preview must be a Model inside a watched ViewportFrame")
        assert(activePlayers[player], "preview owner must be a current player")
        watchPreview(model)
        local record = previewModels[model]
        local binding = {}
        record.binding, record.player = binding, player
        refreshPreview(model, record)
        return function()
            if previewModels[model] ~= record or record.binding ~= binding then return end
            record.binding, record.player = nil, nil
            refreshPreview(model, record)
        end
    end

    table.insert(connections, RunService.RenderStepped:Connect(function()
        for _, record in pairs(activePlayers) do if record.mask then record.mask.Sync() end end
        for _, record in pairs(previewModels) do if record.mask then record.mask.Sync() end end
    end))

    local gameStarted = false
    local function startGame()
        if gameStarted then return end
        gameStarted = true
        local playerGui = LocalPlayer:FindFirstChildOfClass("PlayerGui")
        if playerGui then manager:WatchRoot(playerGui, "game") end
        table.insert(connections, LocalPlayer.ChildAdded:Connect(function(child)
            if child:IsA("PlayerGui") then manager:WatchRoot(child, "game") end
        end))
        -- Optional executor access. An inaccessible CoreGui must not stop other roots.
        pcall(function() manager:WatchRoot(game:GetService("CoreGui"), "game") end)
        manager:WatchRoot(game:GetService("Workspace"), "game")
    end

    function manager:Refresh(appearanceOnly)
        if not self.Alive then return end
        if not appearanceOnly then textRules = {} end
        if scopeEnabled(self.Options, "game") or scopeEnabled(self.PlayerOptions, "game") then startGame() end
        for node, record in pairs(appearanceOnly and imageNodes or watched) do apply(node, record) end
        for player, record in pairs(activePlayers) do refreshCharacter(player, record) end
        for model, record in pairs(previewModels) do refreshPreview(model, record) end
        for panel in pairs(panels) do
            for key, control in pairs(panel.Controls) do control:Set(self.Options[key], true) end
            for key, control in pairs(panel.PlayerControls) do control:Set(self.PlayerOptions[key], true) end
            panel.Method = self.Options.Method
            if panel.MethodControl then panel.MethodControl:Set(panel.Method, true) end
            if panel.EditCustom then panel.EditCustom:SetVisible(panel.Method == "custom") end
            if panel.RandomStatus then
                panel.RandomStatus:Set(panel.Method ~= "randomised" and ""
                    or randomState == "loading" and "loading random identity…"
                    or randomState == "ready" and "random identity ready"
                    or randomState == "fallback" and "using anonymous identity"
                    or "")
            end
        end
    end

    function manager:SetOptions(options)
        assert(self.Alive and type(options) == "table", "privacy options must be a table")
        for key, value in pairs(options) do
            if key == "Method" then
                assert(value == "anonymous" or value == "custom" or value == "randomised",
                    "method must be anonymous, custom or randomised")
            else
                assert(self.Options[key] ~= nil and type(value) == "boolean", "invalid privacy option: " .. tostring(key))
            end
        end
        if options.Method == "randomised" and randomState == "idle" then
            pendingIdentity = replacementIdentity()
        end
        local changed, appearanceOnly = false, true
        for key, value in pairs(options) do
            if self.Options[key] ~= value then
                changed = true
                if key ~= "HideAvatar" then appearanceOnly = false end
                self.Options[key] = value
            end
        end
        if self.Options.Method == "randomised" then startRandom() end
        if changed then self:Refresh(appearanceOnly) end
    end
    function manager:SetPlayerOptions(options)
        assert(self.Alive and type(options) == "table", "player privacy options must be a table")
        for key, value in pairs(options) do
            if key == "Method" then
                assert(value == "anonymous", "players currently support the anonymous method")
            else
                assert(self.PlayerOptions[key] ~= nil and type(value) == "boolean", "invalid player privacy option: " .. tostring(key))
            end
        end
        local changed, appearanceOnly = false, true
        for key, value in pairs(options) do
            if self.PlayerOptions[key] ~= value then
                self.PlayerOptions[key], changed = value, true
                if key ~= "HideAvatar" then appearanceOnly = false end
            end
        end
        if changed then self:Refresh(appearanceOnly) end
    end
    function manager:Restore()
        self.Options.Enabled, self.PlayerOptions.Enabled = false, false
        self:Refresh()
    end
    function manager:SetLibrary(lib)
        assert(lib == Library, "PrivacyManager is bound to its creating library")
        return self
    end

    function manager:BuildPrivacySection(tab, column, opts)
        opts = opts or {}
        local window = tab.Window
        local connectionStart, repaintStart = #Library.Connections, #Library.RepaintHooks
        local overlayBefore = {}
        for _, node in ipairs(window.Overlay:GetChildren()) do overlayBefore[node] = true end
        local section = tab:Section(opts.Title or "privacy", column or 1)
        local panel = { Section = section, Instance = section.Frame, Controls = {}, PlayerControls = {}, Alive = true }
        local labels = opts.Labels or {}
        local function toggle(owner, key, fallback)
            local control = owner:Toggle({
                Text = labels[key] or fallback, Flag = false, Default = self.Options[key],
                Callback = function(value) self:SetOptions({ [key] = value }) end,
            })
            panel.Controls[key] = control
            return control
        end
        -- Edits remain a draft until apply; closing the editor keeps that draft.
        local editor = window:Modal({
            Title = labels.CustomTitle or "custom identity",
            Width = opts.EditorWidth or 420, Height = opts.EditorHeight or 0.86,
        })
        panel.CustomEditor = editor
        editorRoots[editor.Root] = true
        panel.Draft = { Username = custom.Name, DisplayName = custom.DisplayName, UserId = ("%.0f"):format(custom.UserId), Appearance = custom.Appearance, AccountId = custom.AccountId }
        local draft, fields = panel.Draft, {}
        panel.EditorControls = fields
        local content = editor.Content
        content:Label("edit your identity, then apply. user identity must be enabled to display it.")
        content:Label("account")
        fields.Account = content:Input({ Text = "username or user id", Flag = false, Placeholder = "enter an account" })
        fields.LoadStatus = content:Label("")
        local updatePreview = function() end
        local loading = false
        fields.Load = content:Button({ Text = "load account", Callback = function()
            if loading or not panel.Alive then return end
            loading = true
            fields.LoadStatus:Set("loading account…")
            local ok, identity = pcall(self.LoadAccount, self, fields.Account:Get())
            loading = false
            if not panel.Alive then return end
            if not ok then fields.LoadStatus:Set(tostring(identity)); return end
            draft.AccountId = identity.AccountId
            for key, value in pairs({ Username = identity.Name, DisplayName = identity.DisplayName,
                UserId = ("%.0f"):format(identity.UserId), Appearance = identity.Appearance }) do
                draft[key] = value
                fields[key]:Set(value, true)
            end
            updatePreview()
            fields.LoadStatus:Set("account loaded · edit or apply identity")
        end })
        content:Divider()
        content:Label("identity")
        for _, field in ipairs({ { "Username", "username" }, { "DisplayName", "display name" }, { "UserId", "user id" } }) do
            local key = field[1]
            fields[key] = content:Input({
                Text = field[2], Flag = false, Default = draft[key],
                Callback = function(value) draft[key] = value; updatePreview() end,
            })
        end
        content:Divider()
        content:Label("appearance")
        fields.Appearance = content:Dropdown({
            Text = "avatar & character", Flag = false, Options = { "loaded account", "keep mine", "anonymous" }, Default = draft.Appearance,
            Callback = function(value) draft.Appearance = value; updatePreview() end,
        })
        content:Label("badges · coming later")
        fields.StatusIcon = content:Dropdown({
            Text = "status icon · left", Flag = false,
            Options = { "default", "none", "premium", "friend", "place owner", "star creator", "administrator", "intern" },
            Default = "default", Disabled = true,
        })
        fields.Verification = content:Dropdown({
            Text = "verification · right", Flag = false, Options = { "default", "none", "verified" },
            Default = "default", Disabled = true,
        })
        content:Divider()
        content:Label("preview")
        fields.Preview = content:Label("")
        updatePreview = function()
            fields.Preview:Set(draft.DisplayName .. "\n@" .. draft.Username .. " · id " .. draft.UserId
                .. "\nappearance: " .. draft.Appearance)
        end
        updatePreview()
        fields.Status = content:Label("")
        fields.Actions = content:ButtonRow({
            { Text = "close", Callback = function() editor:SetOpen(false) end },
            { Text = "apply identity", Callback = function()
                if not panel.Alive then return end
                local ok, err = pcall(function()
                    local idText = fields.UserId:Get():match("^%s*(.-)%s*$")
                    assert(idText:match("^%d+$"), "user id must contain digits only")
                    self:SetCustom({ Name = fields.Username:Get(), DisplayName = fields.DisplayName:Get(),
                        UserId = tonumber(idText), Appearance = fields.Appearance:Get(), AccountId = draft.AccountId })
                    self:SetMethod("custom")
                end)
                fields.Status:Set(ok and "identity applied" or tostring(err))
            end },
        })
        local editButton
        panel.Method = self.Options.Method
        toggle(section, "Enabled", "user identity"):Gear(function(content)
            toggle(content, "HideUsername", "hide username")
            toggle(content, "HideDisplayName", "hide display name")
            toggle(content, "HideAvatar", "hide avatar")
            toggle(content, "HideUserIds", "hide user ids")
            content:Divider()
            toggle(content, "AffectFacility", "affect facility")
            toggle(content, "AffectGame", "affect game")
        end, { MaxHeight = opts.GearMaxHeight or 220 })
        panel.MethodControl = section:Dropdown({
            Text = "method", Flag = false, Options = { "anonymous", "custom", "randomised" }, Default = self.Options.Method,
            Callback = function(value)
                self:SetMethod(value)
                panel.Method = value
                if editButton then editButton:SetVisible(value == "custom") end
            end,
        })
        editButton = section:Button({
            Text = "edit custom identity",
            Callback = function() editor:SetOpen(true) end,
        })
        editButton:SetVisible(self.Options.Method == "custom")
        panel.EditCustom = editButton
        panel.RandomStatus = section:Label(self.Options.Method ~= "randomised" and ""
            or randomState == "loading" and "loading random identity…"
            or randomState == "ready" and "random identity ready"
            or randomState == "fallback" and "using anonymous identity"
            or "")
        section:Divider()
        local playerLabels = opts.PlayerLabels or {}
        local function playerToggle(owner, key, fallback)
            local control = owner:Toggle({
                Text = playerLabels[key] or fallback, Flag = false, Default = self.PlayerOptions[key],
                Callback = function(value) self:SetPlayerOptions({ [key] = value }) end,
            })
            panel.PlayerControls[key] = control
            return control
        end
        playerToggle(section, "Enabled", "players identity"):Gear(function(content)
            playerToggle(content, "HideUsername", "hide usernames")
            playerToggle(content, "HideDisplayName", "hide display names")
            playerToggle(content, "HideAvatar", "hide avatars")
            playerToggle(content, "HideUserIds", "hide user ids")
            content:Divider()
            playerToggle(content, "AffectFacility", "affect facility")
            playerToggle(content, "AffectGame", "affect game")
        end, { MaxHeight = opts.GearMaxHeight or 220 })
        panel.PlayerMethodControl = section:Dropdown({
            Text = playerLabels.Method or "method", Flag = false, Options = { "anonymous" },
            Default = "anonymous", Disabled = true,
        })
        local ownedConnections, hooks, floating = {}, {}, {}
        for i = connectionStart + 1, #Library.Connections do table.insert(ownedConnections, Library.Connections[i]) end
        for i = repaintStart + 1, #Library.RepaintHooks do table.insert(hooks, Library.RepaintHooks[i]) end
        for _, node in ipairs(window.Overlay:GetChildren()) do
            if not overlayBefore[node] then table.insert(floating, node) end
        end
        panels[panel] = true
        function panel:Destroy(fromRoot)
            if not self.Alive then return end
            self.Alive = false
            panels[self] = nil
            editorRoots[editor.Root] = nil
            editor:Destroy()
            for _, connection in ipairs(ownedConnections) do
                connection:Disconnect()
                local index = table.find(Library.Connections, connection)
                if index then table.remove(Library.Connections, index) end
            end
            for _, hook in ipairs(hooks) do
                local index = table.find(Library.RepaintHooks, hook)
                if index then table.remove(Library.RepaintHooks, index) end
            end
            local ownedRoots = { self.Instance }
            for _, node in ipairs(floating) do table.insert(ownedRoots, node) end
            for i = #(Library.Painted or {}), 1, -1 do
                local node = Library.Painted[i][1]
                for _, root in ipairs(ownedRoots) do
                    if node == root or node:IsDescendantOf(root) then table.remove(Library.Painted, i); break end
                end
            end
            for i = #(window.FloatStack or {}), 1, -1 do
                if table.find(floating, window.FloatStack[i].Frame) then table.remove(window.FloatStack, i) end
            end
            for _, node in ipairs(floating) do node:Destroy() end
            if not fromRoot then self.Instance:Destroy() end
            if self.Tab then self.Tab:Destroy() end
        end
        panel.Instance.Destroying:Once(function() panel:Destroy(true) end)
        return panel
    end

    function manager:BuildPrivacyTab(window, opts)
        opts = opts or {}
        local tab = window:Tab(opts.Title or "privacy", opts.Icon or "shield")
        local panel = self:BuildPrivacySection(tab, 1, opts)
        panel.Tab = tab
        return panel
    end

    local function untrackPlayer(player)
        local record = activePlayers[player]
        if not record then return end
        activePlayers[player], activeById[player.UserId] = nil, nil
        detachCharacter(record)
        for _, connection in ipairs(record.connections) do connection:Disconnect() end
    end
    local function trackPlayer(player)
        if activePlayers[player] then return end
        local previous = activeById[player.UserId]
        if previous then untrackPlayer(previous) end
        rememberIdentity(player)
        local record = { connections = {} }
        activePlayers[player], activeById[player.UserId] = record, player
        local function changed()
            rememberIdentity(player)
            manager:Refresh()
        end
        table.insert(record.connections, player:GetPropertyChangedSignal("DisplayName"):Connect(changed))
        table.insert(record.connections, player:GetPropertyChangedSignal("Name"):Connect(changed))
        table.insert(record.connections, player.CharacterAdded:Connect(function(model) attachCharacter(player, record, model) end))
        table.insert(record.connections, player.CharacterRemoving:Connect(function(model)
            if record.model == model then detachCharacter(record) end
        end))
        attachCharacter(player, record, player.Character)
    end

    function manager:Destroy()
        if not self.Alive then return end
        self.Alive = false
        for model in pairs(previewModels) do forgetPreview(model) end
        for player in pairs(activePlayers) do untrackPlayer(player) end
        for node in pairs(watched) do forget(node, true) end
        for root, record in pairs(roots) do
            for _, connection in ipairs(record.connections) do connection:Disconnect() end
            roots[root] = nil
        end
        for _, connection in ipairs(connections) do connection:Disconnect() end
        for panel in pairs(panels) do panel:Destroy() end
        for id, rigs in pairs(accounts) do
            for _, rig in pairs(rigs) do rig:Destroy() end
            accounts[id] = nil
        end
        if Library.PrivacyManager == self then Library.PrivacyManager = nil end
        if Library.Addons.PrivacyManager == self then Library.Addons.PrivacyManager = nil end
    end

    trackPlayer(LocalPlayer)
    for _, player in ipairs(Players:GetPlayers()) do trackPlayer(player) end
    table.insert(connections, Players.PlayerAdded:Connect(function(player)
        trackPlayer(player)
        if randomIdentity and player.UserId == randomIdentity.UserId then
            randomIdentity, pendingIdentity, randomState = nil, nil, "fallback"
        end
        manager:Refresh()
    end))
    table.insert(connections, Players.PlayerRemoving:Connect(function(player)
        -- Keep identity snapshots for old messages and a stable alias on rejoin.
        untrackPlayer(player)
        manager:Refresh()
    end))
    for root in pairs(Library.GuiRoots or {}) do manager:WatchRoot(root, "facility") end
    return manager
end
