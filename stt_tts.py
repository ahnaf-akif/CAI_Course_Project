from google.cloud import speech
from google.protobuf import wrappers_pb2
from google.cloud import texttospeech_v1

client_stt = speech.SpeechClient()
client_tts = texttospeech_v1.TextToSpeechClient()

def sample_recognize(content):
  audio=speech.RecognitionAudio(content=content)

  config=speech.RecognitionConfig(
  # encoding=speech.RecognitionConfig.AudioEncoding.MP3,
  # sample_rate_hertz=24000,
  language_code="en-US",
  model="latest_long",
  audio_channel_count=1,
  enable_word_confidence=True,
  enable_word_time_offsets=True,
  )

  operation=client_stt.long_running_recognize(config=config, audio=audio)

  response=operation.result(timeout=90)

  txt = ''
  for result in response.results:
    txt = txt + result.alternatives[0].transcript + '\n'

  return txt

def speech_to_text(fileName):
    file = open(fileName,'rb')
    data = file.read()
    file.close()

    text = sample_recognize(data)

    print(text)

    file = open(fileName + '.txt','w')
    file.write(text)
    file.close()

    # Saving the sentiment text file
    # file_sentiment = open(fileName + '_sentiment.txt', 'w')
    # file_sentiment.write("Sentiment Type: " + sentiment_type(text))
    # file_sentiment.close()

    return text
    

def sample_synthesize_speech(text=None, ssml=None):
    input = texttospeech_v1.SynthesisInput()
    if ssml:
      input.ssml = ssml
    else:
      input.text = text

    voice = texttospeech_v1.VoiceSelectionParams()
    voice.language_code = "en-UK"
    # voice.ssml_gender = "MALE"

    audio_config = texttospeech_v1.AudioConfig()
    audio_config.audio_encoding = "LINEAR16"

    request = texttospeech_v1.SynthesizeSpeechRequest(
        input=input,
        voice=voice,
        audio_config=audio_config,
    )

    response = client_tts.synthesize_speech(request=request)

    return response.audio_content

def text_to_speech(text, speech_file_path):
    wav = sample_synthesize_speech(text)

    file = open(speech_file_path,'wb')
    file.write(wav)
    file.close()
