-- Internal native-card checks; not the user showcase.
local now, queued, signals, instances = 0, {}, {}, {}
os.clock = function() return now end
math.clamp = function(n, lo, hi) return math.max(lo, math.min(hi, n)) end
table.clear = function(t) for k in pairs(t) do t[k] = nil end end
table.find = function(t, value) for i, v in ipairs(t) do if v == value then return i end end end
warn = function(message) print("WARN:", message) end
local function resume(thread)
    local ok, delay = coroutine.resume(thread)
    assert(ok, delay)
    if coroutine.status(thread) ~= "dead" then queued[thread] = now + (tonumber(delay) or 0) end
end
task = {
    spawn = function(fn, ...)
        local thread = type(fn) == "thread" and fn or coroutine.create(fn)
        resume(thread)
        return thread
    end,
    wait = function(delay) return coroutine.yield(delay or 0) end,
    cancel = function(thread) queued[thread] = nil end,
}
local function advance(seconds)
    now = now + seconds
    local due = {}
    for thread, when in pairs(queued) do if when <= now then table.insert(due, thread) end end
    for _, thread in ipairs(due) do queued[thread] = nil; resume(thread) end
end
local function signal()
    local s = { connections = {} }
    table.insert(signals, s)
    function s:Connect(fn)
        local c = { Connected = true, fn = fn }
        function c:Disconnect() self.Connected = false end
        table.insert(self.connections, c)
        return c
    end
    function s:Fire(...)
        for _, c in ipairs(self.connections) do if c.Connected then c.fn(...) end end
    end
    return s
end
Enum = setmetatable({}, { __index = function(t, k)
    local value = setmetatable({}, { __index = function(_, n) return k .. "." .. n end })
    rawset(t, k, value); return value
end })
Vector2 = { new = function(x, y) return { X = x, Y = y } end }
UDim = { new = function(scale, offset) return { Scale = scale, Offset = offset } end }
local dimMeta = { __eq = function(a, b)
    return a.X.Scale == b.X.Scale and a.X.Offset == b.X.Offset and a.Y.Scale == b.Y.Scale and a.Y.Offset == b.Y.Offset
end }
UDim2 = {
    new = function(xs, xo, ys, yo) return setmetatable({ X = UDim.new(xs, xo), Y = UDim.new(ys, yo) }, dimMeta) end,
}
UDim2.fromOffset = function(x, y) return UDim2.new(0, x, 0, y) end
UDim2.fromScale = function(x, y) return UDim2.new(x, 0, y, 0) end
local instanceMethods = {}
local function size(object)
    local props = rawget(object, "_props")
    if props.AbsoluteOverride then return props.AbsoluteOverride end
    local parentSize = props.Parent and size(props.Parent) or Vector2.new(680, 580)
    local d = props.Size or UDim2.fromOffset(100, 100)
    return Vector2.new(d.X.Scale * parentSize.X + d.X.Offset, d.Y.Scale * parentSize.Y + d.Y.Offset)
end
local objectMeta = {
    __index = function(t, k)
        if instanceMethods[k] then return instanceMethods[k] end
        if k == "AbsoluteSize" then return size(t) end
        if k == "TextBounds" then return Vector2.new(#t.Text * 6, t.TextSize or 13) end
        return t._props[k]
    end,
    __newindex = function(t, k, value)
        local old = t._props[k]
        t._props[k] = value
        if k == "Parent" then
            if old then for i, v in ipairs(old._children) do if v == t then table.remove(old._children, i); break end end end
            if value then table.insert(value._children, t) end
        end
        if old ~= value and t._signals[k] then t._signals[k]:Fire() end
    end,
}
Instance = { new = function(class)
    local object = setmetatable({ _props = { ClassName = class, Name = class, Visible = true, IsLoaded = true, Text = "",
        Destroying = signal(), Activated = signal(), MouseEnter = signal(), MouseLeave = signal() }, _signals = {}, _children = {} }, objectMeta)
    table.insert(instances, object)
    return object
end }
function instanceMethods:GetPropertyChangedSignal(key)
    self._signals[key] = self._signals[key] or signal()
    return self._signals[key]
end
function instanceMethods:Destroy()
    if self._props.Destroyed then return end
    self.Destroying:Fire()
    self._props.Destroyed = true
    local children = { table.unpack(self._children) }
    for _, child in ipairs(children) do child:Destroy() end
    self.Parent = nil
end

local deferred = {}
task.defer = function(fn) table.insert(deferred, fn) end
local function flush()
    while #deferred > 0 do local batch = deferred; deferred = {}; for _, fn in ipairs(batch) do fn() end end
end
local function New(class, props)
    local obj = Instance.new(class)
    for k, v in pairs(props) do obj[k] = v end
    return obj
end
Color3 = { new = function(r,g,b) return {r,g,b} end }
typeof = function(v) return type(v) end
local Theme = setmetatable({Font="font"}, {__index=function(_,k) return k end})
local Library = {RepaintHooks={}}
function Library:OnRepaint(fn) table.insert(self.RepaintHooks,fn); return fn end
function Library:SafeCallback(_, fn, ...) if fn then fn(...) end end
local function Corner(parent,r) return New("UICorner",{Parent=parent,CornerRadius=UDim.new(0,r)}) end
local function Stroke(parent) return New("UIStroke",{Parent=parent}) end
local function List(parent,p) return New("UIListLayout",{Parent=parent,Padding=UDim.new(0,p)}) end
local function Label(parent,t,c,s) return New("TextLabel",{Parent=parent,Text=t,TextColor3=c,TextSize=s}) end
local function AttachIcon(parent,icon,c,s)
    if not icon then return end
    return New("ImageLabel",{Parent=parent,Image=icon,ImageColor3=c,Size=UDim2.fromOffset(s,s)})
end
local Elements, Tab = {}, {}
local f = assert(io.open("main.luau")); local source = f:read("*a"); f:close()
assert(load(source), "whole library syntax")
local block = assert(source:match("(do\n\tlocal function color.-)\nlocal Window = {}"))
local install = assert(load("return function(Elements,Tab,New,Theme,Library,Corner,Stroke,List,Label,AttachIcon)\n"..block.."\nend"))()
install(Elements,Tab,New,Theme,Library,Corner,Stroke,List,Label,AttachIcon)
local parent = New("Frame",{Size=UDim2.fromOffset(612,480)})
local window = {Scale=New("UIScale",{Scale=1})}
local tab = setmetatable({Page=parent,Window=window,Order=0},{__index=Tab})
local owner = tab:Cards()
local profile = owner:ProfileCard({Title="quit",Subtitle="@quit",Eyebrow="Welcome",Badge={Text="Preview",Detail="Home prototype"}})
local function child(root,name)
    for _, c in ipairs(root._children) do if c.Name==name then return c end end
end
for _, width in ipairs({282,380,460,509,510,569,570,612,750,900}) do
    parent.Size = UDim2.fromOffset(width,480); profile:Refresh()
    local privacy, badge = child(profile.Instance,"Privacy"), child(profile.Instance,"Badge")
    assert(privacy.Position.Y.Offset >= badge.Position.Y.Offset + badge.Size.Y.Offset + 10)
    assert(profile.Instance.Size.Y.Offset == privacy.Position.Y.Offset + 32 + 14)
    if width<510 then assert(privacy.Position.X.Offset==14 and privacy.Size.X.Offset==width-28) end
end
profile.HideName:Set(true); profile:SetTitle("changed")
assert(profile.Title.Instance.Text=="Hidden user")
profile.HideName:Set(false); assert(profile.Title.Instance.Text=="changed")
local oldHeight=profile.Instance.Size.Y.Offset
profile.Privacy:SetVisible(false); assert(profile.Instance.Size.Y.Offset<oldHeight)
profile.Badge:SetVisible(false); profile:SetAvatarVisible(false)
profile.Badge:SetStyle({BackgroundColor="Accent",CornerRadius=4,DetailAlignment="Left"})
local media=owner:MediaCard({Title="Game",Image="image",Fields={{Id="id",Label="Place",Value="123"}},Actions={
    {Id="a",Text="Rejoin"},{Id="b",Text="Copy"},{Id="c",Text="Lowest",Span=2}}})
for _, width in ipairs({282,380,569,570,612,900}) do
    parent.Size=UDim2.fromOffset(width,480); media:Refresh()
    for _, a in pairs(media.Actions) do
        assert(a.Instance.Position.X.Offset>=14)
        assert(a.Instance.Position.X.Offset+a.Instance.Size.X.Offset<=width-14+0.001)
        assert(a.Instance.Position.Y.Offset+a.Instance.Size.Y.Offset<=media.Instance.Size.Y.Offset-14)
    end
end
media:RemoveAction("c"); media:RemoveField("id"); media:AddField({Id="id",Label="New",Value=5})
media:SetField("id",6); assert(media.Fields.id.Value.Instance.Text=="6")
media.Actions.a:SetVisible(false); media.Actions.b:SetSpan(2)
media:SetImage(""); media:SetDescription("Description")
local stats=owner:StatGrid({{Id="fps",Label="FPS",Value=60,Icon="gauge"}})
stats:Add({Id="ping",Label="Ping",Value=12}); stats:Set("fps",144)
assert(stats.Items.fps.Value.Instance.Text=="144")
stats:Remove("ping"); stats:Remove("fps"); assert(stats.Instance.Size.Y.Offset==0)
local status=owner:StatusCard({Title="Runtime",Description="Ready",Icon="shield"})
status:SetDescription("Changed")
flush()
local calls=0; local original=profile.Refresh
profile.Refresh=function(self) calls=calls+1; original(self) end
for _, scale in ipairs({0.97,0.98,0.99,1}) do
    window.Scale.Scale=scale
    profile.Instance.AbsoluteOverride=Vector2.new(900*scale,100)
    profile.Instance:GetPropertyChangedSignal("AbsoluteSize"):Fire()
    flush()
end
assert(calls<=1,"scale-only animation reflowed")
for _, fn in ipairs(Library.RepaintHooks) do fn() end
local hooks=#Library.RepaintHooks
profile:Destroy(); media:Destroy(); stats:Destroy(); status:Destroy()
flush(); assert(#Library.RepaintHooks==hooks-4)
print("PASS: whole-library Lua syntax; card construction; responsive bounds; compact alignment; privacy; optional content; mutation; icons; theme repaint; scale-only reflow; cleanup")
