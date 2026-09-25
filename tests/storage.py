"""Exercise storage/config logic with Lua 5.4 and simulated executor IO.

Run: python tests/storage.py (requires lupa). Does not emulate Roblox UI.
"""
import json
from pathlib import Path
from lupa.lua54 import LuaRuntime

root = Path(__file__).resolve().parents[1]
lua = LuaRuntime(unpack_returned_tuples=True)

def plain(value):
    if hasattr(value, 'items'):
        return {key: plain(item) for key, item in value.items()}
    return value

lua.globals().encode = lambda value: json.dumps(plain(value))
lua.globals().decode = lambda value: lua.table_from(json.loads(value), recursive=True)
lua.execute('''
typeof = type
table.clear = function(t) for k in pairs(t) do t[k] = nil end end
table.find = function(t, v) for i, x in ipairs(t) do if x == v then return i end end end
string.split = function(s, delimiter)
    local out = {}
    for part in (s .. delimiter):gmatch('(.-)' .. delimiter) do out[#out + 1] = part end
    return out
end
game = {GetService = function() return {JSONEncode = function(_, t) return encode(t) end,
    JSONDecode = function(_, s) return decode(s) end} end}
Library = {Registry = {}, Theme = {}, ClearDirty = function(self) self.Dirty = false end}
''')
main = (root / 'main.luau').read_text()
lua.execute(main[main.index('function Library:GetConfig'):main.index('function Library:CaptureDefaults')])
filesystem = main[main.index('local FileSystem = {}'):main.index('Library.FileSystem = FileSystem')]
lua.execute(filesystem + '\nLibrary.FileSystem = FileSystem')
factory = lua.execute((root / 'addons/SaveManager.luau').read_text())
lua.globals().manager = factory(lua.globals().Library)
lua.execute('''
local fs = Library.FileSystem
assert(manager:SetConfigFolder('seized/configs/game1'))
assert(manager:Path('one.json') == 'seized/configs/game1/one.json')
assert(manager:AutoloadPath() == 'seized/configs/game1/autoload.txt')
local scale, enabled = 100, true
Library.Registry.scale = {Get = function() return scale end, Set = function(v) scale = v end}
Library.Registry.enabled = {Get = function() return enabled end, Set = function(v) enabled = v end}
local ok, file, storage = manager:Save('one')
assert(ok and file == 'one.json' and storage == 'memory')
scale, enabled = 80, false
assert(manager:Load('one'))
assert(scale == 100 and enabled)
Library.Registry.newFlag = {Get = function() return 'automatically saved' end, Set = function() end}
assert(manager:Save('two'))
local shared = fs:Read(manager:Path('two.json'))
assert(decode(shared).newFlag == 'automatically saved')
assert(manager:SetAutoload('one'))
assert(#manager:List() == 2) -- excludes autoload.txt
assert(not manager:Save('../outside'))
assert(not manager:Delete('../outside'))
assert(not manager:SetAutoload('missing'))
assert(manager:Delete('one'))
assert(manager:GetAutoload() == nil)
assert(manager:SetSettingsFolder('seized/settings/game1'))
assert(manager:AutoloadPath() == 'seized/settings/game1/autoload.txt')
fs:Write(manager:Path('bad.json'), '42')
assert(not manager:Load('bad'))
Library.Registry.broken = {Get = function() return 1 end, Set = function() error('setter failed') end}
assert(manager:Save('broken'))
assert(not manager:Load('broken'))
Library.Registry.broken = nil
assert(manager:SetFolder('legacy'))
assert(manager:Path('one.json') == 'legacy/configs/one.json')
assert(manager:AutoloadPath() == 'legacy/settings/autoload.txt')

local files, folders = {}, {}
fs.Native = true
isfile = function(path) return files[path] ~= nil end
readfile = function(path) return assert(files[path]) end
writefile = function(path, value) files[path] = value end
delfile = function(path) files[path] = nil end
isfolder = function(path) return folders[path] == true end
makefolder = function(path) folders[path] = true end
listfiles = function(path)
    local result = {}
    for key in pairs(files) do if key:sub(1, #path + 1) == path .. '/' then result[#result + 1] = key end end
    return result
end
assert(manager:SetConfigFolder('seized/configs/game2'))
local saved, _, mode = manager:Save('disk')
assert(saved and mode == 'disk')
Library.Dirty = true
writefile = function() error('disk full') end
assert(not manager:Save('failure'))
assert(Library.Dirty and fs.Memory[manager:Path('failure.json')] == nil)
assert(not manager:SetAutoload('disk'))
delfile = function() error('denied') end
assert(not manager:Delete('disk'))
delfile = function() end -- no-op must not count as a deletion
assert(not manager:Delete('disk'))
isfile = nil
assert(not manager:Delete('disk'))
assert(fs:Read(manager:Path('disk.json')) == nil)
assert(not fs:EnsureFolder('../outside'))
assert(not fs:EnsureFolder('/outside'))
''')
lua.execute('''
Color3 = {fromRGB = function(r, g, b) return {R = r / 255, G = g / 255, B = b / 255} end}
math.clamp = function(v, low, high) return math.max(low, math.min(high, v)) end
''')
theme_factory = lua.execute((root / 'addons/ThemeManager.luau').read_text())
lua.globals().themeManager = theme_factory(lua.globals().Library)
lua.execute('''
Library.FileSystem.Native = false
assert(themeManager:SetSettingsFolder('seized/settings'))
assert(themeManager:Path() == 'seized/settings/theme.json')
for _, entry in ipairs(themeManager.Keys) do Library.Theme[entry[1]] = Color3.fromRGB(10, 20, 30) end
local ok, storage = themeManager:Save()
assert(ok and storage == 'memory')
Library.FileSystem.Native = true
assert(not themeManager:Save()) -- simulated writefile failure is propagated
''')
print('PASS: paths, automatic flags, memory/disk saves, load, autoload, theme storage, deletion and IO failures')
