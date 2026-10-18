"""Infographic layout library. Every layout draws native, editable PowerPoint shapes."""
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.util import Pt

from .draw import E, mix, polar, rgb, words

AREA = (0.6, 2.0, 12.13, 4.75)
MS_COLORS = ("F25022", "7FBA00", "00A4EF", "FFB900")


def items(d, key, hi, fields=("label", "detail", "icon")):
    v = d.get(key) or []
    if isinstance(v, dict):
        v = list(v.values())
    if not isinstance(v, list):
        v = [v]
    out = []
    for x in v[:hi]:
        if isinstance(x, dict):
            out.append(x)
        else:
            out.append({fields[0]: str(x)})
    return out


def g(x, *keys, default=""):
    for k in keys:
        if isinstance(x, dict) and x.get(k) not in (None, ""):
            return x[k]
    return default


def num(v, default=0.0):
    try:
        if isinstance(v, str):
            v = v.replace(",", "").strip().split(" ")[0].rstrip("%")
        return float(v)
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------------------------
def stack(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    layers = items(d, "layers", 6)
    side = g(d, "side_label", "bracket")
    n = max(1, len(layers))
    bw = w - (2.0 if side else 0)
    gap = 0.14
    bh = min(1.05, (h - gap * (n - 1)) / n)
    y0 = y + (h - (n * bh + (n - 1) * gap)) / 2
    for i, L in enumerate(layers):
        yy = y0 + i * (bh + gap)
        col = t.accent(i)
        inset = 0.18 * i if d.get("taper") else 0
        c.box(x + inset, yy, bw - 2 * inset, bh, fill=t.card,
              line=mix(col, t.card, 0.55) if t.dark else t.card_line, shadow=True)
        s = bh - 0.2
        c.box(x + inset + 0.1, yy + 0.1, s, s, fill=col, radius=min(0.12, s / 3), glow=(col, 8, 35) if t.dark else None)
        c.icon(x + inset + 0.1 + s * 0.18, yy + 0.1 + s * 0.18, s * 0.64, g(L, "icon", default="layers"), t.on_accent)
        lx = x + inset + bh + 0.12
        c.text(lx, yy + 0.08, 3.3, bh - 0.16, g(L, "label", "name"), size=21, font=t.font_head, anchor="m", role="label")
        c.text(lx + 3.45, yy + 0.08, bw - 2 * inset - (lx - x - inset) - 3.65, bh - 0.16, g(L, "detail", "desc"),
               size=16, color=t.subtext, anchor="m", role="detail")
    if side:
        sx = x + bw + 0.3
        total = n * bh + (n - 1) * gap
        c.box(sx, y0, 0.08, total, fill=t.primary, shape="rect", glow=(t.primary, 10, 50) if t.dark else None)
        c.box(sx + 0.25, y0 + total / 2 - 0.75, 1.45, 1.5, fill=mix(t.primary, t.bg, 0.85 if not t.dark else 0.75),
              line=t.primary, line_w=1.25)
        c.text(sx + 0.33, y0 + total / 2 - 0.7, 1.29, 1.4, side, size=17, font=t.font_head, color=t.text,
               align="c", anchor="m", role="label")


def flow(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    steps = items(d, "steps", 6)
    n = max(1, len(steps))
    gap = 0.55
    cw = (w - gap * (n - 1)) / n
    ch = min(h - 0.1, 4.1)
    y0 = y + (h - ch) / 2
    for i, s in enumerate(steps):
        xx = x + i * (cw + gap)
        col = t.accent(i)
        c.box(xx, y0 + 0.5, cw, ch - 0.5, fill=t.card, line=mix(col, t.card, 0.5) if t.dark else t.card_line, shadow=True)
        c.badge(xx + cw / 2, y0 + 0.5, 1.0, g(s, "icon", default="arrow"), fill=col, glow=(col, 10, 45))
        c.text(xx + 0.2, y0 + 1.12, cw - 0.4, 0.3, f"{i + 1:02d}", size=12, color=col, font=t.font_head,
               align="c", role="ornament")
        c.text(xx + 0.18, y0 + 1.45, cw - 0.36, 0.95, g(s, "label", "name"), size=20, font=t.font_head,
               align="c", anchor="m", role="label")
        c.text(xx + 0.2, y0 + 2.45, cw - 0.4, ch - 2.6, g(s, "detail", "desc"), size=15, color=t.subtext,
               align="c", role="detail")
        if i < n - 1:
            c.box(xx + cw + 0.15, y0 + 0.5 + (ch - 0.5) / 2 - 0.22, 0.25, 0.44, fill=t.muted, shape="chevron")


def hub(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    center = d.get("center") or {"label": g(d, "hub", default="Local AI"), "icon": "ai"}
    if isinstance(center, str):
        center = {"label": center, "icon": "ai"}
    spokes = items(d, "spokes", 8)
    n = max(1, len(spokes))
    cx, cy = x + w / 2, y + h / 2
    rx, ry = w / 2 - 1.5, h / 2 - 0.45
    nw, nh = 2.75, 0.82
    pts = [polar(cx, cy, rx, ry, i, n) for i in range(n)]
    for px, py in pts:
        c.line(cx, cy, px, py, color=mix(t.primary, t.bg, 0.45), width=1.75, dash=True)
    D = 2.15
    c.box(cx - D / 2 - 0.22, cy - D / 2 - 0.22, D + 0.44, D + 0.44, fill=t.primary, shape="ellipse", alpha=14)
    c.box(cx - D / 2, cy - D / 2, D, D, fill=t.primary, shape="ellipse", glow=(t.primary, 18, 45) if t.dark else None,
          shadow=True)
    c.icon(cx - 0.42, cy - 0.78, 0.84, g(center, "icon", default="ai"), t.on_accent)
    c.text(cx - D / 2 + 0.2, cy + 0.08, D - 0.4, 0.75, g(center, "label", "name"), size=18, font=t.font_head,
           color=t.on_accent, align="c", anchor="t", role="label")
    for i, (s, (px, py)) in enumerate(zip(spokes, pts)):
        col = t.accent(i + 1)
        c.box(px - nw / 2, py - nh / 2, nw, nh, fill=t.card, line=mix(col, t.card, 0.4) if t.dark else t.card_line,
              shadow=True, radius=nh / 2)
        c.badge(px - nw / 2 + nh / 2, py, nh - 0.16, g(s, "icon", default="idea"), fill=col)
        c.text(px - nw / 2 + nh + 0.02, py - nh / 2 + 0.06, nw - nh - 0.14, nh - 0.12, g(s, "label", "name"),
               size=15, font=t.font_head, anchor="m", role="label")


def compare(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    left = d.get("left") or {}
    right = d.get("right") or {}
    verdict = g(d, "verdict", "conclusion")
    vh = 0.78 if verdict else 0
    pw = (w - 1.0) / 2
    ph = h - vh - (0.22 if verdict else 0)
    for side, xx, hi in ((left, x, False), (right, x + pw + 1.0, True)):
        col = t.primary if hi else t.muted
        c.box(xx, y, pw, ph, fill=t.card, line=t.primary if hi else (t.card_line if not t.dark else "2A3142"),
              line_w=2.25 if hi else 1, shadow=True, glow=(t.primary, 10, 30) if (hi and t.dark) else None)
        c.badge(xx + 0.65, y + 0.62, 0.82, g(side, "icon", default="laptop" if hi else "cloud"), fill=col)
        c.text(xx + 1.2, y + 0.22, pw - 1.4, 0.8, g(side, "title", "label"), size=23, font=t.font_head,
               anchor="m", role="label")
        pts = items(side, "points", 5)
        rows = max(3, len(pts))
        rh = (ph - 1.45) / rows
        for j, p in enumerate(pts):
            ry = y + 1.3 + j * rh
            c.icon(xx + 0.45, ry + rh / 2 - 0.17, 0.34, g(p, "icon", default="check" if hi else "pin"),
                   t.primary if hi else t.muted)
            c.text(xx + 0.95, ry, pw - 1.2, rh, g(p, "label", "text"), size=17, color=t.text if hi else t.subtext,
                   anchor="m", role="detail")
    c.box(x + pw + 0.1, y + ph / 2 - 0.4, 0.8, 0.8, fill=t.text, shape="ellipse")
    c.text(x + pw + 0.1, y + ph / 2 - 0.4, 0.8, 0.8, "VS", size=16, font=t.font_head, color=t.bg, align="c",
           anchor="m", role="ornament")
    if verdict:
        vy = y + ph + 0.22
        c.box(x, vy, w, vh, fill=t.primary, glow=(t.primary, 10, 35) if t.dark else None)
        c.icon(x + 0.3, vy + vh / 2 - 0.22, 0.44, g(d, "verdict_icon", default="star"), t.on_accent)
        c.text(x + 0.95, vy + 0.06, w - 1.2, vh - 0.12, verdict, size=20, font=t.font_head, color=t.on_accent,
               anchor="m", role="takeaway")


def kpis(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    its = items(d, "items", 4, fields=("value",))
    n = max(1, len(its))
    gap = 0.35
    cw = (w - gap * (n - 1)) / n
    ch = min(h, 3.9)
    y0 = y + (h - ch) / 2
    for i, it in enumerate(its):
        xx = x + i * (cw + gap)
        col = t.accent(i)
        c.box(xx, y0, cw, ch, fill=t.card, line=mix(col, t.card, 0.5) if t.dark else t.card_line, shadow=True)
        c.box(xx, y0, cw, 0.09, fill=col, shape="rect")
        c.badge(xx + 0.7, y0 + 0.75, 0.78, g(it, "icon", default="chart"), fill=col, glow=(col, 8, 40))
        c.text(xx + 0.3, y0 + 1.3, cw - 0.6, 1.35, g(it, "value", "number"), size=60, font=t.font_number,
               color=col if not (t.key == "microsoft" and col == "FFB900") else t.text, anchor="m", role="value")
        c.text(xx + 0.3, y0 + 2.65, cw - 0.6, 0.8, g(it, "label", "caption"), size=17, anchor="t", role="label")
        src = g(it, "source", "footnote")
        if src:
            c.text(xx + 0.3, y0 + ch - 0.45, cw - 0.6, 0.35, src, size=10, color=t.muted, role="source")


def analogy(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    concept = d.get("concept") or {}
    analog = d.get("analog") or d.get("analogy") or {}
    if isinstance(concept, str):
        concept = {"label": concept}
    if isinstance(analog, str):
        analog = {"label": analog}
    pairs = items(d, "pairs", 4, fields=("concept",))
    lc, rc = t.primary, t.accent(2)
    colw = (w - 1.5) / 2
    # header
    c.badge(x + 0.6, y + 0.55, 1.05, g(concept, "icon", default="ai"), fill=lc, glow=(lc, 12, 45))
    c.text(x + 1.3, y + 0.1, colw - 1.35, 0.9, g(concept, "label", "name"), size=24, font=t.font_head,
           anchor="m", role="label")
    c.badge(x + w - 0.6, y + 0.55, 1.05, g(analog, "icon", default="home"), fill=rc, glow=(rc, 12, 45))
    c.text(x + colw + 1.5, y + 0.1, colw - 1.35, 0.9, g(analog, "label", "name"), size=24, font=t.font_head,
           align="r", anchor="m", role="label")
    c.text(x + colw, y + 0.25, 1.5, 0.6, "is like", size=16, color=t.muted, align="c", anchor="m", italic=True,
           role="ornament")
    n = max(1, len(pairs))
    top = y + 1.4
    rh = min(0.92, (y + h - top - 0.12 * (n - 1)) / n)
    for j, p in enumerate(pairs):
        ry = top + j * (rh + 0.12)
        c.box(x, ry, colw, rh, fill=mix(lc, t.bg, 0.88) if not t.dark else t.card, line=lc, line_w=1.25,
              radius=rh / 2)
        c.text(x + 0.3, ry + 0.04, colw - 0.6, rh - 0.08, g(p, "concept", "left", "from"), size=17,
               anchor="m", align="c", role="detail")
        c.line(x + colw + 0.08, ry + rh / 2, x + colw + 1.42, ry + rh / 2, color=t.muted, width=2, arrow=True, dash=True)
        c.box(x + colw + 1.5, ry, colw, rh, fill=mix(rc, t.bg, 0.86) if not t.dark else t.card, line=rc,
              line_w=1.25, radius=rh / 2)
        c.text(x + colw + 1.8, ry + 0.04, colw - 0.6, rh - 0.08, g(p, "analog", "right", "to"), size=17,
               anchor="m", align="c", role="detail")


def bars(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    data = [b for b in items(d, "bars", 8, fields=("label",)) if g(b, "label")]
    unit = g(d, "unit")
    hl = str(g(d, "highlight"))
    cats = [str(g(b, "label")) for b in data] or ["n/a"]
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("Series", [num(g(b, "value")) for b in data] or [0])
    cwid = w * 0.64
    gf = c.slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, E(x), E(y), E(cwid), E(h), cd)
    ch = gf.chart
    ch.has_legend = False
    ch.font.size = Pt(15)
    ch.font.name = t.font_body
    ch.font.color.rgb = rgb(t.text)
    plot = ch.plots[0]
    plot.gap_width = 55
    plot.vary_by_categories = False
    ser = plot.series[0]
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = rgb(mix(t.muted, t.bg, 0.35))
    for i, b in enumerate(data):
        if str(g(b, "label")) == hl or (not hl and i == 0):
            pt = ser.points[i]
            pt.format.fill.solid()
            pt.format.fill.fore_color.rgb = rgb(t.primary)
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.font.size = Pt(15)
    dl.font.bold = True
    dl.font.color.rgb = rgb(t.text)
    vals = [num(g(b, "value")) for b in data]
    decimals = 0 if all(float(v).is_integer() for v in vals) else (1 if all(float(v * 10).is_integer() for v in vals) else 2)
    dl.number_format = ('#,##0' + ('.' + '0' * decimals if decimals else '')) + (f'" {unit}"' if unit else "")
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    ch.has_title = False
    va = ch.value_axis
    va.visible = False
    va.has_major_gridlines = False
    if vals and max(vals) > 0:
        va.minimum_scale = 0
        va.maximum_scale = max(vals) * 1.3
    ca = ch.category_axis
    ca.format.line.fill.background()
    ca.tick_labels.font.size = Pt(15)
    ca.tick_labels.font.color.rgb = rgb(t.text)
    try:
        ca.reverse_order = True
    except AttributeError:
        pass
    c.report.text(c.index, "label", " ".join(cats), 15, 15, False)
    # callout
    cx = x + cwid + 0.3
    cw = w - cwid - 0.3
    c.box(cx, y + 0.2, cw, h - 0.4, fill=t.card, line=t.card_line if not t.dark else mix(t.primary, t.card, 0.5),
          shadow=True)
    top = next((b for b in data if str(g(b, "label")) == hl), data[0] if data else {"value": "", "label": ""})
    c.badge(cx + 0.7, y + 0.95, 0.85, g(d, "icon", default="speed"), fill=t.primary, glow=(t.primary, 10, 40))
    val = g(top, "value")
    if isinstance(val, (int, float)) or str(val).replace('.', '', 1).isdigit():
        fv = num(val)
        vtxt = f"{fv:,.0f}" if float(fv).is_integer() else f"{fv:,.2f}".rstrip("0").rstrip(".")
    else:
        vtxt = str(val)
    c.text(cx + 0.35, y + 1.55, cw - 0.7, 1.1, vtxt, size=54, font=t.font_number, color=t.primary, role="value")
    c.text(cx + 0.35, y + 2.6, cw - 0.7, 0.4, f"{unit}  |  {g(top, 'label')}".strip(" |"), size=14, color=t.subtext,
           role="label")
    c.text(cx + 0.35, y + 3.1, cw - 0.7, h - 3.45, g(d, "caption"), size=15, color=t.text, role="detail")


def timeline(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    ms = items(d, "milestones", 6, fields=("label",))
    n = max(1, len(ms))
    ly = y + h / 2
    c.box(x + 0.2, ly - 0.035, w - 0.4, 0.07, fill=t.muted if not t.dark else mix(t.primary, t.bg, 0.5), shape="rect")
    cw = min(2.9, 2 * (w - 0.6) / n - 0.25)
    for i, m in enumerate(ms):
        px = x + 0.3 + (w - 0.6) * (i + 0.5) / n
        col = t.accent(i)
        up = i % 2 == 0
        cy0 = ly - 0.42 - 1.5 if up else ly + 0.42
        c.line(px, ly, px, cy0 + (1.5 if up else 0), color=col, width=1.5)
        c.box(px - 0.2, ly - 0.2, 0.4, 0.4, fill=col, shape="ellipse", glow=(col, 10, 50) if t.dark else None)
        c.box(px - cw / 2, cy0, cw, 1.5, fill=t.card, line=mix(col, t.card, 0.4) if t.dark else t.card_line, shadow=True)
        c.icon(px - cw / 2 + 0.15, cy0 + 0.15, 0.4, g(m, "icon", default="calendar"), col)
        c.text(px - cw / 2 + 0.62, cy0 + 0.12, cw - 0.75, 0.45, g(m, "when", "date"), size=15, font=t.font_head,
               color=col, anchor="m", role="label")
        c.text(px - cw / 2 + 0.15, cy0 + 0.62, cw - 0.3, 0.8, g(m, "label", "event"), size=15, role="detail")


def matrix(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    qs = items(d, "quadrants", 4)
    while len(qs) < 4:
        qs.append({"label": ""})
    hl = int(num(d.get("highlight"), 1))
    gx, gy, gw, gh = x + 0.55, y, w - 0.55, h - 0.5
    c.line(gx - 0.25, gy + gh, gx - 0.25, gy, color=t.muted, width=2, arrow=True)
    c.line(gx, gy + gh + 0.22, gx + gw, gy + gh + 0.22, color=t.muted, width=2, arrow=True)
    c.text(gx, gy + gh + 0.27, gw, 0.3, g(d, "x_axis") + "  \u2192", size=13, color=t.subtext, align="r", role="label")
    c.text(gx, gy - 0.02, 4, 0.28, g(d, "y_axis"), size=13, color=t.subtext, role="label")
    qw, qh = (gw - 0.15) / 2, (gh - 0.45) / 2
    for i, q in enumerate(qs[:4]):
        qx = gx + (i % 2) * (qw + 0.15)
        qy = gy + 0.35 + (i // 2) * (qh + 0.15)
        on = i == hl
        col = t.accent(i)
        c.box(qx, qy, qw, qh, fill=t.primary if on else t.card, line=None if on else t.card_line, shadow=True,
              glow=(t.primary, 12, 40) if (on and t.dark) else None)
        c.icon(qx + 0.25, qy + 0.25, 0.5, g(q, "icon", default="idea"), t.on_accent if on else col)
        c.text(qx + 0.9, qy + 0.2, qw - 1.1, 0.6, g(q, "label", "name"), size=20, font=t.font_head,
               color=t.on_accent if on else t.text, anchor="m", role="label")
        c.text(qx + 0.25, qy + 0.9, qw - 0.5, qh - 1.0, g(q, "detail", "desc"), size=15,
               color=t.on_accent if on else t.subtext, role="detail")


def memory(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    cap = num(d.get("capacity"), 0) or 1.0
    unit = g(d, "unit", default="GB")
    blocks = items(d, "blocks", 6)
    sizes = [max(0.0, num(g(b, "size", "value"))) for b in blocks]
    used = sum(sizes)
    scale = 1.0
    if used > cap:
        scale = cap / used
        c.report.issue(c.index, "memory_overcommit", f"{used:g} > {cap:g}")
    c.text(x, y, 6, 0.6, f"{cap:,.0f} {unit}", size=34, font=t.font_number, color=t.primary, role="value")
    c.text(x + 3.2, y + 0.12, w - 3.2, 0.5, g(d, "capacity_label", default="available budget"), size=15,
           color=t.subtext, anchor="m", role="label")
    by, bh = y + 1.35, 1.25
    c.box(x, by, w, bh, fill=t.card, line=t.card_line if not t.dark else "2A3142", radius=0.12)
    cx = x
    for i, (b, s) in enumerate(zip(blocks, sizes)):
        bw = w * s * scale / cap
        if bw <= 0.02:
            continue
        col = t.accent(i)
        c.box(cx + 0.03, by + 0.06, bw - 0.06, bh - 0.12, fill=col, radius=0.1, glow=(col, 6, 35) if t.dark else None)
        lbl = g(b, "label", "name")
        if bw > 1.6:
            c.text(cx + 0.12, by + 0.12, bw - 0.24, 0.55, lbl, size=15, font=t.font_head, color=t.on_accent, role="label")
            c.text(cx + 0.12, by + 0.68, bw - 0.24, 0.45, f"{s:g} {unit}", size=14, color=t.on_accent, role="value")
        else:
            ly = by - 0.65 if i % 2 == 0 else by + bh + 0.08
            c.line(cx + bw / 2, by if i % 2 == 0 else by + bh, cx + bw / 2, ly + (0.6 if i % 2 == 0 else 0), color=col)
            c.text(cx + bw / 2 - 1.1, ly, 2.2, 0.6, f"{lbl} {s:g} {unit}", size=13, align="c", role="label")
        cx += bw
    free = cap - used * scale
    if free > 0.01 * cap:
        fw = w * free / cap
        c.box(cx + 0.03, by + 0.06, fw - 0.06, bh - 0.12, line=t.muted, dash=True, radius=0.1)
        if fw > 1.4:
            c.text(cx + 0.15, by + 0.3, fw - 0.3, 0.6, f"Headroom {free:,.1f} {unit}", size=15, color=t.subtext,
                   align="c", anchor="m", role="label")
    for k in range(5):
        tx = x + w * k / 4
        c.line(tx, by + bh + 0.75, tx, by + bh + 0.9, color=t.muted, width=1)
        c.text(tx - 0.6, by + bh + 0.92, 1.2, 0.3, f"{cap * k / 4:,.0f}", size=11, color=t.muted, align="c",
               role="ornament")
    cap_txt = g(d, "caption")
    if cap_txt:
        c.icon(x, y + h - 0.55, 0.42, "memory", t.primary)
        c.text(x + 0.55, y + h - 0.6, w - 0.6, 0.55, cap_txt, size=16, color=t.subtext, anchor="m", role="detail")


def cta(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    steps = items(d, "steps", 4)
    ask = g(d, "ask", "call_to_action")
    n = max(1, len(steps))
    gap = 0.3
    cw = (w - gap * (n - 1)) / n
    ch = h - 1.55 if ask else h
    for i, s in enumerate(steps):
        xx = x + i * (cw + gap)
        col = t.accent(i)
        c.box(xx, y, cw, ch, fill=t.card, line=mix(col, t.card, 0.5) if t.dark else t.card_line, shadow=True)
        c.box(xx + 0.3, y + 0.3, 0.7, 0.7, fill=col, shape="ellipse", glow=(col, 8, 40) if t.dark else None)
        c.text(xx + 0.3, y + 0.3, 0.7, 0.7, str(i + 1), size=22, font=t.font_head, color=t.on_accent, align="c",
               anchor="m", role="ornament")
        c.icon(xx + cw - 0.8, y + 0.38, 0.52, g(s, "icon", default="check"), col)
        c.text(xx + 0.3, y + 1.15, cw - 0.6, 0.85, g(s, "label", "name"), size=20, font=t.font_head, role="label")
        c.text(xx + 0.3, y + 2.0, cw - 0.6, ch - 2.15, g(s, "detail", "desc"), size=15, color=t.subtext, role="detail")
    if ask:
        ay = y + h - 1.25
        c.box(x, ay, w, 1.25, fill=t.primary, glow=(t.primary, 14, 40) if t.dark else None,
              gradient=(t.primary, mix(t.primary, t.accent(1), 0.6)) if not t.key == "microsoft" else None,
              gradient_angle=0)
        c.icon(x + 0.4, ay + 0.35, 0.55, g(d, "ask_icon", default="flag"), t.on_accent)
        c.text(x + 1.2, ay + 0.12, w - 1.5, 1.0, ask, size=24, font=t.font_head, color=t.on_accent, anchor="m",
               role="takeaway")


def statement(c, d, area=AREA):
    x, y, w, h = area
    t = c.t
    c.badge(x + w / 2, y + 0.75, 1.3, g(d, "icon", default="idea"), fill=t.primary, glow=(t.primary, 18, 50))
    c.text(x + 0.8, y + 1.65, w - 1.6, 1.8, g(d, "text", "statement", "headline"), size=40, font=t.font_head,
           align="c", anchor="m", role="label")
    sub = g(d, "sub", "subtext")
    if sub:
        c.text(x + 1.5, y + 3.55, w - 3.0, 0.9, sub, size=18, color=t.subtext, align="c", role="detail")


TONES = ("primary", "accent1", "accent2", "accent3", "accent4", "muted", "card", "text")


def _tone(t, tone):
    tone = str(tone or "card").lower()
    if tone == "primary":
        return t.primary, t.on_accent
    if tone.startswith("accent"):
        k = int(num(tone[6:], 1))
        return t.accent(k), t.on_accent
    if tone == "muted":
        return mix(t.muted, t.bg, 0.2), t.on_accent if t.dark else "FFFFFF"
    if tone == "text":
        return t.text, t.bg
    return t.card, t.text


def canvas(c, d, area=AREA):
    """Free-form infographic DSL on a 12x6 grid: box|pill|circle|arrow|line|text|icon."""
    x, y, w, h = area
    t = c.t
    gx, gy = w / 12.0, h / 6.0
    els = d.get("elements") or []
    if not isinstance(els, list):
        els = []
    def P(px, py):
        return x + max(0, min(12, num(px))) * gx, y + max(0, min(6, num(py))) * gy
    order = sorted(range(len(els[:40])), key=lambda i: 0 if str(els[i].get("type", "")).lower() in ("arrow", "line") else 1)
    for i in order:
        e = els[i] if isinstance(els[i], dict) else {}
        typ = str(e.get("type", "box")).lower()
        ex, ey = P(e.get("x", 0), e.get("y", 0))
        ew = max(0.3, min(12, num(e.get("w"), 2))) * gx
        eh = max(0.3, min(6, num(e.get("h"), 1))) * gy
        fill, fg = _tone(t, e.get("tone"))
        label = g(e, "label", "text")
        if typ in ("arrow", "line"):
            x2, y2 = P(e.get("x2", num(e.get("x", 0)) + 2), e.get("y2", e.get("y", 0)))
            c.line(ex, ey, x2, y2, color=fill if e.get("tone") else t.muted, width=2.25, arrow=typ == "arrow",
                   dash=bool(e.get("dashed")))
            if label:
                c.text((ex + x2) / 2 - 1.1, (ey + y2) / 2 - 0.42, 2.2, 0.36, label, size=12, color=t.subtext,
                       align="c", role="detail")
        elif typ == "text":
            size = {"s": 14, "m": 20, "l": 30, "xl": 44}.get(str(e.get("size", "m")).lower(), 20)
            c.text(ex, ey, ew, eh, label, size=size, font=t.font_head if size >= 20 else t.font_body,
                   color=t.text if e.get("tone") in (None, "card", "text") else fill, align=str(e.get("align", "l"))[0],
                   role="label" if size >= 20 else "detail")
        elif typ == "icon":
            c.icon(ex, ey, min(ew, eh), e.get("icon", "idea"), fill if e.get("tone") not in (None, "card") else t.primary)
        else:
            shape = {"circle": "ellipse", "pill": "rounded", "box": "rounded", "hexagon": "hexagon",
                     "chevron": "chevron"}.get(typ, "rounded")
            rad = min(ew, eh) / 2 if typ == "pill" else None
            c.box(ex, ey, ew, eh, fill=fill, line=t.card_line if fill == t.card else None, shape=shape, radius=rad,
                  shadow=True, glow=(fill, 8, 35) if (t.dark and fill != t.card) else None)
            pad = 0.12
            if e.get("icon"):
                isz = min(0.55, eh * 0.55)
                if label:
                    c.icon(ex + pad + 0.05, ey + eh / 2 - isz / 2, isz, e["icon"], fg)
                    c.text(ex + isz + 0.3, ey + pad, ew - isz - 0.4, eh - 2 * pad, label, size=16, font=t.font_head,
                           color=fg, anchor="m", role="label")
                else:
                    c.icon(ex + ew / 2 - isz / 2, ey + eh / 2 - isz / 2, isz, e["icon"], fg)
            elif label:
                c.text(ex + pad, ey + pad, ew - 2 * pad, eh - 2 * pad, label, size=16, font=t.font_head, color=fg,
                       align="c", anchor="m", role="label")


LAYOUTS = {
    "stack": stack, "flow": flow, "hub": hub, "compare": compare, "kpis": kpis, "analogy": analogy,
    "bars": bars, "timeline": timeline, "matrix": matrix, "memory": memory, "cta": cta,
    "statement": statement, "canvas": canvas,
}
INFOGRAPHIC = set(LAYOUTS) - {"statement"}
