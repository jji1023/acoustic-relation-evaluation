"""Render a neutral SVG interval plot from caller-supplied numerical values."""

from html import escape


def interval_svg(rows, axis_label):
    """Rows are (label, point, low, high) in proportion units."""
    rows = list(rows)
    if not rows:
        raise ValueError("At least one plot row is required")
    height = 60 + 28 * len(rows)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 580 {height}">',
           '<rect width="100%" height="100%" fill="white"/>']
    for number, (label, point, low, high) in enumerate(rows):
        if not (0 <= low <= high <= 1 and 0 <= point <= 1):
            raise ValueError("Plot requires proportions and ordered interval bounds")
        y = 24 + number * 28
        x_low, x_high, x_point = (176 + 380 * value for value in (low, high, point))
        svg.extend([f'<text x="6" y="{y + 4}" font-size="12">{escape(label)}</text>',
                    f'<line x1="{x_low:.4f}" x2="{x_high:.4f}" y1="{y}" y2="{y}" stroke="#154b70"/>',
                    f'<circle cx="{x_point:.4f}" cy="{y}" r="3.5" fill="#154b70"/>'])
    axis_y = height - 38
    svg.append(f'<path d="M176 {axis_y} H556" stroke="black" fill="none"/>')
    for x, tick in ((176, "0%"), (366, "50%"), (556, "100%")):
        svg.append(f'<text x="{x}" y="{axis_y+13}" text-anchor="middle" font-size="10">{tick}</text>')
    svg.append(f'<text x="366" y="{height-6}" text-anchor="middle" font-size="12">{escape(axis_label)}</text>')
    return "\n".join([*svg, "</svg>"]) + "\n"
