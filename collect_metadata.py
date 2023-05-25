import pandas as pd
import os
import unidecode
import string
from collections import defaultdict
import json
from fuzzywuzzy import process
pd.options.mode.chained_assignment = None  # default='warn'


def remove_honorific(name):
    no_honorific_list = name.split()[1:]
    if 'of' in no_honorific_list:
        ix = no_honorific_list.index('of')
        no_honorific_list = no_honorific_list[:ix]
    if len(no_honorific_list) >= 1:
        surname = no_honorific_list[-1].strip(string.punctuation)
    else:
        surname = name
    if '.' in surname:
        surname = surname.split('.')[1]
    return surname.upper()

def normalize_diacritics(name):
    surname = name.split(',')[0].upper()
    surname = surname.split()[-1]
    return unidecode.unidecode(surname)

def map_nom_names_to_ideology(df_nom_sub):
    df_temp = df_nom_sub[['bioname','nominate_dim1']]
    df_temp['name'] = [normalize_diacritics(x) for x in df_temp['bioname']]
    return df_temp[['name','nominate_dim1']].set_index('name').to_dict()['nominate_dim1']

def map_nom_names_to_dim2(df_nom_sub):
    df_temp = df_nom_sub[['bioname','nominate_dim2']]
    df_temp['name'] = [normalize_diacritics(x) for x in df_temp['bioname']]
    return df_temp[['name','nominate_dim2']].set_index('name').to_dict()['nominate_dim2']


def map_names_speech_to_nom(df_speech,df_nom,congress,out_file):
    state_list = list(set(df_nom['state_abbrev']))
    with open(out_file,'w') as f:
        for state in state_list:
            df_nom_sub = df_nom[(df_nom['congress'] == congress)&(df_nom['state_abbrev']==state)]
            df_speech_sub = df_speech[(df_speech['state_x']==state)]
            nom_surnames = [normalize_diacritics(x) for x in df_nom_sub['bioname']]
            df_nom_sub['surname'] = nom_surnames
            name_to_nom1 = df_nom_sub[['surname','nominate_dim1']].set_index('surname').to_dict()['nominate_dim1']
            name_to_nom2 = df_nom_sub[['surname','nominate_dim2']].set_index('surname').to_dict()['nominate_dim2']

            for i,row in df_speech_sub.iterrows():
                speech_id = row['speech_id']
                firstname = row['firstname']
                lastname = row['lastname']
                try:
                    nearest_name,nearest_score = process.extractOne(lastname,name_to_nom1.keys())
                    if nearest_score >= 80 and nearest_name in name_to_nom1:
                        res = {}
                        res['speech_id'] = speech_id
                        res['nominate_dim1'] = name_to_nom1[nearest_name]
                        res['nominate_dim2'] = name_to_nom2[nearest_name]
                        f.write(json.dumps(res) + '\n')
                except:
                    continue


def map_by_speaker_id(df_nom_sub,metadata_dict,out_file):
    res = defaultdict(lambda: defaultdict())
    speaker_id_to_nom1 = df_nom_sub[['bioguide_id','nominate_dim1']].set_index('bioguide_id').to_dict()['nominate_dim1']
    speaker_id_to_nom2 = df_nom_sub[['bioguide_id','nominate_dim2']].set_index('bioguide_id').to_dict()['nominate_dim2']

    with open(out_file,'w') as f:
        for speech_id in metadata_dict:
            speaker_id = metadata_dict[speech_id]['speaker_id']
            if speaker_id in speaker_id_to_nom1:
                res = {}
                res['speech_id'] = speech_id
                res['nominate_dim1'] = speaker_id_to_nom1[speaker_id] 
                res['nominate_dim2'] = speaker_id_to_nom2[speaker_id] 
                f.write(json.dumps(res) + '\n')



def main():
    print('hi')
    nom_file = '/net/nfs2.mosaic/juliam/dogwhistle/data/congressionalSpeeches/HSall_members.csv'
    hein_dir = '/net/nfs2.mosaic/juliam/dogwhistle/data/congressionalSpeeches/hein-bound/'
    uscr_dir = '/net/nfs2.mosaic/juliam/dogwhistle/data/congressionalSpeeches/metadata/'
    speech_to_nom_out_dir = '/net/nfs2.mosaic/juliam/dogwhistle/data/congressionalSpeeches/speech_to_nominate'
    if not os.path.exists(speech_to_nom_out_dir):
        os.mkdir(speech_to_nom_out_dir)
    hein_start = 56
    hein_end = 103
    uscr_start = 104
    uscr_end = 116


    congress_sessions_hein = list(range(hein_start,hein_end+1))
    congress_sessions_uscr = list(range(uscr_start,uscr_end+1))
    congress_sessions = congress_sessions_hein + congress_sessions_uscr
    
    df_nom = pd.read_csv(nom_file)

    for congress in congress_sessions_hein:
        print(congress)
        speaker_file = os.path.join(hein_dir,str(congress).zfill(3) + '_SpeakerMap.txt')
        metadata_file = os.path.join(hein_dir,'descr_' + str(congress).zfill(3) + '.txt')
        out_file = os.path.join(speech_to_nom_out_dir,str(congress).zfill(3) +'.jsonl')
        df_speaker = pd.read_csv(speaker_file,sep='|',encoding_errors='ignore')
        df_metadata = pd.read_csv(metadata_file,sep='|',encoding_errors='ignore')
        df_speech = df_speaker.merge(df_metadata,on=['speech_id'])
        map_names_speech_to_nom(df_speech,df_nom,congress,out_file)
            

    for congress in congress_sessions_uscr:
        print(congress)
        metadata_file = os.path.join(uscr_dir,'uscr_metadata_' + str(congress).zfill(3) + '.json')
        out_file = os.path.join(speech_to_nom_out_dir,str(congress).zfill(3) +'.jsonl')
        with open(metadata_file,'r') as f:
            metadata_dict = json.load(f)
        df_nom_sub = df_nom[(df_nom['congress'] == congress)]
        map_by_speaker_id(df_nom_sub,metadata_dict,out_file)







if __name__ == "__main__":
    main()