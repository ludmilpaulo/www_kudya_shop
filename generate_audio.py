from gtts import gTTS

# Text in Portuguese
text = "Você tem um novo pedido, por favor, verifique o aplicativo Kudya."

# Create a gTTS object
tts = gTTS(text, lang="pt")

# Save the audio file
tts.save("notification.mp3")

print("Audio file generated successfully.")
