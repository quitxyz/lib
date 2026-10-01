"""Config preset behavior with real storage/serialization and mocked UI (lupa)."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
# Reuse the UI/runtime fixture, without running console-specific tests.
fixture = (root/'tests/console-manager.py').read_text().split("addon=")[0]
exec(fixture.replace("local function control(", "function control("))
def plain(value):
    if hasattr(value, 'items'):
        return {key: plain(item) for key, item in value.items()}
    return value
lua.globals().encode = lambda value: json.dumps(plain(value))
lua.globals().decode = lambda value: lua.table_from(json.loads(value), recursive=True)
lua.execute(r"""
UDim2.fromOffset=UDim2.new
function HttpService:JSONEncode(v) return encode(v) end
function HttpService:JSONDecode(v) return decode(v) end
function string.split(s,delimiter)
 local result={}; for v in (s..delimiter):gmatch('(.-)'..delimiter) do table.insert(result,v) end; return result
end
task.spawn=function(f,...) f(...) end
Library.Registry={}; Library.Flags={}; Library.Defaults={}; Library.Windows={Window}
function Library:SafeCallback(_,f,...) return f(...) end
local originalContent=content
function content(parent,window)
 local c=originalContent(parent,window)
 function c:Input(o)
  local api=control(self,o); api.Value=o.Default or ''; api.Box=new('TextBox')
  api.Box.Parent=api.Instance
  function api:Get() return self.Value end
  return api
 end
 function c:Dropdown(o)
  local api=control(self,o,true)
  function api:Get() return self.Value end
  function api:SetOptions(options) self.Options.Options=options end
  return api
 end
 function c:Label(value)
  local api=control(self,{Default=value})
  function api:SetColor(value) self.Color=value end
  return api
 end
 function c:Divider() end
 return c
end
function Window:Confirm(o) self.confirm=o end
tab={Window=Window}
function tab:Section()
 local frame=new('Frame')
 local c=content(frame,Window); c.Frame=frame; return c
end
""")
main=(root/'main.luau').read_text()
lua.execute(main[main.index('function Library:OnDirtyChanged'):main.index('function Library:CaptureDefaults')])
fs=main[main.index('local FileSystem = {}'):main.index('Library.FileSystem = FileSystem')]
lua.execute(fs+'\nLibrary.FileSystem=FileSystem')
lua.globals().manager=lua.execute((root/'addons/SaveManager.luau').read_text())(lua.globals().Library)
lua.execute(r"""
local fs=Library.FileSystem
fs.Native=false
local enabled=false
Library.Registry.feature={Type='Toggle',Get=function() return enabled end,Set=function(v) enabled=v; Library:MarkDirty('feature') end}
Library.Registry.theme={Type='Input',Get=function() return 'pink' end,Set=function() error('theme must not load') end}
Library.ThemeManager={Flags={'theme'}}
local originalDirtyCalls=0
Library.OnDirty=function() originalDirtyCalls=originalDirtyCalls+1 end
local p=manager:Create(tab,{ConfigFolder='seized/configs/game1',Autoload=false})
local function click(key) p.Controls[key].Options.Callback() end
p.Controls.Name:Set('one'); click('Create')
assert(#manager:List()==1 and fs:Read(manager:Path('one.json')))
assert(not fs:Read(manager:Path('one.json')):find('theme'))
Library.Registry.feature.Set(true)
assert(p.Controls.Dirty.Value=='unsaved changes' and originalDirtyCalls>0)
click('Load'); assert(not enabled and p.Controls.Dirty.Value=='no unsaved changes')
Library.Registry.feature.Set(true); click('Save')
Library.Registry.feature.Set(false); click('Load'); assert(enabled)
click('Create'); assert(#manager:List()==1 and p.Controls.Status.Value:find('already exists'))
click('Copy'); assert(clipboard:find('feature') and clipboard:find('\n'))
p.Controls.Name:Set('shared'); click('Import')
assert(p.ImportModal.Open)
p.JsonInput:Set('{"feature":false,"theme":"bad","unknown":1}')
p.Controls.ImportConfirm.Options.Callback()
assert(not p.ImportModal.Open and enabled) -- import doesn't apply
click('Load'); assert(not enabled)
p.Controls.Autoload:Set('one.json'); click('SetAutoload')
assert(manager:GetAutoload()=='one.json')
local q=manager:Create(tab,{Controls={Sharing=false,Delete=false},Autoload=true})
assert(enabled and q.Controls.Copy==nil and q.Controls.Delete==nil)
Library.Registry.feature.Set(false)
assert(p.Controls.Dirty.Value=='unsaved changes' and q.Controls.Dirty.Value=='unsaved changes')
q:Destroy()
click('Load'); assert(not enabled) -- selected shared
local ok=manager:Import('bad','{"feature":"not a boolean"}'); assert(not ok)
assert(not manager:Import('../bad','{}'))
assert(manager:Import('empty','{}'))
assert(manager:Load('empty')) -- no game controls is valid
assert(not manager:Import('empty','{}')) -- never overwrite on import
p.Controls.Saved:Set('one.json'); click('Delete')
assert(manager:GetAutoload()=='one.json')
Window.confirm.OnConfirm()
assert(manager:GetAutoload()==nil and not table.find(manager:List(),'one.json'))
local old=Library.OnDirty
p:Destroy()
assert(Library.OnDirty==old and next(Library.DirtyListeners)==nil)
Library:MarkDirty('feature')
""")
print('PASS: create/overwrite/load/delete, shared JSON validation, import without apply, autoload, optional controls, dirty subscriptions and cleanup')
