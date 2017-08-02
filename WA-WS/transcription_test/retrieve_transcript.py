import subprocess
import speech_recognition as sr
from pydub import AudioSegment

# need to install ffmpeg and add to path before using
# install from https://ffmpeg.zeranoe.com/builds/
# extract and place in C:/
# add C:\ffmpeg\bin to system path

# video found here: http://video.seattle.gov:8080/media/council/briefing_073117V.mp4

# KIND OF WORKS!
# needs larger servers to actually handle the processing (memory of the splits)
# need to work on the split function itself
# the transcription is close, but definitely needs functionality on stack to allow for editing,
#   so transcription can be rough estimate of what was said, and then someone else can come put in
#   names, times, etc.

# apparently recognize sphinx works with that functionality but I will need to do more testing
# https://cmusphinx.github.io/wiki/tutorialsphinx4/

def strip_audio(video, output):
    command = "ffmpeg -i C:/Users/Maxfield/Desktop/active/jksn-2017/WA-WS/transcription_test/"
    command += video
    command += " -ab 160k -ac 2 -ar 44100 -vn WA-WS/transcription_test/"
    command += output

    subprocess.call(command, shell=True)

def split_audio(audio, output, splits):
    sound = AudioSegment.from_wav(audio)

    # len() and slicing are in milliseconds
    halfway_point = len(sound) / 2
    second_half = sound[halfway_point:]

    # Concatenation is just adding
    second_half_3_times = second_half + second_half + second_half

    # writing mp3 files is a one liner
    second_half_3_times.export(output, format="wav")

def create_transcript(audio_source, output):
    # use the audio file as the audio source

    r = sr.Recognizer()

    with sr.AudioFile(audio_source) as source:
        #reads the audio file. Here we use record instead of
        #listen
        audio = r.record(source)

        try:
            g_transcript = r.recognize_google(audio)
            print('google:', g_transcript)

            text_file = open(output, "w")
            text_file.write(g_transcript)
            text_file.close()

        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")

        except sr.RequestError as e:
            print("Could not request results from Google Speech")


directory = 'C:/Users/Maxfield/Desktop/active/jksn-2017/WA-WS/transcription_test/'
main_video_in = 'test_briefing.mp4'
main_audio_out = 'test_audio.wav'
sub_audio_in = 'sub_test_audio.wav'
sub_audio_out = 'split_audio.wav'
transcribe_out = 'transcribe_out.txt'

#strip_audio(main_video_in, main_audio_out)
#split_audio(directory + sub_audio_in, directory + sub_audio_out, 10)
#create_transcript(directory + sub_audio_in, directory + transcribe_out)

# 40 minute video completed in 33 seconds
