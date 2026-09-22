# Native cards update

Based on quitxyz/lib commit 054eab6011ec41ae5b0886d0e5926da92d167511.

- main.luau: additive native card API; original animation implementation unchanged.
- docs/native-cards.md: options, runtime handles, examples, and limitations.
- docs/SUMMARY.md and docs/api-reference.md: new API links.
- verify-native.lua: internal mock-based verification (run with texlua).
- addons/ and example.luau: unchanged from the repository.

The standalone Facility-Revamped-Home.lua was not edited. This package does not
push changes to GitHub or publish the documentation website. Copy main.luau and
the docs folder to your development branch for review. The verification script
is development-only and must not be loaded in Roblox.

Verified: whole-file syntax, construction, bounds at compact/wide breakpoints,
privacy updates, hidden content, field/action mutations, theme repaint, logical
width caching across scale-only changes, and cleanup. Tests use mocked Roblox
objects; real rendering, native theme interaction, and the reported opening
animation require in-engine verification during the later example migration.
