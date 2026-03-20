import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty


def register():
    # Object property: is this object a color-changing object?
    bpy.types.Object.batch_render_selected = BoolProperty(
        name="Kleur Verander Object",
        description="Markeer dit object als kleur verander object voor batch rendering",
        default=False,
    )

    # Scene properties
    bpy.types.Scene.flamenco_manager_url = StringProperty(
        name="Manager URL",
        description="Flamenco Manager URL (bijv. http://localhost:8080)",
        default="http://localhost:8080",
    )

    bpy.types.Scene.batch_material_library = StringProperty(
        name="Materiaalbibliotheek",
        description="Pad naar .blend bestand met materialen",
        subtype='FILE_PATH',
    )

    bpy.types.Scene.batch_material_name = StringProperty(
        name="Materiaal",
        description="Naam van het materiaal dat op de geselecteerde objecten wordt toegepast",
        default="color_material",
    )

    bpy.types.Scene.batch_output_directory = StringProperty(
        name="Output Map",
        description="Map waar gerenderde afbeeldingen worden opgeslagen",
        subtype='DIR_PATH',
    )

    bpy.types.Scene.batch_render_width = bpy.props.IntProperty(
        name="Breedte",
        default=1280, min=64, max=16384,
    )

    bpy.types.Scene.batch_render_height = bpy.props.IntProperty(
        name="Hoogte",
        default=720, min=64, max=16384,
    )

    bpy.types.Scene.batch_render_samples = bpy.props.IntProperty(
        name="Samples",
        default=128, min=1, max=10000,
    )

    bpy.types.Scene.batch_render_engine = EnumProperty(
        name="Render Engine",
        items=[
            ('CYCLES', "Cycles", "Cycles render engine"),
            ('EEVEE',  "EEVEE",  "EEVEE render engine"),
        ],
        default='CYCLES',
    )

    bpy.types.Scene.batch_open_ui_after_submit = bpy.props.BoolProperty(
        name="Open UI na verzenden",
        description="Open de Flamenco UI automatisch in de browser",
        default=True,
    )


def unregister():
    if hasattr(bpy.types.Object, 'batch_render_selected'):
        del bpy.types.Object.batch_render_selected

    for prop in [
        'flamenco_manager_url',
        'batch_material_library',
        'batch_material_name',
        'batch_output_directory',
        'batch_render_width',
        'batch_render_height',
        'batch_render_samples',
        'batch_render_engine',
        'batch_open_ui_after_submit',
    ]:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)
