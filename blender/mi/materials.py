"""Materials of the «Маҷмааи истиқоматӣ» model: the shared set (complex/materials.py, ab/materials.py)
plus block К's facades (renders 9, 10) and the white model of the blocks to come. Names are what the
web viewer looks up (src/materials.js), keep them stable."""
from complex import materials as base
from ab.materials import AB_SPECS

MI_SPECS = {
    # block К: white frame, black window frames, the dark warm brick of floor 3 and the north-west bay,
    # timber in the loggia box and some panels, warm LED lines (yellow on the renders)
    'K glass': ('#2e3a40', 0.05, 0.0, {}),
    'Brick brown': ('#6a5b55', 0.9, 0.0, {}),
    'Panel white': ('#e4e3df', 0.7, 0.0, {}),
    'Wood slat': ('#9a6a44', 0.65, 0.0, {}),
    'Deck wood': ('#8a6446', 0.8, 0.0, {}),
    'LED warm': ('#ffd27a', 0.5, 0.0, {'emission': ('#ffcf6a', 1.0)}),
    # the windows' spandrels: dark blue-grey glass (renders 9, 10)
    'Spandrel': ('#2c3644', 0.08, 0.0, {}),
    'Railing glass dark': ('#2d3d46', 0.05, 0.0, {'alpha': 0.7}),
    'Sidewalk': ('#d8d2c6', 0.9, 0.0, {}),
    # the shops' back walls: a warm grey, a little light of their own (not the bright beige of Ali Binokor)
    'Shop wall': ('#8f8272', 0.85, 0.0, {'emission': ('#ffd9a8', 0.12)}),
    # (opaque: the viewer draws the lit shops behind it, src/materials.js)
    'Shop glass': ('#3a5559', 0.03, 0.0, {}),
    # the blocks still to come: a white architectural model
    'Massing': ('#efeeea', 0.85, 0.0, {}),
    'Massing groove': ('#cfcdc7', 0.9, 0.0, {}),
    'Massing roof': ('#e2e0da', 0.9, 0.0, {}),
    'Neighbour roof': ('#b9b4ab', 0.9, 0.0, {}),
}


class Mats(dict):
    """the materials by name; a name nobody defined gets a plain grey one (and a warning)"""

    def __missing__(self, name):
        print('material not defined:', name)
        base.SPECS[name] = ('#9a9a9a', 0.8, 0.0, {})
        m = base.build_materials()[name]
        self[name] = m
        return m


def build_materials():
    base.SPECS.update(AB_SPECS)
    base.SPECS.update(MI_SPECS)
    return Mats(base.build_materials())
