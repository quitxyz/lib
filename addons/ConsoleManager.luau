-- Facility addon | ConsoleManager
return function(Library)
    local LogService = game:GetService("LogService")
    local HttpService = game:GetService("HttpService")
    local ConsoleManager = {}

    function ConsoleManager:Create(targetOwner, opts)
        opts = opts or {}
        assert(targetOwner, "ConsoleManager requires a window, tab, or section")
        assert(type(opts.MaxVisibleRows or 100) == "number"
            and (opts.MaxVisibleRows or 100) >= 1 and (opts.MaxVisibleRows or 100) < math.huge,
            "MaxVisibleRows must be positive and finite")
        assert(opts.Output == nil or opts.Output == "console" or opts.Output == "roblox" or opts.Output == "both" or opts.Output == "none",
            "Output must be console, roblox, both, or none")
        assert(opts.Target == nil or opts.Target == "Script" or opts.Target == "Roblox" or opts.Target == "Both",
            "Target must be Script, Roblox, or Both")
        assert(opts.Prefix == nil or type(opts.Prefix) == "string", "Prefix must be a string")
        local window = type(targetOwner.Modal) == "function" and targetOwner or targetOwner.Window
        assert(window, "Console target must belong to a window")
        local connectionStart, repaintStart = #Library.Connections, #Library.RepaintHooks
        local overlayBefore = {}
        for _, child in ipairs(window.Overlay:GetChildren()) do overlayBefore[child] = true end
        local console = { Controls = {}, Window = window }
        local show = opts.Controls or {}
        local prefix = opts.Prefix or "Facility"
        local function labelText(key, fallback) return (opts.Labels or {})[key] or fallback end
        local function entryColor(level)
            local value = (opts.Colors or {})[level] or ({ Print = "Text", Warn = "TextMarked", Error = "Danger" })[level]
            return typeof(value) == "Color3" and value or Library.Theme[value] or Library.Theme.Text
        end
        local maxVisibleRows = opts.MaxVisibleRows or 100
        local output = opts.Output or "console"
        local uiOutput = output == "console" or output == "both"
        local robloxOutput = output == "roblox" or output == "both"
        if opts.UIOutput ~= nil then uiOutput = opts.UIOutput ~= false end
        if opts.RobloxOutput ~= nil then robloxOutput = opts.RobloxOutput ~= false end
        local consoleId = HttpService:GenerateGUID(false)
        local outputPrefix = "[" .. prefix .. ":" .. consoleId .. "] "
        local messageTypes = {
            Print = Enum.MessageType.MessageOutput,
            Warn = Enum.MessageType.MessageWarning,
            Error = Enum.MessageType.MessageError,
        }
        local entries = {}
        local clearedThrough = 0
        local target = opts.Target or "Both"
        local filters = {
            Print = not opts.Filters or opts.Filters.Print ~= false,
            Warn = not opts.Filters or opts.Filters.Warn ~= false,
            Error = not opts.Filters or opts.Filters.Error ~= false,
        }

        local alive = true
        local pending = false
        local pendingThread
        local saveCount = 0

        local consoleModal
        local content
        if type(targetOwner.Modal) == "function" then
            consoleModal = targetOwner:Modal({
                Title = opts.Title or "console", Width = opts.Width or 460, Height = opts.Height or 0.85,
            })
            content = consoleModal.Content
            console.Root, console.Modal = consoleModal.Root, consoleModal
        else
            assert(type(targetOwner.Cards) == "function", "ConsoleManager requires a window, tab, or section")
            content = targetOwner:Cards({ Spacing = opts.Spacing or 9 })
            console.Root = content.Instance
        end
        console.Content = content
        console.Instance = console.Root
        console.Alive = true
        local render

        function console:SetMaxVisibleRows(value)
            assert(type(value) == "number" and value >= 1 and value < math.huge,
                "MaxVisibleRows must be a positive finite number")
            maxVisibleRows = math.floor(value)
            if render and alive then render() end
        end

        console:SetMaxVisibleRows(maxVisibleRows)
        assert(output == "console" or output == "roblox" or output == "both" or output == "none",
            "Output must be console, roblox, both, or none")

        local function matches(entry)
            return (target == "Both" or entry.source == target)
                and filters[entry.level]
        end

        local function formatEntry(entry)
            return ("[%s] [%s] [%s] %s"):format(
                entry.time,
                entry.source,
                entry.level,
                entry.message
            )
        end

        local function scheduleRender()
            if pending or not alive then return end
            pending = true

            pendingThread = task.delay(0.1, function()
                pending = false
                pendingThread = nil

                if alive then
                    render()
                end
            end)
        end

        function console:SetUIOutput(enabled)
            if not alive then return end
            uiOutput = enabled ~= false
            if self.Controls.UIOutput then self.Controls.UIOutput:Set(uiOutput, true) end
        end

        function console:SetRobloxOutput(enabled)
            if not alive then return end
            robloxOutput = enabled ~= false
            if self.Controls.RobloxOutput then self.Controls.RobloxOutput:Set(robloxOutput, true) end
        end

        function console:SetOutput(value)
            assert(value == "console" or value == "roblox" or value == "both" or value == "none",
                "Invalid output destination")
            self:SetUIOutput(value == "console" or value == "both")
            self:SetRobloxOutput(value == "roblox" or value == "both")
        end

        function console:SetTarget(value)
            assert(value == "Script" or value == "Roblox" or value == "Both", "Invalid console target")
            if not alive then return end
            target = value
            if self.Controls.Target then self.Controls.Target:Set(string.lower(value), true) end
            scheduleRender()
        end

        function console:SetFilter(level, enabled)
            assert(messageTypes[level], "Invalid console level")
            if not alive then return end
            filters[level] = enabled ~= false
            if self.Controls[level] then self.Controls[level]:Set(filters[level], true) end
            scheduleRender()
        end

        local function addEntry(source, level, ...)
            if not alive then return end

            local values = table.pack(...)

            for index = 1, values.n do
                values[index] = tostring(values[index])
            end

            table.insert(entries, {
                source = source,
                level = level,
                time = os.date("%H:%M:%S"),
                message = table.concat(values, " ", 1, values.n),
            })

            scheduleRender()
        end

        local function write(level, ...)
            if not alive then return end

            if uiOutput then
                addEntry("Script", level, ...)
            end

            if robloxOutput then
                local values = table.pack(...)
                for index = 1, values.n do
                    values[index] = tostring(values[index])
                end

                local message = table.concat(values, " ", 1, values.n)
                -- RichText is for the UI; native output should be readable plain text.
                message = Library:ResolveText(message, "facility", true)
                message = message:gsub("<[^>]*>", "")

                local success = pcall(function()
                    LogService:Log(messageTypes[level], outputPrefix .. message, {
                        facilityConsole = consoleId,
                    })
                end)

                if not success then
                    -- Older clients may not expose LogService:Log. Keep Error non-throwing.
                    local nativeOutput = level == "Print" and print or warn
                    nativeOutput(outputPrefix .. "[" .. level .. "] " .. message)
                end
            end
        end

        function console:Print(...)
            write("Print", ...)
        end

        function console:Warn(...)
            write("Warn", ...)
        end

        function console:Error(...)
            write("Error", ...)
        end

        if show.Output ~= false then
            local builders = {}
            if show.UIOutput ~= false then
                table.insert(builders, function(column)
                    console.Controls.UIOutput = column:Toggle({
                        Text = labelText("UIOutput", "ui console"),
                        Hint = labelText("UIOutputHint",
                            "send script messages to this console. keeps collecting while the window is hidden."),
                        Flag = false,
                        Default = uiOutput,
                        Callback = function(value) console:SetUIOutput(value) end,
                    })
                end)
            end
            if show.RobloxOutput ~= false then
                table.insert(builders, function(column)
                    console.Controls.RobloxOutput = column:Toggle({
                        Text = labelText("RobloxOutput", "roblox console"),
                        Hint = labelText("RobloxOutputHint",
                            "send script messages to the native roblox console, even when ui console output is off."),
                        Flag = false,
                        Default = robloxOutput,
                        Callback = function(value) console:SetRobloxOutput(value) end,
                    })
                end)
            end
            if #builders > 0 then content:Split(builders) end
        end

        if show.Target ~= false then
            console.Controls.Target = content:Dropdown({
                Text = labelText("Target", "source"),
                Flag = false,
                Options = { "script", "roblox", "both" },
                Default = string.lower(target),
                Multi = false,
                Search = false,

                Callback = function(value)
                    console:SetTarget(({ script = "Script", roblox = "Roblox", both = "Both" })[value])
                end,
            })
        end

        if show.Filters ~= false then
            local builders = {}

            for _, level in ipairs({ "Print", "Warn", "Error" }) do
                local selectedLevel = level

                table.insert(builders, function(column)
                    console.Controls[selectedLevel] = column:Toggle({
                        Text = labelText(selectedLevel, string.lower(selectedLevel) .. "s"),
                        Flag = false,
                        Default = filters[selectedLevel],

                        Callback = function(value)
                            console:SetFilter(selectedLevel, value)
                        end,
                    })
                end)
            end

            content:Split(builders)
        end

        local logArea = Instance.new("ScrollingFrame")
        logArea.Name = "ConsoleOutput"
        logArea.Size = UDim2.new(1, 0, 0, opts.OutputHeight or 190)
        logArea.BorderSizePixel = 0
        logArea.CanvasSize = UDim2.new()
        logArea.AutomaticCanvasSize = Enum.AutomaticSize.Y
        logArea.ScrollingDirection = Enum.ScrollingDirection.Y
        logArea.ScrollBarThickness = 3
        logArea.ZIndex = consoleModal and consoleModal.Scroller.ZIndex or content.Container.ZIndex
        logArea.Parent = content.Container
        console.LogArea = logArea

        local corner = Instance.new("UICorner")
        corner.CornerRadius = UDim.new(0, 6)
        corner.Parent = logArea

        local padding = Instance.new("UIPadding")
        padding.PaddingTop = UDim.new(0, 8)
        padding.PaddingBottom = UDim.new(0, 8)
        padding.PaddingLeft = UDim.new(0, 8)
        padding.PaddingRight = UDim.new(0, 12)
        padding.Parent = logArea

        local layout = Instance.new("UIListLayout")
        layout.Padding = UDim.new(0, 5)
        layout.SortOrder = Enum.SortOrder.LayoutOrder
        layout.Parent = logArea

        render = function()
            local theme = Library.Theme

            logArea.BackgroundColor3 = theme.Field
            logArea.ScrollBarImageColor3 = theme.AccentDim

            for _, child in ipairs(logArea:GetChildren()) do
                if child:IsA("TextLabel") then
                    child:Destroy()
                end
            end

            local visible = {}

            -- Select newest matching entries, then display them in chronological order.
            for index = #entries, clearedThrough + 1, -1 do
                if matches(entries[index]) then
                    table.insert(visible, index)
                    if #visible >= maxVisibleRows then break end
                end
            end

            for position = #visible, 1, -1 do
                local index = visible[position]
                local entry = entries[index]

                local label = Instance.new("TextLabel")
                label.BackgroundTransparency = 1
                label.Size = UDim2.new(1, 0, 0, 0)
                label.AutomaticSize = Enum.AutomaticSize.Y
                label.TextWrapped = true
                label.RichText = opts.RichText ~= false and entry.source == "Script"
                label.TextXAlignment = Enum.TextXAlignment.Left
                label.TextYAlignment = Enum.TextYAlignment.Top
                label.Font = theme.Font
                label.TextSize = opts.TextSize or 12
                label.Text = formatEntry(entry)
                label.TextColor3 = entryColor(entry.level)
                label.LayoutOrder = index
                label.ZIndex = logArea.ZIndex
                label.Parent = logArea
            end

            if #visible == 0 then
                local label = Instance.new("TextLabel")
                label.BackgroundTransparency = 1
                label.Size = UDim2.new(1, 0, 0, 20)
                label.Text = labelText("Empty", "no matching messages.")
                label.TextColor3 = theme.TextDim
                label.TextXAlignment = Enum.TextXAlignment.Left
                label.Font = theme.Font
                label.TextSize = opts.TextSize or 12
                label.ZIndex = logArea.ZIndex
                label.Parent = logArea
            end
        end

        function console:Export(includeCleared)
            local lines = {}
            local first = includeCleared and 1 or clearedThrough + 1

            for index = first, #entries do
                local entry = entries[index]

                if matches(entry) then
                    table.insert(lines, Library:ResolveText(formatEntry(entry), "facility", entry.source == "Script" and opts.RichText ~= false))
                end
            end

            return table.concat(lines, "\n")
        end

        function console:Copy()
            if not alive then return false, "console is destroyed" end
            return pcall(function()
                assert(type(setclipboard) == "function", "Clipboard unavailable")
                setclipboard(self:Export(false))
            end)
        end

        function console:Save()
            if not alive then return false, "console is destroyed" end
            saveCount += 1
            local filename = ("console-%s-%s-%d-%s.txt"):format(
                os.date("%Y%m%d-%H%M%S"), game.JobId, saveCount, consoleId
            )
            local success, result = pcall(function()
                assert(type(writefile) == "function", "File saving unavailable")
                local folder = opts.Folder or "Facility/logs"
                local ready, reason = Library.FileSystem:EnsureFolder(folder)
                assert(ready, reason)
                filename = folder .. "/" .. filename
                writefile(filename, self:Export(true))
                return filename
            end)
            return success, result
        end

        function console:Clear()
            if not alive then return end
            clearedThrough = #entries
            logArea.CanvasPosition = Vector2.zero
            scheduleRender()
        end

        local actions, ids = {}, {}
        if show.Copy ~= false then
            table.insert(ids, "Copy")
            table.insert(actions, { Text = labelText("Copy", "copy to clipboard"), Callback = function()
                local success, reason = console:Copy()
                if not success then console:Error(labelText("CopyFailed", "copy failed:"), reason) end
            end })
        end
        if show.Save ~= false then
            table.insert(ids, "Save")
            table.insert(actions, { Text = labelText("Save", "save console"), Callback = function()
                local success, result = console:Save()
                if success then console:Print(labelText("Saved", "console saved:"), result)
                else console:Error(labelText("SaveFailed", "save failed:"), result) end
            end })
        end
        if #actions > 0 then
            console.ActionRow = content:ButtonRow(actions)
            for index, id in ipairs(ids) do console.Controls[id] = console.ActionRow.Controls[index] end
        end
        if show.Clear ~= false then
            console.Controls.Clear = content:Button({ Text = labelText("Clear", "clear console"), Callback = function() console:Clear() end })
        end
        if consoleModal and opts.MountButton ~= false then
            console.Button = window:IconAction(opts.Icon or "square-terminal", function()
                if alive then consoleModal:Toggle() end
            end, opts.ButtonOrder or 2)
        end

        local function capture(message, kind, context)
            -- Ignore our own forwarded messages, including deferred MessageOut echoes.
            if (type(context) == "table" and context.facilityConsole == consoleId)
                or message:sub(1, #outputPrefix) == outputPrefix then
                return
            end

            local level = kind == Enum.MessageType.MessageError and "Error"
                or kind == Enum.MessageType.MessageWarning and "Warn"
                or "Print"

            addEntry("Roblox", level, message)
        end

        local logConnection
        function console:SetCaptureRoblox(value)
            if logConnection then logConnection:Disconnect(); logConnection = nil end
            if alive and value ~= false then logConnection = LogService.MessageOut:Connect(capture) end
        end
        console:SetCaptureRoblox(opts.CaptureRoblox ~= false)
        Library:OnRepaint(scheduleRender)

        local connections, hooks, floating = {}, {}, {}
        for index = connectionStart + 1, #Library.Connections do
            table.insert(connections, Library.Connections[index])
        end
        for index = repaintStart + 1, #Library.RepaintHooks do
            table.insert(hooks, Library.RepaintHooks[index])
        end
        for _, child in ipairs(window.Overlay:GetChildren()) do
            if not overlayBefore[child] then table.insert(floating, child) end
        end

        function console:GetEntries()
            local result = {}
            for _, entry in ipairs(entries) do
                table.insert(result, { source = entry.source, level = entry.level,
                    time = entry.time, message = entry.message })
            end
            return result
        end

        function console:SetOpen(value)
            if not alive then return end
            if self.Modal then self.Modal:SetOpen(value ~= false)
            else self.Root.Visible = value ~= false end
        end

        function console:Toggle()
            if not alive then return end
            self:SetOpen(self.Modal and not self.Modal.Open or (not self.Modal and not self.Root.Visible))
        end

        function console:Destroy(fromRoot)
            if not alive then return end
            alive, self.Alive = false, false
            if pendingThread then pcall(task.cancel, pendingThread); pendingThread = nil end
            if logConnection then logConnection:Disconnect(); logConnection = nil end
            for _, connection in ipairs(connections) do
                connection:Disconnect()
                local index = table.find(Library.Connections, connection)
                if index then table.remove(Library.Connections, index) end
            end
            for _, hook in ipairs(hooks) do
                local index = table.find(Library.RepaintHooks, hook)
                if index then table.remove(Library.RepaintHooks, index) end
            end
            local ownedRoots = { self.Root }
            for _, frame in ipairs(floating) do table.insert(ownedRoots, frame) end
            if self.Button then table.insert(ownedRoots, self.Button) end
            for index = #(Library.Painted or {}), 1, -1 do
                local instance = Library.Painted[index][1]
                for _, root in ipairs(ownedRoots) do
                    if instance == root or instance:IsDescendantOf(root) then
                        table.remove(Library.Painted, index)
                        break
                    end
                end
            end
            for index = #(window.FloatStack or {}), 1, -1 do
                if table.find(floating, window.FloatStack[index].Frame) then table.remove(window.FloatStack, index) end
            end
            for _, frame in ipairs(floating) do frame:Destroy() end
            if self.Button then self.Button:Destroy() end
            if not fromRoot then
                if self.Modal then self.Modal:Destroy() else self.Root:Destroy() end
            end
            table.clear(connections)
            table.clear(hooks)
            table.clear(floating)
            table.clear(entries)
        end
        console.Root.Destroying:Once(function() console:Destroy(true) end)
        render()
        return console
    end

    return ConsoleManager
end
