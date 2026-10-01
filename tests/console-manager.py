"""Simulated Roblox integration checks for ConsoleManager (requires lupa)."""
from pathlib import Path
from lupa.lua54 import LuaRuntime
root=Path(__file__).resolve().parents[1]
lua=LuaRuntime()
lua.execute(r'''
table.clear=function(t) for k in pairs(t) do t[k]=nil end end
table.find=function(t,v) for i,x in ipairs(t) do if x==v then return i end end end
typeof=type
function signal()
 local s={listeners={}}
 function s:Connect(f) local c={Connected=true,f=f}; function c:Disconnect() self.Connected=false end; self.listeners[#self.listeners+1]=c; return c end
 function s:Once(f) local c; c=self:Connect(function(...) c:Disconnect(); f(...) end); return c end
 function s:Fire(...) for _,c in ipairs(self.listeners) do if c.Connected then c.f(...) end end end
 return s
end
nodes={}; tasks={}; native={}
function new(class)
 local n={ClassName=class,Destroying=signal(),ZIndex=1,Visible=true}; nodes[#nodes+1]=n
 function n:GetChildren() local out={}; for _,x in ipairs(nodes) do if x.Parent==self then out[#out+1]=x end end; return out end
 function n:IsA(c) return self.ClassName==c end
 function n:IsDescendantOf(p) local x=self.Parent; while x do if x==p then return true end; x=x.Parent end; return false end
 function n:Destroy() if self.dead then return end; self.dead=true; self.Destroying:Fire(); for _,x in ipairs(self:GetChildren()) do x:Destroy() end; self.Parent=nil end
 return n
end
Instance={new=new}; local function unit(...) return {...} end
UDim2={new=unit}; UDim={new=unit}; Vector2={zero={}}
Enum={AutomaticSize={Y=1},ScrollingDirection={Y=1},SortOrder={LayoutOrder=1},TextXAlignment={Left=1},TextYAlignment={Top=1},MessageType={MessageOutput='print',MessageWarning='warn',MessageError='error'}}
task={delay=function(_,f) local t={f=f}; tasks[#tasks+1]=t; return t end,cancel=function(t) t.canceled=true end}
function flush() while #tasks>0 do local batch=tasks; tasks={}; for _,t in ipairs(batch) do if not t.canceled then t.f() end end end end
Library={Theme={Text='text',TextDim='dim',TextMarked='warn',Danger='error'},Connections={},RepaintHooks={},Painted={},FileSystem={EnsureFolder=function() return true end}}
function Library:OnRepaint(f) self.RepaintHooks[#self.RepaintHooks+1]=f; return f end
function control(content,opts,floating)
 local n=new('Frame'); n.Parent=content.Container
 local api={Instance=n,Options=opts,Value=opts.Default}
 function api:Set(value,silent) self.Value=value; if not silent and opts.Callback then opts.Callback(value) end end
 function api:SetText(value) self.Options.Text=value end
 function api:SetEnabled(value) self.Enabled=value end
 Library.Connections[#Library.Connections+1]=signal():Connect(function() end)
 Library:OnRepaint(function() end)
 Library.Painted[#Library.Painted+1]={n,'BackgroundColor3','Field'}
 if floating then local panel=new('Frame'); panel.Parent=content.Window.Overlay end
 return api
end
function content(parent,window)
 local c={Container=new('Frame'),Window=window}; c.Container.Parent=parent; c.Instance=c.Container
 function c:Dropdown(opts) return control(self,opts,true) end
 function c:Toggle(opts) return control(self,opts) end
 function c:Split(builders) for _,f in ipairs(builders) do f(self) end end
 function c:ButtonRow(buttons) local r={Controls={}}; for _,b in ipairs(buttons) do r.Controls[#r.Controls+1]=control(self,b) end; return r end
 function c:Button(opts) return control(self,opts) end
 return c
end
Window={Overlay=new('Frame'),FloatStack={}}
function Window:Modal()
 local m={Root=new('Frame'),Open=false,Scroller={ZIndex=1}}
 m.Content=content(m.Root,self)
 function m:SetOpen(value) self.Open=value end
 function m:Toggle() self:SetOpen(not self.Open) end
 function m:Destroy() self.Root:Destroy() end
 return m
end
function Window:IconAction(_,callback)
 local n=new('Button'); n.Callback=callback
 Library.Connections[#Library.Connections+1]=signal():Connect(callback)
 return n
end
LogService={MessageOut=signal()}
function LogService:Log(kind,message,context)
 if failNative then error('unsupported') end
 native[#native+1]={kind=kind,message=message}
 task.delay(0,function() if dropContext then context=nil end; self.MessageOut:Fire(message,kind,context) end)
end
local guid=0
HttpService={GenerateGUID=function() guid=guid+1; return tostring(guid) end}
game={JobId='job',GetService=function(_,name) return name=='LogService' and LogService or HttpService end}
print=function(message) native[#native+1]={message=message}; task.delay(0,function() LogService.MessageOut:Fire(message,'print') end) end
warn=function(message) native[#native+1]={message=message}; task.delay(0,function() LogService.MessageOut:Fire(message,'warn') end) end
setclipboard=function(value) clipboard=value end
writefile=function(path,value) if failWrite then error('disk failure') end; saved=value; savedPath=path end
function rows(console)
 local out={}; for _,n in ipairs(console.LogArea:GetChildren()) do if n:IsA('TextLabel') then out[#out+1]=n end end
 table.sort(out,function(a,b) return (a.LayoutOrder or 0)<(b.LayoutOrder or 0) end); return out
end
''')
addon=(root/'addons/ConsoleManager.luau').read_text().replace('saveCount += 1','saveCount = saveCount + 1')
lua.globals().ConsoleManager=lua.execute(addon)(lua.globals().Library)
lua.execute(r'''
local baselineConnections=#Library.Connections
local baselineHooks=#Library.RepaintHooks
local baselinePainted=#Library.Painted
local c=ConsoleManager:Create(Window,{Folder='seized/logs',Prefix='seized'})
for i=1,150 do c:Print('entry-'..i) end
flush(); assert(#rows(c)==100 and rows(c)[1].Text:find('entry%-51$'))
c:SetMaxVisibleRows(3); assert(#rows(c)==3)
local history=c:GetEntries(); history[1].message='changed'; assert(c:GetEntries()[1].message=='entry-1')
assert(c:Copy() and clipboard:find('entry%-1\n'))
c:Clear(); flush(); assert(rows(c)[1].Text=='no matching messages.')
assert(c:Save() and saved:find('entry%-1\n') and savedPath:find('^seized/logs/'))
failWrite=true; assert(not c:Save()); failWrite=false
c:SetOutput('both'); assert(c.Controls.UIOutput.Value and c.Controls.RobloxOutput.Value)
dropContext=true; c:Warn('same'); c:Warn('same'); flush(); assert(#rows(c)==2)
LogService.MessageOut:Fire('same','warn'); flush(); assert(#rows(c)==3)
assert(c.Controls.Target.Options.Text == 'source')
assert(c.Controls.Target.Options.Options[1] == 'script')
c.Controls.Target:Set('script'); flush(); assert(#rows(c)==2)
c:SetTarget('Roblox'); flush(); assert(#rows(c)==1)
c:SetTarget('Both'); c:Clear(); c:SetOutput('roblox'); c:Error('native error'); flush()
assert(rows(c)[1].Text=='no matching messages.' and native[#native].kind=='error')
local beforeNative = #native
local beforeEntries = #c:GetEntries()
c:SetOutput('none'); c:Print('muted'); flush()
assert(#native == beforeNative and #c:GetEntries() == beforeEntries)
c.Controls.UIOutput:Set(true)
c:Print('ui only'); flush()
assert(#native == beforeNative and #c:GetEntries() == beforeEntries + 1)
c:Clear()
c:SetOutput('both'); failNative=true; c:Error('fallback'); flush(); assert(#rows(c)==1)
failNative=false; c:SetFilter('Error',false); flush(); assert(rows(c)[1].Text=='no matching messages.')
c:SetFilter('Error',true); c:SetOutput('console'); c:SetCaptureRoblox(false)
local count=#c:GetEntries()
LogService.MessageOut:Fire('ignored','print'); flush(); assert(#c:GetEntries()==count)
c:SetCaptureRoblox(true); c:Print('<b>rich</b>'); LogService.MessageOut:Fire('<b>literal</b>','print'); flush()
assert(rows(c)[2].RichText and not rows(c)[3].RichText)
c:Toggle(); assert(c.Modal.Open); c:Toggle(); assert(not c.Modal.Open)
c:Print('pending'); c:Destroy(); flush(); assert(not c.Alive and #c:GetEntries()==0)
assert(#Library.Connections==baselineConnections and #Library.RepaintHooks==baselineHooks and #Library.Painted==baselinePainted)
assert(#Window.Overlay:GetChildren()==0)
assert(not c:Copy() and not c:Save())
local tab={Window=Window,Root=new('Frame')}; function tab:Cards() return content(self.Root,self.Window) end
local inline=ConsoleManager:Create(tab,{CaptureRoblox=false,Controls={Output=false,Target=false,Filters=false,Copy=false,Save=false,Clear=false},Labels={Empty='empty'}})
assert(not inline.Modal and not inline.Button and inline.Controls.Output==nil and rows(inline)[1].Text=='empty')
inline:Print('inline'); inline:SetTarget('Script'); flush(); assert(#rows(inline)==1)
tab.Root:Destroy(); flush(); assert(not inline.Alive and #Library.RepaintHooks==baselineHooks)
local a=ConsoleManager:Create(Window); local b=ConsoleManager:Create(Window)
a:Destroy(); LogService.MessageOut:Fire('still captured','print'); flush(); assert(#b:GetEntries()==1)
b.Modal:Destroy(); flush(); assert(not b.Alive and #Library.Connections==baselineConnections)
local before=#nodes; assert(not pcall(function() ConsoleManager:Create(Window,{MaxVisibleRows=0}) end)); assert(#nodes==before)
assert(not pcall(function() ConsoleManager:Create(Window,{Output='invalid'}) end))
''')
print('PASS: console limits, filters, routing/deduplication, history/export, options, mounts and cleanup')
