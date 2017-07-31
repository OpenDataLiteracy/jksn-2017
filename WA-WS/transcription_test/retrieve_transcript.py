import subprocess
import speech_recognition as sr

# need to install ffmpeg and add to path before using
# install from https://ffmpeg.zeranoe.com/builds/
# extract and place in C:/
# add C:\ffmpeg\bin to system path

command = "ffmpeg -i C:/Users/Maxfield/Desktop/active/jksn-2017/WA-WS/transcription_test/test_briefing.mp4 -ab 160k -ac 2 -ar 44100 -vn WA-WS/transcription_test/test_audio.mp3"

subprocess.call(command, shell=True)

def strip_audio(video, output):
    command = "ffmpeg -i C:/Users/Maxfield/Desktop/active/jksn-2017/WA-WS/transcription_test/"
    command += video
    command += " -ab 160k -ac 2 -ar 44100 -vn WA-WS/transcription_test/"
    command += output

    subprocess.call(command, shell=True)

def create_transcript(audio_source, output):
    # use the audio file as the audio source

    r = sr.Recognizer()

    with sr.AudioFile(audio_source) as source:
        #reads the audio file. Here we use record instead of
        #listen
        audio = r.record(source)

    try:
        print("The audio file contains: " + r.recognize_google(audio))

    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")

    except sr.RequestError as e:
        print("Could not request results from Google Speech")


#strip_audio('test_briefing.mp4', 'test_audio.mp3')
create_transcript('test_audio.mp3', '')

# 40 minute video completed in 33 seconds
