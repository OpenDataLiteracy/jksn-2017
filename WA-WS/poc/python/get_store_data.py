import pyrebase
import requests
import shutil
from bs4 import BeautifulSoup as bs
import json
import datetime
from pprint import pprint
from configure_poc_storage import *

firebase = pyrebase.initialize_app(config)
db = firebase.database()

def clean_events_data(item):
    current_dt = datetime.datetime.now()

    item['EventLocation'] = item['EventLocation'].replace('\r', '').replace('\n', ', ')
    item['EventStoredDatetime'] = str(current_dt)

    return item

def clean_bodies_data(item):
    current_dt = datetime.datetime.now()
    item['BodiesStoredDatetime'] = str(current_dt)

    return item

all_routes = {
            'events': ['http://webapi.legistar.com/v1/seattle/Events', 'EventId', clean_events_data],
            'bodies': ['http://webapi.legistar.com/v1/seattle/Bodies', 'BodyId', clean_bodies_data]
}

def get_all_data(packed_routes, prints=False, toLocal=True):
    for path, routes in packed_routes.items():
        if prints:
            print('getting data from:', routes[0])
            print('-----------------------------------------------------------')

        r = requests.get(routes[0])
        r = r.json()

        if not toLocal:
            for item in r:
                if prints:
                    print('working on:', item)

                store_id = item[routes[1]]
                del item[routes[1]]
                item = routes[2](item)

                if prints:
                    print('completed:', item)

                db.child(path).child(store_id).set(item)

                if prints:
                    print('stored:', path, store_id)
                    print('-------------------------------------------------------')
        else:
            cleaned_r = list()
            for item in r:
                item = routes[2](item)
                cleaned_r.append(item)

            with open('WA-WS/poc/python/local_store_' + path + '.json', 'w', encoding='utf-8') as outfile:
                json.dump(cleaned_r, outfile)

# get_all_data(all_routes)

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

def get_video_feeds(packed_routes, prints=False, toLocal=True):
    constructed_feeds = dict()

    for path, routes in packed_routes.items():
        if prints:
            print('starting work on:', path)

        r = requests.get('http://www.seattlechannel.org/' + routes[0])
        soup = bs(r.content, 'html.parser')

        path_feeds = list()

        paginations = soup.find_all('div', class_='col-xs-12 col-sm-8 col-md-9')

        if prints:
            print('found', len(paginations), 'video elements for:', path)
        for pagination in paginations:
            path_feed = dict()

            bs_link = str(pagination.find('a')['href'])
            path_feed['link'] = bs_link
            try:
                bs_video = str(pagination.find('a')['onclick'])
                video_end = bs_video.find('.mp4\',')
                bs_video = str(pagination.find('a')['onclick'])[26: video_end + 4]
            except:
                bs_video = ''
            path_feed['video'] = bs_video

            try:
                bs_agenda = str(pagination.find('div', class_='titleExcerptText').find('p').text)
                if 'Agenda: ' in bs_agenda:
                    bs_agenda = bs_agenda[8:]
                path_feed['agenda'] = bs_agenda
            except:
                path_feed['agenda'] = ''

            bs_datetime = str(pagination.find('div', class_='videoDate').text)
            path_feed['datetime'] = bs_datetime

            path_feed['body'] = routes[1]

            path_feeds.append(path_feed)

            if prints:
                print('constructed true link:', path_feed)

        if prints:
            print('completed feed construction for:', path)
            print('-----------------------------------------------------------')
        constructed_feeds[path] = path_feeds

    if toLocal:
        with open('WA-WS/poc/python/local_store_videos.json', 'w', encoding='utf-8') as outfile:
            json.dump(constructed_feeds, outfile)

    return constructed_feeds

def get_video_sources(objects, path, prints=True):
    for label, data in objects.items():
        if prints:
            print('starting video sources collection for:', label)

        for datum in data:
            if datum['video'] != '':
                try:
                    tag_start = datum['video'].index('_')
                    tag = datum['video'][tag_start + 1:]
                except:
                    tag = datum['video'][-11:]

                if prints:
                    print('collecting:', datum['video'])

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

video_data = get_video_feeds(video_routes, prints=True)
get_video_sources(video_data, 'C:/Users/Maxfield/Desktop/active/jksn-2017/WA-WS/poc/python/videos/')

def get_local(packed_routes, prints=True):
    unpacked_data = {}

    for path, routes in packed_routes.items():
        with open('WA-WS/poc/python/local_store_' + path + '.json') as data_file:
            local_data = json.load(data_file)

        if prints:
            pprint(local_data)
            print('-----------------------------------------------------------')

        unpacked_data[path] = local_data

    return unpacked_data

#print_local(all_routes)

# testing_url = 'http://webapi.legistar.com/v1/seattle/BodyTypes'
# testing_url_2 = 'http://webapi.legistar.com/v1/seattle/Bodies'
# testing_url_3 = 'http://webapi.legistar.com/v1/seattle/Events/2896?AgendaNote=1&MinutesNote=1&Attachments=1&EventItemAttachments=1'

def get_test_data(url, prints=True):
    r = requests.get(url)
    r = r.json()

    if prints:
        pprint(r)

    return r

def pull_data(path, return_data=False):
    focus = db
    path = path.split('/')

    for part in path:
        if part != '':
            focus = focus.child(part)

    if return_data:
        return focus.get().val()
    else:
        return focus.get()

# get_test_data(testing_url)
# get_test_data(testing_url_2)
# get_test_data(testing_url_3)
# get_all_data(all_routes, prints=True)


# FUTURE DATES TESTING
# data = get_local( { 'bodies': all_routes['bodies'] } , prints=False)
#
# for key, datum in data.items():
#     for item in datum:
#         body_events = get_test_data('http://webapi.legistar.com/v1/seattle/EventDates/' + str(item['BodyId']) + '?FutureDatesOnly=true', prints=False)
#         print(item['BodyName'], body_events)
