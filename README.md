# Amazon_Bedrock_Nova_Sonic

🔊 Nova Sonic Realtime Voice Assistant (Python)

This project demonstrates how to build a fully realtime voice-based AI assistant using Amazon Nova Sonic, the low-latency speech-to-speech model available in Amazon Bedrock.
It allows live microphone input, streams audio to Sonic, and simultaneously receives real-time speech + text responses, which are played back instantly.

🚀 What This Script Does

Opens a bidirectional streaming connection to Amazon Nova Sonic using the new aws-sdk-bedrock-runtime client.

Sends a system instruction to define Sonic’s behavior.

Captures audio from the microphone in real time (16 kHz LPCM).

Streams audio chunks to Sonic using audioInput events.

Reads Sonic’s responses, including:

textOutput (transcribed model response)

audioOutput (24 kHz LPCM audio for playback)

Plays Sonic’s voice in real time using PyAudio.

Runs everything asynchronously:

Mic streaming

Sonic response reading

Audio playback

🧠 How It Works (Brief)

sessionStart
Initializes the realtime session and enables both text and audio modalities.

promptStart
Tells Sonic what type of output to generate (text + 24 kHz speech).

contentStart + textInput
Sends a system message that defines the assistant’s personality and style.

contentStart (AUDIO)
Signals that the user will start speaking.

audioInput
Streams microphone audio to Sonic in small base64-encoded chunks.

textOutput + audioOutput
Sonic responds with natural speech, and the script:

prints the assistant’s text

plays the returned audio

This creates a fluid, natural, voice-interactive AI experience.

🛠️ Technologies Used

Amazon Nova Sonic (Bedrock)

aws-sdk-bedrock-runtime (Python Realtime SDK)

PyAudio for capturing and playing PCM audio

AsyncIO for real-time concurrency

🎤 Result

You get a hands-free, real-time conversation with Nova Sonic — similar to a live voice assistant — entirely from Python and your microphone.
