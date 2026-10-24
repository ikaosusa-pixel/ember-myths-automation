
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280
FPS = 24
SECONDS = 10
OUT = "output"
FRAMES = os.path.join(OUT, "scenes")
VIDEO = os.path.join(OUT, "ember_myths_first_video.mp4")

SCENES = [
    ("EMBER MYTHS", "In 2099, humanity had forgotten the future."),
    ("TOMORROW NOT FOUND", "At 11:59 PM, every screen went dark."),
    ("THE LAST ARCHIVIST", "Kael found a file hidden under his own name."),
    ("A VOICE FROM TOMORROW", "The recording came from seventeen years ahead."),
    ("DO NOT REMEMBER", "If you are watching this... I failed."),
]

os.makedirs(FRAMES, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

def font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def make_scene(index, title, subtitle):
    # Fast gradient background: no per-pixel Python loops.
    img = Image.new("RGB", (W, H), (5, 10, 24))
    draw = ImageDraw.Draw(img, "RGBA")

    # Atmospheric horizon and amber light.
    for y in range(250, 950, 5):
        amount = int(55 * (1 - abs(y - 600) / 500))
        if amount > 0:
            draw.line((0, y, W, y), fill=(190, 75, 25, amount), width=5)

    # Stars and futuristic skyline.
    for i in range(110):
        x = (i * 137 + index * 29) % W
        y = (i * 83 + 47) % 760
        draw.ellipse((x, y, x + 2, y + 2),
                     fill=(150, 210, 255, 150))

    for i in range(18):
        x = i * 43 - 8
        bw = 24 + (i * 17 % 28)
        bh = 120 + (i * 71 % 280)
        top = 850 - bh
        draw.rectangle((x, top, x + bw, 900),
                       fill=(8, 20, 39, 255))
        for wy in range(top + 18, 870, 32):
            draw.rectangle((x + 7, wy, x + 11, wy + 7),
                           fill=(65, 175, 225, 180))
            draw.rectangle((x + bw - 10, wy, x + bw - 6, wy + 7),
                           fill=(255, 155, 60, 170))

    # Tall central tower.
    draw.polygon([(300, 850), (340, 310), (380, 850)],
                 fill=(12, 25, 46, 255))
    draw.line((340, 330, 340, 830),
              fill=(255, 150, 50, 255), width=4)

    # Archivist silhouette.
    draw.ellipse((305, 785, 355, 845), fill=(2, 4, 10, 255))
    draw.polygon([(300, 835), (360, 835), (395, 1060),
                  (265, 1060)], fill=(2, 4, 10, 255))
    draw.ellipse((324, 865, 336, 877),
                 fill=(255, 140, 40, 255))

    # Brand and title.
    draw.text((W // 2, 85), "EMBER MYTHS  /  2099",
              font=font(24), fill=(255, 170, 70),
              anchor="mm")

    draw.rounded_rectangle((30, 920, W - 30, 1150),
                           radius=20, fill=(3, 7, 17, 235),
                           outline=(255, 155, 55, 180), width=2)

    draw.text((W // 2, 980), title, font=font(35),
              fill=(255, 174, 78), anchor="mm")

    # Wrap subtitle into readable lines.
    f = font(24)
    words = subtitle.split()
    lines, line = [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=f)[2] > W - 90:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)

    for j, text in enumerate(lines[:3]):
        draw.text((W // 2, 1040 + j * 34), text,
                  font=f, fill=(240, 244, 250), anchor="mm")

    draw.text((W // 2, 1200), "THE FUTURE HAS A MEMORY",
              font=font(17), fill=(120, 190, 220), anchor="mm")

    img.save(os.path.join(FRAMES, f"scene_{index:02d}.jpg"),
             quality=88)

def run(args):
    subprocess.run(args, check=True)

def main():
    for i, (title, subtitle) in enumerate(SCENES):
        make_scene(i, title, subtitle)

    # Five still scenes, ten seconds each.
    clips = []
    for i in range(len(SCENES)):
        clip = os.path.join(OUT, f"clip_{i:02d}.mp4")
        image = os.path.join(FRAMES, f"scene_{i:02d}.jpg")
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-framerate", str(FPS),
            "-i", image, "-t", str(SECONDS),
            "-vf", "scale=720:1280,format=yuv420p",
            "-r", str(FPS), "-c:v", "libx264",
            "-preset", "ultrafast", "-crf", "25",
            "-an", clip
        ])
        clips.append(clip)

    # Join scenes.
    concat_file = os.path.join(OUT, "clips.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in clips:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    silent = os.path.join(OUT, "silent.mp4")
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c", "copy", silent
    ])

    # English synthetic narration.
    narration = " ".join(subtitle for _, subtitle in SCENES)
    wav = os.path.join(OUT, "narration.wav")
    run([
        "espeak-ng", "-v", "en-us", "-s", "140",
        "-w", wav, narration
    ])

    # Keep video duration at 50 seconds.
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", silent, "-i", wav,
        "-filter_complex",
        "[1:a]apad,atrim=0:50,volume=1.4[a]",
        "-map", "0:v:0", "-map", "[a]",
        "-t", "50", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", VIDEO
    ])

    print("SUCCESS: " + VIDEO)

if __name__ == "__main__":
    main()
