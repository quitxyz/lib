"""Home addon integration checks with simulated Roblox services/tasks (requires lupa)."""
from pathlib import Path
from lupa.lua54 import LuaRuntime

root = Path(__file__).resolve().parents[1]
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
table.clear=function(t) for k in pairs(t) do t[k]=nil end end
table.find=function(t,v) for i,x in ipairs(t) do if x==v then return i end end end
function signal()
 local s={listeners={}}
 function s:Connect(f) local c={Connected=true,f=f}; function c:Disconnect() self.Connected=false end; self.listeners[#self.listeners+1]=c; return c end
 function s:Fire(...) for _,c in ipairs(self.listeners) do if c.Connected then c.f(...) end end end
 return s
end
nodes={}
function node(parent)
 local n={Parent=parent,Destroying=signal()}; nodes[#nodes+1]=n
 function n:Destroy()
  if self.dead then return end; self.dead=true; self.Destroying:Fire()
  for _,child in ipairs(nodes) do if child.Parent==self then child:Destroy() end end
  self.Parent=nil
 end
 return n
end
tasks={}
task={defer=function(f) local t=coroutine.create(f); tasks[#tasks+1]=t; return t end,
 wait=function() coroutine.yield() end, cancel=function(t) assert(coroutine.close(t)) end}
function step() for _,t in ipairs(tasks) do if coroutine.status(t)=='suspended' then local ok,e=coroutine.resume(t); assert(ok,e) end end end
function running() local n=0; for _,t in ipairs(tasks) do if coroutine.status(t)~='dead' then n=n+1 end end; return n end
localPlayer={UserId=1,Name='user',DisplayName='User',GetNetworkPing=function() return .05 end,
 IsFriendsWithAsync=function(_,id) if yieldingFriend then coroutine.yield() end; return id==2 end}
Players={LocalPlayer=localPlayer,MaxPlayers=50}
local friend={UserId=2,Parent=Players}; local stranger={UserId=3,Parent=Players}
Players.GetPlayers=function() return {localPlayer,friend,stranger} end
RunService={RenderStepped=signal()}; requests=0
MarketplaceService={GetProductInfoAsync=function() requests=requests+1; if yieldingDetails then coroutine.yield() end; return {Name='Game',Creator={Name='Creator'}} end}
TeleportService={TeleportToPlaceInstance=function(_,place,job) teleported=job end}
HttpService={JSONDecode=function() return {data={{id='current',playing=1,maxPlayers=50},{id='other',playing=2,maxPlayers=50},{id='full',playing=50,maxPlayers=50}}} end}
local services={Players=Players,RunService=RunService,MarketplaceService=MarketplaceService,TeleportService=TeleportService,HttpService=HttpService}
game={PlaceId=10,GameId=20,PlaceVersion=3,JobId='current',GetService=function(_,name) return services[name] end,HttpGet=function() return '{}' end}
setclipboard=function(value) clipboard=value end
identifyexecutor=function() return 'Executor' end
warnings={}; warn=function(message) warnings[#warnings+1]=message end
Library={SafeCallback=function(_,_,f,...) if f then f(...) end end}
function text(value) local t={Instance={Text=value or ''}}; function t:SetText(v) self.Instance.Text=tostring(v) end; return t end
function card(owner,opts)
 local c={Instance=node(owner.Instance),Alive=true,Options=opts,Title=text(opts.Title),Subtitle=text(opts.Subtitle)}
 c.Instance.Destroying:Connect(function() c.Alive=false end)
 function c:SetTitle(v) self.Title:SetText(v) end
 function c:SetSubtitle(v) self.Subtitle:SetText(v) end
 function c:SetVisible(v) self.Visible=v end
 function c:SetOrder(v) self.Order=v end
 function c:Destroy() self.Instance:Destroy() end
 return c
end
function container(parent,window)
 local c={Instance=node(parent),Window=window}
 c.ProfileCard=card; c.MediaCard=card; c.StatusCard=card
 function c:StatGrid(opts)
  local g=card(self,opts); g.Items={}
  for _,item in ipairs(opts.Items) do g.Items[item.Id]={Value=item.Value} end
  function g:Set(id,value) assert(self.Alive); self.Items[id].Value=value end
  return g
 end
 return c
end
window={tabs={}}
function window:Tab(title,icon)
 local t={Alive=true,Page=node(),Window=self,Title=title}
 function t:Cards() return container(self.Page,self.Window) end
 function t:Destroy() if not self.Alive then return end; self.Alive=false; self.Page:Destroy() end
 self.tabs[#self.tabs+1]=t; return t
end
''')
manager = lua.execute((root / 'addons/HomeManager.luau').read_text())(lua.globals().Library)
lua.globals().HomeManager = manager
lua.execute('''
local home=HomeManager:Create(window,{RunsValue=7,Profile={Badge={Text='premium'}}})
assert(home.Profile.Options.Badge.Width==100 and home.Profile.Options.Badge.Text=='premium')
assert(home.Executor.Options.Title=='Executor' and home.Executor.Options.Description=='')
step(); assert(requests==1 and home.Game.Title.Instance.Text=='Game')
assert(home.Stats.Items.players.Value=='3/50' and home.Stats.Items.friends.Value=='1' and home.Stats.Items.ping.Value=='50ms')
assert(home.Stats.Items.runs.Value==7)
RunService.RenderStepped:Fire(.25); RunService.RenderStepped:Fire(.25); assert(home.Stats.Items.fps.Value==4)
for _,a in ipairs(home.Game.Options.Actions) do if a.Id=='lowest' then a.Callback() end end
assert(teleported=='other')
for _,a in ipairs(home.Game.Options.Actions) do if a.Id=='copyJob' then a.Callback() end end
assert(clipboard=='current')
home.Stats:Destroy(); assert(running()==0)
home:Destroy(); assert(not home.Alive and not home.Tab.Alive)
for _,c in ipairs(RunService.RenderStepped.listeners) do assert(not c.Connected) end
local parent=window:Tab('existing'); local second=HomeManager:Create(parent,{Profile=false,Game=false,Executor=false,Stats={Items={{Id='custom',Label='custom',Value=0,Getter=function() return 42 end}}}})
step(); assert(second.Stats.Items.custom.Value=='42' and not second.Profile)
second:Destroy(); assert(parent.Alive and running()==0)
yieldingFriend=true; yieldingDetails=true
local third=HomeManager:Create(parent,{Order={'Game','Profile'}})
step(); assert(third.Game.Order==1 and third.Profile.Order==2)
third:Destroy(); assert(running()==0)
yieldingFriend=false; yieldingDetails=false
local custom=HomeManager:Create(parent,{Stats=false,Executor=false,Game={Title='custom',Subtitle='custom',Actions={}},Profile={Badge=false}})
local before=requests; step(); assert(requests==before and #custom.Game.Options.Actions==0 and custom.Profile.Options.Badge==false)
custom:Destroy()
local ok=pcall(function() HomeManager:Create(window,{Intervals={ping=0}}) end)
assert(not ok and not window.tabs[#window.tabs].Alive and running()==0)
local a=HomeManager:Create(parent,{RunsValue=7,Game=false}); local b=HomeManager:Create(parent,{RunsValue=7,Game=false})
assert(a.Stats.Items.runs.Value==7 and b.Stats.Items.runs.Value==7)
parent:Destroy(); assert(not a.Alive and not b.Alive and running()==0)
''')
print('PASS: Home defaults, live stats, one details fetch, actions, options, existing-tab ownership, task cancellation, failed builds and multiple instances')
