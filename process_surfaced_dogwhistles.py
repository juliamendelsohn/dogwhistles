import pandas as pd
import os
from collections import Counter
import re
import string
import spacy
nlp = spacy.load('en_core_web_sm')

def parse_response_string(response_string_list):
    all_responses = []
    for response_string in response_string_list:
        s = response_string.replace('"','')
        s = re.sub('\d+\.', '', s)
        s = s.split('\n')
        res_list = [x.strip().strip(string.punctuation).lower() for x in s if len(x)>0]
        all_responses += res_list
    return all_responses

def clean_response_counter(response_counter):
    new_counter = Counter()
    terms = list(response_counter.keys())
    docs = nlp.pipe(terms,disable=['ner'],n_process=8)
    lemmas = [' '.join([t.lemma_ for t in doc]) for doc in docs]
    for (term,lemma) in zip(terms,lemmas):
        term_to_add = term
        if term != lemma and lemma in response_counter:
            term_to_add = lemma
        if term_to_add[:4] == 'the ' and term_to_add[4:] in response_counter:
            term_to_add = term_to_add[4:]        
        new_counter[term_to_add] += response_counter[term] 
    return new_counter

def main():
    surfaced_dogwhistle_file = '/net/nfs2.mosaic/juliam/dogwhistle/surfacing/target_immigrant_prompt0.jsonl'
    output_file = '/net/nfs2.mosaic/juliam/dogwhistle/results/surfacing/target_immigrant_prompt0_cleaned.jsonl'
    df = pd.read_json(surfaced_dogwhistle_file,lines=True)
    df['response_list'] = df['responses'].apply(parse_response_string)
    df['length'] = [len(x) for x in df['response_list']]
    df1 = df.groupby(by=['Category','Variant']).agg({'response_list': 'sum', 'length': 'sum'}).reset_index()
    df1['response_counter'] = [Counter(x) for x in df1['response_list']]
    df1['response_counter_cleaned'] = df1['response_counter'].apply(clean_response_counter)
    df1['response_counts_list'] = [x.most_common() for x in df1['response_counter']]
    df1['response_counts_list_cleaned'] = [x.most_common() for x in df1['response_counter_cleaned']]
    for i,row in df1.iterrows():
        print('BEFORE',row['Variant'],row['response_counts_list'][:5])
        print('AFTER',row['Variant'],row['response_counts_list_cleaned'][:5])
    df1.to_json(output_file,orient='records',lines=True)

if __name__ == "__main__":
    main()
