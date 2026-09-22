# Text and paragraphs

## Label

```lua
section:Label("no groups found.")
section:Label("all systems nominal.", { Style = "success", Icon = "check" })
section:Label("raw value", Color3.fromRGB(200, 200, 200))
```

| Option | Default | Description |
| --- | --- | --- |
| `Style` | `nil` | see the style list |
| `Color` | `TextDim` | explicit color, takes priority over `Style` |
| `Icon` | `nil` | Lucide name, numeric asset id or `rbxassetid://` |
| `TextSize` | `13` | size |
| `Font` | `Gotham` | font |

Text wraps automatically and the height follows the content.

```lua
local label = section:Label("loading…")
label:Set("done")
label:SetStyle("success")
label:SetColor(Color3.fromRGB(255, 0, 0))
```

## Paragraph

A framed card with a title, an icon and a body: useful for explanations and warnings.

```lua
section:Paragraph({
    Title = "careful",
    Content = "Changing this setting restarts the main loop.",
    Style = "warning",
    Icon = "alert-triangle",
})
```

| Option | Default | Description |
| --- | --- | --- |
| `Title` | `""` | title, colored by the style |
| `Content` | `nil` | body text |
| `Style` | `nil` | tints the title, the icon and the outline |
| `Icon` | `nil` | icon in front of the title |
| `ContentColor` | `TextDim` | body color |
| `TextSize` | `12` | body size |

```lua
local para = section:Paragraph({ Title = "status", Content = "…" })
para:Set({ Title = "error", Content = "file not found", Style = "danger" })
```

## Styles

| Name | Color |
| --- | --- |
| `normal`, `text` | light grey |
| `dim`, `muted` | grey |
| `bright`, `title` | off white |
| `warning`, `warn`, `yellow` | yellow |
| `danger`, `error`, `red` | red |
| `success`, `green` | green |
| `accent`, `pink` | accent color |

A `Color3` can be passed directly in place of a style name.
