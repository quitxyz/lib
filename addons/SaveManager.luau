-- Facility addon | SaveManager
-- Sauvegarde et chargement des configurations, au format JSON.

return function(Library)
	local HttpService = game:GetService("HttpService")
	local FileSystem = Library.FileSystem
	local Theme = Library.Theme

	local SaveManager = {}
	SaveManager.Library = Library
	SaveManager.Folder = "Facility"
	SaveManager.Ignore = {}
	SaveManager.Format = "json"

	function SaveManager:SetLibrary(lib)
		self.Library = lib or Library
	end

	function SaveManager:SetIgnoreIndexes(list)
		for _, key in ipairs(list or {}) do self.Ignore[key] = true end
	end

	function SaveManager:IgnoreThemeSettings()
		local library = self.Library
		if library.InterfaceManager then
			self:SetIgnoreIndexes(library.InterfaceManager.Flags)
		end
		if library.ThemeManager then
			self:SetIgnoreIndexes(library.ThemeManager.Flags)
		end
	end

	function SaveManager:SetFolder(folder)
		self.Folder = folder
		self.ConfigFolder = nil
		self.SettingsFolder = nil
		local ok, err = FileSystem:EnsureFolder(folder .. "/configs")
		if not ok then return false, err end
		return FileSystem:EnsureFolder(folder .. "/settings")
	end

	function SaveManager:SetConfigFolder(folder)
		local ok, err = FileSystem:EnsureFolder(folder)
		if not ok then return false, err end
		self.ConfigFolder = folder
		return true, err
	end

	function SaveManager:SetSettingsFolder(folder)
		local ok, err = FileSystem:EnsureFolder(folder)
		if not ok then return false, err end
		self.SettingsFolder = folder
		return true, err
	end

	function SaveManager:ConfigPath()
		return self.ConfigFolder or self.Folder .. "/configs"
	end

	function SaveManager:Path(file)
		return self:ConfigPath() .. "/" .. file
	end

	function SaveManager:List()
		local files = {}
		for _, file in ipairs(FileSystem:List(self:ConfigPath())) do
			if file:sub(-5) == ".json" then table.insert(files, file) end
		end
		return files
	end

	local function filename(name)
		if type(name) ~= "string" then return nil, "invalid config name" end
		name = name:match("^%s*(.-)%s*$")
		if name:sub(-5) == ".json" then name = name:sub(1, -6) end
		if name == "" or #name > 64 or not name:match("^[%w_%- ]+$") then
			return nil, "use 1-64 letters, numbers, spaces, underscores or hyphens"
		end
		return name .. ".json"
	end

	function SaveManager:Save(name)
		local file, err = filename(name)
		if not file then return false, err end
		local ok, encoded = pcall(function()
			return HttpService:JSONEncode(self.Library:GetConfig(self.Ignore))
		end)
		if not ok then return false, "encode failed" end
		local ready, reason = FileSystem:EnsureFolder(self:ConfigPath())
		if not ready then return false, reason end
		local written, storage = FileSystem:Write(self:Path(file), encoded)
		if not written then return false, storage end
		self.Library:ClearDirty()
		return true, file, storage
	end

	function SaveManager:Load(file)
		local normalized, err = filename(file)
		if not normalized then return false, err end
		file = normalized
		local raw, reason = FileSystem:Read(self:Path(file))
		if not raw then return false, reason end
		local ok, data = self:Decode(raw)
		if not ok then return false, data end
		local applied, applyError = self.Library:LoadConfig(data, self.Ignore)
		if applied == false then return false, applyError end
		return true, file
	end

	function SaveManager:Delete(file)
		local normalized, err = filename(file)
		if not normalized then return false, err end
		file = normalized
		local deleted, reason = FileSystem:Delete(self:Path(file))
		if not deleted then return false, reason end
		if self:GetAutoload() == file then
			local cleared, clearError = self:ClearAutoload()
			if not cleared then return false, "config deleted; autoload removal failed: " .. tostring(clearError) end
		end
		return true, file
	end

	function SaveManager:AutoloadPath()
		return (self.SettingsFolder or self.ConfigFolder or self.Folder .. "/settings") .. "/autoload.txt"
	end

	function SaveManager:GetAutoload()
		local name = FileSystem:Read(self:AutoloadPath())
		if name == "" then return nil end
		return name
	end

	function SaveManager:SetAutoload(file)
		local normalized, err = filename(file)
		if not normalized then return false, err end
		local raw, reason = FileSystem:Read(self:Path(normalized))
		if not raw then return false, reason end
		local folder = self.SettingsFolder or self.ConfigFolder or self.Folder .. "/settings"
		local ready, folderError = FileSystem:EnsureFolder(folder)
		if not ready then return false, folderError end
		return FileSystem:Write(self:AutoloadPath(), normalized)
	end

	function SaveManager:ClearAutoload()
		return FileSystem:Delete(self:AutoloadPath())
	end

	function SaveManager:LoadAutoloadConfig()
		local file = self:GetAutoload()
		if not file then return false end
		local ok, err = self:Load(file)
		self.Library:Notify({
			Title = ok and "config loaded" or "config error",
			Text = ok and file or tostring(err),
			Duration = 3,
		})
		return ok
	end

    function SaveManager:Decode(raw)
        local ok, result = pcall(function()
            local decoded = HttpService:JSONDecode(raw)
            assert(type(decoded) == "table", "config must be a JSON object")
            local data = {}
            for flag, value in pairs(decoded) do
                assert(type(flag) == "string", "config must use named flags")
                local entry = self.Library.Registry[flag]
                if entry and not self.Ignore[flag] then
                    local kind = entry.Type
                    if kind == "Slider" then
                        assert(type(value) == "number" and value == value and math.abs(value) < math.huge,
                            "invalid number for " .. flag)
                    elseif kind == "Toggle" then
                        assert(type(value) == "boolean", "invalid toggle for " .. flag)
                    elseif kind == "Input" or kind == "Keybind" or kind == "ColorPicker" then
                        assert(type(value) == "string", "invalid text value for " .. flag)
                    elseif kind == "MultiDropdown" then
                        assert(type(value) == "table", "invalid selection for " .. flag)
                        for _, item in pairs(value) do
                            assert(type(item) == "string", "invalid selection for " .. flag)
                        end
                    elseif kind == "Dropdown" then
                        local current = entry.Get()
                        assert(type(value) == "string" or type(value) == "number", "invalid selection for " .. flag)
                        assert(current == nil or type(value) == type(current), "invalid selection for " .. flag)
                    end
                    data[flag] = value
                end
            end
            return data
        end)
        return ok, result
    end

    local function readableJson(data)
        local keys, lines = {}, { "{" }
        for key in pairs(data) do table.insert(keys, key) end
        table.sort(keys)
        for index, key in ipairs(keys) do
            table.insert(lines, ("    %s: %s%s"):format(
                HttpService:JSONEncode(key), HttpService:JSONEncode(data[key]),
                index < #keys and "," or ""
            ))
        end
        table.insert(lines, "}")
        return table.concat(lines, "\n")
    end

    function SaveManager:Export(file)
        local normalized, reason = filename(file)
        if not normalized then return false, reason end
        local raw, err = FileSystem:Read(self:Path(normalized))
        if not raw then return false, err end
        local ok, data = self:Decode(raw)
        if not ok then return false, data end
        return pcall(readableJson, data)
    end

    function SaveManager:Import(name, raw)
        local file, reason = filename(name)
        if not file then return false, reason end
        if table.find(self:List(), file) then return false, "config already exists; choose a new name" end
        local ok, data = self:Decode(raw)
        if not ok then return false, data end
        local encoded, json = pcall(readableJson, data)
        if not encoded then return false, json end
        local ready, err = FileSystem:EnsureFolder(self:ConfigPath())
        if not ready then return false, err end
        local written, storage = FileSystem:Write(self:Path(file), json)
        if not written then return false, storage end
        return true, file, storage
    end

    function SaveManager:Create(tab, opts)
        opts = opts or {}
        local manager, lib = self, self.Library
        local window = opts.Window or tab.Window or lib.Windows[1]
        assert(window, "config panel requires a window")
        if opts.ConfigFolder then
            local ok, err = self:SetConfigFolder(opts.ConfigFolder)
            assert(ok, err)
        end
        self:IgnoreThemeSettings()
        local labels, show = opts.Labels or {}, opts.Controls or {}
        local function text(key, fallback) return labels[key] or fallback end
        local connectionStart, repaintStart = #lib.Connections, #lib.RepaintHooks
        local overlayBefore = {}
        for _, node in ipairs(window.Overlay:GetChildren()) do overlayBefore[node] = true end
        local section = tab:Section(opts.Title or "configs", opts.Column or 2)
        local api = { Alive = true, Section = section, Instance = section.Frame, Controls = {} }
        local controls = api.Controls
        local importModal, jsonBox, importStatus
        local statusFailed = false
        local function report(message, failed)
            if not api.Alive then return end
            statusFailed = failed == true
            if controls.Status then
                controls.Status:Set(message)
                controls.Status:SetColor(statusFailed and lib.Theme.Danger or lib.Theme.TextDim)
            end
            if failed and opts.OnError then lib:SafeCallback("config error", opts.OnError, message) end
        end
        local function run(action)
            if not api.Alive then return false, "config panel is destroyed" end
            local ok, result = pcall(action)
            if not ok then report(tostring(result), true) end
            return ok, result
        end
        local function storageText(storage)
            return storage == "memory"
                and text("MemoryOnly", "stored in memory only; lost after a fresh execution.")
                or text("Saved", "saved to disk.")
        end
        function api:Refresh(selectFile)
            if not self.Alive then return end
            local files = manager:List()
            local previous = selectFile or controls.Saved:Get()
            local previousAuto = controls.Autoload:Get()
            local current = manager:GetAutoload()
            controls.Saved:SetOptions(files)
            controls.Saved:Set(table.find(files, previous) and previous or files[1], true)
            controls.Autoload:SetOptions(files)
            controls.Autoload:Set(table.find(files, previousAuto) and previousAuto
                or table.find(files, current) and current or files[1], true)
            if controls.AutoloadStatus then
                controls.AutoloadStatus:Set(text("AutoloadPrefix", "currently autoloading: ") .. (current or text("None", "none")))
            end
        end
        local function selected(control)
            local file = control:Get()
            assert(type(file) == "string" and table.find(manager:List(), file), "select an existing config first")
            return file
        end
        local function save(file)
            local ok, result, storage = manager:Save(file)
            assert(ok, result)
            api:Refresh(result)
            report(storageText(storage))
        end
        local function load(file)
            local ok, result = manager:Load(file)
            assert(ok, result)
            api:Refresh(result)
            report(text("LoadedPrefix", "loaded ") .. result)
        end
        local function newName()
            local file, reason = filename(controls.Name:Get())
            assert(file, reason)
            assert(not table.find(manager:List(), file), "config already exists; use save / overwrite")
            return file
        end
        local function row(items)
            local buttons, keys = {}, {}
            for _, item in ipairs(items) do
                local key, fallback, callback = item[1], item[2], item[3]
                if show[key] ~= false then
                    table.insert(keys, key)
                    table.insert(buttons, { Text = text(key, fallback), Callback = function() run(callback) end })
                end
            end
            if #buttons == 0 then return end
            local result = section:ButtonRow(buttons)
            for index, key in ipairs(keys) do controls[key] = result.Controls[index] end
        end
        controls.Name = section:Input({
            Text = text("Name", "config name"), Placeholder = text("NamePlaceholder", "enter a name"), Flag = false,
        })
        if show.Name == false then controls.Name.Instance.Visible = false end
        if show.Create ~= false then
            controls.Create = section:Button({
                Text = text("Create", "create config"), Callback = function() run(function() save(newName()) end) end,
            })
        end
        section:Divider()
        controls.Saved = section:Dropdown({
            Text = text("SavedList", "saved configs"), Flag = false, Options = {}, Empty = text("Empty", "no configs"),
        })
        if show.Saved == false then controls.Saved.Instance.Visible = false end
        row({
            { "Save", "save / overwrite", function() save(selected(controls.Saved)) end },
            { "Load", "load", function() load(selected(controls.Saved)) end },
        })
        row({
            { "Delete", "delete", function()
                local file = selected(controls.Saved)
                window:Confirm({
                    Title = text("DeleteTitle", "delete config"),
                    Text = text("DeletePrompt", "permanently delete %s?"):format(file),
                    Confirm = text("Delete", "delete"), ConfirmColor = lib.Theme.Danger, Cancel = text("Cancel", "cancel"),
                    OnConfirm = function() run(function()
                        local ok, err = manager:Delete(file)
                        api:Refresh()
                        assert(ok, err)
                        report(text("DeletedPrefix", "deleted ") .. file)
                    end) end,
                })
            end },
            { "Refresh", "refresh", function() api:Refresh(); report(text("Refreshed", "config list refreshed.")) end },
        })
        if show.Sharing ~= false then
            controls.Sharing = section:Label(text("Sharing", "sharing"))
            if show.Import ~= false then
                -- Build once, synchronously, so the panel owns all control subscriptions.
                importModal = window:Modal({
                    Title = text("Import", "import config"), Width = opts.ImportWidth or 420, Height = opts.ImportHeight or 360,
                })
                api.ImportModal = importModal
                importModal.Content:Label(text("ImportHelp", "enter a new name in the config panel, then paste JSON here."))
                jsonBox = importModal.Content:Input({
                    Text = text("Json", "config JSON"), Flag = false, Placeholder = text("JsonPlaceholder", "paste the copied config"),
                })
                api.JsonInput = jsonBox
                jsonBox.Box.Parent.Size = UDim2.new(1, 0, 0, opts.JsonHeight or 130)
                jsonBox.Box.MultiLine = true
                jsonBox.Box.TextWrapped = true
                jsonBox.Box.TextYAlignment = Enum.TextYAlignment.Top
                jsonBox.Box.Position = UDim2.fromOffset(10, 8)
                jsonBox.Box.Size = UDim2.new(1, -20, 1, -16)
                importStatus = importModal.Content:Label("")
                controls.ImportConfirm = importModal.Content:Button({
                    Text = text("ImportConfirm", "import"), Callback = function()
                        if not api.Alive then return end
                        local ok, err = pcall(function()
                            local success, file, storage = manager:Import(newName(), jsonBox:Get())
                            assert(success, file)
                            api:Refresh(file)
                            report(text("ImportedPrefix", "imported ") .. file .. ". " .. storageText(storage))
                            importModal:SetOpen(false)
                        end)
                        if not ok then
                            importStatus:Set(tostring(err))
                            importStatus:SetColor(lib.Theme.Danger)
                            report(tostring(err), true)
                        end
                    end,
                })
            end
            row({
                { "Copy", "copy config", function()
                    assert(type(setclipboard) == "function", "clipboard copying unavailable")
                    local file = selected(controls.Saved)
                    local ok, json = manager:Export(file)
                    assert(ok, json)
                    setclipboard(json)
                    report(text("CopiedPrefix", "copied ") .. file)
                end },
                { "Import", "import config", function()
                    importStatus:Set("")
                    if type(getclipboard) == "function" then
                        local ok, value = pcall(getclipboard)
                        if ok and type(value) == "string" then jsonBox:Set(value) end
                    end
                    importModal:SetOpen(true)
                end },
            })
        end
        section:Divider()
        controls.Autoload = section:Dropdown({
            Text = text("Autoload", "autoload config"), Flag = false, Options = {}, Empty = text("Empty", "no configs"),
        })
        if show.Autoload == false then controls.Autoload.Instance.Visible = false end
        row({
            { "SetAutoload", "set autoload", function()
                local ok, storage = manager:SetAutoload(selected(controls.Autoload))
                assert(ok, storage); api:Refresh(); report(storageText(storage))
            end },
            { "RemoveAutoload", "remove autoload", function()
                local ok, err = manager:ClearAutoload()
                assert(ok, err); api:Refresh(); report(text("AutoloadRemoved", "autoload removed."))
            end },
        })
        if show.AutoloadStatus ~= false then controls.AutoloadStatus = section:Label("") end
        if show.Dirty ~= false then controls.Dirty = section:Label("") end
        if show.Status ~= false then controls.Status = section:Label("") end
        local function showDirty(state)
            if not api.Alive or not controls.Dirty then return end
            controls.Dirty:Set(state and text("Unsaved", "unsaved changes") or text("Clean", "no unsaved changes"))
            controls.Dirty:SetColor(state and lib.Theme.Accent or lib.Theme.TextDim)
        end
        local dirtyConnection = lib:OnDirtyChanged(showDirty)
        lib:OnRepaint(function()
            if not api.Alive then return end
            showDirty(lib.Dirty)
            if controls.Status then controls.Status:SetColor(statusFailed and lib.Theme.Danger or lib.Theme.TextDim) end
        end)
        local connections, hooks, floating = {}, {}, {}
        for i = connectionStart + 1, #lib.Connections do table.insert(connections, lib.Connections[i]) end
        for i = repaintStart + 1, #lib.RepaintHooks do table.insert(hooks, lib.RepaintHooks[i]) end
        for _, node in ipairs(window.Overlay:GetChildren()) do
            if not overlayBefore[node] then table.insert(floating, node) end
        end
        function api:Destroy(fromRoot)
            if not self.Alive then return end
            self.Alive = false
            dirtyConnection:Disconnect()
            if importModal then importModal:Destroy() end
            for _, connection in ipairs(connections) do
                connection:Disconnect()
                local index = table.find(lib.Connections, connection)
                if index then table.remove(lib.Connections, index) end
            end
            for _, hook in ipairs(hooks) do
                local index = table.find(lib.RepaintHooks, hook)
                if index then table.remove(lib.RepaintHooks, index) end
            end
            local roots = { self.Instance }
            for _, root in ipairs(floating) do table.insert(roots, root) end
            for i = #(lib.Painted or {}), 1, -1 do
                local node = lib.Painted[i][1]
                for _, root in ipairs(roots) do
                    if node == root or node:IsDescendantOf(root) then table.remove(lib.Painted, i); break end
                end
            end
            for i = #(window.FloatStack or {}), 1, -1 do
                if table.find(floating, window.FloatStack[i].Frame) then table.remove(window.FloatStack, i) end
            end
            for _, node in ipairs(floating) do node:Destroy() end
            if not fromRoot then self.Instance:Destroy() end
        end
        api.Instance.Destroying:Once(function() api:Destroy(true) end)
        showDirty(lib.Dirty)
        run(function()
            api:Refresh()
            if opts.Autoload ~= false then
                local file = manager:GetAutoload()
                if file then load(file) end
            end
        end)
        return api
    end

    function SaveManager:BuildConfigSection(tab, column)
        local panel = self:Create(tab, { Column = column or 2, Autoload = false })
        self.Section = panel.Section
        self.Section.ConfigPanel = panel
        return self.Section
    end

	Library.DirtyIgnore = SaveManager.Ignore
	return SaveManager
end
