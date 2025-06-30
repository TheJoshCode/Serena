from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
import tempfile
import os
from TTS.api import TTS
from fastapi.responses import FileResponse, JSONResponse
import logging
import uvicorn

# Setup logging for detailed debug output
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

logging.debug("Starting FastAPI app")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.debug("CORS middleware configured")

# Load TTS model once, log loading
logging.debug("Loading TTS model...")
tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False, gpu=False)
logging.debug("TTS model loaded successfully")

class Message(BaseModel):
    text: str

@app.post("/api/respond")
def respond(msg: Message):
    logging.debug(f"Received request with text: {msg.text}")

    try:
        # Get response from Qwen model
        logging.debug("Calling ollama chat model 'qwen:3-1.7b'")
        system_prompt = (
            "Your name is Serena. You are a compassionate, attentive AI therapist trained to support users "
            "through reflective conversation, emotional insight, and gentle guidance. "
            "You speak in a warm, calming tone and create a safe, non-judgmental space for users to share their thoughts. "
            "Avoid giving medical advice or diagnoses. Instead, ask thoughtful questions, validate emotions, and encourage self-discovery. "
            "Use clear, empathetic language, and respond in a grounded, human-like way."
        )
        res = ollama.chat(
            model='qwen3:1.7b',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": (msg.text + " /no_think")}
            ]
        )
        logging.debug(f"Received response from ollama: {res}")

        response_text = res['message']['content']
        logging.debug(f"Extracted response text: {response_text}")

        # Generate TTS audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            audio_path = f.name
            logging.debug(f"Temporary audio file created at: {audio_path}")

        tts.tts_to_file(text=response_text, file_path=audio_path, speaker="p268")
        logging.debug(f"TTS audio generated at: {audio_path}")

        response = {"response": response_text, "audio_url": f"/api/audio?path={audio_path}"}
        logging.debug(f"Returning response JSON: {response}")

        return JSONResponse(content=response)

    except Exception as e:
        logging.error(f"Error in /api/respond: {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/audio")
def get_audio(path: str):
    logging.debug(f"Audio request for path: {path}")

    if not os.path.isfile(path):
        logging.error(f"File not found: {path}")
        return JSONResponse(content={"error": "Audio file not found"}, status_code=404)

    try:
        logging.debug(f"Serving audio file: {path}")
        return FileResponse(path, media_type="audio/wav", filename="response.wav")
    except Exception as e:
        logging.error(f"Error serving audio file: {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/test")
def test():
    logging.debug("Test endpoint called")
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
