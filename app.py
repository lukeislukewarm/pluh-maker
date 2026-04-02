import streamlit as st
import numpy as np
import librosa
import soundfile as sf
from mido import MidiFile
from pydub import AudioSegment
import os
import io

st.set_page_config(page_title="pluh maker", page_icon="🔌")

st.markdown("# pluh maker")
st.write("choose a midi file to turn it into pluh")

uploaded_midi = st.file_uploader("upload midi", type=["mid"])

if uploaded_midi:
    pluh_path = "pluh.mp3"
    
    if st.button("start pluh-ing"):
        with st.spinner("pluh-ing... please wait"):
            try:
                y, sr = librosa.load(pluh_path, sr=None)
                
                midi_data = io.BytesIO(uploaded_midi.read())
                mid = MidiFile(file=midi_data)
                
                total_samples = int(mid.length * sr) + (sr * 2)
                final_output = np.zeros(total_samples)
                current_time_sec = 0
                unique_pitches = {}

                for msg in mid:
                    current_time_sec += msg.time
                    if msg.type == 'note_on' and msg.velocity > 0:
                        semitones = msg.note - 59
                        if semitones not in unique_pitches:
                            unique_pitches[semitones] = librosa.effects.pitch_shift(y, sr=sr, n_steps=float(semitones))
                        
                        shifted_pluh = unique_pitches[semitones] * (msg.velocity / 127.0)
                        start_sample = int(current_time_sec * sr)
                        end_sample = start_sample + len(shifted_pluh)
                        if end_sample < len(final_output):
                            final_output[start_sample:end_sample] += shifted_pluh

                out_buffer = io.BytesIO()
                sf.write("temp.wav", final_output, sr)
                AudioSegment.from_wav("temp.wav").export(out_buffer, format="mp3")
                os.remove("temp.wav")
                
                st.success("done!")
                st.audio(out_buffer, format="audio/mp3")
                st.download_button("download pluh remix", out_buffer, file_name="pluh_remix.mp3")
                
            except Exception as e:
                st.error(f"error: {e}")