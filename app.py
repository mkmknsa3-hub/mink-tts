import asyncio
import os
import tempfile

import edge_tts
import gradio as gr

# Myanmar voices only
MYANMAR_VOICES = {
    "Myanmar Female - Nilar": "my-MM-NilarNeural",
    "Myanmar Male - Thiha": "my-MM-ThihaNeural",
}

VOICE_LABELS = list(MYANMAR_VOICES.keys())
DEFAULT_VOICE = "Myanmar Female - Nilar"


async def generate_tts(text: str, voice_label: str, speed: int, pitch: int):
    if not text or not text.strip():
        return None, None, "စာရိုက်ထည့်ပါ။"

    voice = MYANMAR_VOICES[voice_label]
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
        return mp3_path, mp3_path, "ပြီးပါပြီ။ MP3 ထုတ်ပြီးပါပြီ။"

    except Exception as e:
        msg = str(e)
        if "403" in msg:
            return None, None, (
                "403 error ဖြစ်နေပါတယ်။ edge-tts endpoint က request ကိုပိတ်ထားတာပါ။ "
                "requirements.txt မှာ edge-tts==7.2.7 သုံးထားတာသေချာစစ်ပါ။ "
                "အဲဒါပြီးလည်း 403 ဆက်ဖြစ်ရင် Railway IP/region ဘက်က block ဖြစ်နိုင်ပါတယ်။"
            )
        return None, None, f"Error: {msg}"


def run_generate_tts(text, voice_label, speed, pitch):
    return asyncio.run(generate_tts(text, voice_label, speed, pitch))


with gr.Blocks(title="Myanmar TTS") as demo:
    gr.Markdown("## Myanmar TTS\nMyanmar Female / Male ပဲပြထားပါတယ်။")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="စာထည့်ရန်",
                lines=8,
                placeholder="မင်္ဂလာပါ။ ဒီဟာက မြန်မာအသံ စမ်းသပ်ခြင်း ဖြစ်ပါတယ်။",
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

            generate_btn = gr.Button("Generate Voice", variant="primary")

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
