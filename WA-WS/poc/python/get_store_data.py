import pyrebase
import requests
import subprocess
import shutil
from bs4 import BeautifulSoup as bs
import json
import datetime
from pprint import pprint
import os

# database configuration and admin settings
from configure_poc_storage import *

# DATABASE CONNECTION
firebase = pyrebase.initialize_app(config)
db = firebase.database()

# DATA GRABBING

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
# url: the legistar url to pull data from
def get_test_data(url, prints=True):

    # get data from url
    r = requests.get(url)
    r = r.json()

    if prints:
        pprint(r)

    # return json for manipulation
    return r

# get_video_feeds for a dictionary of packed routes
#   packed_route must contain:
#       path:           this will be the overarching body for the database or included in the filename
#       url:            the seattle_channel url to pull data from
#       body_name:      the true body_name used by legistar
#
#   packed_route formatted:
#       '{ path : [ url, body_name ] }'
def get_video_feeds(packed_routes, prints=False, toLocal=True):

    # create empty dictionary to store video information
    constructed_feeds = dict()

    # for each path and packed_route
    for path, routes in packed_routes.items():
        if prints:
            print('starting work on:', path)

        # request the url and scrape the page to collect information
        r = requests.get('http://www.seattlechannel.org/' + routes[0])
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

        # attach the found feeds to the storage dictionary
        constructed_feeds[path] = path_feeds

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
# path: the path from the database origin
# return_data: boolean true or false for if to return the actual values stored or the database object
def get_stored_data(path, return_data=False):

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

# DATA CLEANING

# clean_events_data for an event item
# item must contain:
#   EventLocation: the location of where the event took place
def clean_events_data(item):

    # create a storage time attribute
    current_dt = datetime.datetime.now()
    item['EventStoredDatetime'] = str(current_dt)

    # reconstruct the EventLocation attribute
    item['EventLocation'] = item['EventLocation'].replace('\r', '').replace('\n', ', ')

    return item

# clean_bodies_data for a body item
def clean_bodies_data(item):

    # create a storage time attribute
    current_dt = datetime.datetime.now()
    item['BodyStoredDatetime'] = str(current_dt)

    return item

# clean_video_filename for a video file
def clean_video_filename(item):

    # check filename for spaces:
    if ' ' in item:

        # replace the spaces with underscore
        item = item.replace(' ', '_')

    return item

# rename_video_files for an os location
# video_dir: path in os to video files
# cleaning_func: the cleaning function to repair or fix filenames
def rename_video_files(video_dir, cleaning_func):

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
def check_path_safety(path):
    if '/' != path[-1:]:
        path += '/'

    return path

# video_to_audio_rename with '.wav'
def video_to_audio_rename(video_in):
    return video_in[:-4] + '.wav'

# strip_audio using subprocess to run ffmpeg
# project_path: the overarching project directory, check_path_safety
# video_label: the specific video directory to get, check_path_safety
# audio_label: the specific audio directory to store, check_path_safety
# video_in: the specific video file to get
# audio_out: the specific audio file to store
def strip_audio(project_path, video_label, audio_label, video_in, audio_out):
    command = 'ffmpeg -i '

    command += project_path
    command += video_label
    command += video_in
    command += ' -ab 160k -ac 2 -ar 44100 -vn'
    command += project_path
    command += audio_label
    command += audio_out

    subprocess.call(command, shell=True)

# strip_audio_from_directory for given directory and labels
# project_path: the overarching project directory, check_path_safety
# video_label: the specific video directory to get, check_path_safety
# audio_label: the specific audio directory to store, check_path_safety
# naming_function: a function to construct a name for the output video_file
# delete_video: boolean value to decide if you want to keep the video portion or discard after audio construction
def strip_audio_from_directory(project_path, video_label, audio_label, naming_function, delete_video=False, prints=True):

    # check_path_safety for all path variables
    project_path = check_path_safety(project_path)
    video_label = check_path_safety(video_label)
    audio_label = check_path_safety(audio_label)

    # set working directory to the video_dir
    os.chdir(project_path + video_label)

    if prints:
        print('set cwd to:', os.getcwd)

    # for each video in the found directory
    for video_file in os.listdir():

        # construct the audio file name
        audio_out_label = naming_function(video_file)

        if prints:
            print('stripping audio using:', project_path, video_label, audio_label, video_file, audio_out_label)

        # strip the audio
        strip_audio(project_path, video_label, audio_label, video_file, audio_out_label)

        # check if to delete
        if delete_video:
            os.remove(project_path + video_label + video_file)


# VARIABLES AND OBJECTS

# all_routes is the legistar data packed_routes object
all_routes = {
            'events': ['http://webapi.legistar.com/v1/seattle/Events', 'EventId', clean_events_data],
            'bodies': ['http://webapi.legistar.com/v1/seattle/Bodies', 'BodyId', clean_bodies_data]
}

# video_routes is the seattle_channel packed_routes object
video_routes = {
                'briefings': ['CouncilBriefings', 'Council Briefing'],
                'budget': ['BudgetCommittee', 'Select Budget Committee'],
                'full': ['FullCouncil', 'Full Council'],
                'park': ['mayor-and-council/city-council/seattle-park-district-board', 'Select Committee on Parks Funding'],
                'transportation': ['mayor-and-council/city-council/seattle-transportation-benefit-district', 'Select Committee on Transportation Funding'],
                'arenas': ['mayor-and-council/city-council/select-committee-on-civic-arenas', 'Select Committee on Civic Arenas'],
                'housing': ['mayor-and-council/city-council/select-committee-on-the-2016-seattle-housing-levy', 'Select Committee on the 2016 Seattle Housing Levy'],
                'lighting': ['mayor-and-council/city-council/select-committee-on-the-2016-seattle-city-light-strategic-planning', 'Select Committee on the 2016 Seattle City Light Strategic Planning'],
                'finance': ['mayor-and-council/city-council/2016/2017-affordable-housing-neighborhoods-and-finance-committee', 'Affordable Housing, Neighborhoods, and Finance Committee'],
                'utilities': ['mayor-and-council/city-council/2016/2017-civil-rights-utilities-economic-development-and-arts-committee', 'Civil Rights, Utilities, Economic Development, and Arts Committee'],
                'education': ['mayor-and-council/city-council/2016/2017-education-equity-and-governance-committee', 'Education and Governance Committee'],
                'energy': ['mayor-and-council/city-council/2016/2017-energy-and-environment-committee', 'Energy and Environment Committee'],
                'communities': ['mayor-and-council/city-council/2016/2017-gender-equity-safe-communities-and-new-americans-committee', 'Gender Equity, Safe Communities, and New Americans Committee'],
                'public health': ['mayor-and-council/city-council/2016/2017-human-services-and-public-health-committee', 'Human Services and Public Health Committee'],
                'civic centers': ['mayor-and-council/city-council/2016/2017-parks-seattle-center-libraries-and-waterfront-committee', 'Parks, Seattle Center, Libraries, and Waterfront Committee'],
                'zoning': ['mayor-and-council/city-council/2016/2017-planning-land-use-and-zoning-committee', 'Planning, Land Use, and Zoning Committee'],
                'sustainability': ['mayor-and-council/city-council/2016/2017 Sustainability & Transportation Committee', 'Sustainability and Transportation Committee']
}

# TEMPORARY AND TESTING

# get_future_event_dates
# data = get_local( { 'bodies': all_routes['bodies'] } , prints=False)
#
# for key, datum in data.items():
#     for item in datum:
#         body_events = get_test_data('http://webapi.legistar.com/v1/seattle/EventDates/' + str(item['BodyId']) + '?FutureDatesOnly=true', prints=False)
#         print(item['BodyName'], body_events)

project_path = 'C:/Users/Maxfield/Desktop/active/jksn-2017/WA-WS/poc/python'
video_label = 'video/'
audio_label = 'audio'

strip_audio_from_directory(project_path, video_label, audio_label, video_to_audio_rename, delete_video=True)
