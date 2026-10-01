"""Behavior checks with a mocked Roblox UI/runtime; run with Python + lupa."""
from pathlib import Path
from lupa.lua54 import LuaRuntime
lua = LuaRuntime()
lua.execute(r"""
table.find=function(t,v) for i,x in ipairs(t) do if x==v then return i end end end
function signal()
 local s={listeners={}}
 function s:Connect(f) local c={active=true}; function c:Disconnect() self.active=false end
 c.f=f; table.insert(self.listeners,c); return c end
 function s:Once(f) return self:Connect(f) end
 function s:Fire(...) for _,c in ipairs(self.listeners) do if c.active then c.f(...) end end end
 return s
end
function node()
 local n={Destroying=signal(),Visible=true}
 function n:GetChildren() return {} end
 function n:IsDescendantOf() return false end
 function n:Destroy() self.Destroying:Fire() end
 return n
end
Enum={TeleportState={Started=1,Failed=2}}
Players={LocalPlayer={OnTeleport=signal()}}
local encoded,serial={},0
HttpService={}
function HttpService:JSONEncode(t)
 serial=serial+1; local copy={}; for k,v in pairs(t) do copy[k]=v end
 encoded[tostring(serial)]=copy; return tostring(serial)
end
function HttpService:JSONDecode(s) assert(encoded[s],'bad json'); return encoded[s] end
game={GetService=function(_,n) return n=='Players' and Players or HttpService end}
warnings={}
warn=function(s) table.insert(warnings,s) end
env={seizedExecutions=3}
getgenv=function() return env end
queued={}
queue_on_teleport=function(code) if failQueue then error('failed') end; table.insert(queued,code) end
Library={Connections={},RepaintHooks={},Painted={},Registry={},Flags={},Theme={Danger='red'},FileSystem={Memory={}}}
function Library.FileSystem:EnsureFolder() return true end
function Library.FileSystem:Read(p) return self.Memory[p] end
function Library.FileSystem:Write(p,s) if failWrite then return false,'disk' end; self.Memory[p]=s; return true,'memory' end
function Library:SafeCallback(_,f,...) return f(...) end
function Library:SetToggleKey(v) self.key=v end
function Library:RefreshCursor() end
function Library:Destroy() self.destroyed=true end
Window={Main=node(),Overlay=node(),Scale={Scale=1},BaseScale=1}
function Window:SetUserScale(v) self.scale=v; self.BaseScale=v * 0.8 end
function Window:SetOpacity(v) self.opacity=v end
function Window:Modal()
 local m={Root=node(),Content={buttons={}}}
 function m.Content:Label() end
 function m.Content:Button(o) table.insert(self.buttons,o) end
 function m:SetOpen(v) self.Open=v end
 function m:Destroy() self.Root:Destroy() end
 return m
end
function Window:Confirm(o) self.confirm=o end
tab={Window=Window}
function tab:Section()
 local s={Frame=node()}
 local function control(_,o)
  local c={Options=o,Value=o.Default,Enabled=true}
  function c:Set(v,silent) self.Value=v; if not silent then (o.Callback or o.OnChanged)(v) end end
  function c:SetEnabled(v) self.Enabled=v end
  return c
 end
 s.Toggle=control; s.Slider=control; s.Dropdown=control; s.Keybind=control; s.Button=control
 function s:Divider() end
 return s
end
""")
root = Path(__file__).resolve().parents[1]
lua.globals().manager = lua.execute((root/'addons/InterfaceManager.luau').read_text())(lua.globals().Library)
lua.execute(r"""
local options={Window=Window,SettingsFolder='seized/settings',ResetFolder='seized',
 AutoExecute={Code='ran = true',CarryGlobals={'seizedExecutions'}}}
local a=manager:Create(tab,options)
assert(Window.Main.Visible and Window.scale==1 and Window.opacity==1)
Players.LocalPlayer.OnTeleport:Fire(1); assert(#queued==0)
a.Controls.ShowOnLoad:Set(false)
assert(Window.Main.Visible) -- takes effect next launch, not immediately
a.Controls.Scale:Set(125); assert(Window.scale==1.25)
a.Controls.AutoExecute:Set(true)
a.Controls.AutoExecute:Set(false)
Players.LocalPlayer.OnTeleport:Fire(1); assert(#queued==0)
a.Controls.AutoExecute:Set(true)
failQueue=true; Players.LocalPlayer.OnTeleport:Fire(1); assert(#queued==0 and #warnings==1)
failQueue=false; Players.LocalPlayer.OnTeleport:Fire(1)
Players.LocalPlayer.OnTeleport:Fire(1); assert(#queued==1)
env.seizedExecutions=nil; assert(load(queued[1]))(); assert(env.seizedExecutions==3 and ran)
a:Destroy()
local b=manager:Create(tab,options)
assert(Window.Scale.Scale == Window.BaseScale)
assert(not Library.Open and not Window.Main.Visible and Window.scale==1.25 and b.Controls.AutoExecute.Value)
b:Destroy()
local count=#queued; Players.LocalPlayer.OnTeleport:Fire(1); assert(#queued==count)
queue_on_teleport=nil
local c=manager:Create(tab,{Window=Window,SettingsFolder='other/settings'})
assert(not c.Controls.AutoExecute.Enabled)
c.Controls.AutoExecute:Set(true); assert(not c.Settings.AutoExecute)
failWrite=true; c.Controls.Opacity:Set(80); assert(#warnings==2 and Window.opacity==0.8)
failWrite=false
Library.FileSystem.Memory['seized/configs/a']='config'
local d=manager:Create(tab,options)
assert(d.Controls.Reset.Options.Color == 'red')
d.Controls.Reset.Options.Callback()
assert(Window.confirm.Confirm == 'delete everything')
assert(Window.confirm.Cancel == 'reset interface')
Window.confirm.OnCancel()
assert(Window.scale==1 and Window.opacity==1)
assert(not d.Settings.AutoExecute and d.Settings.ShowOnLoad)
assert(Library.FileSystem.Memory['seized/configs/a']=='config')
d.Controls.Reset.Options.Callback()
assert(Window.confirm.ConfirmColor=='red' and not Library.destroyed)
Window.confirm.OnConfirm()
assert(Library.destroyed and Library.FileSystem.Memory['seized/configs/a']==nil)
assert(Library.FileSystem.Memory['other/settings/interface.json']==nil) -- failed write wasn't saved
""")
print("PASS: settings persistence, startup visibility, routing controls, queue failure/retry/deduplication, carry globals, reset and cleanup")
