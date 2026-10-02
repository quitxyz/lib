-- Facility addon | PrivacyManager
-- Presentation-only local identity masking. Real player references stay untouched.
return function(Library)
    if Library.PrivacyManager and Library.PrivacyManager.Alive then return Library.PrivacyManager end
    local Players = game:GetService("Players")
    local LocalPlayer = Players.LocalPlayer
    assert(LocalPlayer, "PrivacyManager requires a local player")
    local manager = { Alive = true, Options = {
        Enabled = false, HideUsername = true, HideDisplayName = true, HideAvatar = true,
        AffectFacility = true, AffectGame = false,
    } }
    Library.PrivacyManager = manager
    local watched, roots, connections, panels = {}, {}, {}, {}
    local anonymousName = "player 001"

    local function wordByte(value)
        return value ~= "" and (value:match("[%w_]") ~= nil or value:byte() >= 128)
    end

    -- Match literal names with boundaries, longest first, without processing replacements again.
    local function replaceNames(source, names)
        local out, position = {}, 1
        while position <= #source do
            local first, last
            for _, name in ipairs(names) do
                local search = position
                while search <= #source do
                    local a, b = source:find(name, search, true)
                    if not a then break end
                    local before, after = source:sub(a - 1, a - 1), source:sub(b + 1, b + 1)
                    if not wordByte(before) and not wordByte(after) then
                        if not first or a < first or (a == first and b > last) then first, last = a, b end
                        break
                    end
                    search = b + 1
                end
            end
            if not first then table.insert(out, source:sub(position)); break end
            table.insert(out, source:sub(position, first - 1))
            table.insert(out, anonymousName)
            position = last + 1
        end
        return table.concat(out)
    end

    function manager:GetIdentity(player)
        player = player or LocalPlayer
        local enabled = self.Alive and self.Options.Enabled and player == LocalPlayer
        return {
            Name = enabled and self.Options.HideUsername and anonymousName or player.Name,
            DisplayName = enabled and self.Options.HideDisplayName and anonymousName or player.DisplayName,
            UserId = player.UserId,
        }
    end
    function manager:GetName(player) return self:GetIdentity(player).Name end
    function manager:GetDisplayName(player) return self:GetIdentity(player).DisplayName end

    function manager:ResolveText(value, scope, richText)
        if type(value) ~= "string" or not self.Alive or not self.Options.Enabled then return value end
        if scope == "game" then
            if not self.Options.AffectGame then return value end
        elseif not self.Options.AffectFacility then return value end
        local names = {}
        if self.Options.HideUsername and LocalPlayer.Name ~= "" then table.insert(names, LocalPlayer.Name) end
        if self.Options.HideDisplayName and LocalPlayer.DisplayName ~= "" then table.insert(names, LocalPlayer.DisplayName) end
        if #names == 0 then return value end
        if not richText then return replaceNames(value, names) end
        -- Preserve markup attributes; only replace visible text between tags.
        local out, position = {}, 1
        while position <= #value do
            local a, b = value:find("<[^>]*>", position)
            if not a then table.insert(out, replaceNames(value:sub(position), names)); break end
            table.insert(out, replaceNames(value:sub(position, a - 1), names))
            table.insert(out, value:sub(a, b))
            position = b + 1
        end
        return table.concat(out)
    end

    local anonymousAvatar = "rbxasset://textures/ui/GuiImagePlaceholder.png"

    function manager:ResolveImage(value, scope)
        if type(value) ~= "string" or not self.Alive or not self.Options.Enabled or not self.Options.HideAvatar then return value end
        if scope == "game" then
            if not self.Options.AffectGame then return value end
        elseif not self.Options.AffectFacility then return value end
        local query = value:match("^rbxthumb://(.+)$")
        if not query then return value end
        local params = {}
        for key, item in query:gmatch("([^&=?]+)=([^&]+)") do params[key:lower()] = item end
        local kind = (params.type or ""):lower()
        if tonumber(params.id) == LocalPlayer.UserId
            and (kind == "avatarheadshot" or kind == "avatarbust" or kind == "avatar") then
            return anonymousAvatar
        end
        return value
    end

    function manager:GetAvatar(player)
        player = player or LocalPlayer
        if self.Alive and self.Options.Enabled and self.Options.HideAvatar and player == LocalPlayer then
            return anonymousAvatar
        end
        return "rbxthumb://type=AvatarHeadShot&id=" .. player.UserId .. "&w=150&h=150"
    end

    local function scopeOf(node)
        local current = node
        local gameScope = false
        while current do
            if Library.GuiRoots and Library.GuiRoots[current] then return "facility" end
            if roots[current] and roots[current].scope == "game" then gameScope = true end
            current = current.Parent
        end
        return gameScope and "game" or nil
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
        watched[node] = nil
        for _, connection in ipairs(record.connections) do connection:Disconnect() end
        if restore then pcall(function() node[record.property] = record.original end) end
    end

    local function watch(node)
        if not manager.Alive or watched[node] then return end
        local property
        if node:IsA("TextLabel") or node:IsA("TextButton") then property = "Text"
        elseif node:IsA("ImageLabel") or node:IsA("ImageButton") then property = "Image"
        else return end
        local record = { property = property, original = node[property], rendered = node[property], connections = {} }
        watched[node] = record
        table.insert(record.connections, node:GetPropertyChangedSignal(property):Connect(function()
            if record.writing or node[property] == record.rendered then return end
            record.original = node[property]
            apply(node, record)
        end))
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

    function manager:Refresh()
        if not self.Alive then return end
        if self.Options.Enabled and self.Options.AffectGame then startGame() end
        for node, record in pairs(watched) do apply(node, record) end
        for panel in pairs(panels) do
            for key, control in pairs(panel.Controls) do control:Set(self.Options[key], true) end
        end
    end

    function manager:SetOptions(options)
        assert(type(options) == "table", "privacy options must be a table")
        for key, value in pairs(options) do
            assert(self.Options[key] ~= nil and type(value) == "boolean", "invalid privacy option: " .. tostring(key))
        end
        for key, value in pairs(options) do self.Options[key] = value end
        self:Refresh()
    end
    function manager:Restore() self:SetOptions({ Enabled = false }) end
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
        local panel = { Section = section, Instance = section.Frame, Controls = {}, Alive = true }
        local labels = opts.Labels or {}
        local function toggle(owner, key, fallback)
            local control = owner:Toggle({
                Text = labels[key] or fallback, Flag = false, Default = self.Options[key],
                Callback = function(value) self:SetOptions({ [key] = value }) end,
            })
            panel.Controls[key] = control
            return control
        end
        toggle(section, "Enabled", "user identity"):Gear(function(content)
            toggle(content, "HideUsername", "hide username")
            toggle(content, "HideDisplayName", "hide display name")
            toggle(content, "HideAvatar", "hide avatar")
            content:Divider()
            toggle(content, "AffectFacility", "affect facility")
            toggle(content, "AffectGame", "affect game ui")
        end)
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

    function manager:Destroy()
        if not self.Alive then return end
        self.Alive = false
        for node in pairs(watched) do forget(node, true) end
        for root, record in pairs(roots) do
            for _, connection in ipairs(record.connections) do connection:Disconnect() end
            roots[root] = nil
        end
        for _, connection in ipairs(connections) do connection:Disconnect() end
        for panel in pairs(panels) do panel:Destroy() end
        if Library.PrivacyManager == self then Library.PrivacyManager = nil end
        if Library.Addons.PrivacyManager == self then Library.Addons.PrivacyManager = nil end
    end

    for root in pairs(Library.GuiRoots or {}) do manager:WatchRoot(root, "facility") end
    table.insert(connections, LocalPlayer:GetPropertyChangedSignal("DisplayName"):Connect(function() manager:Refresh() end))
    return manager
end
