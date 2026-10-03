"""Privacy resolver and event-driven visual masking checks (Python + lupa)."""
from pathlib import Path
from lupa.lua54 import LuaRuntime
root=Path(__file__).resolve().parents[1]
lua=LuaRuntime()
lua.execute(r"""
randomDraws={}; randomDrawCount=0
Random={new=function() return {NextNumber=function()
 randomDrawCount=randomDrawCount+1
 return table.remove(randomDraws,1) or 0
end} end}
tasks={}
task={defer=function(f) tasks[#tasks+1]=coroutine.create(f) end,wait=function() coroutine.yield() end}
function stepTasks()
 local pending=tasks; tasks={}
 for _,co in ipairs(pending) do
  local ok,err=coroutine.resume(co); assert(ok,err)
  if coroutine.status(co)~='dead' then tasks[#tasks+1]=co end
 end
end
function drainTasks()
 for i=1,30 do if #tasks==0 then return end; stepTasks() end
 error('task did not finish')
end
Vector2={zero="zero vector"}
Enum={HumanoidRigType={R6="R6",R15="R15"},HumanoidDisplayDistanceType={None="None"},NormalId={Front="Front"},Material={SmoothPlastic="SmoothPlastic"},MeshType={Head="Head"}}
Vector3={new=function(x,y,z) return {X=x,Y=y,Z=z} end,zero={X=0,Y=0,Z=0}}
local cfMeta={}
function cf(x,y,z,angle)
 local t={position={x or 0,y or 0,z or 0},angle=angle or 0}
 function t:Inverse()
  local c,s=math.cos(self.angle),math.sin(self.angle)
  local p=self.position
  return cf(-c*p[1]-s*p[3],-p[2],s*p[1]-c*p[3],-self.angle)
 end
 function t:ToObjectSpace(v) return self:Inverse()*v end
 return setmetatable(t,cfMeta)
end
cfMeta.__mul=function(a,b)
 local c,s=math.cos(a.angle),math.sin(a.angle)
 return cf(a.position[1]+c*b.position[1]-s*b.position[3],a.position[2]+b.position[2],
  a.position[3]+s*b.position[1]+c*b.position[3],a.angle+b.angle)
end
CFrame={new=cf,lookAt=function(a,b) return {eye=a,target=b} end}
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
local propsByNode={}
function node(class,parent,text)
 local props={CFrame=CFrame.new(),ClassName=class,Text=text or '',Image='',RichText=false,Transparency=0,LocalTransparencyModifier=0,ImageTransparency=0,ZIndex=1,BackgroundColor3='original background',BackgroundTransparency=1,ImageColor3='original tint',ImageRectOffset='original offset',ImageRectSize='original rect'}
 local events={Destroying=signal(),AncestryChanged=signal(),DescendantAdded=signal(),ChildAdded=signal(),CharacterAdded=signal(),CharacterRemoving=signal()}
 local changed={}
 local attributes={}
 local attributeSignals={}
 local methods={}
 function methods:GetAttribute(k) return attributes[k] end
 function methods:GetAttributeChangedSignal(k) attributeSignals[k]=attributeSignals[k] or signal(); return attributeSignals[k] end
 function methods:SetAttribute(k,v) attributes[k]=v; self:GetAttributeChangedSignal(k):Fire() end
 function methods:Clone()
  local copies={}
  local function copyTree(original)
   local source=propsByNode[original]
   local copy=node(source.ClassName); copies[original]=copy
   for k,v in pairs(source) do if k~='Parent' and k~='dead' then copy[k]=v end end
   for _,child in ipairs(original:GetChildren()) do copyTree(child).Parent=copy end
   return copy
  end
  local root=copyTree(self)
  for original,copy in pairs(copies) do
   for k,v in pairs(propsByNode[original]) do if copies[v] then copy[k]=copies[v] end end
  end
  return root
 end
 function methods:FindFirstChild(name)
  for _,v in ipairs(self:GetChildren()) do if v.Name==name then return v end end
 end
 function methods:IsA(c) return props.ClassName==c or (c=="JointInstance" and props.ClassName=="Weld") or (c=="BasePart" and (props.ClassName=="Part" or props.ClassName=="MeshPart")) end
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
 nodes[#nodes+1]=n; propsByNode[n]=props; n.Parent=parent; return n
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
serverPlayers={LocalPlayer}
Players={LocalPlayer=LocalPlayer,PlayerAdded=signal(),PlayerRemoving=signal()}
function Players:GetPlayers() return serverPlayers end
validAccounts={[456]={Username='AccountUser',DisplayName='Account Display'}}
accountRequests={}; createdRigs={}

function Players:GetUserIdFromNameAsync(name) assert(name=='AccountUser','not found'); return 456 end
function Players:GetHumanoidDescriptionFromUserIdAsync(id) assert(validAccounts[id]); if appearanceFailure then error('appearance unavailable') end; return node('HumanoidDescription') end
function Players:CreateHumanoidModelFromDescriptionAsync(description,kind)
 local model=node('Model'); createdRigs[#createdRigs+1]=model; local h=node('Humanoid',model); h.RigType=kind
 local head=node('Part',model); head.Name='Head'; head.Color='loaded skin'
 local torso=node('Part',model); torso.Name='Torso'; torso.Color='loaded skin'
 local shirt=node('Shirt',model); shirt.ShirtTemplate='loaded shirt'
 -- Unassembled handles deliberately sit far away from the rig body.
 local function accessory(name,weldMode)
  local acc=node('Accessory',model); acc.Name=name
  local part=node('Part',acc); part.Name='Handle'; part.CFrame=CFrame.new(454,-10,-75)
  local mesh=node('SpecialMesh',part); mesh.Scale=Vector3.new(13,13,12)
  if weldMode then
   local weld=node('Weld',part); weld.Name='AccessoryWeld'
   if weldMode=='normal' then
    weld.Part0=part; weld.Part1=head; weld.C0=CFrame.new(1,0.2,0); weld.C1=cf(0,0.7,0,math.pi/2)
   else
    weld.Part0=head; weld.Part1=part; weld.C0=cf(0,0.8,0,-math.pi/2); weld.C1=CFrame.new(1,0.2,0)
   end
  else
   local a=node('Attachment',part); a.Name='HatAttachment'; a.CFrame=CFrame.new(1,0.1,0)
  end
 end
 local attachment=node('Attachment',head); attachment.Name='HatAttachment'; attachment.CFrame=cf(0,0.9,0,math.pi)
 accessory('Hair','normal'); accessory('ScaledHead','reverse'); accessory('WithoutWeld')
 node('JointInstance',model); node('Constraint',model)
 return model
end
UserService={GetUserInfosByUserIdsAsync=function(_,ids)
 accountRequests[#accountRequests+1]=ids[1]
 if yieldLookup then task.wait() end
 assert(validAccounts[ids[1]],'not found'); return {validAccounts[ids[1]]}
end}
RunService={RenderStepped=signal()}
game={GetService=function(_,name)
 if name=='UserService' then return UserService elseif name=='RunService' then return RunService elseif name=='Players' then return Players elseif name=='CoreGui' then return coreGui elseif name=='Workspace' then return workspace end
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
   function t:Get() return self.Value end
   function t:Set(v,silent) self.Value=v; if not silent and opts.Callback then opts.Callback(v) end end
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
 local m={Content=tab:Section(),Options=opts,Open=false,Root=node('Frame',facilityGui)}
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
assert(panel.EditorControls.StatusIcon.Options.Disabled == true)
assert(panel.EditorControls.Verification.Options.Disabled == true)
assert(#panel.EditorControls.StatusIcon.Options.Options == 8)
assert(#panel.EditorControls.Verification.Options.Options == 3)
assert(not panel.EditorControls.BadgeText)
assert(not panel.EditorControls.Preview.Value:find('[default]',1,true))
assert(not panel.EditorControls.Load.Options.Disabled)
assert(p:GetName()=='RealUser')
panel.MethodControl:Set('anonymous'); assert(not panel.EditCustom.Visible)
local premiumIcon=node('ImageLabel',facilityGui)
premiumIcon.Image='rbxasset://textures/ui/PlayerList/PremiumIcon.png'
local nativeBadge=label(facilityGui,utf8.char(0xE000))
panel.Controls.Enabled:Set(true)
assert(premiumIcon.Image=='rbxasset://textures/ui/PlayerList/PremiumIcon.png')
assert(nativeBadge.Text==utf8.char(0xE000))
local originalResolve, textResolutions=p.ResolveText,0
p.ResolveText=function(self,...) textResolutions=textResolutions+1; return originalResolve(self,...) end
p:SetOptions({HideAvatar=false}); p:SetOptions({HideAvatar=true})
assert(textResolutions==0,'avatar toggles must not refresh name text')
p.ResolveText=originalResolve
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
-- Custom identity: apply live fields, preserve independent scopes and appearance.
panel.EditorControls.Username:Set('Alias')
panel.EditorControls.DisplayName:Set('Custom Display')
panel.EditorControls.UserId:Set('987')
panel.EditorControls.Appearance:Set('keep mine')
panel.EditorControls.Actions[2].Callback()
assert(panel.EditorControls.Status.Value=='identity applied')
assert(p.Options.Method=='custom' and p:GetName()=='Alias' and p:GetDisplayName()=='Custom Display' and p:GetUserId()==987)
assert(facilityLabel.Text=='teleport to Alias' and gameLabel.Text=='Custom Display has joined')
assert(avatar.Image==bust and preview(avatar)==nil and ownFace(newBody)==nil)
assert(p:GetAvatar():find('id=123',1,true))
assert(LocalPlayer.Name=='RealUser' and LocalPlayer.UserId==123)
panel.EditorControls.Username:Set('unapplied'); assert(p:GetName()=='Alias')
panel.EditorControls.UserId:Set('-2'); panel.EditorControls.Actions[2].Callback()
assert(p:GetName()=='Alias' and p:GetUserId()==987 and panel.EditorControls.Status.Value~='identity applied')
assert(not pcall(function() p:SetCustom({Name='changed',UserId=0/0}) end))
assert(p:GetName()=='Alias')
assert(not pcall(function() p:SetCustom({Name='<b>markup</b>'}) end))
assert(not pcall(function() p:SetCustom({Appearance='loaded account'}) end))
assert(not pcall(function() p:SetMethod('random') end))
local customCopy=p:GetCustom(); customCopy.Name='external'; assert(p:GetName()=='Alias')
p:SetCustom({Name='A&B',Appearance='anonymous'})
assert(p:ResolveText('<b>RealUser</b>','facility',true)=='<b>A&amp;B</b>')
assert(p:ResolveText('RealUser','facility',false)=='A&B')
assert(avatar.Image=='' and ownFace(newBody))
p:SetOptions({HideUsername=false}); assert(p:GetName()=='RealUser' and p:GetDisplayName()=='Custom Display')
p:SetOptions({HideUsername=true,AffectFacility=false})
assert(facilityLabel.Text=='teleport to RealUser' and gameLabel.Text=='Custom Display has joined')
p:SetOptions({AffectFacility=true})
p:Restore(); assert(p:GetName()=='RealUser' and avatar.Image==bust)
p:SetOptions({Enabled=true}); assert(p:GetName()=='A&B')
p:SetMethod('anonymous'); assert(p:GetName()=='seized.cc/1' and p:GetUserId()==0)
assert(panel.MethodControl:Get()=='anonymous' and not panel.EditCustom.Visible)
-- Account loading is draft-only, and failures leave the active identity intact.
local identity=p:LoadAccount('@AccountUser')
assert(identity.Name=='AccountUser' and identity.UserId==456 and p:GetName()=='seized.cc/1')
assert(not pcall(function() p:LoadAccount('missing') end))
assert(p:GetName()=='seized.cc/1')
panel.EditorControls.Account:Set('456')
panel.EditorControls.Load.Options.Callback()
assert(panel.EditorControls.Username:Get()=='AccountUser')
assert(panel.EditorControls.Appearance:Get()=='loaded account')
panel.EditorControls.Username:Set('Override')
panel.EditorControls.Actions[2].Callback()
assert(panel.EditorControls.Status.Value=='identity applied' and p:GetName()=='Override')
assert(p:GetDisplayName()=='Account Display' and p:GetUserId()==456)
assert(avatar.Image:find('id=456',1,true) and p:GetAvatar():find('id=456',1,true))
local loadedVisual=LocalPlayer.Character.Parent:FindFirstChild('FacilityCustomAppearance')
assert(loadedVisual and not ownFace(newBody))
assert(not loadedVisual:IsDescendantOf(LocalPlayer.Character))
assert(loadedVisual.Parent==LocalPlayer.Character.Parent)
-- A collision state change on the visual is corrected on the next follow update.
loadedVisual:FindFirstChild('Head').CanCollide=true
RunService.RenderStepped:Fire()
assert(loadedVisual:FindFirstChild('Head').CanCollide==false)
local visualHumanoid=loadedVisual:FindFirstChildOfClass('Humanoid')
assert(visualHumanoid.EvaluateStateMachine==false and visualHumanoid.AutoRotate==false)
for _,part in ipairs(loadedVisual:GetDescendants()) do
 if part:IsA('BasePart') then
  assert(part.Anchored and part.CanCollide==false and part.CanTouch==false and part.CanQuery==false)
 end
end
-- The real humanoid is not altered by the visual rig's simulation settings.
assert(not loadedVisual:FindFirstChildOfClass('JointInstance') and not loadedVisual:FindFirstChildOfClass('Constraint'))
local actualHumanoid=LocalPlayer.Character:FindFirstChildOfClass('Humanoid')
if actualHumanoid then assert(actualHumanoid.EvaluateStateMachine~=false) end
assert(loadedVisual:FindFirstChild('Head').Color=='loaded skin')
-- Joint/attachment offsets work before generated handles assemble in Workspace.
newBody.CFrame=CFrame.new(10,20,30); RunService.RenderStepped:Fire()
for name,offset in pairs({Hair={0,0.5,-1,math.pi/2},ScaledHead={0,0.6,1,-math.pi/2},WithoutWeld={1,0.8,0,math.pi}}) do
 local acc=loadedVisual:FindFirstChild(name); local h=acc:FindFirstChild('Handle')
 assert(math.abs(h.CFrame.position[1]-(10+offset[1]))<1e-6)
 assert(math.abs(h.CFrame.position[2]-(20+offset[2]))<1e-6)
 assert(math.abs(h.CFrame.position[3]-(30+offset[3]))<1e-6)
 assert(math.abs(h.CFrame.angle-offset[4])<1e-6)
 assert(h:FindFirstChildOfClass('SpecialMesh').Scale.X==13)
 assert(not h:FindFirstChild('AccessoryWeld')) -- offsets captured before joint removal
end

p:SetCustom({UserId=999}) -- numeric text override does not change the selected account appearance
assert(p:GetUserId()==999 and p:GetAvatar():find('id=456',1,true))
p:Restore(); assert(loadedVisual.Parent==nil and avatar.Image==bust)
p:SetOptions({Enabled=true}); assert(LocalPlayer.Character.Parent:FindFirstChild('FacilityCustomAppearance'))
p:SetCustom({Appearance='keep mine'}); assert(not LocalPlayer.Character.Parent:FindFirstChild('FacilityCustomAppearance'))
p:SetMethod('anonymous'); assert(ownFace(newBody))
-- Random identities use the same reversible, isolated appearance path.
p:SetRandomOptions({MinUserId=456,MaxUserId=456})
p:SetMethod('randomised'); assert(p:GetRandomStatus()=='loading' and ownFace(newBody))
drainTasks()
assert(p:GetRandomStatus()=='ready' and p:GetName()=='AccountUser')
assert(avatar.Image:find('id=456',1,true) and not ownFace(newBody))
local randomVisual=LocalPlayer.Character.Parent:FindFirstChild('FacilityCustomAppearance')
assert(randomVisual and not randomVisual:IsDescendantOf(LocalPlayer.Character))
assert(randomVisual:FindFirstChildOfClass('Humanoid').EvaluateStateMachine==false)
assert(randomVisual:FindFirstChild('Head').CanCollide==false)
p:SetMethod('anonymous'); assert(ownFace(newBody) and randomVisual.Parent==nil)
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
p:SetCustom({AccountId=456,Appearance='loaded account'}); p:SetMethod('custom')
assert(copy.Parent:FindFirstChild('FacilityCustomAppearance') and copyTorso.Transparency==1 and copyHair.Transparency==1)
assert(copy.Parent:FindFirstChild('FacilityCustomAppearance'):FindFirstChildOfClass('Humanoid').EvaluateStateMachine==false)
assert(not copy.Parent:FindFirstChild('FacilityCustomAppearance'):IsDescendantOf(copy))
RunService.RenderStepped:Fire()
p:SetMethod('anonymous'); assert(not copy.Parent:FindFirstChild('FacilityCustomAppearance') and copyTorso.Transparency==0)

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
lua.execute(r"""
-- Default bounds include IDs above 32 bits. Invalid candidates retry asynchronously.
local p=factory(Library)
local panel=p:BuildPrivacySection(tab)
assert(table.find(panel.MethodControl.Options.Options,'randomised'))
assert(p:GetRandomStatus()=='idle')
for _,options in ipairs({{Attempts=0},{Attempts=21},{MinUserId=0},{MaxUserId=0/0},{MinUserId=200,MaxUserId=100},{Other=1}}) do
 assert(not pcall(function() p:SetRandomOptions(options) end))
end
validAccounts[11000000000]={Username='RandomUser',DisplayName='Random Display'}
randomDraws={0,1}; accountRequests={}
p:SetCustom({Name='Pending',DisplayName='Pending Display',Appearance='keep mine'})
p:SetOptions({Enabled=true,Method='custom'})
p:SetMethod('randomised')
assert(p:GetRandomStatus()=='loading' and p:GetName()=='Pending')
assert(panel.RandomStatus.Value=='loading random identity…' and #accountRequests==0)
p:SetMethod('anonymous'); p:SetMethod('randomised')
assert(#tasks==1) -- no duplicate work when switching methods mid-load
stepTasks(); assert(accountRequests[1]==120000000 and p:GetRandomStatus()=='loading')
drainTasks()
assert(accountRequests[2]==11000000000 and #accountRequests==2)
assert(p:GetRandomStatus()=='ready' and p:GetUserId()==11000000000)
assert(p:GetName()=='RandomUser' and p:GetCustom().Name=='Pending')
assert(panel.RandomStatus.Value=='random identity ready')
assert(p:GetAvatar():find('id=11000000000',1,true))
assert(p:ResolveImage('rbxthumb://type=AvatarHeadShot&id=123&w=150&h=150','facility'):find('id=11000000000',1,true))
p:SetOptions({HideUsername=false,HideDisplayName=false,HideUserIds=false,HideAvatar=false})
assert(p:GetName()=='RealUser' and p:GetUserId()==123 and p:GetAvatar():find('id=123',1,true))
p:SetOptions({HideUsername=true,HideDisplayName=true,HideUserIds=true,HideAvatar=true})
p:Restore(); p:SetOptions({Enabled=true}); p:SetMethod('custom'); p:SetMethod('randomised')
assert(#tasks==0 and #accountRequests==2 and p:GetName()=='RandomUser')
assert(not pcall(function() p:SetRandomOptions({Attempts=1}) end))
-- A newly joined real owner must never share the replacement identity.
local joined=node('Player'); joined.UserId=11000000000; joined.Name='RandomUser'; joined.DisplayName='Random Display'
serverPlayers={LocalPlayer,joined}; Players.PlayerAdded:Fire(joined)
assert(p:GetRandomStatus()=='fallback' and p:GetName()=='seized.cc/1')
assert(p:GetName(joined)=='RandomUser')
p:SetMethod('anonymous'); p:SetMethod('randomised'); assert(#tasks==0)
p:Destroy(); serverPlayers={LocalPlayer}

-- Reject local/current server IDs without issuing account requests, then accept a unique one.
p=factory(Library)
local other=node('Player'); other.UserId=124; other.Name='Other'; other.DisplayName='Other'
serverPlayers={LocalPlayer,other}
p:SetRandomOptions({MinUserId=123,MaxUserId=456,Attempts=4})
randomDraws={0,1.5/334,2.5/334,1}; accountRequests={}
p:SetOptions({Enabled=true,Method='randomised'}); drainTasks()
assert(#accountRequests==2 and accountRequests[1]==125 and accountRequests[2]==456)
assert(p:GetUserId()==456 and p:GetIdentity(other).UserId==124)
p:Destroy(); serverPlayers={LocalPlayer}

-- Bounded failure uses anonymous and does not restart when toggling or changing method.
p=factory(Library); accountRequests={}; randomDraws={0,0.25,0.5,0.75,1}
p:SetRandomOptions({MinUserId=900,MaxUserId=904})
p:SetOptions({Enabled=true,Method='randomised'}); drainTasks()
assert(#accountRequests==5 and p:GetRandomStatus()=='fallback' and p:GetName()=='seized.cc/1')
p:SetAnonymous({Prefix='player '}); assert(p:GetName()=='player 1')
p:Restore(); p:SetOptions({Enabled=true}); p:SetMethod('custom'); p:SetMethod('randomised')
assert(#tasks==0 and #accountRequests==5)
p:Destroy()

-- Switching away before completion caches the result without applying it.
p=factory(Library); yieldLookup=true; accountRequests={}
p:SetRandomOptions({MinUserId=456,MaxUserId=456,Attempts=1})
p:SetOptions({Enabled=true,Method='randomised'}); stepTasks()
p:SetCustom({Name='KeepCustom'}); p:SetMethod('custom')
drainTasks(); yieldLookup=false
assert(p:GetRandomStatus()=='ready' and p:GetName()=='KeepCustom')
p:SetMethod('randomised'); assert(p:GetName()=='AccountUser' and #accountRequests==1)
p:Destroy()

-- Server membership is checked again after a yielding lookup.
p=factory(Library); yieldLookup=true
p:SetRandomOptions({MinUserId=456,MaxUserId=456,Attempts=1})
p:SetOptions({Enabled=true,Method='randomised'}); stepTasks()
other.UserId=456; serverPlayers={LocalPlayer,other}
drainTasks(); yieldLookup=false
assert(p:GetRandomStatus()=='fallback' and p:GetUserId()==0)
p:Destroy(); serverPlayers={LocalPlayer}

-- Concurrent custom loading does not consume the random attempt or overwrite the draft.
p=factory(Library); yieldLookup=true; accountRequests={}
local customResult
task.defer(function() customResult=p:LoadAccount('456') end)
stepTasks() -- custom lookup owns the loader while yielded
p:SetRandomOptions({MinUserId=11000000000,MaxUserId=11000000000,Attempts=1})
p:SetOptions({Enabled=true,Method='randomised'})
drainTasks(); yieldLookup=false
assert(customResult.UserId==456 and p:GetUserId()==11000000000)
assert(#accountRequests==2 and p:GetCustom().Name=='seized')
p:Destroy()

-- A failed appearance load also falls back; unload during lookup discards its work.
p=factory(Library); appearanceFailure=true
p:SetRandomOptions({MinUserId=456,MaxUserId=456,Attempts=1})
p:SetOptions({Enabled=true,Method='randomised'}); drainTasks()
assert(p:GetRandomStatus()=='fallback'); appearanceFailure=false; p:Destroy()
p=factory(Library); yieldLookup=true; createdRigs={}
p:SetRandomOptions({MinUserId=456,MaxUserId=456,Attempts=1})
p:SetOptions({Enabled=true,Method='randomised'}); stepTasks(); p:Destroy(); drainTasks(); yieldLookup=false
assert(Library.PrivacyManager==nil and #tasks==0 and #createdRigs==0)
for _,rig in ipairs(createdRigs) do assert(rig.Parent==nil) end
""")

lua.execute(r"""
-- Other players have independent options and session-stable anonymous assignments.
local function makeRig(name,parent)
 local model=node('Model',parent or workspace); model.Name=name
 local humanoid=node('Humanoid',model); humanoid.RigType=Enum.HumanoidRigType.R15
 local head=node('Part',model); head.Name='Head'; head.Color='original player skin'; head.CanCollide=true
 local torso=node('Part',model); torso.Name='UpperTorso'; torso.Color='original player torso'
 local shirt=node('Shirt',model); shirt.ShirtTemplate='original player shirt'
 local hat=node('Accessory',model); local hair=node('Part',hat); hair.Name='Handle'
 hair.LocalTransparencyModifier=0; hair.CanCollide=false
 return model,head,hair,shirt
end
local function makePlayer(id,name,display)
 local player=node('Player'); player.UserId=id; player.Name=name; player.DisplayName=display
 local model,head,hair,shirt=makeRig(name)
 player.Character=model
 return player,head,hair,shirt
end
local function proxy(model) return model:FindFirstChild('FacilityAnonymousHead') end
local alice,aliceHead,aliceHair,aliceShirt=makePlayer(1011,'Alice','Shared')
local bob,bobHead,bobHair=makePlayer(1012,'Bob','Shared')
serverPlayers={LocalPlayer,alice,bob}
local p=factory(Library)
local panel=p:BuildPrivacySection(tab,1,{GearMaxHeight=150})
local second=p:BuildPrivacySection(tab,2)
assert(panel.PlayerControls.Enabled.GearOptions.MaxHeight==150)
assert(panel.PlayerMethodControl.Options.Disabled and panel.PlayerMethodControl:Get()=='anonymous')
assert(not p.PlayerOptions.Enabled and not p.Options.Enabled)
assert(p:GetAnonymousIdentity(alice).Name=='seized.cc/2' and p:GetAnonymousIdentity(bob).Name=='seized.cc/3')
local text=label(facilityGui,'teleport to Alice | Bob | RealUser')
local display=label(facilityGui,'Shared')
local gameText=label(playerGui,'Alice and Bob')
local billboard=node('BillboardGui',alice.Character); local nameTag=label(billboard,'Alice')
local picture=node('ImageLabel',facilityGui); local thumb='rbxthumb://type=AvatarHeadShot&id=1011&w=150&h=150'
picture.Image=thumb
local gamePicture=node('ImageLabel',playerGui); gamePicture.Image=thumb
local unknownPicture=node('ImageLabel',facilityGui); unknownPicture.Image='rbxthumb://type=AvatarHeadShot&id=999999&w=150&h=150'
local input=node('TextBox',facilityGui,'Alice')
local selectedPlayer=alice
local button=node('TextButton',facilityGui,'Alice')
local requestCount=#accountRequests
panel.PlayerControls.Enabled:Set(true)
assert(second.PlayerControls.Enabled.Value==true)
assert(text.Text=='teleport to seized.cc/2 | seized.cc/3 | RealUser')
assert(display.Text=='player') -- ambiguous shared display names get a generic replacement
assert(gameText.Text=='Alice and Bob' and gamePicture.Image==thumb)
assert(picture.Image=='' and picture:FindFirstChildOfClass('ViewportFrame'))
assert(unknownPicture.Image:find('id=999999',1,true))
assert(button.Text=='seized.cc/2' and selectedPlayer==alice and input.Text=='Alice')
assert(p:GetIdentity(alice).UserId==0 and alice.UserId==1011 and alice.Name=='Alice')
assert(p:GetName()=='RealUser' and p:GetAvatar(alice)=='rbxassetid://144080495')
assert(not proxy(alice.Character) and not proxy(LocalPlayer.Character))
assert(p:ResolveText('AliceX Alice 10110 1011')=='AliceX seized.cc/2 10110 0')
assert(p:ResolveText('<font color="#1011">Alice</font>','facility',true)=='<font color="#1011">seized.cc/2</font>')
assert(not pcall(function() p:SetPlayerOptions({Enabled=false,Method='custom'}) end))
assert(p.PlayerOptions.Enabled)
assert(not pcall(function() p:SetPlayerOptions({Bad=true}) end))
p:SetOptions({Enabled=true}); assert(text.Text=='teleport to seized.cc/2 | seized.cc/3 | seized.cc/1')
p:SetCustom({Name='Bob',DisplayName='LocalAlias'}); p:SetMethod('custom')
assert(p:ResolveText('RealUser Bob')=='Bob seized.cc/3') -- replacements are not recursively reprocessed
p:SetOptions({Enabled=false}); assert(p:GetName()=='RealUser' and p:GetName(bob)=='seized.cc/3')
p:SetPlayerOptions({HideUsername=false,HideDisplayName=false,HideUserIds=false})
assert(text.Text=='teleport to Alice | Bob | RealUser' and display.Text=='Shared')
assert(p:GetName(alice)=='Alice' and p:GetUserId(alice)==1011)
p:SetPlayerOptions({HideUsername=true,HideDisplayName=true,HideUserIds=true,AffectGame=true})
assert(gameText.Text=='seized.cc/2 and seized.cc/3' and nameTag.Text=='seized.cc/2')
assert(gamePicture.Image=='' and proxy(alice.Character) and proxy(bob.Character))
assert(aliceHead.Transparency==1 and aliceHair.LocalTransparencyModifier==1 and aliceShirt.ShirtTemplate=='')
assert(aliceHead.CanCollide==true and not proxy(LocalPlayer.Character))
-- Preview ownership follows current players and restores on owner/scope changes.
local viewport=node('ViewportFrame',playerGui)
local aliceCopy,copyHead,copyHair=makeRig('AnonymousPreview',viewport); aliceCopy:SetAttribute('UserId',1011)
assert(proxy(aliceCopy) and copyHead.Transparency==1 and copyHair.Transparency==1)
aliceCopy:SetAttribute('UserId',LocalPlayer.UserId)
assert(not proxy(aliceCopy) and copyHead.Transparency==0)
aliceCopy:SetAttribute('UserId',1011); assert(proxy(aliceCopy))
local unknown,unknownHead=makeRig('Shared',viewport); assert(not proxy(unknown))
local unregister=p:RegisterPreview(unknown,bob); assert(proxy(unknown))
unregister(); assert(not proxy(unknown) and unknownHead.Transparency==0)
local byName=makeRig('Bob',viewport); assert(proxy(byName))
local byId=makeRig('1012',viewport); assert(proxy(byId))
-- No account requests; hide-avatar alone skips text work and restores geometry/images.
local resolve,resolveCount=p.ResolveText,0
p.ResolveText=function(self,...) resolveCount=resolveCount+1; return resolve(self,...) end
p:SetPlayerOptions({HideAvatar=false})
assert(resolveCount==0 and not proxy(alice.Character) and not proxy(aliceCopy))
assert(aliceHair.LocalTransparencyModifier==0 and aliceShirt.ShirtTemplate=='original player shirt')
assert(picture.Image==thumb and gameText.Text=='seized.cc/2 and seized.cc/3')
p.ResolveText=resolve
p:SetPlayerOptions({HideAvatar=true,AffectFacility=false})
assert(text.Text=='teleport to Alice | Bob | RealUser' and picture.Image==thumb)
assert(gameText.Text=='seized.cc/2 and seized.cc/3' and proxy(alice.Character))
p:SetPlayerOptions({AffectFacility=true})
alice.DisplayName='Alice Display'
local changed=label(playerGui,'Alice Display'); assert(changed.Text=='seized.cc/2')
local charlie,charlieHead=makePlayer(1013,'Charlie','Charlie Display')
serverPlayers={LocalPlayer,alice,bob,charlie}; Players.PlayerAdded:Fire(charlie)
assert(p:GetName(charlie)=='seized.cc/4' and proxy(charlie.Character))
local charlieLabel=label(facilityGui,'Charlie'); assert(charlieLabel.Text=='seized.cc/4')
-- Leave restores the old character and previews, while historical text retains its alias.
Players.PlayerRemoving:Fire(alice); serverPlayers={LocalPlayer,bob,charlie}
assert(not proxy(alice.Character) and aliceHead.Transparency==0 and aliceHair.LocalTransparencyModifier==0)
assert(not proxy(aliceCopy) and copyHair.Transparency==0)
assert(p:ResolveText('Alice')=='seized.cc/2')
local oldCharacter=alice.Character
local aliceAgain,newHead,newHair=makePlayer(1011,'Alice','Alice Display')
serverPlayers={LocalPlayer,bob,charlie,aliceAgain}; Players.PlayerAdded:Fire(aliceAgain)
assert(p:GetName(aliceAgain)=='seized.cc/2' and proxy(aliceAgain.Character) and proxy(aliceCopy))
assert(not proxy(oldCharacter))
local previous=aliceAgain.Character
aliceAgain.CharacterRemoving:Fire(previous)
assert(not proxy(previous) and newHair.LocalTransparencyModifier==0)
local replacement,replacementHead,replacementHair=makeRig('Alice')
aliceAgain.Character=replacement; aliceAgain.CharacterAdded:Fire(replacement)
assert(proxy(replacement) and replacementHair.LocalTransparencyModifier==1)
assert(not proxy(previous) and aliceAgain.UserId==1011 and aliceAgain.Character==replacement)
p:SetAnonymous({Prefix='player '}); assert(p:GetName(aliceAgain)=='player 2' and p:GetName(charlie)=='player 4')
p:Restore()
assert(not p.Options.Enabled and not p.PlayerOptions.Enabled)
assert(text.Text=='teleport to Alice | Bob | RealUser' and gameText.Text=='Alice and Bob')
assert(not proxy(replacement) and not proxy(bob.Character) and picture.Image==thumb)
p:SetPlayerOptions({Enabled=true}); assert(p:GetName(aliceAgain)=='player 2')
p:Destroy()
assert(not proxy(replacement) and not proxy(bob.Character) and not proxy(charlie.Character))
assert(not proxy(aliceCopy) and not proxy(byName) and not proxy(byId))
assert(gameText.Text=='Alice and Bob' and picture.Image==thumb)
assert(replacementHead.Color=='original player skin' and replacementHair.LocalTransparencyModifier==0)
assert(#accountRequests==requestCount)
assert(aliceAgain.Name=='Alice' and aliceAgain.Character==replacement and selectedPlayer==alice)
local later=makeRig('Alice'); aliceAgain.CharacterAdded:Fire(later); assert(not proxy(later))
serverPlayers={LocalPlayer}
""")

print("PASS: per-player anonymous mapping/scopes/joins/rejoins/previews/restoration, random discovery/cache/fallback/lifecycle, identity toggles, scope separation, new/live UI, literal boundaries, RichText, character appearance/respawns, restoration and cleanup")
