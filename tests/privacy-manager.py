"""Privacy resolver and event-driven visual masking checks (Python + lupa)."""
from pathlib import Path
from lupa.lua54 import LuaRuntime
root=Path(__file__).resolve().parents[1]
lua=LuaRuntime()
lua.execute(r"""
table.find=function(t,v) for i,x in ipairs(t) do if x==v then return i end end end
function signal()
 local s={listeners={}}
 function s:Connect(f)
  local c={Connected=true,f=f}; function c:Disconnect() self.Connected=false end
  self.listeners[#self.listeners+1]=c; return c
 end
 function s:Once(f) local c; c=self:Connect(function(...) c:Disconnect(); f(...) end); return c end
 function s:Fire(...) for _,c in ipairs(self.listeners) do if c.Connected then c.f(...) end end end
 return s
end
nodes={}
function node(class,parent,text)
 local props={ClassName=class,Text=text or '',RichText=false}
 local events={Destroying=signal(),AncestryChanged=signal(),DescendantAdded=signal(),ChildAdded=signal()}
 local changed={}
 local methods={}
 function methods:IsA(c) return props.ClassName==c end
 function methods:GetPropertyChangedSignal(k) changed[k]=changed[k] or signal(); return changed[k] end
 function methods:IsDescendantOf(root)
  local p=props.Parent; while p do if p==root then return true end; p=p.Parent end; return false
 end
 function methods:GetDescendants()
  local out={}; for _,v in ipairs(nodes) do if v:IsDescendantOf(self) then out[#out+1]=v end end; return out
 end
 function methods:GetChildren()
  local out={}; for _,v in ipairs(nodes) do if v.Parent==self then out[#out+1]=v end end; return out
 end
 function methods:FindFirstChildOfClass(c)
  for _,v in ipairs(self:GetChildren()) do if v:IsA(c) then return v end end
 end
 function methods:Destroy()
  if props.dead then return end
  props.dead=true; events.Destroying:Fire()
  for _,v in ipairs(self:GetChildren()) do v:Destroy() end
  self.Parent=nil
 end
 local n
 n=setmetatable({},{
  __index=function(_,k) return methods[k] or events[k] or props[k] end,
  __newindex=function(_,k,v)
   local old=props[k]; props[k]=v
   if old==v then return end
   if changed[k] then changed[k]:Fire() end
   if k=='Parent' then
    events.AncestryChanged:Fire(n,v)
    if v then
     v.ChildAdded:Fire(n)
     local p=v; while p do p.DescendantAdded:Fire(n); for _,d in ipairs(n:GetDescendants()) do p.DescendantAdded:Fire(d) end; p=p.Parent end
    end
   end
  end,
 })
 nodes[#nodes+1]=n; n.Parent=parent; return n
end
LocalPlayer=node('Player'); LocalPlayer.Name='RealUser'; LocalPlayer.DisplayName='Real Display'; LocalPlayer.UserId=123
playerGui=node('PlayerGui',LocalPlayer)
coreGui=node('CoreGui'); workspace=node('Workspace')
Players={LocalPlayer=LocalPlayer}
game={GetService=function(_,name)
 if name=='Players' then return Players elseif name=='CoreGui' then return coreGui elseif name=='Workspace' then return workspace end
end}
facilityGui=node('ScreenGui',coreGui)
Library={GuiRoots={[facilityGui]=true},Addons={},Connections={},RepaintHooks={},Painted={}}
function label(parent,value) return node('TextLabel',parent,value) end
facilityLabel=label(facilityGui,'teleport to RealUser')
gameLabel=label(playerGui,'Real Display has joined')
input=node('TextBox',playerGui,'RealUser')
billboard=node('BillboardGui',workspace); billboardLabel=label(billboard,'RealUser plot')
health=label(billboard,'100 HP')
Window={Overlay=node('Frame',facilityGui),FloatStack={}}
tab={Window=Window}
function tab:Section()
 local s={Frame=node('Frame',facilityGui)}
 local function content(parent)
  local c={}
  function c:Toggle(opts)
   local t={Options=opts,Value=opts.Default}
   function t:Set(v,silent) self.Value=v; if not silent then opts.Callback(v) end end
   function t:Gear(builder) local frame=node('Frame',Window.Overlay); builder(content(frame)); return self end
   return t
  end
  function c:Divider() end
  return c
 end
 local c=content(s.Frame); c.Frame=s.Frame; return c
end
""")
lua.globals().factory=lua.execute((root/'addons/PrivacyManager.luau').read_text())
lua.execute(r"""
local p=factory(Library)
assert(factory(Library)==p)
assert(facilityLabel.Text=='teleport to RealUser')
local panel=p:BuildPrivacySection(tab,1)
panel.Controls.Enabled:Set(true)
assert(facilityLabel.Text=='teleport to player 001')
assert(gameLabel.Text=='Real Display has joined')
assert(LocalPlayer.Name=='RealUser' and LocalPlayer.DisplayName=='Real Display' and LocalPlayer.UserId==123)
assert(p:GetName()=='player 001' and p:GetIdentity().UserId==123)
local other={Name='Other',DisplayName='Other Display',UserId=456}
assert(p:GetName(other)=='Other')
panel.Controls.AffectGame:Set(true)
assert(gameLabel.Text=='player 001 has joined')
assert(billboardLabel.Text=='player 001 plot' and health.Text=='100 HP')
assert(input.Text=='RealUser') -- editable values aren't rewritten
local newLabel=label(playerGui,'invite RealUser!')
assert(newLabel.Text=='invite player 001!')
newLabel.Text='Real Display is ready'
assert(newLabel.Text=='player 001 is ready')
p:Restore()
assert(newLabel.Text=='Real Display is ready')
assert(facilityLabel.Text=='teleport to RealUser' and billboardLabel.Text=='RealUser plot')
p:SetOptions({Enabled=true,AffectFacility=false})
assert(facilityLabel.Text=='teleport to RealUser' and gameLabel.Text=='player 001 has joined')
p:SetOptions({AffectFacility=true,HideUsername=false})
assert(facilityLabel.Text=='teleport to RealUser' and p:GetName()=='RealUser')
p:SetOptions({HideUsername=true,HideDisplayName=false})
assert(gameLabel.Text=='Real Display has joined')
assert(p:ResolveText('RealUserExtra @RealUser / RealUser_2')=='RealUserExtra @player 001 / RealUser_2')
assert(p:ResolveText('<font color="RealUser">RealUser</font>','facility',true)=='<font color="RealUser">player 001</font>')
LocalPlayer.Name='A.B'; LocalPlayer.DisplayName='A.B Test'
p:SetOptions({HideDisplayName=true})
assert(p:ResolveText('A.B Test vs A.B; AxB')=='player 001 vs player 001; AxB')
LocalPlayer.Name='player'; LocalPlayer.DisplayName='player 001'
assert(p:ResolveText('player 001 vs player')=='player 001 vs player 001') -- no recursive expansion
LocalPlayer.Name='RealUser'; LocalPlayer.DisplayName='Real Display'
p:Refresh()
local moved=label(playerGui,'RealUser')
moved.Parent=nil; assert(moved.Text=='RealUser')
moved.Parent=facilityGui; assert(moved.Text=='player 001')
local futureGui=node('ScreenGui',coreGui)
Library.GuiRoots[futureGui]=true
p:WatchRoot(futureGui,'facility')
local notification=label(futureGui,'hello RealUser')
assert(notification.Text=='hello player 001')
local doomed=label(playerGui,'RealUser'); doomed:Destroy()
p:Destroy()
assert(gameLabel.Text=='Real Display has joined' and newLabel.Text=='Real Display is ready')
assert(facilityLabel.Text=='teleport to RealUser')
assert(not p.Alive and Library.PrivacyManager==nil)
gameLabel.Text='RealUser again'; assert(gameLabel.Text=='RealUser again')
assert(not pcall(function() factory(Library):SetOptions({NotAnOption=true}) end))
Library.PrivacyManager:Destroy()
""")
print("PASS: identity toggles, scope separation, new/live UI, literal boundaries, RichText, restoration and cleanup")
