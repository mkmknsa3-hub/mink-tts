"""
This script implements a simple text‑to‑speech (TTS) web application using
Microsoft's Edge TTS service via the `edge‑tts` Python package.  It exposes a
Gradio user interface that lets users enter arbitrary text, adjust the speech
rate (speed) and pitch (voice height), choose a voice, and select the output
audio format (MP3 or WAV).  The generated audio can be played directly in the
browser and downloaded for offline use.

Before running this script you must install the required dependencies:

```
pip install edge‑tts gradio pydub
```

The `pydub` package relies on FFmpeg to convert MP3 files to WAV.  On most
systems you can install FFmpeg via your package manager (e.g. `apt install
ffmpeg` on Debian/Ubuntu).  If FFmpeg is not available the WAV output option
will not work.

Usage
-----

Run the script from the command line:

```
python app.py
```

The server will start locally on port 7860 by default and can be accessed via
your web browser.  To deploy this app on a cloud platform such as Render,
commit the `app.py` and `requirements.txt` files to a Git repository and
create a new Python Web Service on Render that runs `python app.py` as the
start command.  Render will automatically install dependencies listed in
`requirements.txt` and expose the app publicly.
"""

import asyncio
import os
import tempfile
from typing import Optional, Tuple

import gradio as gr

try:
    import edge_tts  # type: ignore
except ImportError as exc:
    raise RuntimeError(
        "The `edge‑tts` package is not installed. Please install it with 'pip install edge‑tts'."
    ) from exc

# Attempt to import pydub for MP3→WAV conversion.  If pydub is not available or
# FFmpeg is missing, WAV output will be disabled.
try:
    from pydub import AudioSegment  # type: ignore
    _pydub_available = True
except ImportError:
    _pydub_available = False


async def get_voice_choices() -> dict:
    """Retrieve the list of available voices from the Edge TTS service.

    Returns a mapping from a human‑readable label to the voice short name.
    """
    voices = await edge_tts.list_voices()
    choices = {}
    for v in voices:
        # Combine the short name and gender to make selection easier.
        label = f"{v['ShortName']} ({v['Gender']})"
        choices[label] = v["ShortName"]
    return choices


async def synthesize_speech(
    text: str,
    voice: str,
    rate: int,
    pitch: int,
    output_format: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Convert text to speech using Edge TTS and return the path to the audio file.

    Parameters
    ----------
    text : str
        The input text to be synthesized.  Must not be empty.
    voice : str
        The selected voice short name (e.g. "en-US-AriaNeural").
    rate : int
        Percentage to adjust the speech rate.  Positive values speed up the
        speech, negative values slow it down.  Zero leaves the default rate.
    pitch : int
        Pitch adjustment in Hertz.  Positive values increase the pitch
        (higher voice), negative values decrease it (lower voice), zero uses
        the default pitch.
    output_format : str
        Desired output format, either "mp3" or "wav".

    Returns
    -------
    Tuple[str | None, str | None]
        A tuple containing either the path to the generated audio file and
        `None` on success, or `None` and an error message if something goes
        wrong.
    """
    if not text.strip():
        return None, "Please enter some text to convert."

    if not voice:
        return None, "Please select a voice."

    # Format the rate and pitch values into strings understood by edge‑tts.
    rate_str = f"{rate:+d}%"  # e.g. +10% or -10%
    pitch_str = f"{pitch:+d}Hz"  # e.g. +20Hz or -20Hz

    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
        # Always generate MP3 audio first.  We will convert to WAV later if requested.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            mp3_path = tmp.name
        await communicate.save(mp3_path)
    except Exception as exc:
        return None, f"An error occurred during synthesis: {exc}"

    # If the user requested WAV and pydub is available, convert the file.
    if output_format == "wav":
        if not _pydub_available:
            return None, (
                "WAV output is not available because the pydub package or FFmpeg is missing."
            )
        try:
            audio = AudioSegment.from_mp3(mp3_path)
            wav_path = mp3_path.replace(".mp3", ".wav")
            audio.export(wav_path, format="wav")
            # Remove the intermediate MP3 file.
            os.remove(mp3_path)
            return wav_path, None
        except Exception as exc:
            return None, f"Failed to convert to WAV: {exc}"

    # If MP3 is requested or conversion is unavailable, return the MP3 path.
    return mp3_path, None


async def tts_interface(
    text: str,
    voice_label: str,
    rate: int,
    pitch: int,
    output_format: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Wrapper to synthesize speech using human‑readable voice labels.

    Parameters
    ----------
    voice_label : str
        A label of the form "en-US-AriaNeural (Female)".  The actual voice
        short name is extracted from this label.
    """
    # Extract the short name (first token before the space).
    voice_short = voice_label.split(" ")[0]
    return await synthesize_speech(text, voice_short, rate, pitch, output_format)


async def build_interface() -> gr.Interface:
    """Asynchronously construct the Gradio interface with dynamic voice choices."""
    voice_choices = await get_voice_choices()
    default_voice_label = next(iter(voice_choices.keys()))
    # Define UI components.
    text_input = gr.Textbox(
        label="Input Text", lines=5, placeholder="Type the text you want to convert…"
    )
    voice_dropdown = gr.Dropdown(
        choices=list(voice_choices.keys()),
        value=default_voice_label,
        label="Select Voice",
    )
    rate_slider = gr.Slider(
        minimum=-50,
        maximum=50,
        step=1,
        value=0,
        label="Speech Speed Adjustment (%)",
    )
    pitch_slider = gr.Slider(
        minimum=-50,
        maximum=50,
        step=1,
        value=0,
        label="Speech Pitch Adjustment (Hz)",
    )
    format_dropdown = gr.Dropdown(
        choices=["mp3", "wav"],
        value="mp3",
        label="Output Format",
    )
    audio_output = gr.Audio(label="Generated Audio", type="filepath")
    warning_output = gr.Markdown(label="Warning", visible=False)
    interface = gr.Interface(
        fn=tts_interface,
        inputs=[text_input, voice_dropdown, rate_slider, pitch_slider, format_dropdown],
        outputs=[audio_output, warning_output],
        title="Edge TTS Text‑to‑Speech",
        description=(
            "This demo uses Microsoft's Edge text‑to‑speech service.  "
            "Adjust the rate and pitch of the synthetic voice, select a voice, "
            "and choose whether the output should be an MP3 or WAV file.  "
            "After generation, the audio can be played or downloaded."
        ),
        theme=gr.themes.Origin(),
        analytics_enabled=False,
        allow_flagging=False,
    )
    return interface


def main() -> None:
    """Start the Gradio app."""
    async def _launch() -> None:
        interface = await build_interface()
        interface.launch(
            server_name="0.0.0.0",
            server_port=int(os.getenv("PORT", "7860")),
        )
    asyncio.run(_launch())


if __name__ == "__main__":
    main()
