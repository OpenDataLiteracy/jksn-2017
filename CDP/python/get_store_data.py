#import pyrebase
import requests
import subprocess
import shutil
from bs4 import BeautifulSoup as bs
import json
import datetime
import time
import speech_recognition as sr
import re
from pprint import pprint
import os
from pydub import AudioSegment
import math
import operator
import sys
import Levenshtein


# database configuration and admin settings
# from configure_keys import *


# DATABASE CONNECTION
# firebase = pyrebase.initialize_app(config)
# db = firebase.database()

# LEGISTAR

# clean_events_data for an event item
#   item: the event unique item returned from the legistar events api
#
#   item must contain:
#       EventLocation: the location of where the event took place
def clean_events_data(item):

    # create a storage time attribute
    current_dt = datetime.datetime.now()
    item['EventStoredDatetime'] = str(current_dt)

    # reconstruct the EventLocation attribute
    item['EventLocation'] = item['EventLocation'].replace('\r', '').replace('\n', ', ')

    return item

# clean_bodies_data for a body item
#   item: the body unique item returned from legistar bodies api
def clean_bodies_data(item):

    # create a storage time attribute
    current_dt = datetime.datetime.now()
    item['BodyStoredDatetime'] = str(current_dt)

    return item

# get_all_data for a dictionary of packed routes
#   packed_route must contain:
#       path:           this will be the overarching body for the database or included in the filename
#       url:            the legistar url to pull data from
#       storage key:    the key that will be used to store an item in the database
#       cleaning_func:  a function that will be used to clean the data
#
#   packed_route formatted:
#       '{ path : [ url, storage key, cleaning_func ] }'
def get_all_data(packed_routes, prints=False, toLocal=True):

    # for each path and packed_route
    for path, routes in packed_routes.items():
        if prints:
            print('getting data from:', routes[0])
            print('-----------------------------------------------------------')

        # request the url and store the data in json
        r = requests.get(routes[0])
        r = r.json()

        # check output target
        if not toLocal:
            for item in r:
                if prints:
                    print('working on:', item)

                # find the storage key
                store_id = item[routes[1]]
                del item[routes[1]]

                # clean data
                item = routes[2](item)

                if prints:
                    print('completed:', item)

                # store the data in the database
                db.child(path).child(store_id).set(item)

                if prints:
                    print('stored:', path, store_id)
                    print('-------------------------------------------------------')
        # to local
        else:
            # clean data
            cleaned_r = list()
            for item in r:
                item = routes[2](item)
                cleaned_r.append(item)

            # store data locally
            with open('WA-WS/poc/python/local_store_' + path + '.json', 'w', encoding='utf-8') as outfile:
                json.dump(cleaned_r, outfile)

            outfile.close()
            time.sleep(2)

# get_test_data for url
#   url: the legistar url to pull data from
def get_test_data(url, prints=True):

    # get data from url
    r = requests.get(url)
    r = r.json()

    if prints:
        pprint(r)

    # return json for manipulation
    return r

# TRANSCRIPTION

# progress print function
# https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

# clean_video_filename for a video file
#   item: the filename to be cleaned of spaces
def clean_video_filename(item):

    # check filename for spaces:
    if ' ' in item:

        # replace the spaces with underscore
        item = item.replace(' ', '_')

    return item

# rename_video_files for an os location
#   video_dir: path in os to video files
#   cleaning_func: the cleaning function to repair or fix filenames
def rename_video_files(video_dir, cleaning_func=clean_video_filename):

    # ensure path safety
    video_dir = check_path_safety(video_dir)

    # get the current working directory for comparison
    cwd = os.getcwd()

    # check if the path is in the current working directory
    if video_dir not in cwd:

        # update the directory to match path
        os.chdir(video_dir)

    # for each file run the cleaning_func
    for filename in os.listdir():
        os.rename(filename, clean_video_filename(filename))

# check_path_safety to ensure paths end with '/'
#   path: the directory path to be checked for safe endings
def check_path_safety(path):
    if '/' == path[:1]:
        path = path[1:]

    if '/' != path[-1:]:
        path += '/'

    return path

# video_to_audio_rename with '.wav'
#   video_in: the path for the video file to be renamed
def video_to_audio_rename(video_in):
    return video_in[:-4] + '.wav'

# used as the default scraping_function for get_video_feeds
#   path: the label for a general feed
#   routes: the passed through route information
def scrape_seattle_channel(path, routes, prints=True):

    # request the url and scrape the page to collect information
    r = requests.get(routes[0])
    soup = bs(r.content, 'html.parser')

    # each route has multiple videos to collect
    path_feeds = list()
    paginations = soup.find_all('div', class_='col-xs-12 col-sm-8 col-md-9')

    if prints:
        print('found', len(paginations), 'video elements for:', path)

    # for each video section find and store the video information
    for pagination in paginations:
        path_feed = dict()

        # page link
        bs_link = str(pagination.find('a')['href'])
        path_feed['link'] = bs_link

        # video source
        try:
            bs_video = str(pagination.find('a')['onclick'])
            video_end = bs_video.find('.mp4\',')
            bs_video = str(pagination.find('a')['onclick'])[26: video_end + 4]
        except:
            bs_video = ''
        path_feed['video'] = bs_video

        # agenda
        try:
            bs_agenda = str(pagination.find('div', class_='titleExcerptText').find('p').text)
            if 'Agenda: ' in bs_agenda:
                bs_agenda = bs_agenda[8:]
            path_feed['agenda'] = bs_agenda
        except:
            path_feed['agenda'] = ''

        # date published
        bs_datetime = str(pagination.find('div', class_='videoDate').text)
        path_feed['datetime'] = bs_datetime

        # body name
        path_feed['body'] = routes[1]

        # path name
        path_feed['path'] = path

        # append this feed to list of feeds
        path_feeds.append(path_feed)

        if prints:
            print('constructed true link:', path_feed)

    if prints:
        print('completed feed construction for:', path)
        print('-----------------------------------------------------------')

    return path_feeds

# get_video_feeds for a dictionary of packed routes
#   packed_route must contain:
#       path:           this will be the overarching body for the database or included in the filename
#       url:            the seattle_channel url to pull data from
#       body_name:      the true body_name used by legistar
#
#   packed_route formatted:
#       '{ path : [ url, body_name ] }'
#
#   storage_path: the path to the json file for where to store the constructed_feeds
#
#   scraping_function must return:
#       path_feeds must contain:
#           path_feed: dictionary of video source information
#
#           path_feed must contain:
#               link: the link to where the video file is viewable (optional)
#               video: the file path to where the video is stored on the cities servers
#               agenda: the agenda/ description of the video as labeled by the city (optional)
#               datetime: the datetime that the video was published (optional)
#               body: the associated body, given by routes[1]
#
#           path _feed formatted:
#               '{ link: l, video: v, agenda: a, datetime: d, body: b }'
#
#       path_feeds formatted:
#           '[ path_feed, path_feed, ... , path_feed ]'
def get_video_feeds(packed_routes, storage_path, scaping_function=scrape_seattle_channel, prints=True, toLocal=True):

    # create empty list to store video information
    constructed_feeds = list()

    # for each path and packed_route
    for path, routes in packed_routes.items():
        if prints:
            print('starting work on:', path)

        # attach the found feeds to the storage list
        for item in scraping_function(path=path, routes=routes, prints=prints):
            constructed_feeds.append(item)

    # store the found feeds locally
    if toLocal:
        previous_feeds = list()

        # add to previous store
        try:

            # read the previous store
            with open(storage_path, 'r') as previous_store:
                temp = previous_store.read()

            # safety
            previous_store.close()
            time.sleep(2)

            # load the store data
            previous_feeds = json.loads(temp)

            if prints:
                print('previous store length:\t', len(previous_feeds))

            previous_videos = list()

            for previous_feed in previous_feeds:
                previous_videos.append(previous_feed['video'])

            # only add new items
            for new_feed in constructed_feeds:

                if new_feed['video'] not in previous_videos:
                    previous_feeds.append(new_feed)

            if prints:
                print('new store length:\t', len(previous_feeds))

            # set the new feeds appended to old
            constructed_feeds = previous_feeds

        # no previous store found, create new
        except Exception as e:
            print(e)

            if prints:
                print('no previous storage found...')

        with open(storage_path, 'w', encoding='utf-8') as outfile:
            json.dump(constructed_feeds, outfile)

        # safety
        outfile.close()
        time.sleep(2)

    # return the data for manipulation
    return constructed_feeds

# get_video_sources for a json/ dictionary of video information
#   objects_file: the path to the stored video feeds file containing video_json objects
#       video_json must contain:
#           label:           this is the assigned body name assigned during the get_video_feeds process 'path'
#           data:            the list of data returned from the get_video_feeds process
#               datum must contain:
#                   link:       the pagelink for where the video is on seattle channel website
#                   video:      the video source, should be a .mp4 file
#                   agenda:     an agenda description
#                   datetime:   the datetime of when the video took place
#                   body:       the name of the body which was holding the event
#
#               data formatted:
#                   [ { link: l, video: v, agenda: a, datetime: d, body: b } ]
#
#       video_json formatted:
#           '{ label :  data }'
#
#   storage_path: the path to where to store the videos
#   throughput_path: the path to where we can check if we need to store the video
def get_video_sources(objects_file, storage_path, throughput_path, prints=True):

    # ensure path safety
    storage_path = check_path_safety(storage_path)
    throughput_path = check_path_safety(throughput_path)

    # ensure directory safety
    if not os.path.exists(storage_path):
        os.mkdir(storage_path)

    # read the video_feeds
    with open(objects_file) as objects_:
        objects = json.load(objects_)

    # ensure safe close
    objects_.close()

    completed_stores = 0

    # for each dictionary in list of data
    for datum in objects:

        # check that a video source exists
        if datum['video'] != '':

            # create a video tag for storage
            try:
                tag_start = datum['video'].index('_')
                tag = datum['video'][tag_start + 1:]
            except:
                tag = datum['video'][-11:]

            # ensure safety against errors
            try:

                # check it the video exists
                if os.path.exists(throughput_path + clean_video_filename(datum['path']) + '_' + tag[:-4] + '.wav'):
                    if prints:
                        print('audio stored previously, skipping', datum['video'], 'collection...')

                # video must need to be downloaded
                else:
                    if prints:
                        print('collecting:', datum['video'])

                    # request the video source and store the file
                    r = requests.get(datum['video'], stream=True)
                    if r.status_code == 200:
                        with open((storage_path + clean_video_filename(datum['path']) + '_' + tag), 'wb') as mp4_out:
                            r.raw.decode_content = True
                            shutil.copyfileobj(r.raw, mp4_out)

                            completed_stores += 1

                        mp4_out.close()
                        time.sleep(2)

            # print the exception for error handling
            except Exception as e:

                print(e)

    if prints:
        print('completed all video collections')
        print('----------------------------------------------------------------------')

    return completed_stores

# strip_audio using subprocess to run ffmpeg
#   project_directory: the overarching project directory, check_path_safety
#   video_dir: the specific video directory to get, check_path_safety
#   audio_dir: the specific audio directory to store, check_path_safety
#   video_in: the specific video file to get
#   audio_out: the specific audio file to store
def strip_audio(video_dir, audio_dir, video_in, audio_out):
    command = 'ffmpeg -hide_banner -i '

    command += video_dir
    command += video_in
    command += ' -ab 160k -ac 2 -ar 44100 -vn '
    command += audio_dir
    command += audio_out

    subprocess.call(command, shell=True)

# strip_audio_from_directory for given directory and dirs
#   project_directory: the overarching project directory, check_path_safety
#   video_dir: the specific video directory to get, check_path_safety
#   audio_dir: the specific audio directory to store, check_path_safety
#   naming_function: a function to construct a name for the output video_file
#   delete_video: boolean value to decide if you want to keep the video portion or discard after audio construction
def strip_audio_from_directory(video_dir, audio_dir, video_dir_cleaning_function=rename_video_files, naming_function=video_to_audio_rename, end_path='transcripts/', delete_video=False, prints=True):

    # check_path_safety for all path variables
    video_dir = check_path_safety(video_dir)
    audio_dir = check_path_safety(audio_dir)

    if not os.path.exists(audio_dir):
        os.mkdir(audio_dir)

    # ensure file naming conventions follow same pattern
    video_dir_cleaning_function(video_dir)

    # set working directory to the video_dir
    os.chdir(video_dir)

    if prints:
        print('set cwd to:', os.getcwd())

    completed_strips = 0

    # for each video in the found directory
    for video_file in os.listdir():

        # construct the audio file name
        audio_out_label = naming_function(video_file)

        # ensure safety against errors
        try:

            # check if the audio exists
            if os.path.exists(audio_dir + audio_out_label):
                if prints:
                    print('audio stored previously, skipping', video_file, 'strip...')

            # audio needs to be stripped
            else:

                if prints:
                    print('stripping audio using:', video_dir, audio_dir, video_file, audio_out_label)

                # strip the audio
                strip_audio(video_dir, audio_dir, video_file, audio_out_label)

                completed_strips += 1

        except Exception as e:

            print(e)

        # ensure safety against already removed files
        try:

            # check if to delete
            if delete_video:

                if prints:
                    print('delete_video is marked as True, deleting original video file for:', audio_out_label)

                os.remove(video_dir + video_file)

        # file already removed
        except FileNotFoundError as e:

            if prints:
                print('File already removed')

    return completed_strips

# name_audio_splits for a project_directory, a targetted output_directory, and a list of audio_splits
#   project_directory: the overarching project directory path
#   output_directory: the containing folder for where the audio_splits will result to
def name_audio_splits(project_directory, output_directory, audio_splits):

    # create empty dict for labels and associated split files
    split_names = dict()

    # simple name by index value
    for i in range(len(audio_splits)):
        split_names[project_directory + output_directory + str(i) + '.wav'] = audio_splits[i]

    # return dict
    return split_names

# split_audio_into_parts for an overarching project_directory and a targetted audio file
#   project_directory: the overarching project directory path where the audio file is located
#   audio_file: the specific file you want to split
#   naming_function: a function to assign names to the audio splits, (WORK IN PROGRESS, DON'T CHANGE FROM DEFAULT)
#   split_length: the time in ms for the length of an individual audio split
#   splits_directory: the output directory for where all the splits folder will then be nested
def split_audio_into_parts(project_directory, audio_file, naming_function=name_audio_splits, split_length=18000, override_splits=False, splits_directory='transcripts/', prints=True):

    # check_path_safety for all pathing variables
    project_directory = check_path_safety(project_directory)
    splits_directory = check_path_safety(splits_directory)

    # create the subfolder label for checking and future storage
    subfolder = check_path_safety(splits_directory + audio_file[:-4])

    # ensure the splits directory exists
    if not os.path.exists(project_directory + splits_directory):
        os.mkdir(project_directory + splits_directory)

    # create the specific store_directory for checking and future storage
    store_directory = check_path_safety(project_directory + subfolder)

    # if the transcript exists already, no need to create splits unless directly overriden
    if os.path.exists(project_directory + splits_directory + audio_file[:-4] + '.txt') and not override_splits:

        if prints:
            print('transcript exists, no need for splits...')

        return store_directory

    if prints:
        print('creating audio splits for:\t', project_directory + audio_file)

    # check if the splits already exist
    if os.path.exists(store_directory):

        if prints:
            print('audio splits for:\t', audio_file, 'already exists...')

        # they existed, return the store_directory path
        return store_directory

    # create an AudioSegment from full audio file
    audio_as_segment = AudioSegment.from_wav(project_directory + audio_file)

    if prints:
        print('audio was stored as segment...')

    # create the list of smaller audio segments according to split_length
    audio_segments = [audio_as_segment[i:i+split_length] for i in range(0, len(audio_as_segment), split_length)]

    if prints:
        print('audio splits created successfully...')

    # combine the audio segments with their naming conventions, for now, this is forced
    split_names = name_audio_splits(project_directory=project_directory, output_directory=subfolder, audio_splits=audio_segments)

    if prints:
        print('audio splits assigned names based off of', str(naming_function) + '...')

    # create the storage directory
    os.mkdir(store_directory)

    total_s = len(audio_segments)
    i = 0

    # store each split AudioSegment under its associated label
    for output_path, split in split_names.items():
        split.export(output_path, format='wav')

        if prints:
            progress(count=i, total=total_s)

        i += 1

    if prints:
        print('')

    if prints:
        print('created audio splits for:\t', audio_file, '\t||\t', store_directory)

    # return the store_directory path
    return store_directory

# name_transcription simple switch to file
#   audio_label: the current audio filename
def name_transcription(audio_label):
    return audio_label[:-1] + '.txt'

#generate_transcript_from_audio_splits for a directory of audio files each less than 18 seconds in length
#   audio_directory: the directory of audio splits path you want to generate transcripts for
#   naming_function: a naming function for labeling the generated transcripts and storing them
def generate_transcript_from_audio_splits(audio_directory, naming_function=name_transcription, prints=True):

    # check_path_safety for audio splits directory
    audio_directory = check_path_safety(audio_directory)

    # construct a transcribed_name for checking and future processing
    transcribed_name = name_transcription(audio_directory)

    # check if the transcription already exists
    if os.path.exists(transcribed_name):
        print('transcript for:\t', transcribed_name, 'already exists...')
        return 'existed, not opened'

    if prints:
        print('starting transcription from audio splits in:\t', audio_directory)

    # no file found, start transcription engine
    r = sr.Recognizer()

    # ensure the current working directory is the audio_directory
    os.chdir(audio_directory)

    # start transcription string
    transcript = ''

    # find audio splits
    splits = os.listdir()

    if prints:
        print('found', len(splits), 'splits in directory to transcribe from...')

    total_s = len(splits)

    # for each split (assuming standard splits naming)
    for i in range(total_s):

        # follow google transcription engine process
        with sr.AudioFile(audio_directory + str(i) + '.wav') as source:

            # record audio
            audio = r.record(source)

            try:

                # try to transcribe the recording
                g_transcript = r.recognize_google(audio)

                # add successful transcription to cumulative transcript
                transcript += ' ' + g_transcript

            # no reason to stop transcription process with UVE, but alert user of error
            except sr.UnknownValueError as e:
                pass

            # major error, stop the engine and return
            except sr.RequestError as e:
                return 'Could not request results from Google Speech...', e

            if prints:
                progress(count=i, total=total_s)

    # transcription fence post fix
    transcript = transcript[1:]

    # create and store the transcription in a file
    with open(transcribed_name , "w") as outfile:
        outfile.write(transcript)

    outfile.close()
    time.sleep(2)

    if prints:
        print('stored transcription at:\t', transcribed_name)

    if prints:
        print('created transcript for:\t', transcribed_name, '\t||\t',  transcript[:20] + '...')

    # return the transcript string
    return transcript

# generate_transcripts_for_directory for a directory of audio files
#   project_directory: the directory path you want to generate transcripts for
#   transcript_naming_function: a naming function for labeling the generated transcripts and storing them
#   delete_originals: boolean to determine if you want to delete the original audio files once transcription is completed
#   delete_splits: boolean to determine if you want to delete the audio split files once transcription is completed
def generate_transcripts_from_directory(project_directory, transcript_naming_function=name_transcription, audio_splits_directory='transcripts/', delete_originals=False, delete_splits=False, prints=True):

    # check_path_safety for project
    project_directory = check_path_safety(project_directory)
    audio_splits_directory = check_path_safety(audio_splits_directory)

    # after check, set the directory to match
    os.chdir(project_directory)

    if prints:
        print('starting work for', project_directory, '...')
        print('-------------------------------------------------------')

    completed_transcripts = 0

    # for all .wav files create audio splits and generate transcript
    for filename in os.listdir():

        # ensure file is valid for transcription process
        if '.wav' in filename:

            # split_audio_dir = project_directory + audio_splits_directory + filename[:-4] + '.txt'
            #
            # # check if transcript exists before creating splits
            # if not os.path.exists(audio_splits_directory + filename[:-4] + '.txt'):

            # create audio splits and save the splits directory for use in processing transcript
            split_audio_dir = split_audio_into_parts(project_directory=project_directory, audio_file=filename, splits_directory=audio_splits_directory, prints=prints)

            # create the transcript from the audio split directory
            transcript = generate_transcript_from_audio_splits(audio_directory=split_audio_dir, naming_function=transcript_naming_function, prints=prints)

            completed_transcripts += 1

            # check if the user wants to delete the created audio splits
            if delete_splits:

                # files exist
                try:

                    # ensure safety in file deletion
                    os.chdir(project_directory)

                    # they do, delete folder and all contents
                    shutil.rmtree(split_audio_dir)

                    if prints:
                        print('delete_splits marked true, deleted audio splits for:\t', filename)

                # files don't exist because previous transcription creation
                except FileNotFoundError as e:

                    # files were previously deleted
                    if prints:
                        print('delete_splits marked true, audio was never created, thus never deleted for:\t', filename)

            # check if user wants to delete original audio file
            if delete_originals:

                # they do, delete file in original project_directory
                os.remove(project_directory + filename)

                if prints:
                    print('delete_originals marked true, deleted original audio for:\t', filename)

            if prints:
                print('---------------------------------------------------------------------------')

    if prints:
        print('completed transcript generation for all files in', project_directory)

    return completed_transcripts

# RELEVANCY

# generate_all_keywords for a document
#   document: the direct path to the document
def generate_words_from_doc(document, prints=True):

    # initialize py-dict for synonyms
    # dictionary = PyDictionary()

    # construct results dictionary object to store all generated information
    results = dict()

    # construct base term frequency dictionary object to store term frequency information
    results['tf'] = dict()

    if prints:
        print('started work on:', document, '...')

    # open the transcription file and read the content
    with open(document) as transcript_file:
        transcript = transcript_file.read()

    transcript_file.close()
    time.sleep(2)

    # replace any conjoining characters with spaces and split the transcription into words
    words = re.sub('[_-]', ' ', transcript).split()

    if prints:
        print('split words...')

    # for each word in the transcription
    for word in words:

        # get rid of any non-alphanumeric characters
        word = re.sub('[!@#$]', '', word)

        # temporary fixes for transcription generated decimals and percents
        word = word.replace('/', ' over ')
        word = word.replace('.', ' point ')
        word = word.lower()

        # try adding to the word counter
        try:
            results['tf'][word]['count'] += 1

        # must not have been initialized yet
        except:

            # construct the synonyms list
            synonym_add_list = list()

            # to_check_synonyms = dictionary.synonym(word)
            #
            # if type(to_check_synonyms) is list:
            #     for synonym in dictionary.synonym(word):
            #         if ' ' not in synonym_add_list:
            #             synonym_add_list.append(synonym)

            # initialize the word counter and add the synonyms
            results['tf'][word] = {'count': 1, 'synonyms': synonym_add_list}

    # store the word length of the transcription
    results['length'] = float(len(words))

    if prints:
        print('initial pass for transcript complete')

    # for each word in the generated term frequency dictionary
    for word, data in results['tf'].items():

        # compute the true term frequency
        results['tf'][word]['score'] = float(data['count']) / results['length']

    if prints:
        print('secondary pass for transcript complete, sending completed dictionary')

    # return the completed term frequency dictionary
    return results

# generate_tfidf_from_directory for a directory of transcripts
#   project_directory: the directory path where transcripts are stored
#   output_file: the output file path to store the final tfidf json object
def generate_tfidf_from_directory(project_directory, output_file, prints=True):

    # check_path_safety for project
    project_directory = check_path_safety(project_directory)

    # after check, set the directory to match
    os.chdir(project_directory)

    if prints:
        print('starting work on:', project_directory, '...')

    # initialize results dictionary
    results = dict()

    # initialize base dictionaries for storage of deep information
    results['words'] = dict()
    results['transcripts'] = dict()

    transcript_counter = 0

    # for all .txt files generate words information and calculate tfidf
    for filename in os.listdir():

        # ensure file is valid for tfidf process
        if '.txt' in filename:

            # increment total transcriptions counter
            transcript_counter += 1

            # get words information for file
            file_results = generate_words_from_doc(document=project_directory+filename, prints=prints)

            if prints:
                print('adding word set to corpus...')

            # get results for all words in corpus
            for word, score in file_results['tf'].items():

                # try adding to word counter
                try:
                    results['words'][word] += 1

                # was not initialized yet
                except:
                    results['words'][word] = 1

            # add single file results to total file results
            results['transcripts'][filename[:-4]] = file_results

            if prints:
                print('completed file:', filename, '...')
                print('---------------------------------------------------------------')

    # add corpus results to total file results
    results['corpus'] = float(transcript_counter)

    if prints:
        print('starting second pass word tfidf scoring')
        print('---------------------------------------------------------------')

    # for each transcript construct a tfidf dictionary to hold completed computation
    for transcript, data in results['transcripts'].items():

        # deep copy
        temp_data_hold = dict(data)

        # base layer for storage
        data['tfidf'] = dict()

        # for each word compute tfidf score
        for word, score in temp_data_hold['tf'].items():

                # debug items
                # print('transcript:', transcript, '\tword:', word, '\ttf score:', score, '\n\toccurances:', score['score'] * data['length'], '\tlength:', data['length'])

                # actual computation
                data['tfidf'][word] = float(score['score']) * math.log(results['corpus'] / float(results['words'][word]))

    if prints:
        print('completed all files, storing and returning results for:', project_directory)
        print('----------------------------------------------------------------------------------------')

    # completed all computation, dump into output file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(results, outfile)

    outfile.close()
    time.sleep(2)

    # return the final dictionary object
    return results

# predict_relevancy for a corpus of tfidf documents
#   search: the word, phrase, or sentence to find in the corpus
#   tfidf_store: the tfidf created json object's path created by generate_tfidf_from_directory
#   edit_distance: boolean true and false allowance of similar (misspelled) search terms
#   adjusted_distance_stop: float value to determine the cut off point of search term similarity
#   results: number of results you want to recieve back
def predict_relevancy(search, tfidf_store, edit_distance=True, adjusted_distance_stop = 0.26, results=10):

    # open the locally stored json
    with open(tfidf_store) as data_file:
        tfidf_dict = json.load(data_file)

    data_file.close()
    time.sleep(2)

    # split the search into words
    split_search = search.split()

    # initialize the found comparisons dict
    found_dict = dict()

    # for transcript, data in tfidf_dict['transcripts'].items():
    #
    #     correct_found = dict()
    #     similar_found = dict()
    #
    #     chain_find = 10
    #     found_position_index = -1
    #     position_index = 0
    #     found_previous = False
    #
    #     for stored_word, score in data['tfidf'].items():
    #
    #         found_word = False
    #
    #         for search_word in split_search:
    #
    #             if not found_word:
    #
    #                 if stored_word == search_word:
    #
    #                     correct_found[stored_word] = score
    #
    #                     position_diff = position_index - found_position_index
    #                     if position_diff == 1:
    #                         correct_found[stored_word] *= chain_find
    #
    #                     found_position_index = position_index
    #                     chain_find *= 2
    #                     found_word = True
    #
    #                 else:
    #
    #                     if edit_distance:
    #
    #                         adjusted_distance = float(Levenshtein.distance(stored_word, search_word)) / len(stored_word)
    #
    #                         if adjusted_distance < adjusted_distance_stop:
    #
    #                             true_weight = ((1 - adjusted_distance_stop) - adjusted_distance) * score
    #                             similar_found[stored_word] = true_weight
    #
    #                             position_diff = position_index - found_position_index
    #                             if position_diff == 1:
    #                                 similar_found[stored_word] *= chain_find
    #
    #                             found_position_index = position_index
    #                             chain_find *= 2
    #                             found_word = True
    #
    #         if found_word:
    #             found_previous = True
    #
    #         else:
    #             chain_find = 10
    #             found_previous = False
    #
    #         position_index += 1
    #
    #
    #     found_dict[transcript] = dict()
    #     found_dict[transcript]['relevancy'] = 0
    #     found_dict[transcript]['searched'] = dict()
    #
    #     for correct_word, correct_score in correct_found.items():
    #         found_dict[transcript]['relevancy'] += (correct_score * len(correct_found))
    #         found_dict[transcript]['searched'][correct_word] = {'score': correct_score, 'count': data['tf'][correct_word]['count']}
    #
    #     for similar_word, similar_score in similar_found.items():
    #         found_dict[transcript]['relevancy'] += similar_score
    #         found_dict[transcript]['searched'][similar_word] = {'score': similar_score, 'count': data['tf'][similar_word]['count']}

    # for each search term, construct relevancy dictionaries
    for transcript, data in tfidf_dict['transcripts'].items():

        correct_found = dict()
        similar_found = dict()

        # for each data point and information stored in stored dictionary
        for search_word in split_search:

            correct_chain_find = 0
            similar_chain_find = 0

            # for each word and it's score
            for stored_word, score in data['tfidf'].items():

                # if the word direct matches the search term
                if stored_word == search_word:

                    true_weight = score
                    correct_found[stored_word] = true_weight

                    # try adding the tfidf score to the relevancy score
                    # try:
                    #     found_dict[transcript]['relevancy'] += true_weight
                    #
                    #
                    #     # the stored_word comparison isn't already in the found words
                    #     if stored_word not in found_dict[transcript]['searched']:
                    #         found_dict[transcript]['searched'].append({stored_word: true_weight})
                    #
                    # # relevancy score needs to be initialized
                    # except:
                    #     found_dict[transcript] = {'relevancy': true_weight, 'searched': [{stored_word: true_weight}]}
                    #
                    # correct_chain_find += true_weight

                # direct search term not found as a word
                else:

                    # check if edit distance is allowed as attribute for searching
                    if edit_distance:

                        # calculate the adjusted_distance
                        adjusted_distance = float(Levenshtein.distance(stored_word, search_word)) / len(stored_word)

                        # if the adjusted_distance isn't too large
                        if adjusted_distance < adjusted_distance_stop:

                            true_weight = ((1 - adjusted_distance_stop) - adjusted_distance) * score
                            similar_found[stored_word] = true_weight

                            # # try adding the adjusted_distance scored to relevancy score
                            # try:
                            #     found_dict[transcript]['relevancy'] += true_weight
                            #
                            #     # the stored_word comparison isn't already in the found words
                            #     if stored_word not in found_dict[transcript]['searched']:
                            #         found_dict[transcript]['searched'].append({stored_word: true_weight})
                            #
                            # # must initialize relevancy score
                            # except:
                            #     found_dict[transcript] = {'relevancy': true_weight, 'searched': [{stored_word: true_weight}]}
                            #
                            # similar_chain_find += true_weight

        found_dict[transcript] = dict()
        found_dict[transcript]['relevancy'] = 0
        found_dict[transcript]['searched'] = dict()

        for correct_word, correct_score in correct_found.items():
            found_dict[transcript]['relevancy'] += (correct_score * 3)
            found_dict[transcript]['searched'][correct_word] = correct_score

        for similar_word, similar_score in similar_found.items():
            found_dict[transcript]['relevancy'] += similar_score
            found_dict[transcript]['searched'][similar_word] = similar_score

    # sort the found data by the relevancy score
    found_dict = sorted(found_dict.items(), key=lambda x: x[1]['relevancy'], reverse=True)

    print('searched corpus for:', search)

    # return the found data
    return found_dict[:results]

# DATA GRABBING

# get_local_data for a dictionary of packed_routes
#   packed_route must contain:
#       path:           this will be the overarching body for the database or included in the filename
#       url:            the legistar url to pull data from
#       storage key:    the key that will be used to store an item in the database
#       cleaning_func:  a function that will be used to clean the data
#
#   packed_route formatted:
#       '{ path : [ url, storage key, cleaning_func ] }'
#
#   os_path: the directory path where the json data can be found
def get_local_data(packed_routes, os_path, prints=True):

    # create unpacked_data dictionary
    unpacked_data = dict()

    # for each path and packed_route
    for path, routes in packed_routes.items():

        # open the locally stored json
        with open(os_path + '_' + path + '.json') as data_file:
            local_data = json.load(data_file)

        data_file.close()
        time.sleep(2)

        if prints:
            pprint(local_data)
            print('-----------------------------------------------------------')

        # store the retrieved data
        unpacked_data[path] = local_data

    # return the data for manipulation
    return unpacked_data

# get_stored_data
#   path: the path from the database origin
#   return_data: boolean true or false for if to return the actual values stored or the database object
def get_stored_data(path, return_data=True):

    # get a focus target
    focus = db

    # split the path given by the user for child function
    path = path.split('/')

    # navigate to target data
    for part in path:
        if part != '':
            focus = focus.child(part)

    # found the target return data desired
    if return_data:
        return focus.get().val()
    else:
        return focus.get()


# TEMPORARY AND TESTING

# ABANDONED

# get_future_event_dates
#
# not needed for searching relevancy of videos/ events/ meetings
#
# data = get_local( { 'bodies': all_routes['bodies'] } , prints=False)
#
# for key, datum in data.items():
#     for item in datum:
#         body_events = get_test_data('http://webapi.legistar.com/v1/seattle/EventDates/' + str(item['BodyId']) + '?FutureDatesOnly=true', prints=False)
#         print(item['BodyName'], body_events)
