"""Slimme 9:16-crop: volg het gezicht in plaats van balken of blur.

Draait lokaal met OpenCV (gratis). Per venster van een paar seconden kijken we waar het
grootste gezicht staat; de crop springt alleen mee als het gezicht duidelijk verschuift,
zodat het beeld rustig blijft (zoals een cameraman die af en toe bijstuurt).
"""
import statistics

WINDOW = 2.0            # seconden per venster
SAMPLES_PER_SEC = 2     # zoveel beelden per seconde bekijken
MIN_HIT_RATE = 0.3      # in minstens dit deel van de beelden moet een gezicht staan
MOVE_THRESHOLD = 0.08   # crop pas verplaatsen bij een verschuiving van 8% van de breedte


def face_centers(path, duration):
    """Horizontaal midden (0..1) van het grootste gezicht per venster; None als er geen was.
    Geeft (centers, hit_rate) terug, of (None, 0) als OpenCV ontbreekt."""
    try:
        import cv2
    except ImportError:
        return None, 0.0
    if not hasattr(cv2, "CascadeClassifier"):        # OpenCV 5 zonder Haar-detectie
        return None, 0.0
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return None, 0.0
    n_windows = max(1, int(duration // WINDOW) + (1 if duration % WINDOW > 0.2 else 0))
    per_window = max(1, int(WINDOW * SAMPLES_PER_SEC))
    centers, hits, total = [], 0, 0
    try:
        for wi in range(n_windows):
            xs = []
            for k in range(per_window):
                t = wi * WINDOW + (k + 0.5) * WINDOW / per_window
                if t >= duration:
                    break
                cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
                ok, frame = cap.read()
                if not ok:
                    continue
                total += 1
                h, w = frame.shape[:2]
                scale = 480 / w if w > 480 else 1.0
                small = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale != 1.0 else frame
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6,
                                                 minSize=(int(small.shape[0] * 0.08),) * 2)
                if len(faces):
                    x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                    xs.append((x + fw / 2) / small.shape[1])
                    hits += 1
            centers.append(statistics.median(xs) if xs else None)
    finally:
        cap.release()
    return centers, (hits / total if total else 0.0)


def smooth_centers(centers):
    """Vul vensters zonder gezicht op en negeer kleine verschuivingen."""
    known = [c for c in centers if c is not None]
    if not known:
        return []
    out, current = [], None
    for c in centers:
        if c is None:
            c = current if current is not None else known[0]
        if current is None or abs(c - current) > MOVE_THRESHOLD:
            current = c
        out.append(current)
    return out


def crop_x_expression(centers, src_w, src_h, out_w=1080, out_h=1920):
    """FFmpeg-expressie voor de x-positie van de crop na `scale=-2:out_h`."""
    scaled_w = round(src_w * out_h / src_h / 2) * 2
    max_x = max(0, scaled_w - out_w)

    def x_for(c):
        return int(min(max_x, max(0, c * scaled_w - out_w / 2)))

    xs = [x_for(c) for c in centers]
    # opeenvolgende gelijke vensters samenvoegen
    parts = []
    for i, x in enumerate(xs):
        if parts and parts[-1][1] == x:
            continue
        parts.append((i * WINDOW, x))
    expr = str(parts[-1][1])
    for t, x in reversed(parts[:-1]):
        nxt = next(pt for pt, _ in parts if pt > t)
        expr = f"if(lt(t\\,{nxt:g})\\,{x}\\,{expr})"
    return expr


def face_crop_filter(path, duration, src_w, src_h):
    """Filter voor een 1080x1920 crop die het gezicht volgt, of None als dat niet kan
    (geen OpenCV, te weinig gezichten, of de video is al staand)."""
    if src_w / src_h <= 9 / 16 + 0.01:
        return None
    centers, hit_rate = face_centers(path, duration)
    if not centers or hit_rate < MIN_HIT_RATE:
        return None
    smooth = smooth_centers(centers)
    if not smooth:
        return None
    return f"scale=-2:1920,crop=1080:1920:{crop_x_expression(smooth, src_w, src_h)}:0"
