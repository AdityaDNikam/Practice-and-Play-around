import asyncio
from dotenv import load_dotenv
load_dotenv()
import speech_recognition as sr
from openai import OpenAI, AsyncOpenAI
from openai.helpers import LocalAudioPlayer
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

async def tts(speech: str):
    async with openai_client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=speech,
        response_format="pcm"
    ) as response:
        await LocalAudioPlayer().play(response)


def main():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        r.pause_threshold = 2
        print("Speak Something...")
        audio = r.listen(source)
        STT = r.recognize_google(audio)
        
        SYSTEM_PROMPT = '''You are an expert voice agent and you need to answer the input prompts in less than 100 words, direct and on point.'''

        responce = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": STT}
            ]
        )

        print("STT :", STT)
        print("AI :", responce.choices[0].message.content)
        asyncio.run(tts(responce.choices[0].message.content))


if __name__ == "__main__":
    main()
