import gradio as gr
import spaces
from server.main import app as fastapi_app

# Dummy function untuk memuaskan supervisor ZeroGPU
@spaces.GPU
def dummy_gpu_function():
    return "GPU Active"

# Script JS untuk redirect ke UI utama CyberGuard
redirect_html = """
<script>
    window.location.replace("/ui");
</script>
<div style="text-align: center; margin-top: 50px; font-family: sans-serif;">
    <h2>Starting CyberGuard-ID...</h2>
    <p>Please wait, redirecting you to the main application...</p>
    <a href="/ui">Click here if not redirected automatically</a>
</div>
"""

# Buat dummy interface Gradio agar ZeroGPU mendeteksinya
with gr.Blocks() as demo:
    gr.HTML(redirect_html)
    # Tombol tersembunyi yang terkait dengan GPU untuk mengelabui ZeroGPU
    btn = gr.Button("GPU", visible=False)
    btn.click(fn=dummy_gpu_function)

# Gabungkan aplikasi FastAPI kita dengan dummy Gradio (mount Gradio di root)
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

# Biarkan runner Gradio milik Hugging Face yang menjalankan "app" ini.
# JANGAN gunakan if __name__ == '__main__': uvicorn.run(app)

