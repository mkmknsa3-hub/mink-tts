import asyncio
import os
import re
import tempfile

import edge_tts
import gradio as gr

MYANMAR_VOICES = {
    "Myanmar Female - Nilar": "my-MM-NilarNeural",
    "Myanmar Male - Thiha": "my-MM-ThihaNeural",
}

VOICE_LABELS = list(MYANMAR_VOICES.keys())
DEFAULT_VOICE = "Myanmar Female - Nilar"


def clamp_pause(value) -> int:
    try:
        value = int(value)
    except Exception:
        value = 120
    return max(0, min(value, 2000))


def preprocess_text(text: str, pause_ms: int) -> str:
    text = text.strip()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n\s*\n+", "\n", text)
    text = text.replace("\n", f" <break time='{pause_ms}ms'/> ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def generate_tts(text: str, voice_label: str, speed: int, pitch: int, pause_ms: int):
    if not text or not text.strip():
        return None, None, "စာရိုက်ထည့်ပါ။"

    if voice_label not in MYANMAR_VOICES:
        return None, None, "အသံရွေးပါ။"

    voice = MYANMAR_VOICES[voice_label]
    rate = f"{speed:+d}%"
    pitch_value = f"{pitch:+d}Hz"
    pause_ms = clamp_pause(pause_ms)

    processed_text = preprocess_text(text, pause_ms)

    ssml = f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="my-MM">
    <voice name="{voice}">
        <prosody rate="{rate}" pitch="{pitch_value}">
            {processed_text}
        </prosody>
    </voice>
</speak>
"""

    temp_dir = tempfile.mkdtemp()
    mp3_path = os.path.join(temp_dir, "output.mp3")

    try:
        communicate = edge_tts.Communicate(ssml=ssml, voice=voice)
        await communicate.save(mp3_path)
        return mp3_path, mp3_path, f"ပြီးပါပြီ။ Pause = {pause_ms}ms"
    except TypeError:
        return None, None, (
            "ဒီ edge-tts version က SSML parameter မယူပါ။ "
            "requirements.txt မှာ edge-tts==7.2.7 ထားပြီး redeploy ပြန်လုပ်ပါ။"
        )
    except Exception as e:
        return None, None, f"Error: {str(e)}"


def run_generate_tts(text, voice_label, speed, pitch, pause_ms):
    return asyncio.run(generate_tts(text, voice_label, speed, pitch, pause_ms))


with gr.Blocks(title="Myanmar TTS") as demo:
    gr.Markdown(
        """
# Myanmar TTS

- Myanmar Female / Male only
- Speed control
- Pitch control
- Pause (ms) number input
- MP3 preview / download
        """
    )

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="စာထည့်ရန်",
                lines=8,
                placeholder="မင်္ဂလာပါ။\nဒီဟာက မြန်မာအသံ စမ်းသပ်ခြင်း ဖြစ်ပါတယ်။",
            )

            voice_dropdown = gr.Dropdown(
                choices=VOICE_LABELS,
                value=DEFAULT_VOICE,
                label="အသံရွေးရန်",
            )

            speed_slider = gr.Slider(
                minimum=-50,
                maximum=50,
                value=0,
                step=1,
                label="အမြန်နှုန်း (%)",
            )

            pitch_slider = gr.Slider(
                minimum=-50,
                maximum=50,
                value=0,
                step=1,
                label="Pitch (Hz)",
            )

            pause_input = gr.Number(
                value=120,
                precision=0,
                label="Pause (ms)",
                info="Enter နေရာ pause length. ဥပမာ 80, 120, 200"
            )

            generate_btn = gr.Button("Generate Voice", variant="primary")

        with gr.Column():
            audio_output = gr.Audio(label="Preview", type="filepath")
            file_output = gr.File(label="Download MP3")
            status_output = gr.Textbox(label="Status", interactive=False)

    generate_btn.click(
        fn=run_generate_tts,
        inputs=[text_input, voice_dropdown, speed_slider, pitch_slider, pause_input],
        outputs=[audio_output, file_output, status_output],
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    demo.launch(server_name="0.0.0.0", server_port=port)
