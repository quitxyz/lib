-- Facility addon | InterfaceManager
-- Reglages de l'interface elle-meme : touche du menu, echelle, dechargement.

return function(Library)
	local InterfaceManager = {}
	InterfaceManager.Library = Library
	InterfaceManager.Folder = "Facility"
	InterfaceManager.Flags = { "interface_menu_key", "interface_scale", "interface_hotkeys" }

	function InterfaceManager:SetLibrary(lib)
		self.Library = lib or Library
	end

	function InterfaceManager:SetWindow(window)
		self.Window = window
	end

	function InterfaceManager:SetFolder(folder)
		self.Folder = folder
		self.Library:BuildFolders(folder)
	end

	function InterfaceManager:GetWindow()
		return self.Window or self.Library.Windows[1]
	end

	function InterfaceManager:BuildInterfaceSection(tab, column)
		self.Settings = self.Settings or { MenuKey = "RightShift", Scale = 100, Hotkeys = false }

		local section = tab:Section("interface", column or 1)
		local window = self:GetWindow()

		local menuKey = section:Keybind({
			Text = "menu key",
			Flag = "interface_menu_key",
			Default = self.Settings.MenuKey,
			OnChanged = function(key)
				self.Settings.MenuKey = key or ""
				self.Library:SetToggleKey(key)
			end,
		})

		local scale = section:Slider({
			Text = "ui scale",
			Flag = "interface_scale",
			Min = 70,
			Max = 130,
			Suffix = "%",
			Default = self.Settings.Scale,
			Callback = function(v)
				self.Settings.Scale = v
				local win = self:GetWindow()
				if win then win:SetUserScale(v / 100) end
			end,
		})

		local hotkeys = section:Toggle({
			Text = "hotkeys panel",
			Flag = "interface_hotkeys",
			Hint = "shows active keybinds on screen",
			Default = self.Settings.Hotkeys == true,
			Callback = function(state)
				self.Settings.Hotkeys = state
				self.Library:SetHotkeysVisible(state)
			end,
		})

		section:Button({
			Text = "unload",
			Callback = function()
				local window = self:GetWindow()
				if not window then return self.Library:Destroy() end
				window:Confirm({
					Title = "unload",
					Text = "Unload the interface? Unsaved changes will be lost.",
					Confirm = "unload",
					Cancel = "cancel",
					OnConfirm = function() self.Library:Destroy() end,
				})
			end,
		})

		menuKey:Set(self.Settings.MenuKey)
		scale:Set(self.Settings.Scale)
		hotkeys:Set(self.Settings.Hotkeys == true)

		self.Section = section
		return section
	end

    -- Modern preset. Legacy BuildInterfaceSection remains available.
    function InterfaceManager:Create(tab, opts)
        opts = opts or {}
        local lib = self.Library
        local window = opts.Window or tab.Window or self:GetWindow()
        assert(window, "InterfaceManager requires a window")
        local HttpService = game:GetService("HttpService")
        local Players = game:GetService("Players")
        local fs = lib.FileSystem
        local folder = opts.SettingsFolder or (self.Folder .. "/settings")
        if opts.ResetFolder then
            assert(type(opts.ResetFolder) == "string" and opts.ResetFolder:match("^[%w_%-]+$"),
                "ResetFolder must be a single script-owned root folder")
        end
        local ready, reason = fs:EnsureFolder(folder)
        assert(ready, reason)
        local path = folder .. "/interface.json"
        local auto = opts.AutoExecute or {}
        assert(type(auto) == "table", "AutoExecute must be a table")
        assert(not (auto.URL and auto.Code), "Provide AutoExecute.URL or Code, not both")
        assert(auto.URL == nil or (type(auto.URL) == "string" and auto.URL:match("^https://")),
            "AutoExecute.URL must be an HTTPS URL")
        assert(auto.Code == nil or type(auto.Code) == "string", "AutoExecute.Code must be a string")
        local queueTeleport = queue_on_teleport or queueonteleport
        local loader = auto.Code
        if auto.URL then
            loader = ("local source = game:HttpGet(%q)\nlocal chunk, err = loadstring(source)\nassert(chunk, err)\nchunk()"):format(auto.URL)
        end
        local canQueue = type(queueTeleport) == "function" and type(loader) == "string" and loader ~= ""
        local defaults = opts.Defaults or {}
        local values = {
            ShowOnLoad = defaults.ShowOnLoad ~= false,
            AutoExecute = auto.Default == true,
            Notifications = defaults.Notifications or "right",
            Scale = defaults.Scale or 100,
            Opacity = defaults.Opacity or 100,
            MenuBind = defaults.MenuBind or "RightShift",
        }
        local function valid(key, value)
            if key == "ShowOnLoad" or key == "AutoExecute" then return type(value) == "boolean" end
            if key == "Notifications" then return value == "right" or value == "none" end
            if key == "Scale" then return type(value) == "number" and value >= 60 and value <= 140 end
            if key == "Opacity" then return type(value) == "number" and value >= 20 and value <= 100 end
            if key == "MenuBind" then return type(value) == "string" end
            return false
        end
        local resetDefaults = {}
        for key, value in pairs(values) do
            assert(valid(key, value), "Invalid default: " .. key)
            resetDefaults[key] = value
        end
        local function report(message)
            if opts.OnError then lib:SafeCallback("interface", opts.OnError, message)
            else warn("Interface: " .. tostring(message)) end
        end
        local raw = fs:Read(path)
        if raw then
            local ok, saved = pcall(HttpService.JSONDecode, HttpService, raw)
            if ok and type(saved) == "table" then
                for key in pairs(values) do if valid(key, saved[key]) then values[key] = saved[key] end end
            else report("Could not read saved interface settings; using defaults.") end
        end
        local api = { Alive = true, Controls = {}, Settings = values, SettingsPath = path }
        local show, labels = opts.Controls or {}, opts.Labels or {}
        local function text(key, fallback) return labels[key] or fallback end
        local connectionStart, hookStart = #lib.Connections, #lib.RepaintHooks
        local overlayBefore = {}
        for _, node in ipairs(window.Overlay:GetChildren()) do overlayBefore[node] = true end
        local section = tab:Section(opts.Title or "ui & script", opts.Column or 1)
        api.Section, api.Instance = section, section.Frame
        local initializing = true
        function api:Save()
            local ok, encoded = pcall(HttpService.JSONEncode, HttpService, values)
            if not ok then return false, encoded end
            return fs:Write(path, encoded)
        end
        local function change(key, value)
            if not api.Alive or not valid(key, value) then return end
            if key == "AutoExecute" and value and not canQueue then
                if api.Controls.AutoExecute then api.Controls.AutoExecute:Set(false, true) end
                return
            end
            values[key] = value
            if key == "Notifications" then lib.NotificationsEnabled = value ~= "none"
            elseif key == "Scale" then window:SetUserScale(value / 100)
            elseif key == "Opacity" then window:SetOpacity(value / 100)
            elseif key == "MenuBind" then lib:SetToggleKey(value) end
            -- ShowOnLoad changes the next launch, not the currently visible window.
            if not initializing then
                local ok, err = api:Save()
                if not ok then report("Could not save interface settings: " .. tostring(err)) end
            end
        end
        local function flag(key)
            local flags = opts.Flags or {}
            return flags[key] or false
        end
        if show.ShowOnLoad ~= false then
            api.Controls.ShowOnLoad = section:Toggle({
                Text = text("ShowOnLoad", "show ui on load"), Flag = flag("ShowOnLoad"),
                Hint = text("ShowOnLoadHint", "show the window when the script starts. applies on the next launch."),
                Default = values.ShowOnLoad,
                Callback = function(value) change("ShowOnLoad", value) end,
            })
        end
        if show.AutoExecute ~= false then
            api.Controls.AutoExecute = section:Toggle({
                Text = text("AutoExecute", "auto execute"), Flag = flag("AutoExecute"),
                Hint = text("AutoExecuteHint", canQueue
                    and "run this script again after teleporting. does not run when roblox first opens."
                    or "requires a configured script loader and queue teleport support."),
                Default = canQueue and values.AutoExecute,
                Callback = function(value) change("AutoExecute", value) end,
            })
            api.Controls.AutoExecute:SetEnabled(canQueue)
        end
        if show.Notifications ~= false then
            api.Controls.Notifications = section:Dropdown({
                Text = text("Notifications", "notifications"), Flag = flag("Notifications"),
                Options = { "right", "none" }, Default = values.Notifications,
                Callback = function(value) change("Notifications", value) end,
            })
        end
        for _, key in ipairs({ "Scale", "Opacity" }) do
            if show[key] ~= false then
                local selected = key
                api.Controls[key] = section:Slider({
                    Text = text(key, key == "Scale" and "ui scale" or "ui opacity"),
                    Flag = flag(key), Min = key == "Scale" and 60 or 20,
                    Max = key == "Scale" and 140 or 100, Suffix = "%", Default = values[key],
                    Callback = function(value) change(selected, value) end,
                })
            end
        end
        section:Divider()
        if show.MenuBind ~= false then
            api.Controls.MenuBind = section:Keybind({
                Text = text("MenuBind", "menu bind"), Flag = flag("MenuBind"), Default = values.MenuBind,
                OnChanged = function(value) change("MenuBind", value or "") end,
            })
        end
        if show.Unload ~= false then
            api.Controls.Unload = section:Button({
                Text = text("Unload", "unload"), Callback = function() lib:Destroy() end,
            })
        end
        function api:ResetInterface()
            if not self.Alive then return false, "interface is destroyed" end
            initializing = true
            for key, value in pairs(resetDefaults) do
                -- Reset always disables auto execution, regardless of its creation default.
                if key == "AutoExecute" then value = false end
                values[key] = value
                local control = self.Controls[key]
                if control then control:Set(value, true) end
                change(key, value)
            end
            initializing = false
            local ok, result = self:Save()
            if not ok then report("Interface reset could not be saved: " .. tostring(result)) end
            return ok, result
        end
        local resetModal
        if show.Reset ~= false and show.HardReset ~= false then
            resetModal = window:Modal({ Title = text("Reset", "reset"), Width = 330, Height = 220 })
            api.ResetModal = resetModal
            resetModal.Content:Label(text("ResetHelp", "reset interface preferences or delete all script files."))
            resetModal.Content:Button({
                Text = text("ResetInterface", "reset interface"),
                Callback = function()
                    local ok = api:ResetInterface()
                    if ok then resetModal:SetOpen(false) end
                end,
            })
            if opts.ResetFolder then
                local resetFolder = opts.ResetFolder
                resetModal.Content:Button({
                    Text = text("ResetConfirm", "delete everything"), Color = lib.Theme.Danger,
                    Callback = function()
                        resetModal:SetOpen(false)
                        window:Confirm({
                            Title = text("HardReset", "hard reset"),
                            Text = text("ResetPrompt", "delete all script settings and configs, then unload?"),
                            Confirm = text("ResetConfirm", "delete everything"), ConfirmColor = lib.Theme.Danger,
                            Cancel = text("Cancel", "cancel"),
                            OnConfirm = function()
                                local ok, err = pcall(function()
                                    if fs.Native then
                                        assert(type(isfolder) == "function", "Folder checks unavailable")
                                        if isfolder(resetFolder) then
                                            assert(type(delfolder) == "function", "Folder deletion unavailable")
                                            delfolder(resetFolder)
                                            assert(not isfolder(resetFolder), "Folder was not deleted")
                                        end
                                    end
                                    for name in pairs(fs.Memory) do
                                        if name == resetFolder or name:sub(1, #resetFolder + 1) == resetFolder .. "/" then
                                            fs.Memory[name] = nil
                                        end
                                    end
                                end)
                                if not ok then report("Hard reset failed: " .. tostring(err)); return end
                                lib:Destroy()
                            end,
                        })
                    end,
                })
            end
            resetModal.Content:Button({
                Text = text("Cancel", "cancel"),
                Callback = function() resetModal:SetOpen(false) end,
            })
            api.Controls.Reset = section:Button({
                Text = text("Reset", "reset"),
                Callback = function() resetModal:SetOpen(true) end,
            })
            api.Controls.HardReset = api.Controls.Reset -- legacy handle
        end
        local teleportConnection
        local queued = false
        if canQueue then
            teleportConnection = Players.LocalPlayer.OnTeleport:Connect(function(state)
                if not api.Alive or not values.AutoExecute or queued then return end
                if state ~= Enum.TeleportState.Started then return end
                -- Queue at departure so switching the toggle off beforehand queues nothing.
                local ok, err = pcall(function()
                    local prelude = ""
                    if auto.CarryGlobals then
                        assert(type(getgenv) == "function", "getgenv unavailable for CarryGlobals")
                        local carried = {}
                        for _, name in ipairs(auto.CarryGlobals) do
                            carried[name] = getgenv()[name]
                        end
                        local encoded = HttpService:JSONEncode(carried)
                        prelude = ("local carried = game:GetService(%q):JSONDecode(%q)\nfor name, value in pairs(carried) do getgenv()[name] = value end\n")
                            :format("HttpService", encoded)
                    end
                    local guard = ""
                    if fs.Native then
                        guard = ("local ok, saved = pcall(function() return game:GetService(%q):JSONDecode(readfile(%q)) end)\nif ok and saved.AutoExecute == false then return end\n")
                            :format("HttpService", path)
                    end
                    queueTeleport(guard .. prelude .. loader)
                end)
                queued = ok
                if not ok then report("Auto execute could not be queued: " .. tostring(err)) end
            end)
        end
        -- A successful queue is retained across failed teleports by some executors.
        -- Do not enqueue duplicates on retry; executor-specific queue retention varies.
        local connections, hooks, floating, registered = {}, {}, {}, {}
        for i = connectionStart + 1, #lib.Connections do table.insert(connections, lib.Connections[i]) end
        for i = hookStart + 1, #lib.RepaintHooks do table.insert(hooks, lib.RepaintHooks[i]) end
        for _, node in ipairs(window.Overlay:GetChildren()) do
            if not overlayBefore[node] then table.insert(floating, node) end
        end
        for key in pairs(api.Controls) do
            local name = flag(key)
            if name then registered[name] = lib.Registry[name] end
        end
        function api:Destroy(fromRoot)
            if not self.Alive then return end
            self.Alive = false
            if teleportConnection then teleportConnection:Disconnect() end
            if resetModal then resetModal:Destroy() end
            for _, connection in ipairs(connections) do
                connection:Disconnect()
                local index = table.find(lib.Connections, connection)
                if index then table.remove(lib.Connections, index) end
            end
            for _, hook in ipairs(hooks) do
                local index = table.find(lib.RepaintHooks, hook)
                if index then table.remove(lib.RepaintHooks, index) end
            end
            for name, entry in pairs(registered) do
                if lib.Registry[name] == entry then lib.Registry[name], lib.Flags[name] = nil, nil end
            end
            for i = #(lib.Painted or {}), 1, -1 do
                local node = lib.Painted[i][1]
                if node == self.Instance or node:IsDescendantOf(self.Instance) then table.remove(lib.Painted, i) end
            end
            for i = #(window.FloatStack or {}), 1, -1 do
                if table.find(floating, window.FloatStack[i].Frame) then table.remove(window.FloatStack, i) end
            end
            for i = #(lib.Painted or {}), 1, -1 do
                local node = lib.Painted[i][1]
                for _, root in ipairs(floating) do
                    if node == root or node:IsDescendantOf(root) then table.remove(lib.Painted, i); break end
                end
            end
            for _, node in ipairs(floating) do node:Destroy() end
            if not fromRoot then self.Instance:Destroy() end
        end
        api.Instance.Destroying:Once(function() api:Destroy(true) end)
        for _, key in ipairs({ "Notifications", "Scale", "Opacity", "MenuBind" }) do change(key, values[key]) end
        -- Avoid the window's opening animation when applying the initial visibility.
        window.Scale.Scale = window.BaseScale
        lib.Open = values.ShowOnLoad
        window.Visible = values.ShowOnLoad
        window.Main.Visible = values.ShowOnLoad
        lib:RefreshCursor()
        initializing = false
        return api
    end

	return InterfaceManager
end
