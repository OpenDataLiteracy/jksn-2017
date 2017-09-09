from get_store_data import *

# VARIABLES AND OBJECTS

# all_routes is the legistar data packed_routes object
all_routes = {
            'events': ['http://webapi.legistar.com/v1/seattle/Events', 'EventId', clean_events_data]
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

# generate_log_file for a log_object
#   log_name: a name for the log to be stored
#   log_type: 'block', 'system', or 'consolidated'
#   log_object: the actual object to be logged
#   log_directory: where the log should be stored
def generate_log_file(log_name, log_type, log_object, log_directory):

    # ensure path safety
    log_directory = check_path_safety(log_directory)

    # check if the log folder exists, if not, create it
    if not os.path.exists(log_directory):
        os.mkdir(log_directory)

    # check if it is a system log
    if log_type == 'system':

        # create a consolidated log if it is
        consolidated = dict()
        consolidated['completed_feeds'] = 0
        consolidated['avg_feeds_duration'] = 0
        consolidated['completed_videos'] = 0
        consolidated['avg_videos_duration'] = 0
        consolidated['completed_audios'] = 0
        consolidated['avg_audios_duration'] = 0
        consolidated['completed_transcripts'] = 0
        consolidated['avg_transcripts_duration'] = 0
        consolidated['tfidf_duration'] = 0
        consolidated['search_duration'] = 0
        consolidated['avg_block_duration'] = 0

        for block in log_object:
            consolidated['system_start'] = block['system_start']
            consolidated['completed_feeds'] += block['completed_feeds']
            consolidated['avg_feeds_duration'] += block['feeds_duration']
            consolidated['completed_videos'] += block['completed_videos']
            consolidated['avg_videos_duration'] += block['videos_duration']
            consolidated['completed_audios'] += block['completed_audios']
            consolidated['avg_audios_duration'] += block['audios_duration']
            consolidated['completed_transcripts'] += block['completed_transcripts']
            consolidated['avg_transcripts_duration'] += block['transcripts_duration']
            consolidated['tfidf_duration'] = block['tfidf_duration']
            consolidated['search_duration'] = block['search_duration']
            consolidated['avg_block_duration'] += block['block_duration']
            consolidated['system_runtime'] = block['system_runtime']

        num_blocks = len(blocks)

        consolidated['avg_feeds_duration'] = consolidated['avg_feeds_duration'] / num_blocks
        consolidated['avg_videos_duration'] = consolidated['avg_videos_duration'] / num_blocks
        consolidated['avg_audios_duration'] = consolidated['avg_audios_duration'] / num_blocks
        consolidated['avg_transcripts_duration'] = consolidated['avg_transcripts_duration'] / num_blocks
        consolidated['avg_block_duration'] = consolidated['avg_block_duration'] / num_blocks

        pprint(log_object)

        log_name = 'consolidated_' + str(datetime.datetime.fromtimestamp(consolidated['system_start'])).replace(' ', '_').replace(':', '-')[:-7]
        generate_log_file(log_name=log_name, log_type='consolidated', log_object=consolidated, log_directory=log_directory)

    # store the log_object in specified path
    with open(log_directory + log_name + '.json', 'w', encoding='utf-8') as logfile:
        json.dump(log_object, logfile)

    # ensure log_file safety
    logfile.close()
    time.sleep(1)

# run_cdp for a city_council
#   project_directory: the overarching project directory path where all files will be stored
#   legistar_routes: the packed_routes object with legistar information
#   video_routes: the packed_routes object with video collection information
#   log_directory: the location of where logs will be stored
#   delete_videos: boolean to keep or remove videos after audio is split
#   delete_splits: boolean to keep or remove audio splits after transcript is generated
#   test_search_term: string search term for testing the speed of predict_relevancy
#   print: add or remove print statements from functions
#   block_sleep_duration: time in seconds to sleep after a single collection cycle
#   run_duration: time in seconds to run the system for
#   logging: boolean to keep or stop logging
def run_cdp(project_directory, legistar_routes, video_routes, scraping_function, log_directory, delete_videos=False, delete_splits=False, test_search_term='bicycle infrastructure', prints=True, block_sleep_duration=21600, run_duration=-1, logging=True):

    # ensure safety of the entire run
    try:

        # ensure safety of paths
        project_directory = check_path_safety(project_directory)
        log_directory = check_path_safety(log_directory)

        # create system logging information
        system_start = time.time()
        time_elapsed = 0

        # create blocks list for logging information
        blocks = list()

        # check to see if the runner should continue
        while (time_elapsed + block_sleep_duration) <= run_duration or run_duration == -1:

            # create block logging information
            block_start = time.time()
            block = dict()
            block['system_start'] = system_start
            block['block_start'] = block_start

            # @RUN
            # Run for video feeds
            feeds_start = time.time()
            block['completed_feeds'] = get_video_feeds(packed_routes=video_routes, storage_path=(project_directory + 'video_feeds.json'), scraping_function=scraping_function, prints=prints)
            feeds_duration = time.time() - feeds_start

            block['feeds_duration'] = (float(feeds_duration) / 60.0 / 60.0)

            # @RUN
            # Run for mass video collection
            videos_start = time.time()
            block['completed_videos'] = get_video_sources(objects_file=(project_directory + 'video_feeds.json'), storage_path=(project_directory + 'Video/'), throughput_path=(project_directory + 'Audio/'), prints=prints)
            videos_duration = time.time() - videos_start

            block['videos_duration'] = (float(videos_duration) / 60.0 / 60.0)

            # @RUN
            # Run for mass audio stripping
            audios_start = time.time()
            block['completed_audios'] = strip_audio_from_directory(video_dir=(project_directory + 'Video/'), audio_dir=(project_directory + 'Audio/'), delete_video=delete_videos, prints=prints)
            audios_duration = time.time() - audios_start

            block['audios_duration'] = (float(audios_duration) / 60.0 / 60.0)

            # @RUN
            # Run for mass transcripts
            transcripts_start = time.time()
            block['completed_transcripts'] = generate_transcripts_from_directory(project_directory=(project_directory + 'Audio/'), delete_splits=delete_splits, prints=prints)
            transcripts_duration = time.time() - transcripts_start

            block['transcripts_duration'] = (float(transcripts_duration) / 60.0 / 60.0)

            # @RUN
            # Run for mass tfidf
            tfidf_start = time.time()
            generate_tfidf_from_directory(project_directory=(project_directory + 'Audio/transcripts'), output_file=(project_directory + 'tfidf.json'), prints=prints)
            tfidf_duration = time.time() - tfidf_start

            block['tfidf_duration'] = (float(tfidf_duration) / 60.0 / 60.0)

            # @RUN
            # Run for testing speed of search
            search_start = time.time()
            pprint(predict_relevancy(search=test_search_term, tfidf_store=(project_directory + 'tfidf.json')))
            search_duration = time.time() - search_start

            block['search_duration'] = (float(search_duration) / 60.0 / 60.0)

            block_duration = time.time() - block_start
            block['block_duration'] = block_duration

            time_elapsed = time.time() - system_start
            block['system_runtime'] = time_elapsed

            # check logging to log the block information
            if logging:
                log_name = 'block_' + str(datetime.datetime.fromtimestamp(block_start)).replace(' ', '_').replace(':', '-')[:-7]
                generate_log_file(log_name=log_name, log_type='block', log_object=block, log_directory=log_directory)

            # append the block to system log
            blocks.append(block)

            # sleep the system if it wont overflow into system downtown
            if (time_elapsed + block_sleep_duration) <= run_duration or run_duration == -1:
                print('SLEEPING SYSTEM FOR:', (float(block_sleep_duration) / 60.0 / 60.0), 'HOURS...')
                time.sleep(block_sleep_duration)

        # check logging to log the system information
        if logging:
            log_name = 'system_' + str(datetime.datetime.fromtimestamp(system_start)).replace(' ', '_').replace(':', '-')[:-7]
            generate_log_file(log_name=log_name, log_type='system', log_object=blocks, log_directory=log_directory)

        # return the basic block information
        return blocks

    # print any exception that occurs and stop the run
    except Exception as e:
        print('---------------------------------------------------------------')
        print('---------------------- ENCOUNTERED ERROR ----------------------')
        print('---------------------------------------------------------------')
        return e

project_directory = 'C:/Users/jmax825/desktop/jksn-2017/CDP/resources/'
print(run_cdp(project_directory=project_directory, legistar_routes=all_routes, video_routes=video_routes, scraping_function=scrape_seattle_channel, log_directory=(project_directory + 'logs/')))
