import gradio as gr
import asyncio
import edge_tts
import os

# မြန်မာအသံ (၂) မျိုးတည်းကိုသာ ရွေးချယ်ခွင့်ပေးခြင်း
VOICES = {
    "မြန်မာ (အမျိုးသမီး) - Nilar": "my-MM-NilarNeural",
    "မြန်မာ (အမျိုးသား) - Thiha": "my-MM-ThihaNeural"
}

async def generate_voice(text, voice_name, rate, pitch):
    if not text.strip():
        return None
        
    voice_id = VOICES[voice_name]
    
    # Format speed and pitch for edge-tts
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    
    output_file = "output_voice.mp3"
    
    try:
        # Latest edge-tts communication
        communicate = edge_tts.Communicate(text, voice_id, rate=rate_str, pitch=pitch_str)
        await communicate.save(output_file)
        return output_file
    except Exception as e:
        print(f"Detailed Error: {str(e)}")
        raise gr.Error(f"အသံထုတ်လုပ်ရာတွင် အမှားအယွင်းရှိနေပါသည်: {str(e)}")

# Gradio UI - Version 4.x အသစ်ဆုံးပုံစံ
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🇲🇲 Myanmar Male/Female TTS (Railway Optimized)")
    
    with gr.Row():
        with gr.Column():
            input_text = gr.Textbox(
                label="စာသားထည့်ပါ", 
                lines=5, 
                placeholder="ဒီမှာ စာရိုက်ပါ..."
            )
            
            # မြန်မာ ၂ မျိုးတည်းသာ ပြသရန်
            voice_opt = gr.Dropdown(
                choices=list(VOICES.keys()), 
                label="အသံရွေးချယ်ပါ", 
                value="မြန်မာ (အမျိုးသမီး) - Nilar"
            )
            
            with gr.Row():
                rate_slider = gr.Slider(minimum=-50, maximum=50, value=0, label="အမြန်နှုန်း (Speed %)")
                pitch_slider = gr.Slider(minimum=-50, maximum=50, value=0, label="အသံနေအထား (Pitch Hz)")
            
            btn = gr.Button("အသံထုတ်မည်", variant="primary")
            
        with gr.Column():
            audio_output = gr.Audio(label="ရလဒ် အသံဖိုင်", type="filepath")

    btn.click(
        fn=generate_voice, 
        inputs=[input_text, voice_opt, rate_slider, pitch_slider], 
        outputs=audio_output
    )

if __name__ == "__main__":
    # Railway PORT configuration
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
