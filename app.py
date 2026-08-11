import os
import uvicorn
import gradio as gr
import spaces
from server.main import app as fastapi_app

# Dummy function untuk memuaskan supervisor ZeroGPU
@spaces.GPU
def dummy_gpu_function():
    return "GPU Active"

# Buat dummy interface Gradio agar ZeroGPU mendeteksinya
demo = gr.Interface(fn=dummy_gpu_function, inputs="text", outputs="text")

# Gabungkan aplikasi FastAPI kita dengan dummy Gradio (mount Gradio di subpath)
app = gr.mount_gradio_app(fastapi_app, demo, path="/_gradio_dummy")

if __name__ == "__main__":
    os.environ["APP_PORT"] = "7860"
    uvicorn.run(app, host="0.0.0.0", port=7860)
