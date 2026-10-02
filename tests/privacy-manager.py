"""Privacy resolver and event-driven visual masking checks (Python + lupa)."""
from pathlib import Path
from lupa.lua54 import LuaRuntime
root=Path(__file__).resolve().parents[1]
lua=LuaRuntime()
lua.execute(r"""
Vector2={zero="zero vector"}
Enum={NormalId={Front="Front"},Material={SmoothPlastic="SmoothPlastic"},MeshType={Head="Head"}}
Vector3={new=function(x,y,z) return {X=x,Y=y,Z=z} end,zero={X=0,Y=0,Z=0}}
CFrame={new=function(...) return {position={...}} end,lookAt=function(a,b) return {eye=a,target=b} end}
UDim2={fromScale=function(x,y) return {x=x,y=y} end}
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
 local props={ClassName=class,Text=text or '',Image='',RichText=false,Transparency=0,LocalTransparencyModifier=0,ImageTransparency=0,ZIndex=1,BackgroundColor3='original background',BackgroundTransparency=1,ImageColor3='original tint',ImageRectOffset='original offset',ImageRectSize='original rect'}
 local events={Destroying=signal(),AncestryChanged=signal(),DescendantAdded=signal(),ChildAdded=signal(),CharacterAdded=signal(),CharacterRemoving=signal()}
 local changed={}
 local attributes={}
 local attributeSignals={}
 local methods={}
 function methods:GetAttribute(k) return attributes[k] end
 function methods:GetAttributeChangedSignal(k) attributeSignals[k]=attributeSignals[k] or signal(); return attributeSignals[k] end
 function methods:SetAttribute(k,v) attributes[k]=v; self:GetAttributeChangedSignal(k):Fire() end
 function methods:Clone() local copy=node(props.ClassName); return copy end
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
RunService={RenderStepped=signal()}
game={GetService=function(_,name)
 if name=='RunService' then return RunService elseif name=='Players' then return Players elseif name=='CoreGui' then return coreGui elseif name=='Workspace' then return workspace end
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
  function c:Input(opts)
   local t={Instance=node('Frame',parent),Options=opts,Value=opts.Default or ''}
   function t:Set(v) self.Value=v; if opts.Callback then opts.Callback(v) end end
   return t
  end
  c.Dropdown=c.Input
  function c:Button(opts)
   local t={Options=opts,Visible=true}; function t:SetVisible(v) self.Visible=v end; return t
  end
  function c:ButtonRow(opts) return opts end
  function c:Label(value)
   local t={Value=value}; function t:Set(v) self.Value=v end; return t
  end
  function c:Divider() end
  return c
 end
 local c=content(s.Frame); c.Frame=s.Frame; return c
end
function Window:Modal(opts)
 local m={Content=tab:Section(),Options=opts,Open=false}
 function m:SetOpen(v) self.Open=v end
 function m:Destroy() self.Destroyed=true; self.Content.Frame:Destroy() end
 return m
end
""")
lua.globals().factory=lua.execute((root/'addons/PrivacyManager.luau').read_text())
lua.execute(r"""
local p=factory(Library)
assert(factory(Library)==p)
assert(facilityLabel.Text=='teleport to RealUser')
local panel=p:BuildPrivacySection(tab,1,{GearMaxHeight=160})
assert(panel.Controls.Enabled.GearOptions.MaxHeight==160)
assert(not panel.EditCustom.Visible)
panel.MethodControl:Set('custom'); assert(panel.EditCustom.Visible)
panel.EditCustom.Options.Callback(); assert(panel.CustomEditor.Open)
panel.EditorControls.DisplayName:Set('test name')
assert(panel.EditorControls.Preview.Value:find('test name',1,true))
panel.EditorControls.Badge:Set('custom'); assert(panel.EditorControls.BadgeText.Instance.Visible)
panel.EditorControls.BadgeText:Set('tester')
assert(panel.EditorControls.Preview.Value:find('test name tester',1,true))
assert(panel.EditorControls.Load.Options.Disabled)
assert(p:GetName()=='RealUser')
panel.MethodControl:Set('anonymous'); assert(not panel.EditCustom.Visible)
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
assert(placeholder=='rbxassetid://144080495' and avatar.Image=="")
assert(avatar.BackgroundColor3=='original background' and avatar.BackgroundTransparency==1)
assert(avatar.ImageRectSize=='original rect')
avatar.BackgroundColor3='updated background'; assert(avatar.BackgroundColor3=='updated background')
local function preview(image)
 for _,child in ipairs(image:GetChildren()) do if child.Name=='FacilityAnonymousPortrait' then return child end end
end
assert(preview(avatar) and preview(avatar):IsA('ViewportFrame'))
assert(preview(avatar).CurrentCamera)
local portrait=preview(avatar)
assert(portrait.CurrentCamera.CFrame.eye.Z == -3.1)
assert(portrait.CurrentCamera.CFrame.target.Y == 2.5)
local portraitWorld=portrait:FindFirstChildOfClass('WorldModel')
local portraitHead=portraitWorld:FindFirstChildOfClass('Part')
local headMesh=portraitHead:FindFirstChildOfClass('SpecialMesh')
assert(headMesh.Scale.X==1.25 and headMesh.Scale.Y==1.25 and headMesh.Scale.Z==1.25)
local firstPreview=preview(avatar)
avatar.Image=bust; assert(preview(avatar)~=firstPreview and firstPreview.Parent==nil)
avatar.Image=head
avatar.ImageTransparency=0.5; assert(preview(avatar).ImageTransparency==0.5)
assert(panel.Controls.HideAvatar.Value==true)
local gameAvatar=node('ImageButton',playerGui); gameAvatar.Image=bust
assert(gameAvatar.Image=="")
local otherAvatar=node('ImageLabel',playerGui)
otherAvatar.Image='rbxthumb://type=AvatarHeadShot&id=456&w=150&h=150'
assert(otherAvatar.Image:find('id=456',1,true))
assert(p:ResolveImage('rbxthumb://type=GameIcon&id=123&w=150&h=150')=='rbxthumb://type=GameIcon&id=123&w=150&h=150')
assert(p:ResolveImage('rbxassetid://123')=='rbxassetid://123')
p:SetOptions({AffectGame=false}); assert(gameAvatar.Image==bust and avatar.Image=="")
p:SetOptions({AffectGame=true,AffectFacility=false}); assert(gameAvatar.Image=="" and avatar.Image==head)
p:SetOptions({AffectFacility=true})
avatar.Image=bust; assert(avatar.Image=="")
panel.Controls.HideAvatar:Set(false)
assert(avatar.Image==bust and gameAvatar.Image==bust)
assert(preview(avatar)==nil and preview(gameAvatar)==nil)
assert(avatar.BackgroundColor3=='updated background' and avatar.BackgroundTransparency==1)
assert(avatar.ImageColor3=='original tint' and avatar.ImageRectSize=='original rect')
panel.Controls.HideAvatar:Set(true)
assert(avatar.Image=="")
avatar.Parent=nil; assert(avatar.Image==bust)
avatar.Parent=facilityGui; assert(avatar.Image=="")
p:Restore(); assert(avatar.Image==bust)
p:SetOptions({Enabled=true})
local function ownFace(head)
 for _,child in ipairs(head.Parent:GetChildren()) do
  if child.Name=='FacilityAnonymousHead' then
   for _,decal in ipairs(child:GetChildren()) do if decal.Name=='FacilityAnonymousFace' then return decal end end
  end
 end
end
assert(ownFace(body) and ownFace(body).Texture=='rbxassetid://144080495')
assert(ownFace(body).Transparency==0 and body.Transparency==1)
local proxy=ownFace(body).Parent
local proxyMesh=proxy:FindFirstChildOfClass("SpecialMesh")
assert(proxyMesh.Scale.X==1.25 and proxyMesh.Scale.Y==1.25 and proxyMesh.Scale.Z==1.25)
assert(proxy.Anchored and not proxy.CanCollide and not proxy.CanQuery and not proxy.CanTouch)
body.CFrame=CFrame.new(4,5,6); body.LocalTransparencyModifier=0.8
RunService.RenderStepped:Fire()
assert(proxy.CFrame==body.CFrame and proxy.LocalTransparencyModifier==0.8)
body.Transparency=0.4; RunService.RenderStepped:Fire()
assert(body.Transparency==1 and proxy.Transparency==0.4)
body.Transparency=0
RunService.RenderStepped:Fire()
assert(body.Color=='255,255,255' and body.TextureID=='')
assert(face.Transparency==1 and shirt.ShirtTemplate=='')
assert(handle.LocalTransparencyModifier==1 and sparkles.Enabled==false)
assert(rootPart.Color=='root color' and toolPart.Color=='tool color')
body.Color='updated color'; assert(body.Color=='255,255,255')
p:SetOptions({HideAvatar=false})
assert(body.Color=='updated color' and body.TextureID=='body texture')
assert(ownFace(body)==nil and body.Transparency==0)
assert(face.Transparency==0 and shirt.ShirtTemplate=='shirt texture')
assert(handle.LocalTransparencyModifier==0 and sparkles.Enabled==true)
p:SetOptions({HideAvatar=true,AffectGame=false}); assert(body.Color=='updated color')
p:SetOptions({AffectGame=true})
assert(ownFace(body))
p:Refresh(); local faceCount=0
for _,child in ipairs(character:GetChildren()) do if child.Name=='FacilityAnonymousHead' then faceCount=faceCount+1 end end
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
assert(p:GetAnonymousIdentity().Appearance.Face=='rbxassetid://144080495')
assert(not pcall(function() p:SetAnonymous({Prefix='<b>oops</b>'}) end))
p:SetAnonymous({Prefix='seized.cc/'})
-- Existing/open, newly created, late-owned and explicitly registered previews.
local viewport=node('ViewportFrame',playerGui)
local camera=node('Camera',viewport); viewport.CurrentCamera=camera
local function rig(parent,name)
 local model=node('Model'); model.Name=name
 local head=node('Part',model); head.Name='Head'; head.Color='skin'
 local torso=node('Part',model); torso.Name='Torso'; torso.Color='skin'
 local humanoid=node('Humanoid',model)
 local accessory=node('Accessory',model); local hair=node('Part',accessory)
 local clothes=node('Shirt',model); clothes.ShirtTemplate='outfit'
 model.Parent=parent
 return model,head,torso,hair,clothes
end
p:Restore()
local copy,copyHead,copyTorso,copyHair,copyShirt=rig(viewport,'RealUser')
assert(copyHair.Transparency==0 and copyShirt.ShirtTemplate=='outfit')
p:SetOptions({Enabled=true})
assert(copyHair.Transparency==1 and copyHair.LocalTransparencyModifier==0)
assert(copyHead.Transparency==1 and copyTorso.Color=='255,255,255' and ownFace(copyHead))
assert(copyShirt.ShirtTemplate=='' and viewport.CurrentCamera==camera)
local lateAccessory=node('Accessory',copy); local lateHair=node('Part',lateAccessory)
assert(lateHair.Transparency==1)
copyShirt.ShirtTemplate='new outfit'; assert(copyShirt.ShirtTemplate=='')
p:SetOptions({AffectGame=false})
assert(copyHair.Transparency==0 and copyShirt.ShirtTemplate=='new outfit' and ownFace(copyHead)==nil)
p:SetOptions({AffectGame=true})
local unit,unitHead,unitTorso,unitHair=rig(viewport,'SomeUnit')
assert(unitHair.Transparency==0 and unitHead.Transparency==0)
unit:SetAttribute('UserId',123)
assert(unitHair.Transparency==1)
unit:SetAttribute('UserId',456)
assert(unitHair.Transparency==0 and ownFace(unitHead)==nil)
local unregister=p:RegisterPreview(unit,LocalPlayer)
assert(unitHair.Transparency==1)
unregister(); assert(unitHair.Transparency==0)
copy.Parent=nil
assert(copyHair.Transparency==0 and copyShirt.ShirtTemplate=='new outfit')
copy.Parent=viewport; assert(copyHair.Transparency==1)
copy.Name='SomeoneElse'; assert(copyHair.Transparency==0)
copy.Name='RealUser'; assert(copyHair.Transparency==1)
local facilityViewport=node('ViewportFrame',facilityGui)
local facilityRig,facilityHead,facilityTorso,facilityHair=rig(facilityViewport,'RealUser')
p:SetOptions({AffectGame=false}); assert(facilityHair.Transparency==1 and copyHair.Transparency==0)
p:SetOptions({AffectFacility=false}); assert(facilityHair.Transparency==0)
p:SetOptions({AffectGame=true,AffectFacility=true})
-- A clone made while privacy was active includes the owned head and hidden real head.
local inherited,inheritedReal=rig(nil,'RealUser')
inheritedReal.Transparency=1
local inheritedProxy=node('Part',inherited); inheritedProxy.Name='FacilityAnonymousHead'
inherited.Parent=viewport
local visibleHeads=0
for _,child in ipairs(inherited:GetChildren()) do
 if child.Name=='FacilityAnonymousHead' and child.Transparency==0 then visibleHeads=visibleHeads+1 end
end
assert(visibleHeads==1 and inheritedProxy.Transparency==1)
local rebuilt,rebuiltHead,rebuiltTorso,rebuiltHair=rig(viewport,'RealUser')
rebuilt:Destroy(); assert(rebuilt.Parent==nil)
local doomed=label(playerGui,'RealUser'); doomed:Destroy()
p:Destroy()
assert(copyHair.Transparency==0 and copyShirt.ShirtTemplate=='new outfit')
assert(facilityHair.Transparency==0 and ownFace(facilityHead)==nil)
assert(gameLabel.Text=='Real Display has joined' and newLabel.Text=='Real Display is ready')
assert(facilityLabel.Text=='teleport to RealUser')
assert(not p.Alive and Library.PrivacyManager==nil)
assert(avatar.Image==bust and gameAvatar.Image==bust)
assert(preview(avatar)==nil and preview(gameAvatar)==nil)
assert(newBody.Color=='new body color' and ownFace(newBody)==nil)
newBody.Color='after unload'; assert(newBody.Color=='after unload')
gameLabel.Text='RealUser again'; assert(gameLabel.Text=='RealUser again')
assert(not pcall(function() factory(Library):SetOptions({NotAnOption=true}) end))
Library.PrivacyManager:Destroy()
""")
print("PASS: identity toggles, scope separation, new/live UI, literal boundaries, RichText, character appearance/respawns, restoration and cleanup")
