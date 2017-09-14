from cdp_runner import *

with open('D:/jksn-2017/CDP/resources/stores/tfidf.json', 'r') as tfidf_file:
    tfidf_contents = json.load(tfidf_file)

with open('D:/jksn-2017/CDP/resources/stores/video_feeds.json', 'r') as feeds_file:
    feeds_contents = json.load(feeds_file)

storage_dir = 'D:/jksn-2017/CDP/resources/stores/'


testing_routes = {
            'events': ['http://webapi.legistar.com/v1/seattle/Events', 'EventId', clean_events_data, 'EventDate', clean_time_data, 'EventCalculatedTime']
}


#get_video_feeds(video_routes, storage_dir)
#get_data_by_routed(testing_routes, storage_dir)
#generate_tfidf_from_directory(project_directory + 'Audio/transcripts', storage_dir)


with open('D:/jksn-2017/CDP/resources/stores/local_store_events_by_EventDate.json', 'r') as events_file:
    events_contents = json.load(events_file)

def get_event_storage_name(agenda):

    return predict_relevancy(agenda)

    storage_name = ''
    secondary_name = ''

    for path, routes in video_routes.items():
        if body_name == routes[1]:
            storage_name += path

            storage_name += '_'
            storage_name += date[5:7]
            storage_name += date[8:10]
            storage_name += date[2:4]

            secondary_name = storage_name
            secondary_name += time[-2:]

    return {'main': storage_name, 'secondary': secondary_name}

def apply_naming_conventions_to_routed_legistar_data(data_path, rewrite=True):

    with open(data_path, 'r') as data_file:
        data = json.load(data_file)

    data_file.close()

    for key, datum in data.items():

        datum_length = len(datum)

        if datum_length == 2:

            time_period_one = 'AM' in datum[0]['EventTime']
            time_period_two = 'AM' in datum[1]['EventTime']

            if time_period_one != time_period_two:
                datum[0]['NamingConvention'] = 'AM'
                datum[1]['NamingConvention'] = 'PM'

        elif datum_length > 2:

            characters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

            for i in range(datum_length):
                datum[i]['NamingConvention'] = characters[i]

    if rewrite:
        os.remove(data_path)

        with open(data_path, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile)

        outfile.close()

    return data

pprint(apply_naming_conventions_to_routed_legistar_data('D:/jksn-2017/CDP/resources/stores/local_store_events_by_EventDate.json'))
