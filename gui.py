import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import threading
import sys
import tempfile
import json

from settings import settings
from blender_detect import require_blender, find_blender
from version import __version__
import updater
import addon_installer

# Apply saved appearance settings
ctk.set_appearance_mode(settings.get("appearance_mode") or "dark")
ctk.set_default_color_theme("blue")


def get_python_executable():
    if getattr(sys, 'frozen', False):
        return sys.executable
    venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
    if os.path.exists(venv_python):
        return venv_python
    # Windows venv path
    venv_python_win = os.path.join(os.path.dirname(__file__), "venv", "Scripts", "python.exe")
    if os.path.exists(venv_python_win):
        return venv_python_win
    return sys.executable


python_exec = get_python_executable()

# Temp file paths (cross-platform)
progress_file = os.path.join(tempfile.gettempdir(), "render_progress.txt")
compression_progress_file = os.path.join(tempfile.gettempdir(), "compression_progress.txt")

# Global state
selected_files = []
compression_input = []
output_folder = ""
compression_output_folder = ""
all_objects = {}
object_vars = {}        # dict[str, ctk.BooleanVar]
marked_objects = {}     # dict[filename, {"front": [...], "back": [...]}]


def get_script_path(script_name):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, script_name)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)


# ── Status bar ─────────────────────────────────────────────────────────────

STATUS_COLORS = {
    "info":    ("#1f538d", "#3a7ebf"),   # (light_mode, dark_mode) fg-ish
    "success": ("#1a6b3c", "#2d9653"),
    "warning": "#b85c00",
    "error":   "#c0392b",
}


def update_status(message, status_type="info"):
    app.after(0, lambda: _update_status(message, status_type))


def _update_status(message, status_type):
    status_label.configure(text=message)


# ── Auto-updater ───────────────────────────────────────────────────────────

def _show_update_dialog(release: dict) -> None:
    tag = release.get("tag_name", "onbekend")
    notes = release.get("body", "").strip()
    notes_preview = (notes[:300] + "…") if len(notes) > 300 else notes

    win = ctk.CTkToplevel(app)
    win.title("Update beschikbaar")
    win.geometry("480x320")
    win.resizable(False, False)
    win.grab_set()

    ctk.CTkLabel(
        win,
        text=f"Nieuwe versie beschikbaar: {tag}",
        font=ctk.CTkFont(size=15, weight="bold"),
    ).pack(pady=(20, 6), padx=20)

    if notes_preview:
        ctk.CTkLabel(
            win,
            text=notes_preview,
            wraplength=440,
            justify="left",
            text_color="gray",
        ).pack(padx=20, pady=(0, 12))

    progress_bar = ctk.CTkProgressBar(win)
    progress_bar.set(0)
    progress_bar.pack(fill="x", padx=20, pady=(0, 8))
    progress_bar.pack_forget()

    status_lbl = ctk.CTkLabel(win, text="")
    status_lbl.pack(pady=(0, 8))

    btn_frame = ctk.CTkFrame(win, fg_color="transparent")
    btn_frame.pack(pady=8)

    def _on_status(msg, kind="info"):
        app.after(0, lambda: status_lbl.configure(text=msg))
        update_status(msg, kind)

    def _on_progress(pct):
        app.after(0, lambda: (progress_bar.pack(fill="x", padx=20, pady=(0, 8)),
                               progress_bar.set(pct)))

    def _do_install():
        install_btn.configure(state="disabled")
        later_btn.configure(state="disabled")

        def _task():
            ok = updater.install_update(release, _on_progress, _on_status)
            if ok:
                app.after(800, app.destroy)

        threading.Thread(target=_task, daemon=True).start()

    install_btn = ctk.CTkButton(
        btn_frame, text="Nu installeren", fg_color="#2d9653",
        hover_color="#1a6b3c", command=_do_install,
    )
    install_btn.pack(side="left", padx=(0, 10))

    later_btn = ctk.CTkButton(
        btn_frame, text="Later", fg_color="gray40",
        hover_color="gray30", command=win.destroy,
    )
    later_btn.pack(side="left")


def _run_update_check() -> None:
    """Background thread: check GitHub for a newer release."""
    release = updater.check_for_update()
    if release:
        app.after(0, lambda: _show_update_dialog(release))


def schedule_update_check() -> None:
    """Called once after the main window is ready (3 s delay)."""
    threading.Thread(target=_run_update_check, daemon=True).start()


# ── Render tab ─────────────────────────────────────────────────────────────

def extract_objects_from_blend(blend_file):
    """
    Run extract_objects.py inside Blender and return (objects_list, marks_dict).
    marks_dict = {"front": [...], "back": [...]}
    """
    try:
        blender_exe = require_blender(app)
    except RuntimeError as e:
        update_status(str(e), "error")
        return [], {"front": [], "back": []}

    extract_script = get_script_path("extract_objects.py")
    try:
        result = subprocess.run([
            blender_exe,
            "--background",
            "--factory-startup",
            blend_file,
            "--python", extract_script,
        ], capture_output=True, text=True, check=True)

        objects = []
        marks   = {"front": [], "back": []}
        _skip_prefixes = ('Blender', 'Info', 'Extracted', 'Objects saved to', 'Error', 'Usage', 'BATCH_MARKS:')

        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('BATCH_MARKS:'):
                try:
                    marks = json.loads(line[len('BATCH_MARKS:'):])
                except Exception:
                    pass
            elif not any(line.startswith(p) for p in _skip_prefixes):
                objects.append(line)

        return objects, marks
    except Exception as e:
        print(f"Error extracting objects from {blend_file}: {e}")
        return [], {"front": [], "back": []}


def browse_blend_files():
    global selected_files, all_objects
    initial = settings.get("last_blend_dir") or ""
    files = filedialog.askopenfilenames(
        title="3D Bestanden Selecteren",
        initialdir=initial or None,
        filetypes=[("Blender files", "*.blend")],
    )
    if not files:
        return
    selected_files = list(files)
    settings.set("last_blend_dir", os.path.dirname(selected_files[0]))
    render_input_label.configure(text=f"{len(files)} bestand(en) geselecteerd")

    update_status("Objecten extraheren uit Blender bestanden...", "info")
    all_objects = {}

    def extract_task():
        global marked_objects
        marked_objects = {}
        for bf in selected_files:
            objs, marks = extract_objects_from_blend(bf)
            fname = os.path.basename(bf)
            all_objects[fname]    = objs
            marked_objects[fname] = marks
        app.after(0, _refresh_object_checkboxes)
        total       = sum(len(v) for v in all_objects.values())
        total_marks = sum(
            len(m.get("selected", []))
            for m in marked_objects.values()
        )
        msg = f"Objecten geëxtraheerd uit {len(selected_files)} bestand(en) — {total} objecten"
        if total_marks:
            msg += f", {total_marks} kleur verander object(en) gevonden"
        update_status(msg, "success")

    threading.Thread(target=extract_task, daemon=True).start()


def _refresh_object_checkboxes():
    global object_vars
    for w in objects_scroll_frame.winfo_children():
        w.destroy()
    object_vars = {}

    for filename, objs in all_objects.items():
        marks        = marked_objects.get(filename, {"selected": []})
        selected_set = set(marks.get("selected", []))

        for obj in objs:
            if obj in selected_set:
                label_text = f"{filename}: {obj}  [kleur]"
                text_color = ("#1a6b3c", "#2d9653")   # groen
            else:
                label_text = f"{filename}: {obj}"
                text_color = ("gray10", "gray90")

            var = ctk.BooleanVar(value=True)
            cb  = ctk.CTkCheckBox(
                objects_scroll_frame,
                text=label_text,
                variable=var,
                text_color=text_color,
                command=_update_selection_label,
            )
            cb.pack(anchor="w", padx=5, pady=2)
            object_vars[label_text] = var

    _update_selection_label()


def _update_selection_label():
    selected = sum(1 for v in object_vars.values() if v.get())
    total = len(object_vars)
    selection_label.configure(text=f"Geselecteerd: {selected} / {total} object(en)")


def select_all_objects():
    for v in object_vars.values():
        v.set(True)
    _update_selection_label()


def clear_selection():
    for v in object_vars.values():
        v.set(False)
    _update_selection_label()


def browse_output_folder():
    global output_folder
    initial = settings.get("last_output_dir") or ""
    folder = filedialog.askdirectory(title="Uitvoermap Kiezen", initialdir=initial or None)
    if folder:
        output_folder = folder
        settings.set("last_output_dir", folder)
        output_label.configure(text=folder)


def open_material_file():
    try:
        blender_exe = require_blender(app)
    except RuntimeError as e:
        update_status(str(e), "error")
        return

    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    material_path = os.path.join(base_dir, "Materialen.blend")
    if os.path.exists(material_path):
        subprocess.Popen([blender_exe, material_path])
    else:
        update_status("Fout: Materialen.blend niet gevonden!", "error")


def start_render():
    global selected_files, output_folder

    if not selected_files:
        update_status("Selecteer eerst een .blend bestand om te renderen.", "warning")
        return
    if not output_folder:
        update_status("Selecteer eerst een output map voor de renders.", "warning")
        return

    selected_objects = [k for k, v in object_vars.items() if v.get()]
    if not selected_objects:
        update_status("Selecteer eerst objecten om te renderen.", "warning")
        return

    render_progress.set(0)
    render_progress.grid()

    batch_render_script = get_script_path("batch_render.py")
    update_status("Render gestart...", "info")

    if os.path.exists(progress_file):
        os.remove(progress_file)

    def render_task():
        try:
            subprocess.run([
                python_exec,
                batch_render_script,
                *selected_files,
                "|".join(selected_objects),
                output_folder,
            ], check=True)
            update_status("Render voltooid!", "success")
        except Exception as e:
            update_status(f"Fout bij renderen: {e}", "error")
        finally:
            app.after(500, lambda: render_progress.grid_remove())

    def poll_render_progress():
        try:
            if os.path.exists(progress_file):
                with open(progress_file) as f:
                    current = len(f.readlines())
                # Indeterminate-style: cycle 0→1 based on count mod steps
                render_progress.set((current % 20) / 20)
            app.after(200, poll_render_progress)
        except Exception:
            app.after(200, poll_render_progress)

    threading.Thread(target=render_task, daemon=True).start()
    poll_render_progress()


# ── Compression tab ────────────────────────────────────────────────────────

def browse_compression_files():
    global compression_input
    initial = settings.get("last_compress_input") or ""
    files = filedialog.askopenfilenames(
        title="Afbeeldingen Selecteren",
        initialdir=initial or None,
        filetypes=[("Afbeeldingen", "*.jpg *.jpeg *.png")],
    )
    if files:
        compression_input = list(files)
        settings.set("last_compress_input", os.path.dirname(compression_input[0]))
        compression_input_label.configure(text=f"{len(files)} bestand(en) geselecteerd")


def browse_compression_folder():
    global compression_input
    initial = settings.get("last_compress_input") or ""
    folder = filedialog.askdirectory(title="Map Selecteren", initialdir=initial or None)
    if folder:
        compression_input = [folder]
        settings.set("last_compress_input", folder)
        compression_input_label.configure(text=folder)


def browse_compression_output():
    global compression_output_folder
    initial = settings.get("last_compress_output") or ""
    folder = filedialog.askdirectory(title="Uitvoermap Kiezen", initialdir=initial or None)
    if folder:
        compression_output_folder = folder
        settings.set("last_compress_output", folder)
        compression_output_label.configure(text=folder)


def start_compression():
    if not compression_input or not compression_output_folder:
        update_status("Selecteer input en output voor compressie.", "warning")
        return

    # Count total files
    total_files = 0
    for path in compression_input:
        if os.path.isdir(path):
            for _, _, files in os.walk(path):
                total_files += sum(1 for f in files if f.lower().endswith((".jpg", ".jpeg", ".png")))
        else:
            total_files += 1

    if total_files == 0:
        update_status("Geen afbeeldingen gevonden om te comprimeren.", "warning")
        return

    if os.path.exists(compression_progress_file):
        os.remove(compression_progress_file)

    compress_progress.set(0)
    compress_progress.grid()
    update_status("Compressie gestart...", "info")

    try:
        max_size_kb = int(size_entry.get())
    except ValueError:
        max_size_kb = 300

    compress_script = get_script_path("compress.py")

    def compression_task():
        try:
            subprocess.run([
                python_exec,
                compress_script,
                "--input", ",".join(compression_input),
                "--output", compression_output_folder,
                "--max-size", str(max_size_kb),
                "--progress-file", compression_progress_file,
            ], check=True)
            update_status("Compressie voltooid!", "success")
        except Exception as e:
            update_status(f"Compressiefout: {e}", "error")
        finally:
            app.after(500, lambda: compress_progress.grid_remove())

    def poll_compress_progress():
        try:
            if os.path.exists(compression_progress_file):
                with open(compression_progress_file) as f:
                    current = len(f.readlines())
                compress_progress.set(min(current / max(total_files, 1), 1.0))
                if current < total_files:
                    app.after(100, poll_compress_progress)
                return
            app.after(100, poll_compress_progress)
        except Exception:
            app.after(100, poll_compress_progress)

    threading.Thread(target=compression_task, daemon=True).start()
    poll_compress_progress()


# ── Flamenco tab ───────────────────────────────────────────────────────────

def _get_flamenco_url():
    return flamenco_url_var.get().strip() or settings.get("flamenco_manager_url")


def test_flamenco_connection():
    url = _get_flamenco_url()
    if not url:
        update_status("Vul een Flamenco Manager URL in.", "warning")
        return

    settings.set("flamenco_manager_url", url)
    update_status("Verbinden met Flamenco...", "info")
    flamenco_connect_btn.configure(state="disabled")

    def _task():
        try:
            import urllib.request
            req = urllib.request.urlopen(f"{url.rstrip('/')}/api/v3/version", timeout=5)
            data = json.loads(req.read().decode())
            version = data.get("version", "onbekend")
            app.after(0, lambda: update_status(f"Verbonden met Flamenco {version}", "success"))
        except Exception as e:
            app.after(0, lambda: update_status(f"Kan niet verbinden: {e}", "error"))
        finally:
            app.after(0, lambda: flamenco_connect_btn.configure(state="normal"))

    threading.Thread(target=_task, daemon=True).start()


def submit_to_flamenco():
    """Build a material_batch job from selected color-changing objects and POST to Flamenco."""
    if not selected_files:
        update_status("Selecteer eerst een .blend bestand via de Renderen-tab.", "warning")
        return

    manager_url  = _get_flamenco_url()
    material     = flamenco_material_var.get().strip()
    mat_library  = flamenco_matlib_var.get().strip()

    if not manager_url:
        update_status("Vul de Flamenco Manager URL in.", "warning")
        return
    if not output_folder:
        update_status("Selecteer een output map via de Renderen-tab.", "warning")
        return
    if not material:
        update_status("Vul een materiaalnaam in.", "warning")
        return

    settings.set("flamenco_manager_url",      manager_url)
    settings.set("flamenco_material_name",    material)
    settings.set("flamenco_material_library", mat_library)

    # Collect checked color-changing objects per blend file
    jobs_to_submit = []
    for bf in selected_files:
        fname        = os.path.basename(bf)
        marks        = marked_objects.get(fname, {"selected": []})
        selected_set = set(marks.get("selected", []))

        checked = set()
        for label, var in object_vars.items():
            if var.get() and label.startswith(f"{fname}:"):
                raw = label[len(f"{fname}: "):].split("  [")[0]
                checked.add(raw)

        color_objs = [o for o in selected_set if o in checked]
        if not color_objs:
            continue

        mapping = {o: material for o in color_objs}

        mat_lib_path = mat_library if (mat_library and os.path.isfile(mat_library)) \
                       else get_script_path("Materialen.blend")

        jobs_to_submit.append({
            "blend_file": bf,
            "mat_lib":    mat_lib_path,
            "mapping":    mapping,
            "output_dir": output_folder,
            "count":      len(color_objs),
        })

    if not jobs_to_submit:
        update_status(
            "Geen kleur verander objecten gevonden. Selecteer objecten via de Blender plugin.",
            "warning",
        )
        return

    flamenco_submit_btn.configure(state="disabled")
    update_status(f"Verzenden naar Flamenco ({len(jobs_to_submit)} job(s))...", "info")

    def _task():
        try:
            import urllib.request
            submitted = 0
            for job_info in jobs_to_submit:
                job = {
                    "name": f"Batch Render — {os.path.basename(job_info['blend_file'])} "
                            f"({job_info['count']} object(en))",
                    "job_type": "material_batch",
                    "tasks": [{
                        "name": "render_color_objects",
                        "type": "material_batch",
                        "settings": {
                            "blend_file":              job_info["blend_file"],
                            "material_library":        job_info["mat_lib"],
                            "object_material_mapping": json.dumps(job_info["mapping"]),
                            "output_directory":        job_info["output_dir"],
                        },
                    }],
                }
                body = json.dumps(job).encode()
                req  = urllib.request.Request(
                    f"{manager_url.rstrip('/')}/api/v3/jobs",
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 201:
                        submitted += 1

            app.after(0, lambda: update_status(
                f"{submitted} job(s) verzonden naar Flamenco!", "success"))
        except Exception as e:
            app.after(0, lambda: update_status(f"Fout bij verzenden: {e}", "error"))
        finally:
            app.after(0, lambda: flamenco_submit_btn.configure(state="normal"))

    threading.Thread(target=_task, daemon=True).start()


def _browse_flamenco_matlib():
    path = filedialog.askopenfilename(
        title="Materiaalbibliotheek Kiezen",
        filetypes=[("Blender bestanden", "*.blend")],
    )
    if path:
        flamenco_matlib_var.set(path)
        settings.set("flamenco_material_library", path)


# ── Settings tab ───────────────────────────────────────────────────────────

def pick_blender_path():
    import tkinter as tk
    from tkinter import filedialog

    path = filedialog.askopenfilename(title="Blender Loceren")
    if path and os.path.isfile(path):
        settings.set("blender_path", path)
        blender_path_label.configure(text=path)
        update_status("Blender pad opgeslagen.", "success")


def on_appearance_change(value):
    mode_map = {"Donker": "dark", "Licht": "light", "Systeem": "system"}
    mode = mode_map.get(value, "dark")
    ctk.set_appearance_mode(mode)
    settings.set("appearance_mode", mode)


# ── Main window ────────────────────────────────────────────────────────────

app = ctk.CTk()
app.title("BlenderTools")
app.geometry("960x720")
app.minsize(800, 600)

# Status bar (bottom)
status_bar = ctk.CTkFrame(app, height=30, corner_radius=0)
status_bar.pack(side="bottom", fill="x")
status_label = ctk.CTkLabel(status_bar, text="Gereed", anchor="w")
status_label.pack(side="left", padx=10)

# Tab view
def _on_tab_change():
    if tabs.get() == "Add-ons":
        _refresh_addon_status()

tabs = ctk.CTkTabview(app, command=_on_tab_change)
tabs.pack(fill="both", expand=True, padx=10, pady=10)

tabs.add("Renderen")
tabs.add("Compressie")
tabs.add("Flamenco")
tabs.add("Add-ons")
tabs.add("Instellingen")

# ── Renderen tab ─────────────────────────────────────────────────────────

render_tab = tabs.tab("Renderen")
render_tab.columnconfigure(1, weight=1)

# Materials row
mat_frame = ctk.CTkFrame(render_tab, fg_color="transparent")
mat_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
ctk.CTkLabel(mat_frame, text="Open het bestand met alle beschikbare materialen").pack(side="left", padx=5)
ctk.CTkButton(mat_frame, text="Materialenbestand Openen", command=open_material_file).pack(side="right", padx=5)

# Files row
ctk.CTkButton(render_tab, text="3D Bestanden Selecteren", command=browse_blend_files).grid(
    row=1, column=0, padx=5, pady=5, sticky="w")
render_input_label = ctk.CTkLabel(render_tab, text="Geen bestanden geselecteerd", anchor="w")
render_input_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# Output row
ctk.CTkButton(render_tab, text="Uitvoermap Kiezen", command=browse_output_folder).grid(
    row=2, column=0, padx=5, pady=5, sticky="w")
output_label = ctk.CTkLabel(render_tab, text="Geen map geselecteerd", anchor="w")
output_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")

# Object selection
obj_frame = ctk.CTkFrame(render_tab)
obj_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
render_tab.rowconfigure(3, weight=1)
obj_frame.columnconfigure(0, weight=1)

ctk.CTkLabel(obj_frame, text="Object Selectie", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(8, 0))

objects_scroll_frame = ctk.CTkScrollableFrame(obj_frame, height=180)
objects_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

btn_row = ctk.CTkFrame(obj_frame, fg_color="transparent")
btn_row.pack(fill="x", padx=5, pady=(0, 5))
ctk.CTkButton(btn_row, text="Alles Selecteren", width=140, command=select_all_objects).pack(side="left", padx=(0, 5))
ctk.CTkButton(btn_row, text="Selectie Wissen", width=140, command=clear_selection).pack(side="left")
selection_label = ctk.CTkLabel(btn_row, text="Geen objecten geselecteerd")
selection_label.pack(side="right", padx=5)

# Progress bar (hidden initially)
render_progress = ctk.CTkProgressBar(render_tab, mode="indeterminate")
render_progress.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
render_progress.grid_remove()

# Start button
ctk.CTkButton(render_tab, text="Start Rendering", fg_color="#2d9653", hover_color="#1a6b3c",
              command=start_render).grid(row=5, column=0, columnspan=2, pady=10)

# ── Compressie tab ─────────────────────────────────────────────────────────

compress_tab = tabs.tab("Compressie")
compress_tab.columnconfigure(1, weight=1)

# Input row
input_btn_frame = ctk.CTkFrame(compress_tab, fg_color="transparent")
input_btn_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)
ctk.CTkButton(input_btn_frame, text="Afbeeldingen", command=browse_compression_files).pack(side="left", padx=(0, 5))
ctk.CTkButton(input_btn_frame, text="Map Selecteren", command=browse_compression_folder).pack(side="left")

compression_input_label = ctk.CTkLabel(compress_tab, text="Geen bestanden geselecteerd", anchor="w")
compression_input_label.grid(row=1, column=0, columnspan=2, padx=15, pady=2, sticky="w")

# Output row
ctk.CTkButton(compress_tab, text="Uitvoermap", command=browse_compression_output).grid(
    row=2, column=0, padx=5, pady=5, sticky="w")
compression_output_label = ctk.CTkLabel(compress_tab, text="Geen map geselecteerd", anchor="w")
compression_output_label.grid(row=3, column=0, columnspan=2, padx=15, pady=2, sticky="w")

# Max size row
size_frame = ctk.CTkFrame(compress_tab, fg_color="transparent")
size_frame.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=5)
ctk.CTkLabel(size_frame, text="Maximale bestandsgrootte (KB):").pack(side="left", padx=(5, 5))
size_entry = ctk.CTkEntry(size_frame, width=80)
size_entry.insert(0, str(settings.get("max_file_size_kb")))
size_entry.pack(side="left")
ctk.CTkLabel(size_frame, text="ⓘ  Let op: grootte klopt niet altijd volledig.",
             text_color="gray").pack(side="left", padx=(10, 0))

# Progress bar
compress_progress = ctk.CTkProgressBar(compress_tab)
compress_progress.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
compress_progress.grid_remove()

# Start button
ctk.CTkButton(compress_tab, text="Start Compressie", command=start_compression).grid(
    row=6, column=0, columnspan=2, pady=10)

# ── Flamenco tab ───────────────────────────────────────────────────────────

flamenco_tab = tabs.tab("Flamenco")
flamenco_tab.columnconfigure(1, weight=1)

ctk.CTkLabel(
    flamenco_tab,
    text="Flamenco Render Farm",
    font=ctk.CTkFont(size=16, weight="bold"),
    anchor="w",
).grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(15, 2))

ctk.CTkLabel(
    flamenco_tab,
    text="Verzend batch render jobs naar een Flamenco Manager. Markeer objecten eerst via de Blender plugin.",
    text_color="gray",
    anchor="w",
    wraplength=680,
).grid(row=1, column=0, columnspan=3, sticky="w", padx=15, pady=(0, 12))

# Manager URL
ctk.CTkLabel(flamenco_tab, text="Manager URL:", anchor="w").grid(
    row=2, column=0, sticky="w", padx=15, pady=4)
flamenco_url_var = ctk.StringVar(value=settings.get("flamenco_manager_url"))
ctk.CTkEntry(flamenco_tab, textvariable=flamenco_url_var).grid(
    row=2, column=1, sticky="ew", padx=(0, 5), pady=4)
flamenco_connect_btn = ctk.CTkButton(
    flamenco_tab, text="Verbinden", width=110, command=test_flamenco_connection)
flamenco_connect_btn.grid(row=2, column=2, padx=(0, 15), pady=4)

# Material name
ctk.CTkLabel(flamenco_tab, text="Materiaal:", anchor="w").grid(
    row=3, column=0, sticky="w", padx=15, pady=4)
flamenco_material_var = ctk.StringVar(value=settings.get("flamenco_material_name") or "color_material")
ctk.CTkEntry(flamenco_tab, textvariable=flamenco_material_var).grid(
    row=3, column=1, columnspan=2, sticky="ew", padx=(0, 15), pady=4)

# Material library (optional override)
ctk.CTkLabel(flamenco_tab, text="Materiaalbibliotheek:", anchor="w").grid(
    row=4, column=0, sticky="w", padx=15, pady=4)
flamenco_matlib_var = ctk.StringVar(value=settings.get("flamenco_material_library"))
ctk.CTkEntry(flamenco_tab, textvariable=flamenco_matlib_var,
             placeholder_text="Leeg = gebruik ingebouwde Materialen.blend").grid(
    row=4, column=1, sticky="ew", padx=(0, 5), pady=4)
ctk.CTkButton(flamenco_tab, text="...", width=40, command=_browse_flamenco_matlib).grid(
    row=4, column=2, padx=(0, 15), pady=4)

# Separator
ctk.CTkFrame(flamenco_tab, height=2, fg_color="gray30").grid(
    row=5, column=0, columnspan=3, sticky="ew", padx=15, pady=10)

# Info label
ctk.CTkLabel(
    flamenco_tab,
    text="Gebruik de Renderen-tab om .blend bestanden te laden. Kleur verander objecten (geselecteerd via de Blender plugin) worden automatisch herkend.",
    text_color="gray",
    anchor="w",
    wraplength=680,
).grid(row=6, column=0, columnspan=3, sticky="w", padx=15, pady=(0, 10))

# Submit button
flamenco_submit_btn = ctk.CTkButton(
    flamenco_tab,
    text="Verzend naar Flamenco",
    fg_color="#2d9653",
    hover_color="#1a6b3c",
    height=40,
    command=submit_to_flamenco,
)
flamenco_submit_btn.grid(row=7, column=0, columnspan=3, padx=15, pady=10, sticky="ew")

# ── Add-ons tab ────────────────────────────────────────────────────────────

addons_tab = tabs.tab("Add-ons")
addons_tab.columnconfigure(0, weight=1)

# Header
ctk.CTkLabel(
    addons_tab,
    text="Blender Add-ons",
    font=ctk.CTkFont(size=16, weight="bold"),
    anchor="w",
).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 2))

ctk.CTkLabel(
    addons_tab,
    text="Installeer BlenderTools add-ons rechtstreeks in je Blender installatie.",
    text_color="gray",
    anchor="w",
).grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 15))

# ── Flamenco Batch Render card ──────────────────────────────────────────────

addon_card = ctk.CTkFrame(addons_tab)
addon_card.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=5)
addon_card.columnconfigure(0, weight=1)

ctk.CTkLabel(
    addon_card,
    text="Flamenco Batch Render",
    font=ctk.CTkFont(size=13, weight="bold"),
    anchor="w",
).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 2))

ctk.CTkLabel(
    addon_card,
    text="Markeer objecten als Front/Back en dien batch render jobs in bij Flamenco Manager.",
    text_color="gray",
    anchor="w",
    wraplength=600,
    justify="left",
).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

addon_status_label = ctk.CTkLabel(addon_card, text="", anchor="w")
addon_status_label.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 4))

addon_btn_frame = ctk.CTkFrame(addon_card, fg_color="transparent")
addon_btn_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 12))

addon_install_btn = ctk.CTkButton(addon_btn_frame, text="Installeren", width=130)
addon_install_btn.pack(side="left", padx=(0, 8))

addon_remove_btn = ctk.CTkButton(
    addon_btn_frame, text="Verwijderen", width=130,
    fg_color="gray40", hover_color="gray30",
)
addon_remove_btn.pack(side="left")


def _refresh_addon_status():
    blender_exe = find_blender()
    if not blender_exe:
        addon_status_label.configure(text="Blender niet gevonden — stel het pad in via Instellingen.", text_color="gray")
        addon_install_btn.configure(state="disabled")
        addon_remove_btn.configure(state="disabled")
        return

    installed = addon_installer.is_installed(blender_exe)
    if installed:
        addon_status_label.configure(text="Status: geïnstalleerd", text_color="#2d9653")
        addon_install_btn.configure(state="normal", text="Herinstalleren")
        addon_remove_btn.configure(state="normal")
    else:
        addon_status_label.configure(text="Status: niet geïnstalleerd", text_color="gray")
        addon_install_btn.configure(state="normal", text="Installeren")
        addon_remove_btn.configure(state="disabled")


def _do_addon_install():
    try:
        blender_exe = require_blender(app)
    except RuntimeError as e:
        update_status(str(e), "error")
        return

    addon_install_btn.configure(state="disabled")
    addon_remove_btn.configure(state="disabled")
    update_status("Add-on installeren...", "info")

    def _task():
        ok, msg = addon_installer.install(blender_exe)
        app.after(0, lambda: _on_addon_done(ok, msg))

    threading.Thread(target=_task, daemon=True).start()


def _do_addon_remove():
    try:
        blender_exe = require_blender(app)
    except RuntimeError as e:
        update_status(str(e), "error")
        return

    addon_install_btn.configure(state="disabled")
    addon_remove_btn.configure(state="disabled")
    update_status("Add-on verwijderen...", "info")

    def _task():
        ok, msg = addon_installer.uninstall(blender_exe)
        app.after(0, lambda: _on_addon_done(ok, msg))

    threading.Thread(target=_task, daemon=True).start()


def _on_addon_done(ok, msg):
    update_status(msg.replace("\n", " "), "success" if ok else "error")
    _refresh_addon_status()


addon_install_btn.configure(command=_do_addon_install)
addon_remove_btn.configure(command=_do_addon_remove)

# Initial status check (deferred so Blender detection doesn't block startup)
app.after(500, _refresh_addon_status)

# ── Instellingen tab ───────────────────────────────────────────────────────

settings_tab = tabs.tab("Instellingen")
settings_tab.columnconfigure(1, weight=1)

ctk.CTkLabel(settings_tab, text="Blender Installatie",
             font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2,
                                                             sticky="w", padx=15, pady=(15, 5))

detected = find_blender() or "Niet gevonden"
blender_path_label = ctk.CTkLabel(settings_tab, text=detected, anchor="w", wraplength=600)
blender_path_label.grid(row=1, column=0, padx=15, pady=2, sticky="w")
ctk.CTkButton(settings_tab, text="Blender Loceren...", command=pick_blender_path).grid(
    row=1, column=1, padx=5, pady=2, sticky="e")

ctk.CTkLabel(settings_tab, text="Weergave",
             font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, columnspan=2,
                                                             sticky="w", padx=15, pady=(20, 5))

mode_reverse = {"dark": "Donker", "light": "Licht", "system": "Systeem"}
current_mode = mode_reverse.get(settings.get("appearance_mode"), "Donker")
appearance_menu = ctk.CTkOptionMenu(
    settings_tab,
    values=["Donker", "Licht", "Systeem"],
    command=on_appearance_change,
)
appearance_menu.set(current_mode)
appearance_menu.grid(row=3, column=0, padx=15, pady=5, sticky="w")

# ── Updates section ─────────────────────────────────────────────────────────

ctk.CTkLabel(settings_tab, text="Updates",
             font=ctk.CTkFont(size=14, weight="bold")).grid(
    row=4, column=0, columnspan=2, sticky="w", padx=15, pady=(20, 5))

ctk.CTkLabel(settings_tab, text=f"Huidige versie: {__version__}", anchor="w").grid(
    row=5, column=0, padx=15, pady=2, sticky="w")


def _manual_check():
    update_status("Controleren op updates...", "info")

    def _task():
        release = updater.check_for_update()
        if release:
            app.after(0, lambda: _show_update_dialog(release))
        else:
            update_status("Je gebruikt de nieuwste versie.", "success")

    threading.Thread(target=_task, daemon=True).start()


ctk.CTkButton(settings_tab, text="Controleer op updates", command=_manual_check).grid(
    row=5, column=1, padx=5, pady=2, sticky="e")

# ── Start auto-update check after window is ready ───────────────────────────

app.after(3000, schedule_update_check)

app.mainloop()
