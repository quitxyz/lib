-- Facility addon | HomeManager
-- A configurable Home layout. Script-specific status and tier data are supplied by the caller.
return function(Library)
    local Players = game:GetService("Players")
    local RunService = game:GetService("RunService")
    local MarketplaceService = game:GetService("MarketplaceService")
    local TeleportService = game:GetService("TeleportService")
    local HttpService = game:GetService("HttpService")
    local HomeManager = {}
    local loadedAt = os.clock()

    local function copy(value)
        if type(value) ~= "table" then return value end
        local result = {}
        for key, item in pairs(value) do result[key] = copy(item) end
        return result
    end

    local function options(defaults, supplied)
        local result = copy(defaults)
        for key, value in pairs(supplied or {}) do
            if key == "Badge" or key == "Privacy" then
                result[key] = type(value) == "table" and options(result[key] or {}, value) or value
            else
                result[key] = copy(value)
            end
        end
        return result
    end

    local function sessionText(started)
        local elapsed = math.max(0, math.floor(os.clock() - started))
        local hours, minutes, seconds = math.floor(elapsed / 3600), math.floor(elapsed / 60) % 60, elapsed % 60
        if hours > 0 then return ("%dh %dm %ds"):format(hours, minutes, seconds) end
        if minutes > 0 then return ("%dm %ds"):format(minutes, seconds) end
        return ("%ds"):format(seconds)
    end

    function HomeManager:Create(target, opts)
        opts = opts or {}
        assert(target, "HomeManager requires a window, tab, or section")
        local ownsTab = type(target.Tab) == "function"
        local tab = ownsTab and target:Tab(opts.Title or "general", opts.Icon or "home") or nil
        local parent = tab or target
        assert(type(parent.Cards) == "function", "Target must support Cards")
        local container = parent:Cards({ Spacing = opts.Spacing or 9 })
        local home = { Instance = container.Instance, Container = container, Tab = tab or (target.Page and target),
            Window = container.Window, Alive = true, Cards = {} }
        local connections, threads = {}, {}
        local player = opts.Player or Players.LocalPlayer
        local started = opts.SessionStarted or loadedAt

        local function spawn(callback)
            -- defer lets us register the task before it can complete or yield.
            local thread = task.defer(callback)
            table.insert(threads, thread)
            return thread
        end

        local function connect(signal, callback)
            local connection = signal:Connect(callback)
            table.insert(connections, connection)
            return connection
        end

        local function report(message)
            if not home.Alive then return end
            if opts.OnError then
                Library:SafeCallback("home", opts.OnError, tostring(message))
            else
                warn("Facility | home: " .. tostring(message))
            end
        end

        function home:Destroy(fromRoot)
            if not self.Alive then return end
            self.Alive = false
            for _, connection in ipairs(connections) do connection:Disconnect() end
            for _, thread in ipairs(threads) do
                if thread ~= coroutine.running() and coroutine.status(thread) ~= "dead" then
                    pcall(task.cancel, thread)
                end
            end
            table.clear(connections)
            table.clear(threads)
            if not fromRoot then self.Instance:Destroy() end
            if ownsTab and tab.Alive then tab:Destroy() end
        end
        connect(home.Instance.Destroying, function() home:Destroy(true) end)

        local built, buildError = pcall(function()

        local function add(name, method, values)
            local card = container[method](container, values)
            home[name], home.Cards[name] = card, card
            if values.Visible == false then card:SetVisible(false) end
            return card
        end

        if opts.Profile ~= false then
            add("Profile", "ProfileCard", options({
                Image = player and ("rbxthumb://type=AvatarHeadShot&id=" .. player.UserId .. "&w=150&h=150") or "",
                Eyebrow = "welcome back,", Title = player and player.DisplayName or "player",
                Subtitle = player and ("@" .. player.Name) or "",
                Badge = { Text = "preview", Icon = "sparkles", Width = 100, CornerRadius = 8,
                    ContentAlignment = "Center", DetailAlignment = "Center", VerticalAlignment = "Bottom" },
                Privacy = { Visible = false },
            }, opts.Profile))
        end

        if opts.Stats ~= false then
            local getters = {
                players = function() return #Players:GetPlayers() .. "/" .. Players.MaxPlayers end,
                friends = function()
                    if not player then return "unknown" end
                    local count = 0
                    for _, other in ipairs(Players:GetPlayers()) do
                        if other ~= player then
                            local friend = player:IsFriendsWithAsync(other.UserId)
                            if friend and other.Parent == Players then count = count + 1 end
                        end
                    end
                    return count
                end,
                session = function() return sessionText(started) end,
                ping = function()
                    if not player then return "unknown" end
                    return math.floor(player:GetNetworkPing() * 1000 + 0.5) .. "ms"
                end,
            }
            for id, getter in pairs(opts.Getters or {}) do
                assert(getter == false or type(getter) == "function", "Stat getter must be a function or false")
                getters[id] = getter
            end
            local gridOptions = options({ Spacing = 8, Items = {
                { Id = "players", Icon = "users", Label = "players", Value = #Players:GetPlayers() .. "/" .. Players.MaxPlayers },
                { Id = "friends", Icon = "user", Label = "friends", Value = "—" },
                { Id = "runs", Icon = "zap", Label = "runs", Value = opts.RunsValue or "—" },
                { Id = "session", Icon = "clock", Label = "session", Value = sessionText(started) },
                { Id = "fps", Icon = "gauge", Label = "FPS", Value = "—" },
                { Id = "ping", Icon = "wifi", Label = "ping", Value = "—" },
            } }, opts.Stats)
            local grid = add("Stats", "StatGrid", gridOptions)
            local statThreads = {}
            local fpsConnection
            for _, item in ipairs(gridOptions.Items) do
                local getter = item.Getter
                if getter == nil then getter = getters[item.Id] end
                if type(getter) == "function" then
                    local interval = item.Interval or (opts.Intervals or {})[item.Id] or (item.Id == "friends" and 10 or 1)
                    assert(type(interval) == "number" and interval > 0 and interval < math.huge, "Stat interval must be positive and finite")
                    local entry = grid.Items[item.Id]
                    table.insert(statThreads, spawn(function()
                        while home.Alive and grid.Alive and grid.Items[item.Id] == entry do
                            local success, value = pcall(getter)
                            if not home.Alive or not grid.Alive or grid.Items[item.Id] ~= entry then break end
                            grid:Set(item.Id, success and value ~= nil and tostring(value) or "unknown")
                            task.wait(interval)
                        end
                    end))
                elseif item.Id == "fps" and getter ~= false then
                    local entry = grid.Items.fps
                    local frames, elapsed = 0, 0
                    fpsConnection = connect(RunService.RenderStepped, function(deltaTime)
                        if not home.Alive or not grid.Alive or grid.Items.fps ~= entry then
                            fpsConnection:Disconnect()
                            return
                        end
                        frames, elapsed = frames + 1, elapsed + deltaTime
                        if elapsed >= 0.5 then
                            grid:Set("fps", math.floor(frames / elapsed + 0.5))
                            frames, elapsed = 0, 0
                        end
                    end)
                end
            end
            connect(grid.Instance.Destroying, function()
                if fpsConnection then fpsConnection:Disconnect() end
                for _, thread in ipairs(statThreads) do
                    if thread ~= coroutine.running() and coroutine.status(thread) ~= "dead" then pcall(task.cancel, thread) end
                end
                table.clear(statThreads)
            end)
        end

        if opts.Game ~= false then
            local findingServer = false
            local function hop(lowest)
                if findingServer then return end
                findingServer = true
                local success, reason = pcall(function()
                    local url = ("https://games.roblox.com/v1/games/%d/servers/Public?sortOrder=%s&excludeFullGames=true&limit=100")
                        :format(game.PlaceId, lowest and "Asc" or "Desc")
                    local response = HttpService:JSONDecode(game:HttpGet(url))
                    local candidates = {}
                    for _, server in ipairs(response.data or {}) do
                        if server.id ~= game.JobId and server.playing < server.maxPlayers then
                            table.insert(candidates, server)
                        end
                    end
                    if not home.Alive or not home.Game.Alive then return end
                    assert(#candidates > 0, "no other available server found")
                    local server = candidates[1]
                    if lowest then
                        for _, candidate in ipairs(candidates) do
                            if candidate.playing < server.playing then server = candidate end
                        end
                    else
                        server = candidates[math.random(#candidates)]
                    end
                    TeleportService:TeleportToPlaceInstance(game.PlaceId, server.id, player)
                end)
                findingServer = false
                if not success then report(reason) end
            end
            local function action(id, text, callback)
                return { Id = id, Text = text, Callback = function()
                    if not home.Alive or not home.Game.Alive then return end
                    local success, reason = pcall(callback)
                    if not success then report(reason) end
                end }
            end
            local gameOptions = options({
                Image = "rbxthumb://type=GameIcon&id=" .. game.GameId .. "&w=150&h=150",
                ImageSize = 64, ImageRadius = 8, Title = "loading game…", Subtitle = "",
                Description = "server version: " .. game.PlaceVersion,
                Fields = {
                    { Id = "place", Label = "place ID", Value = tostring(game.PlaceId) },
                    { Id = "universe", Label = "universe ID", Value = tostring(game.GameId) },
                },
                Actions = {
                    action("rejoin", "rejoin", function() TeleportService:TeleportToPlaceInstance(game.PlaceId, game.JobId, player) end),
                    action("hop", "server hop", function() hop(false) end),
                    action("lowest", "join lowest server", function() hop(true) end),
                    action("copyJoinLink", "copy join link", function()
                        setclipboard(("roblox://experiences/start?placeId=%s&gameInstanceId=%s"):format(game.PlaceId, game.JobId))
                    end),
                    action("copyJob", "copy job ID", function() setclipboard(game.JobId) end),
                    action("copyUniverse", "copy universe", function() setclipboard(tostring(game.GameId)) end),
                },
            }, opts.Game)
            local card = add("Game", "MediaCard", gameOptions)
            local initialTitle, initialSubtitle = card.Title.Instance.Text, card.Subtitle.Instance.Text
            if not opts.Game or opts.Game.Title == nil or opts.Game.Subtitle == nil then
                spawn(function()
                    local success, details = pcall(function() return MarketplaceService:GetProductInfoAsync(game.PlaceId) end)
                    if not home.Alive or not card.Alive then return end
                    if (not opts.Game or opts.Game.Title == nil) and card.Title.Instance.Text == initialTitle then
                        card:SetTitle(success and details.Name or "unknown game")
                    end
                    if (not opts.Game or opts.Game.Subtitle == nil) and card.Subtitle.Instance.Text == initialSubtitle then
                        card:SetSubtitle(success and details.Creator and ("by " .. details.Creator.Name) or "unknown creator")
                    end
                end)
            end
        end

        if opts.Executor ~= false then
            local name = "unknown executor"
            local identify = identifyexecutor or getexecutorname
            if type(identify) == "function" then
                local success, value = pcall(identify)
                if success and type(value) == "string" and value ~= "" then name = value end
            end
            add("Executor", "StatusCard", options({ Icon = "shield-check", CenterImage = true,
                Title = name, Description = "", DescriptionRichText = true }, opts.Executor))
        end

        local order = opts.Order or { "Profile", "Stats", "Game", "Executor" }
        local ordered, nextOrder = {}, 0
        for _, name in ipairs(order) do
            assert(not ordered[name] and (name == "Profile" or name == "Stats" or name == "Game" or name == "Executor"), "Invalid or duplicate Home card order")
            ordered[name] = true
            if home.Cards[name] then nextOrder = nextOrder + 1; home.Cards[name]:SetOrder(nextOrder) end
        end
        for _, name in ipairs({ "Profile", "Stats", "Game", "Executor" }) do
            if home.Cards[name] and not ordered[name] then nextOrder = nextOrder + 1; home.Cards[name]:SetOrder(nextOrder) end
        end
        end)
        if not built then
            home:Destroy()
            error(buildError, 2)
        end
        return home
    end

    return HomeManager
end
