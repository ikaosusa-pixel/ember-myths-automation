
import os
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280
FPS = 24
SCENE_SECONDS = 10
OUT_DIR = "output"
OUT_FILE = os.path.join(OUT_DIR, "ember_myths_first_video.mp4")

SCENES = [
    ("EMBER MYTHS", "2099. Humanity had forgotten the future."),
    ("TOMORROW NOT FOUND", "At 11:59 PM, every screen went dark."),
    ("THE LAST ARCHIVIST", "Kael found a file hidden under his own name."),
    ("A VOICE FROM TOMORROW", "The recording was seventeen years in the future."),
    ("DO NOT REMEMBER", "If you are watching this... I failed."),
]

os.makedirs(OUT_DIR, exist_ok=True)

def get_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

TITLE_FONT = get_font(43)
BODY_FONT = get_font(27)
SMALL_FONT = get_font(20)

def make_frame(scene_index, local_frame, total_frames):
    t = local_frame / max(1, total_frames)
    img = Image.new("RGB", (W, H), (5, 8, 18))
    px = img.load()

    # Atmospheric blue-black gradient with amber horizon.
    for y in range(H):
        for x in range(W):
            horizon = max(0, 1 - abs(y - (H * 0.43)) / (H * 0.48))
            glow = max(0, 1 - math.sqrt(
                ((x - W * 0.52) / (W * 0.72)) ** 2 +
                ((y - H * 0.43) / (H * 0.62)) ** 2
            ))
            r = int(5 + 48 * horizon * glow)
            g = int(8 + 22 * horizon * glow)
            b = int(18 + 28 * horizon * glow)
            px[x, y] = (r, g, b)

    d = ImageDraw.Draw(img, "RGBA")

    # Distant futuristic skyline.
    for i in range(18):
        bw = 22 + (i * 13 % 45)
        bx = (i * 47) % W
        bh = 130 + (i * 71 % 310)
        by = int(H * 0.68 - bh)
        d.rectangle((bx, by, bx + bw, H * 0.72),
                    fill=(8, 18, 35, 235))
        for wy in range(by + 20, int(H * 0.68), 28):
            d.rectangle((bx + 6, wy, bx + 10, wy + 7),
                        fill=(40, 180, 220, 100))
            if bx + bw - 12 > bx + 12:
                d.rectangle((bx + bw - 12, wy, bx + bw - 8, wy + 7),
                            fill=(255, 145, 55, 120))

    # Central glowing tower.
    cx = W // 2
    d.polygon([(cx - 65, H * 0.68), (cx - 24, H * 0.29),
               (cx + 20, H * 0.29), (cx + 67, H * 0.68)],
              fill=(10, 24, 43, 245))
    d.line((cx, H * 0.30, cx, H * 0.66),
           fill=(255, 156, 61, 210), width=4)

    # Foreground silhouette of the archivist.
    person_x = int(W * 0.5 + math.sin(t * math.pi) * 10)
    d.ellipse((person_x - 34, H * 0.65, person_x + 34, H * 0.72),
              fill=(3, 5, 12, 255))
    d.polygon([(person_x - 27, H * 0.70),
               (person_x + 27, H * 0.70),
               (person_x + 52, H * 0.91),
               (person_x - 50, H * 0.91)],
              fill=(3, 5, 12, 255))
    d.ellipse((person_x - 18, H * 0.61, person_x + 18, H * 0.66),
              fill=(4, 8, 15, 255))

    title, subtitle = SCENES[scene_index]
    alpha = int(255 * min(1, t * 5 + 0.15, (1 - t) * 5 + 0.15))

    d.text((W // 2, 95), "EMBER MYTHS  /  2099",
           font=SMALL_FONT, fill=(255, 170, 76, 230), anchor="mm")

    # Text panel.
    d.rounded_rectangle((35, 900, W - 35, 1125), radius=20,
                        fill=(3, 7, 16, 218),
                        outline=(255, 156, 61, 110), width=2)

    d.text((W // 2, 962), title, font=TITLE_FONT,
           fill=(255, 178, 91, alpha), anchor="mm",
           stroke_width=1, stroke_fill=(35, 13, 4, alpha))

    # Wrap subtitle into two lines if needed.
    words = subtitle.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if d.textbbox((0, 0), test, font=BODY_FONT)[2] > W - 100:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    for j, line in enumerate(lines[:3]):
        d.text((W // 2, 1030 + j * 38), line, font=BODY_FONT,
               fill=(235, 241, 250, alpha), anchor="mm")

    d.text((W // 2, 1195), "THE FUTURE HAS A MEMORY.",
           font=SMALL_FONT, fill=(120, 180, 205, 210), anchor="mm")

    return img

def main():
    frames_per_scene = FPS * SCENE_SECONDS
    raw_video = os.path.join(OUT_DIR, "silent_video.mp4")
    frames_dir = os.path.join(OUT_DIR, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    # Render frames as numbered images.
    for scene_index in range(len(SCENES)):
        for frame_index in range(frames_per_scene):
            frame = make_frame(scene_index, frame_index, frames_per_scene)
            frame.save(os.path.join(
                frames_dir,
                f"frame_{scene_index * frames_per_scene + frame_index:05d}.jpg"
            ), quality=90)

    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "frame_%05d.jpg"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "ultrafast", "-crf", "24",
        raw_video
    ], check=True)

    # Create English narration using espeak-ng.
    narration = " ".join(subtitle for _, subtitle in SCENES)
    narration_file = os.path.join(OUT_DIR, "narration.wav")
    subprocess.run([
        "espeak-ng", "-v", "en-us", "-s", "145",
        "-w", narration_file, narration
    ], check=True)

    # Mix narration with a quiet cinematic ambient bed.
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", raw_video, "-i", narration_file,
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-filter_complex",
        "[1:a]volume=1.5[narr];[2:a]volume=0.0[silence];"
        "[narr][silence]amix=inputs=2:duration=first[a]",
        "-map", "0:v:0", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart", OUT_FILE
    ], check=True)

    print(f"Video created: {OUT_FILE}")

if __name__ == "__main__":
    main()
