import asyncio
import os
import tempfile
from typing import Dict, List, Tuple

import edge_tts
import gradio as gr


def load_voices() -> Tuple[List[str], Dict[str, str]]:
    voices = asyncio.run(edge_tts.list_voices())
    voice_map = {}
    labels = []

    for v in voices:
        label = f"{v['ShortName']} | {v['Locale']} | {v['Gender']}"
        voice_map[label] = v["ShortName"]
        labels.append(label)

    labels.sort()
    return labels, voice_map


VOICE_LABELS, VOICE_MAP = load_voices()

DEFAULT_VOICE = next(
    (v for v in VOICE_LABELS if "en-US-AriaNeural" in v),
    VOICE_LABELS[0] if VOICE_LABELS else None,
)


async def generate_tts(text: str, voice_label: str, speed: int, pitch: int):
    if not text or not text.strip():
        return None, None, "Please enter some text."

    if not voice_label:
        return None, None, "Please select a voice."

    voice = VOICE_MAP[voice_label]
    rate = f"{speed:+d}%"
    pitch_value = f"{pitch:+d}Hz"

    temp_dir = tempfile.mkdtemp()
    mp3_path = os.path.join(temp_dir, "output.mp3")

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch_value,
        )
        await communicate.save(mp3_path)
        return mp3_path, mp3_path, "Done. MP3 generated successfully."
    except Exception as e:
        return None, None, f"Error: {str(e)}"


def run_generate_tts(text, voice_label, speed, pitch):
    return asyncio.run(generate_tts(text, voice_label, speed, pitch))


with gr.Blocks(title="Edge TTS UI") as demo:
    gr.Markdown("# Edge TTS UI")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="Enter Text",
                lines=8,
                placeholder="Type your text here..."
            )

            voice_dropdown = gr.Dropdown(
                choices=VOICE_LABELS,
                value=DEFAULT_VOICE,
                label="Voice"
            )

            speed_slider = gr.Slider(
                minimum=-50,
                maximum=50,
                value=0,
                step=1,
                label="Speed (%)"
            )

            pitch_slider = gr.Slider(
                minimum=-50,
                maximum=50,
                value=0,
                step=1,
                label="Pitch (Hz)"
            )

            generate_btn = gr.Button("Generate Voice")

        with gr.Column():
            audio_output = gr.Audio(label="Preview", type="filepath")
            file_output = gr.File(label="Download MP3")
            status_output = gr.Textbox(label="Status", interactive=False)

    generate_btn.click(
        fn=run_generate_tts,
        inputs=[text_input, voice_dropdown, speed_slider, pitch_slider],
        outputs=[audio_output, file_output, status_output],
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    demo.launch(server_name="0.0.0.0", server_port=port)
