#!/usr/bin/env python3
"""Photo restoration for the Ubaldo Rizzo catalogue.

Pipeline (sculptures):  Real-ESRGAN x4 upscaling -> BiRefNet cut-out -> white balance from the
original wall/cloth -> gentle tone curve -> composite on a seamless studio backdrop with a soft
contact shadow.  Flat works (paintings, reliefs) are only upscaled and tone-corrected.
Nothing is generated: every pixel of the sculpture comes from the original photograph.
Usage: python3 enhance.py IN_DIR OUT_DIR [names...]
"""
import sys, os, time
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image, ImageFilter, ImageOps

torch.set_num_threads(os.cpu_count() or 2)
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------- Real-ESRGAN compact model (SRVGGNetCompact) ----------
class SRVGGNetCompact(nn.Module):
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        self.body = nn.ModuleList([nn.Conv2d(num_in_ch, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)])
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1)); self.body.append(nn.PReLU(num_parameters=num_feat))
        self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
        self.upsampler = nn.PixelShuffle(upscale)
    def forward(self, x):
        out = x
        for m in self.body: out = m(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode="nearest")

_sr = None
def sr_model():
    global _sr
    if _sr is None:
        m = SRVGGNetCompact()
        sd = torch.load(os.path.join(HERE, "models/realesr-general-x4v3.pth"), map_location="cpu", weights_only=True)
        m.load_state_dict(sd.get("params", sd), strict=True); m.eval(); _sr = m
    return _sr

def upscale(img, tile=256):
    x = torch.from_numpy(np.asarray(img.convert("RGB")).astype(np.float32) / 255.).permute(2, 0, 1)[None]
    _, _, h, w = x.shape; s = 4; pad = 12
    out = torch.zeros(1, 3, h * s, w * s)
    with torch.inference_mode():
        for y0 in range(0, h, tile):
            for x0 in range(0, w, tile):
                y1, x1 = min(y0 + tile, h), min(x0 + tile, w)
                ya, xa, yb, xb = max(y0 - pad, 0), max(x0 - pad, 0), min(y1 + pad, h), min(x1 + pad, w)
                o = sr_model()(x[:, :, ya:yb, xa:xb])
                out[:, :, y0*s:y1*s, x0*s:x1*s] = o[:, :, (y0-ya)*s:(y0-ya)*s + (y1-y0)*s, (x0-xa)*s:(x0-xa)*s + (x1-x0)*s]
    a = out.clamp(0, 1)[0].permute(1, 2, 0).numpy() * 255
    lz = np.asarray(img.convert("RGB").resize((w * s, h * s), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))).astype(np.float32)
    return Image.fromarray(np.clip(0.55 * a + 0.45 * lz, 0, 255).round().astype(np.uint8))

# ---------- segmentation ----------
_seg = None
def cutout_mask(img):
    """IS-Net saliency mask, refined with GrabCut and a guided filter on the full-resolution image."""
    global _seg
    import cv2
    from rembg import new_session, remove
    if _seg is None: _seg = new_session("isnet-general-use")
    small = img.copy(); small.thumbnail((1024, 1024))
    prob = np.asarray(remove(small, session=_seg, only_mask=True).convert("L").resize(img.size, Image.BILINEAR)).astype(np.float32) / 255.
    work = img.copy(); work.thumbnail((1400, 1400)); ws = work.size
    p = cv2.resize(prob, ws)
    a = cv2.cvtColor(np.asarray(work), cv2.COLOR_RGB2BGR)
    gc = np.full(p.shape, cv2.GC_PR_BGD, np.uint8)
    gc[p > 0.35] = cv2.GC_PR_FGD
    k = max(3, int(min(ws) * 0.012)) | 1
    gc[cv2.erode((p > 0.85).astype(np.uint8), np.ones((k, k), np.uint8)) > 0] = cv2.GC_FGD
    gc[cv2.dilate((p > 0.08).astype(np.uint8), np.ones((k * 4 + 1, k * 4 + 1), np.uint8)) == 0] = cv2.GC_BGD
    if (gc == cv2.GC_FGD).sum() > 50:
        bgm, fgm = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        cv2.grabCut(a, gc, None, bgm, fgm, 4, cv2.GC_INIT_WITH_MASK)
        hard = np.where((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD), 1., 0.).astype(np.float32)
    else:
        hard = (p > 0.5).astype(np.float32)
    hard = cv2.morphologyEx(hard, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    # keep the largest connected component (+ any big pieces), fill holes from GrabCut noise
    n, lab, stats, _ = cv2.connectedComponentsWithStats((hard > 0.5).astype(np.uint8))
    if n > 1:
        big = stats[1:, cv2.CC_STAT_AREA].max()
        keep = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > big * 0.35]
        hard = np.isin(lab, keep).astype(np.float32)
    guide = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.
    soft = cv2.ximgproc.guidedFilter(guide, hard, radius=max(2, int(min(ws) * 0.004)), eps=1e-3)
    soft = np.clip((soft - 0.15) / 0.7, 0, 1)
    m = Image.fromarray((soft * 255).astype(np.uint8)).resize(img.size, Image.BILINEAR)
    return m

# ---------- colour ----------
def white_balance(img, mask, strength=0.6):
    a = np.asarray(img).astype(np.float32)
    bg = np.asarray(mask) < 40
    hsv = np.asarray(img.convert("HSV")).astype(np.float32)
    ref = bg & (hsv[..., 2] > 150) & (hsv[..., 1] < 70)        # light, unsaturated background = wall / cloth
    if ref.sum() < 500 and bg.sum() > 2000:                     # warm-lit cloth: use the brightest background as white
        v = hsv[..., 2]; ref = bg & (v >= np.percentile(v[bg], 80))
    if ref.sum() < 500: return img
    mean = a[ref].mean(0); gain = mean.mean() / np.maximum(mean, 1)
    gain = 1 + (gain - 1) * strength
    return Image.fromarray(np.clip(a * gain, 0, 255).astype(np.uint8))

def tone(img, mask=None):
    """Colour-preserving levels: one black/white point from luminance, applied equally to all channels."""
    a = np.asarray(img).astype(np.float32)
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    sel = lum[np.asarray(mask) > 0] if mask is not None else lum.ravel()
    if sel.size < 100: sel = lum.ravel()
    lo, hi = np.percentile(sel, 0.6), np.percentile(sel, 99.4)
    if os.environ.get("CAP"): lo, hi = min(lo, 25), max(hi, 255 / 1.25 + lo)   # never brighten more than 25 %
    a = np.clip((a - lo) * (255. / max(hi - lo, 1)), 0, 255) / 255.
    a = a + 0.10 * (a - a * a) * (a < .5) * 2 - 0.04 * (a - .5) * (a > .5)   # lift shadows a little
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))

def is_gray(img):
    hsv = np.asarray(img.convert("HSV")); return hsv[..., 1].mean() < 28

# ---------- studio backdrop ----------
def backdrop(w, h, gray):
    top, bot = (np.array([236, 231, 223]) if not gray else np.array([232, 231, 229])), (np.array([214, 206, 194]) if not gray else np.array([206, 205, 203]))
    t = np.linspace(0, 1, h)[:, None, None] ** 1.4
    grad = top * (1 - t) + bot * t
    yy, xx = np.mgrid[0:h, 0:w]
    v = 1 - 0.08 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h * .45) / (h * .7)) ** 2)
    return Image.fromarray(np.clip(grad * v[..., None], 0, 255).astype(np.uint8))

def compose(fg, mask, out_w=1600, out_h=2000, gray=False):
    bb = mask.point(lambda v: 255 if v > 30 else 0).getbbox()
    if not bb: return None
    fg, mask = fg.crop(bb), mask.crop(bb)
    fw, fh = fg.size
    wide = fw > fh * 1.15
    W, H = (2000, 1500) if wide else (out_w, out_h)
    k = min(W * .78 / fw, H * .80 / fh)
    fg = fg.resize((max(1, int(fw * k)), max(1, int(fh * k))), Image.LANCZOS)
    mask = mask.resize(fg.size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8))
    bg = backdrop(W, H, gray)
    x0 = (W - fg.size[0]) // 2; y0 = int(H * .88) - fg.size[1]
    # contact shadow: flattened silhouette of the bottom of the object
    sh = Image.new("L", (W, H), 0)
    base = mask.crop((0, int(fg.size[1] * .85), fg.size[0], fg.size[1]))
    bw = base.getbbox()
    if bw:
        sw = (bw[2] - bw[0]) * 1.15; ell = Image.new("L", (int(sw), max(8, int(sw * .12))), 0)
        from PIL import ImageDraw
        ImageDraw.Draw(ell).ellipse([0, 0, ell.size[0] - 1, ell.size[1] - 1], fill=150)
        sh.paste(ell, (int(x0 + bw[0] - sw * .065), int(y0 + fg.size[1] - ell.size[1] * .55)))
        sh = sh.filter(ImageFilter.GaussianBlur(max(6, sw * .05)))
    bg = Image.composite(Image.new("RGB", (W, H), (60, 52, 44)), bg, sh.point(lambda v: v * .55))
    bg.paste(fg, (x0, y0), mask)
    return bg

def process(path, outpath, kind="sculpture"):
    t = time.time()
    src = Image.open(path).convert("RGB")
    big = upscale(src)
    if kind != "sculpture":
        res = tone(big)
        res.thumbnail((2000, 2000), Image.LANCZOS); res.save(outpath, quality=86, progressive=True, optimize=True)
        return time.time() - t
    gray = is_gray(src)
    mask = cutout_mask(big)
    col = white_balance(big, mask, strength=float(os.environ.get("WB", "0.25"))) if not gray else ImageOps.grayscale(big).convert("RGB")
    col = tone(col, mask=mask.point(lambda v: 255 if v > 128 else 0))
    res = compose(col, mask, gray=gray)
    bb = mask.point(lambda v: 255 if v > 30 else 0).getbbox()
    if bb:  # transparent cut-out for the dark journey
        cut = col.copy(); cut.putalpha(mask); cut = cut.crop(bb); cut.thumbnail((1400, 1400), Image.LANCZOS)
        os.makedirs(os.path.join(os.path.dirname(outpath), "cut"), exist_ok=True)
        cut.save(os.path.join(os.path.dirname(outpath), "cut", os.path.splitext(os.path.basename(outpath))[0] + ".webp"), quality=88, method=5)
    if res is None: res = tone(big)
    res.save(outpath, quality=86, progressive=True, optimize=True)
    return time.time() - t

if __name__ == "__main__":
    ind, outd = sys.argv[1], sys.argv[2]; os.makedirs(outd, exist_ok=True)
    names = sys.argv[3:] or sorted(os.listdir(ind))
    for n in names:
        kind = "sculpture" if n.startswith(("sculture-", "pietra-")) else "flat"
        o = os.path.join(outd, n)
        if os.path.exists(o): continue
        dt = process(os.path.join(ind, n), o, kind)
        print(f"{n} {kind} {dt:.1f}s", flush=True)
