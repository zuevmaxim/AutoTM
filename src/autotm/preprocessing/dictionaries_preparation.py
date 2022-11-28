import os
import artm
import pandas as pd
import re
import multiprocessing as mp


def get_words_dict(text, stop_list):
    all_words = text
    words = sorted(set(all_words) - stop_list)

    return {w: all_words.count(w) for w in words}


def vocab_preparation(VOCAB_PATH, DICTIONARY_PATH):
    if not os.path.exists(VOCAB_PATH):
        with open(DICTIONARY_PATH, 'r') as dictionary_file:
            with open(VOCAB_PATH, 'w') as vocab_file:
                dictionary_file.readline()
                dictionary_file.readline()
                for line in dictionary_file:
                    elems = re.split(', ', line)
                    vocab_file.write(' '.join(elems[:2]) + '\n')


def calculate_cooc_dicts(window=10):
    with open()
        raise NotImplementedError


def prepearing_cooc_dict(BATCHES_DIR, WV_PATH, VOCAB_PATH, COOC_DICTIONARY_PATH,
                         cooc_file_path_tf, cooc_file_path_df,
                         ppmi_dict_tf, ppmi_dict_df, cooc_min_tf=0,
                         cooc_min_df=0, cooc_window=10, n_jobs=-1):
    '''
    :param BATCHES_DIR:
    :param WV_PATH:
    :param VOCAB_PATH:
    :param COOC_DICTIONARY_PATH:
    :param cooc_file_path_tf:
    :param cooc_file_path_df:
    :param ppmi_dict_tf:
    :param ppmi_dict_df:
    :param cooc_min_tf:
    :param cooc_min_df:
    :param cooc_window: size of the window where to search for the cooccurrences
    :return:
    '''

    ! bigartm - c $WV_PATH - v $VOCAB_PATH - -cooc - window
    10 - -write - cooc - tf $cooc_file_path_tf - -write - cooc - df $cooc_file_path_df - -write - ppmi - tf $ppmi_dict_tf - -write - ppmi - df $ppmi_dict_df

    cooc_dict = artm.Dictionary()
    cooc_dict.gather(
        data_path=BATCHES_DIR,
        cooc_file_path=ppmi_dict_tf,
        vocab_file_path=VOCAB_PATH,
        symmetric_cooc_values=True)
    cooc_dict.save_text(COOC_DICTIONARY_PATH)


def return_string_part(name_type, text):
    tokens = text.split()
    tokens = [item for item in tokens if item != '']
    tokens_dict = get_words_dict(tokens, set())

    return " |" + name_type + ' ' + ' '.join(['{}:{}'.format(k, v) for k, v in tokens_dict.items()])


def prepare_voc(batches_dir, vw_path, data_path, column_name='processed_text.txt'):
    print('Starting...')
    with open(vw_path, 'w', encoding='utf8') as ofile:
        num_parts = 0
        try:
            for file in os.listdir(data_path):
                if file.startswith('part'):
                    print('part_{}'.format(num_parts), end='\r')
                    if file.split('.')[-1] == 'csv':
                        part = pd.read_csv(os.path.join(data_path, file))
                    else:
                        part = pd.read_parquet(os.path.join(data_path, file))
                    part_processed = part[column_name].tolist()
                    for text in part_processed:
                        result = return_string_part('@default_class', text)
                        ofile.write(result + '\n')
                    num_parts += 1

        except NotADirectoryError:
            print('part 1/1')
            part = pd.read_csv(data_path)
            part_processed = part[column_name].tolist()
            for text in part_processed:
                result = return_string_part('@default_class', text)
                ofile.write(result + '\n')

    print(' batches {} \n vocabulary {} \n are ready'.format(batches_dir, vw_path))


def prepare_batch_vectorizer(batches_dir, vw_path, data_path, column_name='processed_text.txt'):
    #     if not glob.glob(os.path.join(batches_dir, "*")):
    prepare_voc(batches_dir, vw_path, data_path, column_name=column_name)
    batch_vectorizer = artm.BatchVectorizer(data_path=vw_path,
                                            data_format="vowpal_wabbit",
                                            target_folder=batches_dir,
                                            batch_size=100)
    #     else:
    #         batch_vectorizer = artm.BatchVectorizer(data_path=batches_dir, data_format='batches')

    return batch_vectorizer


def prepare_all(BATCHES_DIR, WV_PATH, DOCUMENTS_TO_BATCH_PATH, DICTIONARY_PATH,
                VOCAB_PATH, COOC_DICTIONARY_PATH, cooc_file_path_tf,
                cooc_file_path_df, ppmi_dict_tf, ppmi_dict_df):
    # TODO: check why batch vectorizer is returning (unused further)
    batch_vectorizer = prepare_batch_vectorizer(BATCHES_DIR, WV_PATH, DOCUMENTS_TO_BATCH_PATH)

    my_dictionary = artm.Dictionary()
    my_dictionary.gather(data_path=BATCHES_DIR, vocab_file_path=WV_PATH)
    my_dictionary.filter(min_df=3, class_id='text')
    my_dictionary.save_text(DICTIONARY_PATH)

    vocab_preparation(VOCAB_PATH, DICTIONARY_PATH)
    prepearing_cooc_dict(BATCHES_DIR, WV_PATH, VOCAB_PATH,
                         COOC_DICTIONARY_PATH, cooc_file_path_tf,
                         cooc_file_path_df, ppmi_dict_tf,
                         ppmi_dict_df)