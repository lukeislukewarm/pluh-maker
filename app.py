import streamlit as st
import numpy as np
import librosa
import soundfile as sf
from mido import MidiFile
from pydub import AudioSegment
import os
import io
import subprocess
import tempfile
import glob

st.set_page_config(page_title="pluh maker", page_icon="🔌")

st.markdown("# pluh maker")
st.write("choose a midi file or paste a MuseScore link to turn it into pluh")


def download_midi_from_musescore(url: str) -> str:
    temp_dir = tempfile.mkdtemp()

    command = [
        "npx",
        "dl-librescore@latest",
        "-i",
        url.strip(),
        "-t",
        "midi",
        "-o",
        temp_dir,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    st.write("Download folder:")
    st.code(temp_dir)

    st.write("dl-librescore output:")
    st.code(result.stdout + "\n" + result.stderr)

    all_files = glob.glob(os.path.join(temp_dir, "**", "*"), recursive=True)

    st.write("Files found:")
    st.write(all_files)

    midi_files = [
        f for f in all_files
        if os.path.isfile(f) and f.lower().endswith((".mid", ".midi"))
    ]

    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)

    if not midi_files:
        raise FileNotFoundError("No MIDI file was downloaded.")

    return midi_files[0]


uploaded_midi = st.file_uploader("upload midi", type=["mid", "midi"])

musescore_url = st.text_input(
    "or paste a MuseScore link",
    placeholder="https://musescore.com/..."
)

if uploaded_midi or musescore_url:
    pluh_path = "pluh.mp3"

    if st.button("start pluh-ing"):
        with st.spinner("pluh-ing... please wait"):
            try:
                y, sr = librosa.load(pluh_path, sr=None)

                if musescore_url:
                    midi_path = download_midi_from_musescore(musescore_url)
                    mid = MidiFile(midi_path)
                else:
                    midi_data = io.BytesIO(uploaded_midi.read())
                    mid = MidiFile(file=midi_data)

                total_samples = int(mid.length * sr) + (sr * 2)
                final_output = np.zeros(total_samples)
                current_time_sec = 0
                unique_pitches = {}

                for msg in mid:
                    current_time_sec += msg.time

                    if msg.type == "note_on" and msg.velocity > 0:
                        semitones = msg.note - 59

                        if semitones not in unique_pitches:
                            unique_pitches[semitones] = librosa.effects.pitch_shift(
                                y,
                                sr=sr,
                                n_steps=float(semitones)
                            )

                        shifted_pluh = unique_pitches[semitones] * (msg.velocity / 127.0)
                        start_sample = int(current_time_sec * sr)
                        end_sample = start_sample + len(shifted_pluh)

                        if end_sample < len(final_output):
                            final_output[start_sample:end_sample] += shifted_pluh

                out_buffer = io.BytesIO()

                sf.write("temp.wav", final_output, sr)
                AudioSegment.from_wav("temp.wav").export(out_buffer, format="mp3")
                os.remove("temp.wav")

                out_buffer.seek(0)

                st.success("done!")
                st.audio(out_buffer, format="audio/mp3")

                st.download_button(
                    "download pluh remix",
                    out_buffer,
                    file_name="pluh_remix.mp3",
                    mime="audio/mp3"
                )

            except Exception as e:
                st.error(f"error: {e}")

else:
    st.info("upload a MIDI file or paste a MuseScore link")
