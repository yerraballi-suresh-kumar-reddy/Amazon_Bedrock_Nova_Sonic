import asyncio, base64, json, uuid, pyaudio
from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
from aws_sdk_bedrock_runtime.config import Config
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

# Audio settings
IN_RATE, OUT_RATE, CHUNK = 16000, 24000, 1024
FORMAT = pyaudio.paInt16

def b64(x): return base64.b64encode(x).decode()  # convert audio bytes → base64 string

class Sonic:
    def __init__(self):
        # unique IDs required by Sonic
        self.prompt = str(uuid.uuid4())     # identifies this conversation turn
        self.text = str(uuid.uuid4())       # system prompt content ID
        self.audio = str(uuid.uuid4())      # user audio content ID
        self.q = asyncio.Queue()            # audio queue for playback

    async def send(self, s, obj):
        """Send any event (JSON) to Sonic stream."""
        chunk = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(bytes_=json.dumps(obj).encode())
        )
        await s.input_stream.send(chunk)

    async def start(self):
        """Start realtime Sonic session + system prompt + mic + speaker."""
        
        # Create Bedrock client using AWS CLI credentials
        cfg = Config(
            endpoint_uri="https://bedrock-runtime.us-east-1.amazonaws.com",
            region="us-east-1",
            aws_credentials_identity_resolver=EnvironmentCredentialsResolver()
        )
        client = BedrockRuntimeClient(cfg)

        # Open realtime bidirectional stream to Nova Sonic
        stream = await client.invoke_model_with_bidirectional_stream(
            InvokeModelWithBidirectionalStreamOperationInput(model_id="amazon.nova-sonic-v1:0")
        )

        # Start session: tell Sonic we want text + audio streaming
        await self.send(stream, {"event":{"sessionStart":{"modalities":["text","audio"]}}})

        # Describe output formats we expect (24 kHz audio, plain text)
        await self.send(stream, {"event":{"promptStart":{
            "promptName":self.prompt,
            "audioOutputConfiguration":{
                "mediaType":"audio/lpcm","sampleRateHertz":24000,"sampleSizeBits":16,
                "channelCount":1,"encoding":"base64","audioType":"SPEECH","voiceId":"matthew"
            },
            "textOutputConfiguration":{"mediaType":"text/plain"}
        }}})

        # SYSTEM prompt start
        await self.send(stream, {"event":{"contentStart":{
            "promptName":self.prompt,"contentName":self.text,"type":"TEXT",
            "role":"SYSTEM","textInputConfiguration":{"mediaType":"text/plain"}
        }}})

        # Actual instruction Sonic should follow
        await self.send(stream, {"event":{"textInput":{
            "promptName":self.prompt,"contentName":self.text,
            "content":"You are a helpful assistant speaking naturally."
        }}})

        # End SYSTEM prompt block
        await self.send(stream, {"event":{"contentEnd":{
            "promptName":self.prompt,"contentName":self.text
        }}})

        # Launch background tasks:
        asyncio.create_task(self.read(stream))  # read Sonic output
        asyncio.create_task(self.mic(stream))   # send mic input
        await self.speaker()                    # play audio output

    async def read(self, stream):
        """Read text + audio events from Sonic."""
        while True:
            out = await stream.await_output()        # wait for Sonic event
            part = await out[1].receive()
            if not part.value.bytes_: continue       # skip empty payloads
            msg = json.loads(part.value.bytes_.decode())

            # Print assistant text
            if "textOutput" in msg.get("event", {}):
                print("Assistant:", msg["event"]["textOutput"]["content"])

            # Queue audio for playback
            if "audioOutput" in msg.get("event", {}):
                await self.q.put(base64.b64decode(msg["event"]["audioOutput"]["content"]))

    async def mic(self, stream):
        """Continuously send microphone audio to Sonic."""
        pa = pyaudio.PyAudio()
        mic = pa.open(format=FORMAT, channels=1, rate=IN_RATE, input=True, frames_per_buffer=CHUNK)

        # Begin USER audio stream
        await self.send(stream, {"event":{"contentStart":{
            "promptName":self.prompt,"contentName":self.audio,"type":"AUDIO","role":"USER",
            "audioInputConfiguration":{
                "mediaType":"audio/lpcm","sampleRateHertz":16000,"sampleSizeBits":16,
                "channelCount":1,"encoding":"base64","audioType":"SPEECH","responsesEnabled":True
            }
        }}})

        print("🎤 Speak now…")

        # Capture → encode → send continuously
        while True:
            audio_bytes = mic.read(CHUNK, exception_on_overflow=False)
            await self.send(stream, {"event":{"audioInput":{
                "promptName":self.prompt,"contentName":self.audio,
                "content": b64(audio_bytes)
            }}})
            await asyncio.sleep(0.01)  # prevent CPU hogging

    async def speaker(self):
        """Play Sonic audio output."""
        pa = pyaudio.PyAudio()
        sp = pa.open(format=FORMAT, channels=1, rate=OUT_RATE, output=True)

        # Consume queued audio from read()
        while True:
            sp.write(await self.q.get())

# Run conversation
asyncio.run(Sonic().start())
