
name: Ember Myths - Generate First Video

on:
  workflow_dispatch:
  push:
    paths:
      - "video.py"
      - ".github/workflows/render.yml"

permissions:
  contents: read

jobs:
  render:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - name: Get project files
        uses: actions/checkout@v4

      - name: Install requirements
        run: |
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends espeak-ng
          python -m pip install Pillow imageio-ffmpeg
          FFMPEG_PATH="$(python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
          sudo ln -sf "$FFMPEG_PATH" /usr/local/bin/ffmpeg
          ffmpeg -version
          espeak-ng --version

      - name: Generate myth video
        run: python video.py

      - name: Upload finished MP4
        uses: actions/upload-artifact@v4
        with:
          name: ember-myths-first-video
          path: output/ember_myths_first_video.mp4
          if-no-files-found: error
          retention-days: 7
