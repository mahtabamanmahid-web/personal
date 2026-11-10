# মানবতার আলো ফাউন্ডেশন — vertical reel

HyperFrames project for the 1080×1920 promo reel (84 s).

- `assets/voice.mp3`: the supplied voice-over, untouched.
- `tools/script.txt`: the supplied script. `tools/align.py` times every word against the voice (pauses found with ffmpeg `silencedetect`), writes `assets/transcript.json` and fails if any word differs from the script.
- `tools/build.py`: generates `index.html`, `compositions/s01–s17.html` (scenes), `captions.html` and `finish.html` from that transcript.
- `renders/manobotar-alo-reel.mp4`: the delivery render.

Rebuild: `python3 tools/align.py && python3 tools/build.py && npx hyperframes check && npx hyperframes render --quality delivery -o renders/manobotar-alo-reel.mp4`
