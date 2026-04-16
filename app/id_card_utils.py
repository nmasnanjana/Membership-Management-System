"""
ID card image generation utilities.

Generates a simple landscape front + back card as PNG bytes.
Design is intentionally minimal and can be refined later.
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Tuple

import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import date as _date, datetime as _datetime


@dataclass(frozen=True)
class IdCardImages:
    front_png: bytes
    back_png: bytes


def _load_font(path: str | None, size: int) -> ImageFont.ImageFont | None:
    if not path:
        return None
    try:
        if os.path.exists(path):
            # Prefer RAQM layout engine when available (better for complex scripts like Sinhala).
            layout = getattr(ImageFont, "Layout", None)
            if layout is not None and hasattr(layout, "RAQM"):
                try:
                    return ImageFont.truetype(path, size, layout_engine=layout.RAQM)
                except Exception:
                    pass
            return ImageFont.truetype(path, size)
    except Exception:
        return None
    return None


def _load_system_font(name: str, size: int) -> ImageFont.ImageFont | None:
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        return None


def _fit_font_for_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str | None,
    max_width: int,
    start_size: int,
    min_size: int,
    *,
    language: str | None = None,
) -> ImageFont.ImageFont:
    """
    Load a font (prefer RAQM if available) and reduce size until text fits max_width.
    Always returns a usable font (falls back to default).
    """
    text = text or ""
    for size in range(start_size, min_size - 1, -1):
        f = _load_font(font_path, size) if font_path else None
        if f is None:
            continue
        try:
            bbox = draw.textbbox((0, 0), text, font=f, language=language)
            w = bbox[2] - bbox[0]
        except Exception:
            # If bbox fails, assume it might fit; return the font.
            return f
        if w <= max_width:
            return f
    return ImageFont.load_default()


def _pick_sinhala_font_path() -> str | None:
    """
    Prefer Sinhala Unicode fonts that render cleanly.
    (FM Abaya is legacy non-unicode; we avoid that.)
    """
    base = os.path.join(os.path.dirname(__file__), "static", "fonts")
    candidates = [
        os.path.join(base, "AbhayaLibre-Regular.ttf"),
        os.path.join(base, "NotoSerifSinhala-Regular.ttf"),
        os.path.join(base, "NotoSansSinhala-Regular.ttf"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _format_date(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (_date, _datetime)):
        try:
            return value.strftime("%Y-%m-%d")
        except Exception:
            return str(value)
    return str(value)


def _draw_badge(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, *, r: int = 14, fill=(255, 255, 255, 255), text_fill=(31, 41, 55, 255), font=None):
    draw.ellipse((x, y, x + (r * 2), y + (r * 2)), fill=fill)
    if not label:
        return
    f = font or ImageFont.load_default()
    try:
        bb = draw.textbbox((0, 0), label, font=f)
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]
    except Exception:
        tw, th = 10, 10
    draw.text((x + r - (tw // 2), y + r - (th // 2) - 1), label, fill=text_fill, font=f)


def _safe_text(value: str | None) -> str:
    return (value or "").strip()


def _load_profile_image(path: str | None, size: Tuple[int, int]) -> Image.Image | None:
    if not path:
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img.thumbnail(size, Image.Resampling.LANCZOS)
        # Place on a fixed canvas to ensure consistent box size
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        x = (size[0] - img.size[0]) // 2
        y = (size[1] - img.size[1]) // 2
        canvas.paste(img, (x, y), img)
        return canvas
    except Exception:
        return None


def _make_qr(member_id: str, size: int) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(member_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    return img.resize((size, size), Image.Resampling.NEAREST)


def generate_member_id_card_images(
    *,
    member_id: str,
    first_name: str,
    last_name: str | None,
    initials: str | None,
    role_label: str | None,
    profile_image_path: str | None,
    dob=None,
    phone_no: str | None = None,
    guid: str | None = None,
    system_name: str = "බිබිලාදෙණිය - ස.ණ.ස ළමා සමාජය",
) -> IdCardImages:
    """
    Returns PNG bytes for front + back images.

    Landscape dimensions: 1016x638 (~credit card ratio, but larger for clarity).
    """
    W, H = 1016, 638
    bg = (255, 255, 255, 255)  # white (outer background)
    card = (55, 65, 81, 255)  # slate-700
    accent = (59, 130, 246, 255)  # blue-500
    white = (249, 250, 251, 255)
    muted = (209, 213, 219, 255)
    dark_text = (17, 24, 39, 255)
    light_border = (229, 231, 235, 255)

    # Fonts: load Sinhala title font from bundled file (do NOT depend on OS fonts).
    sinhala_font_path = _pick_sinhala_font_path()
    # We'll auto-fit the Sinhala title later against available width.

    # Other fonts: try common system fonts; fall back safely.
    font_title = _load_system_font("DejaVuSans.ttf", 42) or ImageFont.load_default()
    font_sub = _load_system_font("DejaVuSans.ttf", 24) or ImageFont.load_default()
    font_small = _load_system_font("DejaVuSans.ttf", 20) or ImageFont.load_default()
    font_id = _load_system_font("DejaVuSansMono.ttf", 34) or ImageFont.load_default()
    # back member-id font will be auto-fit later
    font_id_back = _load_system_font("DejaVuSansMono.ttf", 44) or ImageFont.load_default()

    # ---------- FRONT ----------
    front = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(front)

    # Card container
    pad = 24
    d.rounded_rectangle((pad, pad, W - pad, H - pad), radius=24, fill=card, outline=(75, 85, 99, 255), width=2)
    # Accent bar
    d.rounded_rectangle((pad, pad, W - pad, pad + 90), radius=24, fill=(30, 64, 175, 255))
    d.rectangle((pad, pad + 45, W - pad, pad + 90), fill=(30, 64, 175, 255))
    # Centered title (Sinhala)
    title = system_name
    max_title_width = (W - (pad * 2) - 48)
    try:
        # Single-line title; disable kerning to avoid reported glyph overlaps.
        font_title_si = _fit_font_for_text(
            d,
            title,
            sinhala_font_path,
            max_title_width,
            start_size=34,
            min_size=18,
            language="si",
        )
        tb = d.textbbox((0, 0), title, font=font_title_si, language="si", direction="ltr", features=["-kern"])
        tw = tb[2] - tb[0]
        th = tb[3] - tb[1]
    except Exception:
        tw, th = 400, 24
        font_title_si = font_sub
    try:
        d.text(((W - tw) // 2, pad + (90 - th) // 2), title, fill=white, font=font_title_si, language="si", direction="ltr", features=["-kern"])
    except Exception:
        # Absolute fallback: don't crash card generation if font rendering fails
        d.text((pad + 24, pad + 22), "ID Card", fill=white, font=font_sub)

    # Left: Profile box (square photo, slightly longer container)
    img_box = (pad + 24, pad + 120, pad + 24 + 300, pad + 120 + 320)
    d.rounded_rectangle(img_box, radius=18, fill=white, outline=light_border, width=2)
    profile = _load_profile_image(profile_image_path, (260, 260))
    if profile:
        front.paste(profile, (img_box[0] + 20, img_box[1] + 20), profile)
    else:
        # Placeholder
        d.text((img_box[0] + 105, img_box[1] + 145), "PHOTO", fill=dark_text, font=font_sub)

    # Right: Member text
    name_initials = " ".join([_safe_text(initials), _safe_text(first_name), _safe_text(last_name)]).strip()
    if not name_initials:
        name_initials = _safe_text(first_name) or member_id

    x0 = pad + 24 + 330
    y0 = pad + 140

    # Content block (corporate, simple labels)
    line_gap = 44
    label_w = 170

    def row(label: str, value: str):
        nonlocal y0
        d.text((x0, y0), label, fill=muted, font=font_small)
        d.text((x0 + label_w, y0), value, fill=white, font=font_sub)
        y0 += line_gap

    full_name = " ".join([_safe_text(initials), _safe_text(first_name), _safe_text(last_name)]).strip()
    if not full_name:
        full_name = _safe_text(first_name) or member_id

    row("Name:", full_name)
    row("Date of Birth:", _format_date(dob))
    row("Phone No:", _safe_text(phone_no))
    row("Member ID:", member_id)

    # (Front QR removed — back side contains QR)

    # ---------- BACK ----------
    back = Image.new("RGBA", (W, H), bg)
    d2 = ImageDraw.Draw(back)
    # Card container
    d2.rounded_rectangle((pad, pad, W - pad, H - pad), radius=24, fill=card, outline=(75, 85, 99, 255), width=2)

    # Two-tone background inside the card: top stays dark, bottom is light blue
    inner = (pad + 2, pad + 2, W - pad - 2, H - pad - 2)
    mid_y = (inner[1] + inner[3]) // 2
    # Bottom half blue (clipped to rounded corners)
    back_blue = (0, 102, 255, 255)  # #0066ff
    radius_inner = 22
    mask_bottom = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask_bottom)
    md.rounded_rectangle(inner, radius=radius_inner, fill=255)
    md.rectangle((inner[0], inner[1], inner[2], mid_y), fill=0)  # keep only bottom half
    blue_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(blue_layer).rectangle((inner[0], mid_y, inner[2], inner[3]), fill=back_blue)
    back.paste(blue_layer, (0, 0), mask_bottom)

    # QR centered (on top of all layers)
    qr = _make_qr(member_id, 360)
    bx = (W - 360) // 2
    by = pad + 105
    back.paste(qr, (bx, by), qr)

    # Member ID below QR (centered) - same size as GUID
    member_id_text = member_id
    back_id_font = font_small
    try:
        bbox = d2.textbbox((0, 0), member_id_text, font=back_id_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except Exception:
        tw, th = 200, 24
    tx = (W - tw) // 2
    d2.text((tx, by + 360 + 14), member_id_text, fill=white, font=back_id_font)

    # Footer: left property text, right GUID
    footer_y = H - pad - 52
    d2.text((pad + 24, footer_y), "This card is property of the club.", fill=white, font=font_small)
    guid_text = (guid or "").strip()
    if guid_text:
        try:
            gb = d2.textbbox((0, 0), guid_text, font=font_small)
            gw = gb[2] - gb[0]
        except Exception:
            gw = 260
        d2.text((W - pad - 24 - gw, footer_y), guid_text, fill=white, font=font_small)

    # Contact info (left: phone + whatsapp, right: email)
    contact_y = footer_y - 58
    icon_r = 13
    # Left block
    _draw_badge(d2, pad + 24, contact_y - 2, "T", r=icon_r, fill=white, text_fill=dark_text, font=font_small)
    d2.text((pad + 24 + (icon_r * 2) + 10, contact_y), "0322256755", fill=white, font=font_small)
    _draw_badge(d2, pad + 24, contact_y + 30 - 2, "W", r=icon_r, fill=white, text_fill=dark_text, font=font_small)
    d2.text((pad + 24 + (icon_r * 2) + 10, contact_y + 30), "0703488856", fill=white, font=font_small)
    # Right block
    email = "sanasabibiladeniya@gmail.com"
    try:
        eb = d2.textbbox((0, 0), email, font=font_small)
        ew = eb[2] - eb[0]
    except Exception:
        ew = 320
    right_x = W - pad - 24 - ew
    _draw_badge(d2, right_x - (icon_r * 2) - 10, contact_y + 14 - 2, "@", r=icon_r, fill=white, text_fill=dark_text, font=font_small)
    d2.text((right_x, contact_y + 14), email, fill=white, font=font_small)

    # Export bytes
    out_front = io.BytesIO()
    out_back = io.BytesIO()
    front.convert("RGBA").save(out_front, format="PNG", optimize=True)
    back.convert("RGBA").save(out_back, format="PNG", optimize=True)
    return IdCardImages(front_png=out_front.getvalue(), back_png=out_back.getvalue())

