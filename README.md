# Advanced Fluid Handling Continued (AFHC)

**Advanced Fluid Handling Continued** is an unofficial Factorio 2.1 continuation of **Advanced Fluid Handling**, originally created by **TheStaplergun**.

This repository carries the Factorio 2.1 and Space Age compatibility work forward under a new standalone mod identity:

- Title: `Advanced Fluid Handling Continued`
- Internal mod name: `advanced-fluid-handling-continued`
- Short name: `AFHC`
- Current AFHC version line: `0.0.x`
- Target: Factorio `2.1`

Upstream/original repository: `https://github.com/TheStaplergun/pipemod`

## Why this continuation exists

I wanted to continue using Advanced Fluid Handling with Factorio 2.1. The original project has received a version bump for the newer Factorio version, but several underlying compatibility issues and problems in the current repository still needed to be addressed.

While working on the mod, I fixed those issues and updated the code for proper Factorio 2.1 compatibility. I then submitted the complete set of fixes back to the original project as a pull request so the original maintainer could review and merge the work into the official repository.

At the time of writing, that pull request is still waiting for review or acceptance, and I have not received a response from the original maintainer.

Because the compatibility work was complete and the mod was otherwise left in a partially updated state, I created **Advanced Fluid Handling Continued (AFHC)** as a separately identified continuation so the working Factorio 2.1 version can be maintained, tested and packaged independently.

This is not intended to take ownership of, replace or compete with the original project. The full compatibility work was offered back to the original repository first, and I would still be happy to see those fixes incorporated upstream.

AFHC is primarily a compatibility and maintenance continuation focused on:

- Proper Factorio 2.1 compatibility.
- Fixing issues present in the current original repository.
- Preserving the original gameplay, balance, graphics and overall design as closely as possible.
- Keeping the mod usable while the submitted fixes remain unmerged.

The original mod remains the foundation of this project, and full credit for the original work belongs to **TheStaplergun** and the other original contributors.

## What the mod adds

- Three tiers of independently rotatable multi-port pipes-to-ground.
- I, L, T, and cross-shaped underground pipe extensions.
- Three tiers of underground pumps.
- Adjustable overflow and top-up valves plus a check valve.
- `Ctrl + R` and `Ctrl + Shift + R` controls for underground-port rotation.
- Numpad `+` and `-` controls for adjusting valve thresholds.

## Factorio 2.1 continuation

The AFHC version includes the Factorio 2.1 compatibility work and fixes from this fork:

- Factorio 2.1 prototype compatibility.
- Optional Space Age 2.1 support.
- Updated pipe-connection and valve definitions.
- Deterministic tier upgrade chains.
- Fluid, quality, health, last-user and ghost-tag preservation during scripted replacements.
- Fixes for issues encountered in the original repository during the 2.1 migration.
- Existing gameplay prototype names retained where practical for save compatibility.
- Deterministic Factorio-ready ZIP builds with SHA-256 checksums.

AFHC uses its own internal mod identity but intentionally keeps the established item, recipe, technology and entity prototype names. Because those prototype names overlap with the original `underground-pipe-pack`, AFHC declares the original mod as incompatible so both cannot be enabled at the same time.

The runtime remote interface uses `script.mod_name`, so under AFHC it is automatically registered as:

`advanced-fluid-handling-continued`

## Versioning

AFHC starts its own independent version history at:

`0.0.1`

The original Advanced Fluid Handling version numbers are not reused for AFHC releases. This keeps the continuation clearly separated from official upstream releases.

## Building the Factorio mod

Run:

```bash
python scripts/build_afhc.py
```

The finished files are written to `dist/`, for example:

```text
advanced-fluid-handling-continued_0.0.1.zip
advanced-fluid-handling-continued_0.0.1.zip.sha256
```

The release builder:

- validates `info.json` and the Factorio 2.1 target;
- checks that required mod files are present;
- rewrites legacy `__underground-pipe-pack__/...` self-asset paths to `__advanced-fluid-handling-continued__/...` inside the release archive;
- verifies that the finished ZIP contains no stale legacy self-asset namespaces;
- creates one correctly named mod root folder inside the ZIP;
- generates a SHA-256 checksum.

The namespace migration is performed on raw file bytes so inherited locale files are preserved without forcing a text encoding conversion.

## GitHub Actions and releases

The workflow in `.github/workflows/build-release.yml` validates and builds the mod on pull requests and on pushes to `master`.

For a new version on `master`, the workflow:

- reads the version from `info.json`;
- builds the Factorio-ready ZIP and checksum;
- creates a tag in the form `afhc-v<version>`;
- creates a GitHub Release named `Advanced Fluid Handling Continued version <version>`;
- attaches the ZIP and SHA-256 checksum to the release.

For example, AFHC version `0.0.1` produces:

- Tag: `afhc-v0.0.1`
- Release: `Advanced Fluid Handling Continued version 0.0.1`
- ZIP: `advanced-fluid-handling-continued_0.0.1.zip`

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
- Factorio 2.1 compatibility fixes, AFHC continuation and packaging work: **goakiller900**, with testing and development assistance.

## Licensing notice

The original project uses the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)** license.

I am aware that the **NoDerivatives** clause creates a licensing issue for publicly distributing a modified version of the project.

Before creating this continuation, I submitted the complete Factorio 2.1 compatibility fixes back to the original repository and am still waiting for that pull request to be reviewed or accepted. AFHC is being provided in good faith so that the mod can remain usable on Factorio 2.1 while those fixes are pending.

I do not claim ownership of the original work and I am not attempting to replace the original project.

If **TheStaplergun**, as the original author and rights holder, asks me to remove this continuation or its distributed builds, I will respect that request and remove them.

If the original project becomes actively maintained again and the submitted compatibility fixes are merged or otherwise implemented upstream, the need for this continuation can be reconsidered.

The original `LICENSE.txt` is retained unchanged.