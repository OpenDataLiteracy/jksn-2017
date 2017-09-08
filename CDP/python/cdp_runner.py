from get_store_data import *

project_directory = 'D:/jksn-2017/CDP/resources/'

def generate_log_file(log_name, log_type, log_object, log_directory):
    log_directory = check_path_safety(log_directory)

    if not os.path.exists(log_directory):
        os.mkdir(log_directory)

    if log_type == 'system':

        consolidated = dict()
        consolidated['completed_feeds'] = 0
        consolidated['avg_feeds_duration'] = 0
        consolidated['completed_videos'] = 0
        consolidated['avg_videos_duration'] = 0
        consolidated['completed_audios'] = 0
        consolidated['avg_audios_duration'] = 0
        consolidated['completed_transcripts'] = 0
        consolidated['avg_transcripts_duration'] = 0
        consolidated['avg_tfidf_duration'] = 0
        consolidated['avg_search_duration'] = 0
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
            consolidated['avg_tfidf_duration'] += block['tfidf_duration']
            consolidated['avg_search_duration'] += block['search_duration']
            consolidated['avg_block_duration'] += block['block_duration']
            consolidated['system_runtime'] = block['system_runtime']

        num_blocks = len(blocks)

        consolidated['avg_feeds_duration'] = consolidated['avg_feeds_duration'] / num_blocks
        consolidated['avg_videos_duration'] = consolidated['avg_videos_duration'] / num_blocks
        consolidated['avg_audios_duration'] = consolidated['avg_audios_duration'] / num_blocks
        consolidated['avg_transcripts_duration'] = consolidated['avg_transcripts_duration'] / num_blocks
        consolidated['avg_tfidf_duration'] = consolidated['avg_tfidf_duration'] / num_blocks
        consolidated['avg_search_duration'] = consolidated['avg_search_duration'] / num_blocks
        consolidated['avg_block_duration'] = consolidated['avg_block_duration'] / num_blocks

        pprint(log_object)

        log_name = 'consolidated_' + str(datetime.datetime.fromtimestamp(consolidated['system_start'])).replace(' ', '_').replace(':', '-')[:-7]
        generate_log_file(log_name=log_name, log_type='consolidated', log_object=consolidated, log_directory=log_directory)

    with open(log_directory + log_name + '.json', 'w', encoding='utf-8') as logfile:
        json.dump(log_object, logfile)

    logfile.close()
    time.sleep(1)

def run_cdp(project_directory, legistar_routes, video_routes, log_directory, block_sleep_duration=21600, run_duration=-1, logging=True):

    try:
        project_directory = check_path_safety(project_directory)
        log_directory = check_path_safety(log_directory)

        system_start = time.time()
        time_elapsed = 0

        blocks = list()

        while (time_elapsed + block_sleep_duration) <= run_duration or run_duration == -1:
            block_start = time.time()
            block = dict()
            block['system_start'] = system_start
            block['block_start'] = block_start

            # @RUN
            # Run for video feeds
            feeds_start = time.time()
            block['completed_feeds'] = get_video_feeds(packed_routes=video_routes, storage_path=(project_directory + 'video_feeds.json'))
            feeds_duration = time.time() - feeds_start

            block['feeds_duration'] = (float(feeds_duration) / 60.0 / 60.0)

            # @RUN
            # Run for mass video collection
            videos_start = time.time()
            block['completed_videos'] = get_video_sources(objects_file=(project_directory + 'video_feeds.json'), storage_path=(project_directory + 'Video/'), throughput_path=(project_directory + 'Audio/'))
            videos_duration = time.time() - videos_start

            block['videos_duration'] = (float(videos_duration) / 60.0 / 60.0)

            # @RUN
            # Run for mass audio stripping
            audios_start = time.time()
            block['completed_audios'] = strip_audio_from_directory(video_dir=(project_directory + 'Video/'), audio_dir=(project_directory + 'Audio/'), delete_video=True)
            audios_duration = time.time() - audios_start

            block['audios_duration'] = (float(audios_duration) / 60.0 / 60.0)

            # @RUN
            # Run for mass transcripts
            transcripts_start = time.time()
            block['completed_transcripts'] = generate_transcripts_from_directory(project_directory=(project_directory + 'Audio/'), delete_splits=True)
            transcripts_duration = time.time() - transcripts_start

            block['transcripts_duration'] = (float(transcripts_duration) / 60.0 / 60.0)

            # @RUN
            # Run for mass tfidf
            tfidf_start = time.time()
            generate_tfidf_from_directory(project_directory=(project_directory + 'Audio/transcripts'), output_file=(project_directory + 'tfidf.json'))
            tfidf_duration = time.time() - tfidf_start

            block['tfidf_duration'] = (float(tfidf_duration) / 60.0 / 60.0)

            # @RUN
            # Run for testing speed of search
            search_start = time.time()
            predict_relevancy(search='transportation funding budget', tfidf_store=(project_directory + 'tfidf.json'))
            search_duration = time.time() - search_start

            block['search_duration'] = (float(search_duration) / 60.0 / 60.0)

            block_duration = time.time() - block_start
            block['block_duration'] = block_duration

            time_elapsed = time.time() - system_start
            block['system_runtime'] = time_elapsed

            if logging:
                log_name = 'block_' + str(datetime.datetime.fromtimestamp(block_start)).replace(' ', '_').replace(':', '-')[:-7]
                generate_log_file(log_name=log_name, log_type='block', log_object=block, log_directory=log_directory)

            blocks.append(block)

            if (time_elapsed + block_sleep_duration) <= run_duration or run_duration == -1:
                print('SLEEPING SYSTEM FOR:', (float(block_sleep_duration) / 60.0 / 60.0), 'HOURS...')
                time.sleep(block_sleep_duration)

        if logging:
            log_name = 'system_' + str(datetime.datetime.fromtimestamp(system_start)).replace(' ', '_').replace(':', '-')[:-7]
            generate_log_file(log_name=log_name, log_type='system', log_object=blocks, log_directory=log_directory)

        return blocks

    except Exception as e:
        print('---------------------------------------------------------------')
        print('---------------------- ENCOUNTERED ERROR ----------------------')
        print('---------------------------------------------------------------')
        return e

print(run_cdp(project_directory=project_directory, legistar_routes=all_routes, video_routes=video_routes, log_directory=(project_directory + 'logs/')))
