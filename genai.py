import google.generativeai as genai

genai.configure(api_key='AIzaSyC5aTzb6s1TcWlM9DDNnVoGw6egfEsJd7w')

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash-latest"
)

def genai_analysis(filename):

  file = upload_to_gemini(filename, mime_type="audio/wav")

  prompt = """
  Please provide a transcript for this audio and do sentiment analysis. 
  Return result should follow the below format: 
  
  TEXT: User's speech transcript
  Sentiment: Positive | Negative | Neutral
  """

  # result = model.generate_content([file, "Please provide a transcript for this audio and do sentiment analysis. Return result as json file. example: 'text': '<transcript of the audio>, 'sentiment': <positive or negative or neurtal> "])
  result = model.generate_content([file, prompt])
  print(f"{result.text}")

  f = open(filename + '_transcript_with_sentiment.txt','w')
  f.write(result.text)
  f.close()