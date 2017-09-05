#import pyrebase
import requests
import subprocess
import shutil
from bs4 import BeautifulSoup as bs
import json
import datetime
import speech_recognition as sr
import re
from pprint import pprint
import os
from pydub import AudioSegment
import math
import operator
from PyDictionary import PyDictionary
import Levenshtein


# database configuration and admin settings
from configure_keys import *


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
def get_video_feeds(packed_routes, scaping_function=scrape_seattle_channel, prints=False, toLocal=True):

    # create empty dictionary to store video information
    constructed_feeds = dict()

    # for each path and packed_route
    for path, routes in packed_routes.items():
        if prints:
            print('starting work on:', path)

        # attach the found feeds to the storage dictionary
        constructed_feeds[path] = scrape_seattle_channel(path=path, routes=routes, prints=prints)

    # store the found feeds locally
    if toLocal:
        with open('WA-WS/poc/python/local_store_videos.json', 'w', encoding='utf-8') as outfile:
            json.dump(constructed_feeds, outfile)

    # return the data for manipulation
    return constructed_feeds

# get_video_sources for a json/ dictionary of video information
#  video_json must contain:
#       label:           this is the assigned body name assigned during the get_video_feeds process 'path'
#       data:            the list of data returned from the get_video_feeds process
#           datum must contain:
#               link:       the pagelink for where the video is on seattle channel website
#               video:      the video source, should be a .mp4 file
#               agenda:     an agenda description
#               datetime:   the datetime of when the video took place
#               body:       the name of the body which was holding the event
#
#           data formatted:
#               [ { link: l, video: v, agenda: a, datetime: d, body: b } ]
#
#   video_json formatted:
#       '{ label :  data }'
def get_video_sources(objects, path, prints=True):

    # for each label and list of data
    for label, data in objects.items():
        if prints:
            print('starting video sources collection for:', label)

        # for each dictionary in list of data
        for datum in data:

            # check that a video source exists
            if datum['video'] != '':

                # create a video tag for storage
                try:
                    tag_start = datum['video'].index('_')
                    tag = datum['video'][tag_start + 1:]
                except:
                    tag = datum['video'][-11:]

                if prints:
                    print('collecting:', datum['video'])

                # request the video source and store the file
                r = requests.get(datum['video'], stream=True)
                if r.status_code == 200:
                    with open((path + label + '_' + tag), 'wb') as mp4_out:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, mp4_out)

                if prints:
                    print('collected:', datum['video'])

        if prints:
            print('completed collection for:', label)
            print('-----------------------------------------------------------')

# strip_audio using subprocess to run ffmpeg
#   project_directory: the overarching project directory, check_path_safety
#   video_label: the specific video directory to get, check_path_safety
#   audio_label: the specific audio directory to store, check_path_safety
#   video_in: the specific video file to get
#   audio_out: the specific audio file to store
def strip_audio(project_directory, video_label, audio_label, video_in, audio_out):
    command = 'ffmpeg -i '

    command += project_directory
    command += video_label
    command += video_in
    command += ' -ab 160k -ac 2 -ar 44100 -vn '
    command += project_directory
    command += audio_label
    command += audio_out

    subprocess.call(command, shell=True)

# strip_audio_from_directory for given directory and labels
#   project_directory: the overarching project directory, check_path_safety
#   video_label: the specific video directory to get, check_path_safety
#   audio_label: the specific audio directory to store, check_path_safety
#   naming_function: a function to construct a name for the output video_file
#   delete_video: boolean value to decide if you want to keep the video portion or discard after audio construction
def strip_audio_from_directory(project_directory, video_label, audio_label, naming_function, delete_video=False, prints=True):

    # check_path_safety for all path variables
    project_directory = check_path_safety(project_directory)
    video_label = check_path_safety(video_label)
    audio_label = check_path_safety(audio_label)

    # set working directory to the video_dir
    os.chdir(project_directory + video_label)

    if prints:
        print('set cwd to:', os.getcwd)

    # for each video in the found directory
    for video_file in os.listdir():

        # construct the audio file name
        audio_out_label = naming_function(video_file)

        if prints:
            print('stripping audio using:', project_directory, video_label, audio_label, video_file, audio_out_label)

        # strip the audio
        strip_audio(project_directory, video_label, audio_label, video_file, audio_out_label)

        # check if to delete
        if delete_video:
            os.remove(project_directory + video_label + video_file)

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
def split_audio_into_parts(project_directory, audio_file, naming_function=name_audio_splits, split_length=18000, splits_directory='transcripts/', prints=True):

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

    # store each split AudioSegment under its associated label
    for output_path, split in split_names.items():
        split.export(output_path, format='wav')

        if prints:
            print('stored audio split', output_path + '...')

    if prints:
        print('created audio splits for:\t', audio_file, '\t||\t', store_directory)
        print('-------------------------------------------------------')

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

        # open the file and return the transcription
        with open(transcribed_name, 'r') as transcript_file:
            transcript = transcript_file.read()

            if prints:
                print('transcript for:\t', transcribed_name, 'already exists\t||\t',  transcript[:20] + '...')
                print('---------------------------------------------------------------------------')

        return transcript

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

    # for each split (assuming standard splits naming)
    for i in range(len(splits)):

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
                print('Google Speech Recognition could not understand audio...', e)

            # major error, stop the engine and return
            except sr.RequestError as e:
                return 'Could not request results from Google Speech...', e

            if prints:
                print('transcribed:\t', audio_directory + str(i) + '.wav')

    # transcription fence post fix
    transcript = transcript[1:]

    # create and store the transcription in a file
    out_file = open(transcribed_name , "w")
    out_file.write(transcript)
    out_file.close()

    if prints:
        print('stored transcription at:\t', transcribed_name)

    if prints:
        print('created transcript for:\t', transcribed_name, '\t||\t',  transcript[20:] + '...')
        print('---------------------------------------------------------------------------')

    # return the transcript string
    return transcript

# generate_transcripts_for_directory for a directory of audio files
#   project_directory: the directory path you want to generate transcripts for
#   transcript_naming_function: a naming function for labeling the generated transcripts and storing them
#   delete_originals: boolean to determine if you want to delete the original audio files once transcription is completed
#   delete_splits: boolean to determine if you want to delete the audio split files once transcription is completed
def generate_transcripts_from_directory(project_directory, transcript_naming_function=name_transcription, delete_originals=False, delete_splits=False, prints=True):

    # check_path_safety for project
    project_directory = check_path_safety(project_directory)

    # after check, set the directory to match
    os.chdir(project_directory)

    if prints:
        print('starting work for', project_directory, '...')
        print('-------------------------------------------------------')

    # for all .wav files create audio splits and generate transcript
    for filename in os.listdir():

        # ensure file is valid for transcription process
        if '.wav' in filename:

            # create audio splits and save the splits directory for use in processing transcript
            split_audio_dir = split_audio_into_parts(project_directory=project_directory, audio_file=filename, prints=prints)

            # create the transcript from the audio split directory
            transcript = generate_transcript_from_audio_splits(audio_directory=split_audio_dir, naming_function=transcript_naming_function, prints=prints)

            # if delete_splits:
            #     os.remove(split_audio_dir)
            #
            #     if prints:
            #         print('delete_splits marked true, deleted audio splits for:\t', filename)
            #
            # if delete_originals:
            #     os.remove(project_directory + filename)
            #
            #     if prints:
            #         print('delete_originals marked true, deleted original audio for:\t', filename)

    if prints:
        print('completed transcript generation for all files in', project_directory)

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
        print('---------------------------------------------------------------')

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

    # add corpus results to total file results
    results['corpus'] = float(transcript_counter)

    if prints:
        print('starting second pass word tfidf scoring')

    # for each transcript construct a tfidf dictionary to hold completed computation
    for transcript, data in results['transcripts'].items():

        # deep copy
        temp_data_hold = dict(data)

        # base layer for storage
        data['tfidf'] = dict()

        # for each word compute tfidf score
        for word, score in temp_data_hold['tf'].items():
                # print('transcript:', transcript, '\tword:', word, '\ttf score:', score, '\n\toccurances:', score * data['length'], '\tlength:', data['length'])

                # actual computation
                data['tfidf'][word] = float(score) * math.log(results['corpus'] / float(results['words'][word]))

    if prints:
        print('completed all files, storing and returning results for:', project_directory)
        print('----------------------------------------------------------------------------------------')

    # completed all computation, dump into output file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(results, outfile)

    # return the final dictionary object
    return results

# predict_relevancy for a corpus of tfidf documents
#   search: the word, phrase, or sentence to find in the corpus
#   tfidf_store: the tfidf created json object's path created by generate_tfidf_from_directory
#   edit_distance: boolean true and false allowance of similar (misspelled) search terms
#   adjusted_distance_stop: float value to determine the cut off point of search term similarity
#   results: number of results you want to recieve back
def predict_relevancy(search, tfidf_store, edit_distance=True, adjusted_distance_stop = 0.42, results=10):

    # open the locally stored json
    with open(tfidf_store) as data_file:
        tfidf_dict = json.load(data_file)

    # split the search into words
    split_search = search.split()

    # initialize the found comparisons dict
    found_dict = dict()

    # for each search term, construct relevancy dictionaries
    for search_word in split_search:

        # for each data point and information stored in stored dictionary
        for transcript, data in tfidf_dict['transcripts'].items():

            # for each word and it's score
            for stored_word, score in data['tfidf'].items():

                # if the word direct matches the search term
                if stored_word == search_word:

                    # try adding the tfidf score to the relevancy score
                    try:
                        found_dict[transcript]['relevancy'] += score

                        # the stored_word comparison isn't already in the found words
                        if stored_word not in found_dict[transcript]['searched']:
                            found_dict[transcript]['searched'].append(stored_word)

                    # relevancy score needs to be initialized
                    except:
                        found_dict[transcript] = {'relevancy': score, 'searched': [stored_word]}

                # direct search term not found as a word
                else:

                    # check if edit distance is allowed as attribute for searching
                    if edit_distance:

                        # calculate the adjusted_distance
                        adjusted_distance = float(Levenshtein.distance(stored_word, search_word)) / len(stored_word)

                        # if the adjusted_distance isn't too large
                        if adjusted_distance < adjusted_distance_stop:

                            # try adding the adjusted_distance scored to relevancy score
                            try:
                                found_dict[transcript]['relevancy'] += ((0.6 - adjusted_distance) * score)

                                # the stored_word comparison isn't already in the found words
                                if stored_word not in found_dict[transcript]['searched']:
                                    found_dict[transcript]['searched'].append(stored_word)

                            # must initialize relevancy score
                            except:
                                found_dict[transcript] = {'relevancy': ((0.6 - adjusted_distance) * score), 'searched': [stored_word]}

    # sort the found data by the relevancy score
    found_dict = sorted(found_dict.items(), key=lambda x: x[1]['relevancy'], reverse=True)

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


# VARIABLES AND OBJECTS

# all_routes is the legistar data packed_routes object
all_routes = {
            'events': ['http://webapi.legistar.com/v1/seattle/Events', 'EventId', clean_events_data],
            'bodies': ['http://webapi.legistar.com/v1/seattle/Bodies', 'BodyId', clean_bodies_data]
}

# video_routes is the seattle_channel packed_routes object
video_routes = {
                'briefings': ['http://www.seattlechannel.org/CouncilBriefings', 'Council Briefing'],
                'budget': ['http://www.seattlechannel.org/BudgetCommittee', 'Select Budget Committee'],
                'full': ['http://www.seattlechannel.org/FullCouncil', 'Full Council'],
                'park': ['http://www.seattlechannel.org/mayor-and-council/city-council/seattle-park-district-board', 'Select Committee on Parks Funding'],
                'transportation': ['http://www.seattlechannel.org/mayor-and-council/city-council/seattle-transportation-benefit-district', 'Select Committee on Transportation Funding'],
                'arenas': ['http://www.seattlechannel.org/mayor-and-council/city-council/select-committee-on-civic-arenas', 'Select Committee on Civic Arenas'],
                'housing': ['http://www.seattlechannel.org/mayor-and-council/city-council/select-committee-on-the-2016-seattle-housing-levy', 'Select Committee on the 2016 Seattle Housing Levy'],
                'lighting': ['http://www.seattlechannel.org/mayor-and-council/city-council/select-committee-on-the-2016-seattle-city-light-strategic-planning', 'Select Committee on the 2016 Seattle City Light Strategic Planning'],
                'finance': ['http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-affordable-housing-neighborhoods-and-finance-committee', 'Affordable Housing, Neighborhoods, and Finance Committee'],
                'utilities': ['http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-civil-rights-utilities-economic-development-and-arts-committee', 'Civil Rights, Utilities, Economic Development, and Arts Committee'],
                'education': ['http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-education-equity-and-governance-committee', 'Education and Governance Committee'],
                'energy': ['http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-energy-and-environment-committee', 'Energy and Environment Committee'],
                'communities': ['http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-gender-equity-safe-communities-and-new-americans-committee', 'Gender Equity, Safe Communities, and New Americans Committee'],
                'public health': ['http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-human-services-and-public-health-committee', 'Human Services and Public Health Committee'],
                'civic centers': ['http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-parks-seattle-center-libraries-and-waterfront-committee', 'Parks, Seattle Center, Libraries, and Waterfront Committee'],
                'zoning': ['http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-planning-land-use-and-zoning-committee', 'Planning, Land Use, and Zoning Committee'],
                'sustainability': ['http://www.seattlechannel.org/mayor-and-council/city-council/2016/2017-sustainability-and-transportation-committee', 'Sustainability and Transportation Committee']
}

# TEMPORARY AND TESTING

#pprint(generate_words_from_doc(document='D:/Audio/transcripts/arenas_041717V.txt'))

pprint(predict_relevancy(search='asdf housing', tfidf_store='D:/tfidf.json'))

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

# REAL RUNNING

# @RUN
# Run for mass transcripts
# generate_transcripts_for_directory(project_directory='D:/Audio', delete_splits=True)

# @RUN
# Run for mass tfidf
# generate_tfidf_from_directory(project_directory='D:/Audio/transcripts', output_file='D:/tfidf.json')
