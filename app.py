import os
import uvicorn
from server.main import app

import spaces

@spaces.GPU
def dummy_gpu_function():
    pass

# Hugging Face Spaces (Gradio SDK) selalu mencari file app.py dan membuka port 7860.
# Dengan file ini, kita "mengelabui" sistem Gradio agar menjalankan FastAPI kita di port tersebut secara gratis!

if __name__ == "__main__":
    # Paksa aplikasi untuk berjalan di port 7860
    os.environ["APP_PORT"] = "7860"
    uvicorn.run(app, host="0.0.0.0", port=7860)
