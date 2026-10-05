"""Turn literal colours in the Place Lab stylesheet and components into theme variables.

Every literal becomes --c-<hex>. Light values are the originals; dark values follow the
colour's role: light surfaces become dark surfaces, dark ink becomes light text, faint dark
shadows stay shadows, and mid-tone accents are lifted for contrast on a dark ground.
Run once after adding colours; it rewrites the files in place and the palette block in place.css.
"""
import colorsys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / 'src/place.css'
COMPONENTS = ['src/place_report_view.tsx', 'src/place_history_charts.tsx', 'src/findings_app.tsx',
              'src/place_timeline_bar.tsx', 'src/place_zip_time_chart.tsx', 'src/place_toolbar.tsx']
START, END = '/* palette:start */', '/* palette:end */'
HEX = re.compile(r'#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
RGBA = re.compile(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)')


def normal(h):
    h = h.lower()
    if len(h) == 3:
        h = ''.join(c*2 for c in h)
    return h


def dark(h):
    r, g, b = (int(h[i:i+2], 16)/255 for i in (0, 2, 4))
    alpha = h[6:8]
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)
    a = int(alpha, 16)/255 if alpha else 1
    if light < .35 and a < .5:          # translucent dark ink is a shadow or hatch: keep it dark
        return '#000000' + (alpha or '')
    if light >= .72:                    # paper, cream, soft fills -> deep green-grey surfaces
        light, sat = .085 + (1-light)*.55, min(sat, .22)
    elif light <= .36:                  # ink and dark greens -> light text
        light, sat = .9 - light*.35, min(sat, .3)
    else:                               # accents: lift so they read on dark
        light = min(.74, light+.16)
    r, g, b = colorsys.hls_to_rgb(hue, light, sat)
    return '#' + ''.join(f'{round(v*255):02x}' for v in (r, g, b)) + (alpha or '')


def to_vars(text, seen, skip_hex=False):
    def rgba(m):
        r, g, b, a = m.groups()
        h = f'{int(r):02x}{int(g):02x}{int(b):02x}' + (f'{round(float(a)*255):02x}' if a else '')
        seen.add(h)
        return f'var(--c-{h})'
    def hexed(m):
        h = normal(m.group(1)); seen.add(h)
        return f'var(--c-{h})'
    text = RGBA.sub(rgba, text)
    return text if skip_hex else HEX.sub(hexed, text)


def build():
    seen = set()
    css = CSS.read_text()
    if START in css:
        css = css[:css.index(START)] + css[css.index(END)+len(END):]
    css = to_vars(css, seen)
    for rel in COMPONENTS:
        path = ROOT / rel
        path.write_text(HEX.sub(lambda m: (seen.add(normal(m.group(1))), f'var(--c-{normal(m.group(1))})')[1], path.read_text()))
    # Colours that JavaScript reads for the map canvas and text are added explicitly.
    seen.update(['e8eee9', '173c35', 'a7bba9', '6d625075', '245647b3', 'fffdf6e8', '386451', '204a3b', '445a5866',
                 '5a6d68', '465351', '86511c', '295e7e', '684779', '23767a', 'a63824', '30251d', '929d9b'])
    keys = sorted(seen)
    light = ''.join(f'--c-{k}:#{k};' for k in keys)
    darks = ''.join(f'--c-{k}:{dark(k)};' for k in keys)
    block = (f"{START}\n:root{{color-scheme:light;{light}}}\n"
             f"@media (prefers-color-scheme:dark){{:root{{color-scheme:dark;{darks}}}}}\n{END}\n")
    CSS.write_text(block + css)
    return len(keys)


if __name__ == '__main__':
    print('palette colours:', build())
