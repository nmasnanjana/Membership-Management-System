"""
ID card image generation utilities.

Generates a simple landscape front + back card as PNG bytes.
Design is intentionally minimal and can be refined later.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Tuple

import qrcode
from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class IdCardImages:
    front_png: bytes
    back_png: bytes


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
    guid: str | None = None,
    system_name: str = "Membership Management System",
) -> IdCardImages:
    """
    Returns PNG bytes for front + back images.

    Landscape dimensions: 1016x638 (~credit card ratio, but larger for clarity).
    """
    W, H = 1016, 638
    bg = (31, 41, 55, 255)  # slate-800
    card = (55, 65, 81, 255)  # slate-700
    accent = (59, 130, 246, 255)  # blue-500
    white = (249, 250, 251, 255)
    muted = (209, 213, 219, 255)

    # Fonts (fallback to default if unavailable)
    try:
        font_title = ImageFont.truetype("DejaVuSans.ttf", 42)
        font_sub = ImageFont.truetype("DejaVuSans.ttf", 24)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 20)
        font_id = ImageFont.truetype("DejaVuSansMono.ttf", 34)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_id = ImageFont.load_default()

    # ---------- FRONT ----------
    front = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(front)

    # Card container
    pad = 24
    d.rounded_rectangle((pad, pad, W - pad, H - pad), radius=24, fill=card, outline=(75, 85, 99, 255), width=2)
    # Accent bar
    d.rounded_rectangle((pad, pad, W - pad, pad + 90), radius=24, fill=(30, 64, 175, 255))
    d.rectangle((pad, pad + 45, W - pad, pad + 90), fill=(30, 64, 175, 255))
    d.text((pad + 24, pad + 22), system_name, fill=white, font=font_sub)

    # Left: Profile box
    img_box = (pad + 24, pad + 120, pad + 24 + 240, pad + 120 + 300)
    d.rounded_rectangle(img_box, radius=18, fill=(17, 24, 39, 255), outline=(75, 85, 99, 255), width=2)
    profile = _load_profile_image(profile_image_path, (220, 280))
    if profile:
        front.paste(profile, (img_box[0] + 10, img_box[1] + 10), profile)
    else:
        # Placeholder
        d.text((img_box[0] + 70, img_box[1] + 130), "PHOTO", fill=muted, font=font_sub)

    # Right: Member text
    name_initials = " ".join([_safe_text(initials), _safe_text(first_name), _safe_text(last_name)]).strip()
    if not name_initials:
        name_initials = _safe_text(first_name) or member_id

    x0 = pad + 24 + 280
    y0 = pad + 140
    d.text((x0, y0), "Member ID Card", fill=white, font=font_title)
    y0 += 72
    d.text((x0, y0), name_initials, fill=white, font=font_sub)
    y0 += 44
    if role_label:
        d.text((x0, y0), f"Role: {role_label}", fill=muted, font=font_small)
        y0 += 34
    d.text((x0, y0), "Member ID", fill=muted, font=font_small)
    y0 += 28
    d.rounded_rectangle((x0, y0, x0 + 320, y0 + 64), radius=14, fill=(17, 24, 39, 255), outline=accent, width=2)
    d.text((x0 + 18, y0 + 14), member_id, fill=white, font=font_id)

    # QR on front (small)
    qr_small = _make_qr(member_id, 170)
    qx = W - pad - 24 - 170
    qy = pad + 140
    front.paste(qr_small, (qx, qy), qr_small)
    d.text((qx, qy + 178), "Scan for Member ID", fill=muted, font=font_small)

    # ---------- BACK ----------
    back = Image.new("RGBA", (W, H), bg)
    d2 = ImageDraw.Draw(back)
    # Card container
    d2.rounded_rectangle((pad, pad, W - pad, H - pad), radius=24, fill=card, outline=(75, 85, 99, 255), width=2)

    # Two-tone background inside the card: top stays dark, bottom is light blue
    inner = (pad + 2, pad + 2, W - pad - 2, H - pad - 2)
    mid_y = (inner[1] + inner[3]) // 2
    # Bottom half light blue (keep rounded corners by drawing over existing fill)
    light_blue = (186, 230, 253, 255)  # sky-200
    d2.rectangle((inner[0], mid_y, inner[2], inner[3]), fill=light_blue)

    # QR centered (on top of all layers)
    qr = _make_qr(member_id, 360)
    bx = (W - 360) // 2
    by = pad + 105
    back.paste(qr, (bx, by), qr)

    # Member ID below QR (centered)
    member_id_text = member_id
    try:
        bbox = d2.textbbox((0, 0), member_id_text, font=font_id)
        tw = bbox[2] - bbox[0]
    except Exception:
        tw = 200
    tx = (W - tw) // 2
    d2.text((tx, by + 360 + 18), member_id_text, fill=(17, 24, 39, 255), font=font_id)

    # Footer: left property text, right GUID
    footer_y = H - pad - 52
    d2.text((pad + 24, footer_y), "This card is property of the club.", fill=(17, 24, 39, 255), font=font_small)
    guid_text = (guid or "").strip()
    if guid_text:
        try:
            gb = d2.textbbox((0, 0), guid_text, font=font_small)
            gw = gb[2] - gb[0]
        except Exception:
            gw = 260
        d2.text((W - pad - 24 - gw, footer_y), guid_text, fill=(17, 24, 39, 255), font=font_small)

    # Export bytes
    out_front = io.BytesIO()
    out_back = io.BytesIO()
    front.convert("RGBA").save(out_front, format="PNG", optimize=True)
    back.convert("RGBA").save(out_back, format="PNG", optimize=True)
    return IdCardImages(front_png=out_front.getvalue(), back_png=out_back.getvalue())

