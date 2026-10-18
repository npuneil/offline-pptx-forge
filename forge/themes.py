"""Three brand-inspired deck themes. Programmatic look-and-feel only; no official template assets."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Theme:
    key: str
    label: str
    dark: bool
    bg: str
    bg2: str
    card: str
    card_line: str
    text: str
    subtext: str
    muted: str
    primary: str
    accents: tuple
    on_accent: str
    font_head: str
    font_body: str
    font_number: str
    footer: str
    motif: str
    radius: float = 0.12
    measure: dict = field(default_factory=dict)

    def accent(self, i):
        return self.accents[i % len(self.accents)]


THEMES = {
    "microsoft": Theme(
        key="microsoft", label="Microsoft (general corporate)", dark=False,
        bg="FFFFFF", bg2="FFFFFF", card="F3F3F3", card_line="E1E1E1",
        text="1B1B1B", subtext="505050", muted="8A8A8A", primary="0078D4",
        accents=("0078D4", "107C10", "D83B01", "FFB900", "5C2D91"), on_accent="FFFFFF",
        font_head="Segoe UI Semibold", font_body="Segoe UI", font_number="Segoe UI Semibold",
        footer="Microsoft", motif="ms_squares", radius=0.06,
    ),
    "surface": Theme(
        key="surface", label="Surface (light, premium device)", dark=False,
        bg="F7F5F2", bg2="ECE8E2", card="FFFFFF", card_line="E4DFD8",
        text="141414", subtext="4A4A4A", muted="8C8780", primary="1F5FBF",
        accents=("1F5FBF", "3F8F7E", "B8742F", "6B5BD2", "C2416B"), on_accent="FFFFFF",
        font_head="Segoe UI Semibold", font_body="Segoe UI", font_number="Segoe UI Light",
        footer="Surface", motif="surface_bloom", radius=0.18,
    ),
    "surface_ultra": Theme(
        key="surface_ultra", label="Surface Ultra (dark, RTX Spark)", dark=True,
        bg="07080C", bg2="121521", card="141824", card_line="283044",
        text="F4F6FA", subtext="AEB6C8", muted="6F7890", primary="76B900",
        accents=("76B900", "3DA9FC", "9B6BFF", "FFB547", "FF5D8F"), on_accent="07080C",
        font_head="Segoe UI Semibold", font_body="Segoe UI", font_number="Segoe UI Black",
        footer="Surface Laptop Ultra  |  NVIDIA RTX Spark", motif="ultra_glow", radius=0.14,
    ),
}

FONT_FILES = {
    "Segoe UI Semibold": "seguisb.ttf",
    "Segoe UI": "segoeui.ttf",
    "Segoe UI Light": "segoeuil.ttf",
    "Segoe UI Black": "seguibl.ttf",
    "Segoe UI Bold": "segoeuib.ttf",
}


def get(key):
    if key not in THEMES:
        raise KeyError(f"Unknown template '{key}'. Choose: {', '.join(THEMES)}")
    return THEMES[key]
