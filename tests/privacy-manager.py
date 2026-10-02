"""Privacy resolver and event-driven visual masking checks (Python + lupa)."""
from pathlib import Path
from lupa.lua54 import LuaRuntime
root=Path(__file__).resolve().parents[1]
lua=LuaRuntime()
lua.execute(r"""
Vector2={zero="zero vector"}
Enum={NormalId={Front="Front"}}
Color3={fromRGB=function(r,g,b) return r .. "," .. g .. "," .. b end}
table.clear=function(t) for k in pairs(t) do t[k]=nil end end
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
 local props={ClassName=class,Text=text or '',Image='',RichText=false,Transparency=0,BackgroundColor3='original background',BackgroundTransparency=1,ImageColor3='original tint',ImageRectOffset='original offset',ImageRectSize='original rect'}
 local events={Destroying=signal(),AncestryChanged=signal(),DescendantAdded=signal(),ChildAdded=signal(),CharacterAdded=signal(),CharacterRemoving=signal()}
 local changed={}
 local methods={}
 function methods:IsA(c) return props.ClassName==c or (c=="BasePart" and (props.ClassName=="Part" or props.ClassName=="MeshPart")) end
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
Instance={new=function(class) return node(class) end}
LocalPlayer=node('Player'); LocalPlayer.Name='RealUser'; LocalPlayer.DisplayName='Real Display'; LocalPlayer.UserId=123
playerGui=node('PlayerGui',LocalPlayer)
coreGui=node('CoreGui'); workspace=node('Workspace')
character=node('Model',workspace); LocalPlayer.Character=character
body=node('MeshPart',character); body.Name='Head'; body.Color='original color'; body.TextureID='body texture'
face=node('Decal',body); face.Transparency=0
rootPart=node('Part',character); rootPart.Name='HumanoidRootPart'; rootPart.Color='root color'
shirt=node('Shirt',character); shirt.ShirtTemplate='shirt texture'
hat=node('Accessory',character)
handle=node('Part',hat); handle.LocalTransparencyModifier=0
sparkles=node('ParticleEmitter',handle); sparkles.Enabled=true
tool=node('Tool',character); toolPart=node('Part',tool); toolPart.Color='tool color'
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
   function t:Gear(builder,gearOpts) self.GearOptions=gearOpts; local frame=node('Frame',Window.Overlay); builder(content(frame)); return self end
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
local panel=p:BuildPrivacySection(tab,1,{GearMaxHeight=160})
assert(panel.Controls.Enabled.GearOptions.MaxHeight==160)
panel.Controls.Enabled:Set(true)
assert(facilityLabel.Text=='teleport to seized.cc/1')
assert(gameLabel.Text=='Real Display has joined')
assert(LocalPlayer.Name=='RealUser' and LocalPlayer.DisplayName=='Real Display' and LocalPlayer.UserId==123)
assert(p:GetName()=='seized.cc/1' and p:GetIdentity().UserId==0)
assert(p:GetUserId()==0 and LocalPlayer.UserId==123)
assert(p:ResolveText('user id: 123; 1234; x123; 123_x')=='user id: 0; 1234; x123; 123_x')
assert(p:ResolveText('<font color="#123">123</font>','facility',true)=='<font color="#123">0</font>')
local idLabel=label(facilityGui,'user id: 123')
assert(idLabel.Text=='user id: 0')
panel.Controls.HideUserIds:Set(false)
assert(idLabel.Text=='user id: 123' and p:GetUserId()==123)
panel.Controls.HideUserIds:Set(true)
assert(idLabel.Text=='user id: 0')
local other={Name='Other',DisplayName='Other Display',UserId=456}
assert(p:GetUserId(other)==456)
assert(p:GetName(other)=='Other')
panel.Controls.AffectGame:Set(true)
assert(gameLabel.Text=='seized.cc/1 has joined')
local gameIdLabel=label(playerGui,'123'); assert(gameIdLabel.Text=='0')
assert(billboardLabel.Text=='seized.cc/1 plot' and health.Text=='100 HP')
assert(input.Text=='RealUser') -- editable values aren't rewritten
local newLabel=label(playerGui,'invite RealUser!')
assert(newLabel.Text=='invite seized.cc/1!')
newLabel.Text='Real Display is ready'
assert(newLabel.Text=='seized.cc/1 is ready')
p:Restore()
assert(newLabel.Text=='Real Display is ready')
assert(idLabel.Text=='user id: 123' and gameIdLabel.Text=='123')
assert(facilityLabel.Text=='teleport to RealUser' and billboardLabel.Text=='RealUser plot')
p:SetOptions({Enabled=true,AffectFacility=false})
assert(facilityLabel.Text=='teleport to RealUser' and gameLabel.Text=='seized.cc/1 has joined')
assert(idLabel.Text=='user id: 123' and gameIdLabel.Text=='0')
p:SetOptions({AffectFacility=true,HideUsername=false})
assert(facilityLabel.Text=='teleport to RealUser' and p:GetName()=='RealUser')
p:SetOptions({HideUsername=false,HideDisplayName=false})
assert(p:ResolveText('RealUser 123')=='RealUser 0')
p:SetOptions({HideUsername=true,HideDisplayName=false})
assert(gameLabel.Text=='Real Display has joined')
assert(p:ResolveText('RealUserExtra @RealUser / RealUser_2')=='RealUserExtra @seized.cc/1 / RealUser_2')
assert(p:ResolveText('<font color="RealUser">RealUser</font>','facility',true)=='<font color="RealUser">seized.cc/1</font>')
LocalPlayer.Name='A.B'; LocalPlayer.DisplayName='A.B Test'
p:SetOptions({HideDisplayName=true})
assert(p:ResolveText('A.B Test vs A.B; AxB')=='seized.cc/1 vs seized.cc/1; AxB')
LocalPlayer.Name='player'; LocalPlayer.DisplayName='seized.cc/1'
assert(p:ResolveText('seized.cc/1 vs player')=='seized.cc/1 vs seized.cc/1') -- no recursive expansion
LocalPlayer.Name='RealUser'; LocalPlayer.DisplayName='Real Display'
p:Refresh()
local moved=label(playerGui,'RealUser')
moved.Parent=nil; assert(moved.Text=='RealUser')
moved.Parent=facilityGui; assert(moved.Text=='seized.cc/1')
local futureGui=node('ScreenGui',coreGui)
Library.GuiRoots[futureGui]=true
p:WatchRoot(futureGui,'facility')
local notification=label(futureGui,'hello RealUser')
assert(notification.Text=='hello seized.cc/1')
-- Avatar masking follows the same roots and restores the latest source image.
local head='rbxthumb://type=AvatarHeadShot&id=123&w=150&h=150'
local bust='rbxthumb://id=123&type=AvatarBust&w=420&h=420'
local avatar=node('ImageLabel',facilityGui); avatar.Image=head
local placeholder=p:GetAvatar()
assert(placeholder=='rbxasset://textures/face.png' and avatar.Image==placeholder)
assert(avatar.BackgroundColor3=='255,255,255' and avatar.BackgroundTransparency==0)
assert(avatar.ImageRectSize==Vector2.zero)
avatar.BackgroundColor3='updated background'; assert(avatar.BackgroundColor3=='255,255,255')
assert(panel.Controls.HideAvatar.Value==true)
local gameAvatar=node('ImageButton',playerGui); gameAvatar.Image=bust
assert(gameAvatar.Image==placeholder)
local otherAvatar=node('ImageLabel',playerGui)
otherAvatar.Image='rbxthumb://type=AvatarHeadShot&id=456&w=150&h=150'
assert(otherAvatar.Image:find('id=456',1,true))
assert(p:ResolveImage('rbxthumb://type=GameIcon&id=123&w=150&h=150')=='rbxthumb://type=GameIcon&id=123&w=150&h=150')
assert(p:ResolveImage('rbxassetid://123')=='rbxassetid://123')
p:SetOptions({AffectGame=false}); assert(gameAvatar.Image==bust and avatar.Image==placeholder)
p:SetOptions({AffectGame=true,AffectFacility=false}); assert(gameAvatar.Image==placeholder and avatar.Image==head)
p:SetOptions({AffectFacility=true})
avatar.Image=bust; assert(avatar.Image==placeholder)
panel.Controls.HideAvatar:Set(false)
assert(avatar.Image==bust and gameAvatar.Image==bust)
assert(avatar.BackgroundColor3=='updated background' and avatar.BackgroundTransparency==1)
assert(avatar.ImageColor3=='original tint' and avatar.ImageRectSize=='original rect')
panel.Controls.HideAvatar:Set(true)
assert(avatar.Image==placeholder)
avatar.Parent=nil; assert(avatar.Image==bust)
avatar.Parent=facilityGui; assert(avatar.Image==placeholder)
p:Restore(); assert(avatar.Image==bust)
p:SetOptions({Enabled=true})
local function ownFace(head)
 for _,child in ipairs(head:GetChildren()) do if child.Name=='FacilityAnonymousFace' then return child end end
end
assert(ownFace(body) and ownFace(body).Texture=='rbxasset://textures/face.png')
assert(ownFace(body).Transparency==0)
assert(body.Color=='255,255,255' and body.TextureID=='')
assert(face.Transparency==1 and shirt.ShirtTemplate=='')
assert(handle.LocalTransparencyModifier==1 and sparkles.Enabled==false)
assert(rootPart.Color=='root color' and toolPart.Color=='tool color')
body.Color='updated color'; assert(body.Color=='255,255,255')
p:SetOptions({HideAvatar=false})
assert(body.Color=='updated color' and body.TextureID=='body texture')
assert(ownFace(body)==nil)
assert(face.Transparency==0 and shirt.ShirtTemplate=='shirt texture')
assert(handle.LocalTransparencyModifier==0 and sparkles.Enabled==true)
p:SetOptions({HideAvatar=true,AffectGame=false}); assert(body.Color=='updated color')
p:SetOptions({AffectGame=true})
assert(ownFace(body))
p:Refresh(); local faceCount=0
for _,child in ipairs(body:GetChildren()) do if child.Name=='FacilityAnonymousFace' then faceCount=faceCount+1 end end
assert(faceCount==1)
local pants=node('Pants',character); pants.PantsTemplate='late clothing'
assert(pants.PantsTemplate=='')
local detached=node('Decal',body); detached.Transparency=0
assert(detached.Transparency==1)
detached.Parent=workspace; assert(detached.Transparency==0)
local newCharacter=node('Model',workspace)
local newBody=node('Part',newCharacter); newBody.Name='Head'; newBody.Color='new body color'
LocalPlayer.CharacterRemoving:Fire(character)
assert(body.Color=='updated color' and pants.PantsTemplate=='late clothing')
LocalPlayer.Character=newCharacter; LocalPlayer.CharacterAdded:Fire(newCharacter)
assert(newBody.Color=='255,255,255' and ownFace(newBody))
p:SetAnonymous({Prefix='player '})
assert(p:GetName()=='player 1' and p:GetAnonymousIdentity().Name=='player 1')
assert(facilityLabel.Text=='teleport to player 1')
local identity=p:GetAnonymousIdentity(); identity.Name='changed'; identity.Appearance.Face='changed'
assert(p:GetAnonymousIdentity().Appearance.Face=='rbxasset://textures/face.png')
assert(not pcall(function() p:SetAnonymous({Prefix='<b>oops</b>'}) end))
p:SetAnonymous({Prefix='seized.cc/'})
local doomed=label(playerGui,'RealUser'); doomed:Destroy()
p:Destroy()
assert(gameLabel.Text=='Real Display has joined' and newLabel.Text=='Real Display is ready')
assert(facilityLabel.Text=='teleport to RealUser')
assert(not p.Alive and Library.PrivacyManager==nil)
assert(avatar.Image==bust and gameAvatar.Image==bust)
assert(newBody.Color=='new body color' and ownFace(newBody)==nil)
newBody.Color='after unload'; assert(newBody.Color=='after unload')
gameLabel.Text='RealUser again'; assert(gameLabel.Text=='RealUser again')
assert(not pcall(function() factory(Library):SetOptions({NotAnOption=true}) end))
Library.PrivacyManager:Destroy()
""")
print("PASS: identity toggles, scope separation, new/live UI, literal boundaries, RichText, character appearance/respawns, restoration and cleanup")
