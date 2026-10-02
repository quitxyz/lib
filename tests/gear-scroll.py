"""Exercise the actual floating-panel builder with mocked Roblox geometry/signals."""
from pathlib import Path
from lupa.lua54 import LuaRuntime
root = Path(__file__).resolve().parents[1]
source = (root / 'main.luau').read_text()
start = source.index('function Window:CreateFloating(')
end = source.index('\nfunction Window:CloseFloatingFrom', start)
lua = LuaRuntime()
lua.execute(r'''
Enum={AutomaticSize={Y='Y',None='None'},ScrollingDirection={Y='Y'}}
UDim2={new=function(xs,xo,ys,yo) return {X={Scale=xs or 0,Offset=xo or 0},Y={Scale=ys or 0,Offset=yo or 0}} end}
function UDim2.fromOffset(x,y) return UDim2.new(0,x,0,y) end
function signal()
 local s={listeners={}}
 function s:Connect(f) table.insert(self.listeners,f); return {Disconnect=function() end} end
 function s:Fire() for _,f in ipairs(self.listeners) do f() end end
 return s
end
function New(class,props)
 local n=props; n.ClassName=class; n.AbsoluteSize={Y=0}; n.signals={}
 function n:GetPropertyChangedSignal(p) self.signals[p]=self.signals[p] or signal(); return self.signals[p] end
 return n
end
Corner=function() end; Stroke=function() end; Pad=function() end; List=function() end; Track=function(c) return c end
Theme={PopupBg='bg',Accent='accent',PopupBorder='border',AccentDim='scroll'}
Library={hooks={}}; function Library:OnRepaint(f) table.insert(self.hooks,f) end
Window={Overlay={}}; Window.Scale=New('UIScale',{Scale=1})
''')
lua.execute(source[start:end])
lua.execute(r'''
local legacy=Window:CreateFloating(190,false,nil)
assert(legacy.Scroller==nil and legacy.Frame.AutomaticSize=='Y')
local p=Window:CreateFloating(190,false,nil,{MaxHeight=160})
assert(p.Scroller.ClassName=='ScrollingFrame')
assert(p.Scroller.ScrollingDirection=='Y' and p.Scroller.AutomaticCanvasSize=='Y')
p.Content.AbsoluteSize.Y=80; p.Content.signals.AbsoluteSize:Fire()
assert(p.Frame.Size.Y.Offset==92 and not p.Scroller.ScrollingEnabled)
p.Content.AbsoluteSize.Y=300; p.Content.signals.AbsoluteSize:Fire()
assert(p.Frame.Size.Y.Offset==160 and p.Scroller.Size.Y.Offset==148 and p.Scroller.ScrollingEnabled)
-- Changing user/DPI scale does not change the logical cap.
Window.Scale.Scale=2; p.Content.AbsoluteSize.Y=600; Window.Scale.signals.Scale:Fire()
assert(p.Frame.Size.Y.Offset==160)
p.Content.AbsoluteSize.Y=100; p.OnOpen()
assert(p.Frame.Size.Y.Offset==62 and not p.Scroller.ScrollingEnabled)
Theme.AccentDim='new color'; for _,hook in ipairs(Library.hooks) do hook() end
assert(p.Scroller.ScrollBarImageColor3=='new color')
local tiny=Window:CreateFloating(190,false,nil,{MaxHeight=10})
tiny.Content.AbsoluteSize.Y=100; tiny.OnOpen(); assert(tiny.Frame.Size.Y.Offset==32)
''')
print('PASS: optional gear cap, natural sizing, overflow scrolling, scale changes, theme refresh')
