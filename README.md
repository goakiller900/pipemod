# Advanced Fluid Handling Continued (AFHC)

**Advanced Fluid Handling Continued** is a Factorio 2.1 continuation of **Advanced Fluid Handling**, originally created by **TheStaplergun**.

This repository carries the Factorio 2.1 and Space Age compatibility work forward under a new standalone mod identity:

- Title: `Advanced Fluid Handling Continued`
- Internal mod name: `advanced-fluid-handling-continued`
- Short name: `AFHC`
- Target: Factorio `2.1`

Upstream/original repository: `https://github.com/TheStaplergun/pipemod`

## What the mod adds

- Three tiers of independently rotatable multi-port pipes-to-ground.
- I, L, T, and cross-shaped underground pipe extensions.
- Three tiers of underground pumps.
- Adjustable overflow and top-up valves plus a check valve.
- `Ctrl + R` and `Ctrl + Shift + R` controls for underground-port rotation.
- Numpad `+` and `-` controls for adjusting valve thresholds.

## Factorio 2.1 continuation

The AFHC version includes the existing 2.1 compatibility work from this fork:

- Factorio 2.1 prototype compatibility.
- Optional Space Age 2.1 support.
- Updated pipe-connection and valve definitions.
- Deterministic tier upgrade chains.
- Fluid, quality, health, last-user and ghost-tag preservation during scripted replacements.
- Existing gameplay prototype names retained for save compatibility.
- Deterministic Factorio-ready ZIP builds with SHA-256 checksums.

AFHC uses its own internal mod identity but intentionally keeps the established item, recipe, technology and entity prototype names. Because those prototype names overlap with the original `underground-pipe-pack`, AFHC declares the original mod as incompatible so both cannot be enabled at the same time.

The runtime remote interface uses `script.mod_name`, so under AFHC it is automatically registered as:

`advanced-fluid-handling-continued`

## Building the Factorio mod

Run:

```bash
python scripts/build_release.py
```

The finished files are written to `dist/`:

```text
advanced-fluid-handling-continued_2.1.0.zip
advanced-fluid-handling-continued_2.1.0.zip.sha256
```

The release builder:

- validates `info.json` and the Factorio 2.1 target;
- checks required files and Lua `require()` paths;
- rejects known obsolete Factorio prototype fields;
- rewrites legacy `__underground-pipe-pack__/...` self-asset paths to `__advanced-fluid-handling-continued__/...` inside the release archive;
- validates referenced self-assets;
- verifies that the finished ZIP contains no stale legacy self-asset namespaces;
- creates one correctly named mod root folder inside the ZIP;
- generates a SHA-256 checksum.

This packaging-time namespace migration lets the inherited source tree keep its historical layout while producing an AFHC package that resolves graphics and other self-assets through the new mod identity.

## GitHub Actions

The workflow in `.github/workflows/build-release.yml` validates and builds the mod on pushes, pull requests and manual runs. The resulting Factorio ZIP and checksum are uploaded as GitHub Actions artifacts and can be placed directly in the Factorio `mods` directory for testing.

## Testing checklist

A successful build proves that the mod structure and package passed automated checks; it does not replace in-game testing. Before calling a version stable, test at least:

- clean Factorio 2.1 base game;
- Factorio 2.1 with Space Age enabled;
- fresh games and upgraded saves;
- all three technology tiers and recipes;
- placement, mining and rotation in both directions;
- blueprint ghosts, robot construction and upgrade-planner chains;
- underground pumps and circuit connections;
- adjustable valves and fluid preservation;
- optional compatibility combinations used by your mod pack.

## Credits

- Original Advanced Fluid Handling creator and maintainer: **TheStaplergun**.
- Previous fixes and translations: the contributors recorded in the upstream Git history.
- Factorio 2.1 continuation and AFHC packaging work: **goakiller900**, with testing and development assistance.

## Licence

The original `LICENSE.txt` is retained unchanged. It is **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International**.

That licence may restrict public distribution of modified versions. Building and testing AFHC does not itself grant permission to publish the modified package publicly; obtain any permission required from the original rights holder before a public Mod Portal release.
