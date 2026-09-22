local BASE = "https://raw.githubusercontent.com/FacilityHUB/UI-Facility/refs/heads/main/"

local source = game:HttpGet(BASE .. "main.luau")
assert(#source > 1000 and not string.find(source, "404", 1, true),
	"main.luau introuvable a cette URL, verifie le depot et la branche")

local chunk, err = loadstring(source)
assert(chunk, "main.luau ne compile pas : " .. tostring(err))

local Library = chunk()
assert(type(Library) == "table", "main.luau n'a rien retourne, le fichier est incomplet ou tronque")

Library.BaseUrl = BASE

assert(Library.SaveManager, "addons introuvables, verifie Library.BaseUrl et le dossier addons/")

local SaveManager = Library.SaveManager
local InterfaceManager = Library.InterfaceManager
local ThemeManager = Library.ThemeManager

local Window = Library:Window({
	Title = "facility",
	Suffix = ".app",
	Width = 620,
	Height = 620,
})

local General  = Window:Tab("general")
local Display  = Window:Tab("display")
local Objects  = Window:Tab("objects")
local Network  = Window:Tab("network")
local Audio    = Window:Tab("audio")
local Script   = Window:Tab("script")
local Console  = Window:Tab("console")
local Settings = Window:Tab("settings")

local global = General:Section("global", 1)

global:Toggle({
	Text = "enable",
	Flag = "global_enable",
	Callback = function(v) print("enable", v) end,
}):Keybind({ Default = "F", Flag = "global_enable_key" }):Gear(function(panel)
	panel:Slider({ Text = "delay", Flag = "global_delay", Min = 0, Max = 500, Suffix = " ms", Default = 60 })
	panel:Dropdown({ Text = "profile", Flag = "global_profile", Options = { "default", "custom" }, Default = "default" })
end)

global:Toggle({ Text = "auto refresh", Flag = "auto_refresh", Default = true }):Gear(function(panel)
	panel:Slider({ Text = "interval", Flag = "auto_refresh_interval", Min = 1, Max = 60, Suffix = " s", Default = 5 })
end)

global:Toggle({ Text = "simulation", Flag = "simulation", Hint = "runs the local prediction pass" })
global:Toggle({ Text = "cache check", Flag = "cache_check" })
global:Toggle({ Text = "motion smoothing", Flag = "motion_smoothing", Default = true, Hint = "interpolates between frames" }):Gear(function(panel)
	panel:Slider({ Text = "strength", Flag = "motion_strength", Min = 0, Max = 1, Decimals = 2, Default = 0.35 })
end)
global:Toggle({ Text = "no jitter", Flag = "no_jitter", Default = true }):Gear(function(panel)
	panel:Slider({ Text = "threshold", Flag = "jitter_threshold", Min = 0, Max = 20, Default = 4 })
end)
global:Toggle({ Text = "no drift", Flag = "no_drift", Default = true }):Gear(function(panel)
	panel:Slider({ Text = "tolerance", Flag = "drift_tolerance", Min = 0, Max = 10, Decimals = 1, Default = 1.5 })
end)
global:Toggle({ Text = "clamp to bounds", Flag = "clamp_bounds", Hint = "keeps values inside the viewport" })
global:Toggle({ Text = "radius circle", Flag = "radius_circle" })
	:ColorPicker({ Flag = "radius_outline", Default = Color3.fromRGB(232, 161, 168) })
	:ColorPicker({ Flag = "radius_fill", Default = Color3.fromRGB(60, 60, 65), DefaultAlpha = 0.35 })
	:Gear(function(panel)
		panel:Slider({ Text = "thickness", Flag = "radius_thickness", Min = 1, Max = 6, Default = 2 })
	end)
global:Toggle({ Text = "object lock", Flag = "object_lock", Hint = "keeps the current selection" })
global:Toggle({ Text = "fast scan", Flag = "fast_scan" })

local transform = General:Section("transform", 1)

transform:Toggle({ Text = "enable", Flag = "transform_enable" }):Keybind({ Default = "G", Flag = "transform_enable_key" })
transform:Dropdown({ Text = "direction", Flag = "transform_direction", Options = { "forward", "backward", "mirrored" }, Default = "forward" })
transform:Dropdown({ Text = "yaw", Flag = "transform_yaw", Options = { "none", "relative", "absolute" }, Default = "none" })
transform:Dropdown({ Text = "pitch", Flag = "transform_pitch", Options = { "off", "clamped", "free" }, Default = "off" })
transform:Toggle({ Text = "offset angle", Flag = "transform_offset" }):Gear(function(panel)
	panel:Slider({ Text = "angle", Flag = "transform_angle", Min = -180, Max = 180, Suffix = "°", Default = 0 })
end)

local settings = General:Section("settings", 2)

settings:Dropdown({ Text = "visualization", Flag = "visualization", Options = { "visible", "always", "hidden" }, Default = "visible" })
settings:Dropdown({ Text = "anchor", Flag = "anchor", Options = { "head", "torso", "origin", "bounds" }, Default = "head" })
settings:Dropdown({ Text = "target selection", Flag = "target_selection", Options = { "crosshair", "distance", "priority" }, Default = "crosshair" })
settings:Dropdown({ Text = "ignore conditions", Flag = "ignore_conditions", Options = { "friends", "hidden", "inactive" }, Multi = true, Default = { "friends" }, Empty = "none" })
settings:Slider({ Text = "radius", Flag = "radius", Min = 0, Max = 200, Default = 1 })
settings:Slider({ Text = "max distance", Flag = "max_distance", Min = 0, Max = 5000, Default = 0, ZeroText = "0 - unlimited" })
settings:ColorPicker({
	Text = "highlight",
	Flag = "highlight_color",
	Default = Color3.fromRGB(232, 161, 168),
	DefaultAlpha = 1,
	Callback = function(color, alpha) print("highlight", color, alpha) end,
})

local groups = General:Section("group filter", 2)

groups:Search({
	Placeholder = "",
	Label = "search",
	Live = true,
	Callback = function(text) print("query:", text) end,
})
groups:Label("no groups found.")

Display:Section("render", 1):Slider({ Text = "quality", Flag = "render_quality", Min = 1, Max = 10, Default = 8 })
local objects = Objects:Section("filters", 1)
objects:Toggle({ Text = "static objects", Flag = "static_objects" })
objects:Dropdown({
	Text = "material",
	Flag = "objects_material",
	Options = { "plastic", "wood", "metal", "glass", "neon", "concrete", "brick", "sand", "grass", "ice", "marble", "fabric" },
	Default = "plastic",
})
objects:Keybind({
	Text = "hold to inspect",
	Flag = "objects_inspect",
	Default = "E",
	Mode = "hold",
	Callback = function(down) print("inspect", down) end,
})
Network:Section("status", 1):Label("idle.")
Audio:Section("mixer", 1):Slider({ Text = "volume", Flag = "audio_volume", Min = 0, Max = 100, Suffix = "%", Default = 70 })
Script:Section("editor", 1):Button({ Text = "reload scripts" })
local console = Console:Section("output", 1)
console:Label("empty.")

local notes = Console:Section("notes", 2)
notes:Paragraph({
	Title = "how it works",
	Content = "Each option writes into Library.Flags, configs only store flagged elements.",
	Icon = "info",
})
notes:Paragraph({
	Title = "careful",
	Content = "Changing the format only changes the file extension, not the encoding.",
	Style = "warning",
	Icon = "alert-triangle",
})
notes:Paragraph({
	Title = "no filesystem",
	Content = "Without executor file functions, configs stay in memory for the session only.",
	Style = "danger",
	Icon = "x-circle",
})
notes:Label("all systems nominal.", { Style = "success", Icon = "check" })
notes:Label("plain explanatory line, wraps over several lines when the text gets long.")

Window:Action("Connect", function()
	Library:Notify({ Title = "connected", Text = "session started.", Duration = 3 })
end)

SaveManager:SetLibrary(Library)
InterfaceManager:SetLibrary(Library)
InterfaceManager:SetWindow(Window)
ThemeManager:SetLibrary(Library)

SaveManager:IgnoreThemeSettings()
SaveManager:SetIgnoreIndexes({})

InterfaceManager:SetFolder("Facility")
ThemeManager:SetFolder("Facility")
SaveManager:SetFolder("Facility/game")

InterfaceManager:BuildInterfaceSection(Settings, 1)
ThemeManager:BuildThemeSection(Settings, 1)
SaveManager:BuildConfigSection(Settings, 2)

local notifications = Settings:Section("notifications", 1)
notifications:ButtonRow({
	{
		Text = "normal",
		Callback = function()
			Library:Notify("Facility", "test notification.", 4)
		end,
	},
	{
		Text = "warning",
		Callback = function()
			Library:Warn("attention", "this option is experimental.", 4)
		end,
	},
})
notifications:ButtonRow({
	{
		Text = "danger",
		Callback = function()
			Library:Error("risky", "this action cannot be undone.", 4)
		end,
	},
	{
		Text = "success",
		Callback = function()
			Library:Success("done", "config applied.", 4)
		end,
	},
})

Window:SetTab(General)

Library:Notify({
	Title = "Facility",
	Text = "script loaded.",
	Duration = 5,
})

SaveManager:LoadAutoloadConfig()
