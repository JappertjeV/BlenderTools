# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Blender addon** (Python) that enables batch rendering workflows by integrating with [Flamenco](https://flamenco.blender.org/), Blender Studio's distributed render farm manager. Artists mark objects as "Front" or "Back" groups, configure render settings, and submit jobs to Flamenco Manager via its REST API.

- **Blender compatibility:** 3.6.0+
- **No build step** — Blender reads the Python files directly
- **No test framework** — manual testing requires running the addon inside Blender

## Development Workflow

To develop/test changes:
1. Install the addon in Blender via Edit → Preferences → Add-ons → Install from File
2. After editing files, reload scripts in Blender via Scripting workspace or `bpy.ops.script.reload()`
3. Alternatively, symlink this directory into Blender's addons folder for live editing

The addon requires a running [Flamenco Manager](https://flamenco.blender.org/) instance (default: `http://localhost:8080`) to submit jobs.

## Architecture

```
__init__.py       — Addon entry point, registers all submodules, hooks context menu
properties.py     — Scene-level and object-level property definitions (stored in .blend)
operators.py      — All bpy.types.Operator classes (marking, unmarking, Flamenco submission)
ui_panels.py      — Two UI panels: Properties Editor (full config) and 3D Viewport (quick access)
utils.py          — get_marked_objects(scene) helper
```

**Data flow for submission:**
1. Objects are marked FRONT/BACK via operators, which store `batch_render_type` on the object and apply red/blue preview materials
2. On submit, `SubmitToFlamenco` validates inputs, builds a `{object_name → material_name}` mapping, and POSTs a job JSON to `/api/v3/jobs` on the Flamenco Manager
3. All scene settings (manager URL, material library path, output dir, render settings) are persisted as scene properties in the `.blend` file

**Key design detail:** The `requests` library is an optional dependency — the addon imports it with a try/except and reports a user-facing error if it's missing. All other dependencies are stdlib or Blender-bundled (`bpy`).

## Blender Addon Conventions

- Every operator, panel, and property group must be registered/unregistered in `__init__.py`
- `bl_idname` for operators follows `category.operator_name` pattern (e.g., `object.mark_front`)
- Scene properties are accessed via `context.scene.batch_render_*`
- Object properties are accessed via `obj.batch_render_type`
- UI panels define `bl_space_type`, `bl_region_type`, `bl_context` to control where they appear
