from pydub import AudioSegment

AudioSegment.converter = (
    r"C:\Users\wargriff\Downloads\ffmpeg-2026-04-30-git-cc3ca17127-essentials_build"
    r"\ffmpeg-2026-04-30-git-cc3ca17127-essentials_build\bin\ffmpeg.exe"
)

audio = AudioSegment.from_file(
    r"C:\Users\wargriff\Music\Spotify\musique.wav"
)

audio.export(
    r"C:\Users\wargriff\Music\Spotify\musique.mp3",
    format="mp3"
)

print("Conversion OK")