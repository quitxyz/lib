"""Lifecycle/disabled-button checks with mocked Roblox signals (requires lupa)."""
from pathlib import Path
from lupa.lua54 import LuaRuntime

source = (Path(__file__).resolve().parents[1] / 'main.luau').read_text()
lua = LuaRuntime()
lua.execute('''
table.clear = function(t) for k in pairs(t) do t[k] = nil end end
table.find = function(t,v) for i,x in ipairs(t) do if x == v then return i end end end
function signal()
 local s = {listeners={}}
 function s:Connect(f)
  local c={Connected=true,callback=f}
  function c:Disconnect() self.Connected=false end
  self.listeners[#self.listeners+1]=c; return c
 end
 function s:Once(f)
  local c; c=self:Connect(function(...) c:Disconnect(); f(...) end); return c
 end
 function s:Fire(...) for _,c in ipairs(self.listeners) do if c.Connected then c.callback(...) end end end
 return s
end
nodes={}; completions={}; tasks={}
function New(class,props)
 local n={ClassName=class,Destroying=signal(),Activated=signal(),MouseEnter=signal(),MouseLeave=signal()}
 for k,v in pairs(props or {}) do n[k]=v end
 function n:IsDescendantOf(root)
  local p=self.Parent; while p do if p==root then return true end; p=p.Parent end; return false
 end
 function n:Destroy()
  if self.destroyed then return end
  self.destroyed=true; self.Destroying:Fire(); self.Parent=nil
 end
 nodes[#nodes+1]=n; return n
end
Instance={new=function(class) return New(class) end}
function Tween(n,props)
 for k,v in pairs(props) do n[k]=v end
 local completed=signal(); completions[#completions+1]=completed; return {Completed=completed}
end
function finish() local c=completions; completions={}; for _,s in ipairs(c) do s:Fire() end end
task={spawn=function(f) tasks[#tasks+1]=f end}
function flush() while #tasks>0 do local t=tasks; tasks={}; for _,f in ipairs(t) do f() end end end
Theme={Field='field',FieldHover='hover'}; Painted={}; Lighting={}
Library={Connections={},RepaintHooks={},SafeCallback=function(_,_,f) if f then task.spawn(f) end end}
function Track(c) Library.Connections[#Library.Connections+1]=c; return c end
function Label(parent,text) return New('TextLabel',{Parent=parent,Text=text}) end
function LabelColor(_,fallback) return fallback end
function Corner() end; function Stroke() end; function Pad() end; function List() end
function Hover() end
function Disableable(api)
 function api:SetEnabled(v) self.Enabled=v~=false; return self end
 return api
end
local function unit(...) return {...} end
UDim2={new=unit,fromScale=unit,fromOffset=unit}; Vector2={new=unit}; Color3={fromRGB=unit}
Enum={AutomaticSize={Y=1},ScrollBarInset={None=1},TextXAlignment={Center=1},TextTruncate={AtEnd=1},FillDirection={Horizontal=1},KeyCode={Escape=1}}
UserInputService={InputBegan=signal()}; Elements={}; Window={}
function NewContainer(window,frame) return setmetatable({Window=window,Container=frame},{__index=Elements}) end
function Elements:Label(text) return Label(self.Container,text) end
''')
buttons = source[source.index('local function MakeButton'):source.index('function Elements:Split')]
modals = source[source.index('function Window:Modal'):source.index('function Window:SetVisible')]
modals = modals.replace('closeVersion += 1', 'closeVersion = closeVersion + 1')
lua.execute(buttons + '\n' + modals)
lua.execute('''
local container=NewContainer({},New('Frame'))
local clicks=0
local row=container:ButtonRow({{Text='disabled',Disabled=true,Callback=function() clicks=clicks+1 end},{Text='enabled',Callback=function() clicks=clicks+1 end}})
row.Buttons[1].Activated:Fire(); row.Buttons[2].Activated:Fire(); flush()
assert(clicks==1)
for _,n in ipairs(nodes) do if n.Parent==row.Buttons[1] and n.ClassName=='TextLabel' then assert(n.TextTransparency==0.6) end end
local window=setmetatable({Main=New('Frame'),CloseFloating=function() end},{__index=Window})
local panel=window:Modal({}); panel:SetOpen(true); panel:SetOpen(false); panel:SetOpen(true); finish()
assert(panel.Alive and panel.Open and panel.Root.Visible)
panel:SetOpen(false); finish(); assert(panel.Alive and not panel.Root.Visible)
panel:SetOpen(true); panel:Destroy(); finish(); assert(not panel.Alive and panel.Blur==nil and #window.Modals==0)
for _,n in ipairs(nodes) do if n.ClassName=='BlurEffect' then assert(n.destroyed) end end
local baseline=#Library.Connections
local confirmed,dismissed=0,0
local prompt=window:Confirm({OnConfirm=function() confirmed=confirmed+1 end,OnDismiss=function() dismissed=dismissed+1 end})
local confirm
for _,n in ipairs(nodes) do if n.ClassName=='TextLabel' and n.Text=='save' and n:IsDescendantOf(prompt.Root) then confirm=n.Parent end end
confirm.Activated:Fire(); confirm.Activated:Fire(); flush(); finish()
assert(confirmed==1 and dismissed==0 and not prompt.Alive and #window.Modals==0)
assert(#Library.Connections==baseline)
prompt=window:Confirm({OnDismiss=function() dismissed=dismissed+1 end})
prompt:SetOpen(false); flush(); finish(); assert(dismissed==1 and not prompt.Alive)
panel=window:Modal({}); panel:SetOpen(true); panel.Root:Destroy(); finish(); assert(not panel.Alive and #window.Modals==0)
''')
actions = source[source.index('\t\tfunction api:AddAction'):source.index('\t\tfunction api:RemoveAction')]
lua.execute('''
api={Actions={}}; root=New('Frame'); actions={}; paints={}
function paint(f) paints[#paints+1]=f; f() end
function connect(s,f) return s:Connect(f) end
function refresh() end
function label(parent,text)
 local caption={Instance=Label(parent,text)}
 function caption:SetText(value) self.Instance.Text=value end
 return caption
end
''' + actions)
lua.execute('''
local clicks=0
local action=api:AddAction({Id='hop',Text='hop',Callback=function() clicks=clicks+1 end})
action.Instance.MouseEnter:Fire(); assert(action.Instance.BackgroundColor3==Theme.FieldHover)
for _,f in ipairs(paints) do f() end; assert(action.Instance.BackgroundColor3==Theme.FieldHover)
action.Instance.MouseLeave:Fire(); assert(action.Instance.BackgroundColor3==Theme.Field)
action:SetEnabled(false); action.Instance.MouseEnter:Fire(); action.Instance.Activated:Fire(); flush()
assert(clicks==0 and action.Instance.BackgroundColor3==Theme.Field)
action:SetEnabled(true); action.Instance.Activated:Fire(); flush(); assert(clicks==1)
''')
print('PASS: row disabled clicks, modal lifecycle/blur/subscriptions, confirm/dismiss once, Home action hover and disabled state')
