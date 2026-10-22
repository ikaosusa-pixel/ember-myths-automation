
import os
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = 24
SCENE_SECONDS = 6

SCENES = [
    ("EMBER MYTHS", "Legends begin in darkness."),
    ("THE FORGOTTEN GODS", "Before history, there were stories."),
    ("THE FIRE OF PROMETHEUS", "A stolen flame changed humanity forever."),
    ("THE PRICE OF DEFIANCE", "Even the gods demanded a price."),
    ("MORE LEGENDS AWAIT", "Subscribe to Ember Myths for the next tale."),
]

OUT = "output"
os.makedirs(OUT, exist_ok=True)


def get_font(size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
    ]
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_frame(title, subtitle, frame, total):
    img = Image.new("RGB", (W, H), (8, 10, 22))
    pixels = img.load()

    for y in range(H):
        for x in range(W):
            glow = max(0, 1 - math.sqrt(
                ((x - W * 0.5) / (W * 0.8)) ** 2
                + ((y - H * 0.65) / (H * 0.9)) ** 2
            ))
            pixels[x, y] = (
                int(8 + glow * 42),
                int(10 + glow * 18),
                int(22 + glow * 12),
            )

    draw = ImageDraw.Draw(img)
    import random
    random.seed(42)

    for i in range(100):
        x = (i * 197) % W
        y = (i * 113) % int(H * 0.75)
        r = 1 if i % 5 else 2
        draw.ellipse((x, y, x + r, y + r), fill=(180, 155, 115))

    # Distant mountain silhouettes
    for layer, color in [(0, (22, 24, 36)), (1, (14, 16, 27))]:
        points = [(0, H)]
        for x in range(0, W + 1, 80):
            y = 470 + layer * 70 + int(
                50 * math.sin(x / 115 + layer)
                + 25 * math.sin(x / 47)
            )
            points.append((x, y))
        points.append((W, H))
        draw.polygon(points, fill=color)

    # Gentle text fade
    fade = min(1, frame / 30, (total - frame) / 30)
    fade = max(0, fade)
    gold = (int(230 * fade), int(190 * fade), int(115 * fade))
    white = (int(230 * fade), int(230 * fade), int(225 * fade))

    title_font = get_font(58 if len(title) < 22 else 44)
    sub_font = get_font(27)

    box = draw.textbbox((0, 0), title, font=title_font)
    draw.text(((W - (box[2] - box[0])) / 2, 275),
              title, font=title_font, fill=gold)

    box = draw.textbbox((0, 0), subtitle, font=sub_font)
    draw.text(((W - (box[2] - box[0])) / 2, 365),
              subtitle, font=sub_font, fill=white)

    draw.line((440, 425, 840, 425), fill=gold, width=2)
    return img


def main():
    video_path = os.path.join(OUT, "visuals.mp4")
    voice_path = os.path.join(OUT, "narration.wav")
    final_path = os.path.join(OUT, "ember_myths_first_video.mp4")

    frames_per_scene = FPS * SCENE_SECONDS
    total_frames = frames_per_scene * len(SCENES)

    # Render video frames using FFmpeg's raw video input
    ffmpeg = subprocess.Popen([
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        video_path
    ], stdin=subprocess.PIPE)

    for title, subtitle in SCENES:
        for frame in range(frames_per_scene):
            img = make_frame(title, subtitle, frame, frames_per_scene)
            ffmpeg.stdin.write(img.tobytes())

    ffmpeg.stdin.close()
    if ffmpeg.wait() != 0:
        raise RuntimeError("FFmpeg video rendering failed")

    # Generate narration
    narration = " ".join(
        f"{title}. {subtitle}" for title, subtitle in SCENES
    )
    subprocess.run([
        "espeak-ng", "-v", "en-us", "-s", "135",
        "-w", voice_path, narration
    ], check=True)

    # Combine narration and visuals
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-i", voice_path,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
        "-shortest", final_path
    ], check=True)

    print(f"VIDEO CREATED: {final_path}")


if __name__ == "__main__":
    main()
