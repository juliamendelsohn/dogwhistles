from googleapiclient import discovery
import json
import os
from compile_contexts_and_phrases import get_phrases,create_stimuli
import pandas as pd
from tqdm import tqdm 
import time

"""
Calculates Perspective API scores for toxicity, severe toxicity, identity attack, insult, profanity and threat
Inputs: text (string)  
Outputs: scores (dict with each Perspective attribute as a key and the score as the value)
"""
def get_perspective_scores(text):
    API_KEY = os.environ['PERSPECTIVE_API_KEY']

    client = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=API_KEY,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
    )

    attribute_list = ['TOXICITY','SEVERE_TOXICITY','IDENTITY_ATTACK','INSULT','PROFANITY','THREAT']
    attribute_dict = {a:{} for a in attribute_list}

    analyze_request = {
    'comment': { 'text': text},
    'languages': ['en'],
    'requestedAttributes': attribute_dict
    }

    response = client.comments().analyze(body=analyze_request).execute(num_retries=1000)

    scores = {}
    scores['Text'] = text
    for attribute in attribute_list:
        scores[attribute] = response['attributeScores'][attribute]['summaryScore']['value']
    return scores

def add_placeholder(template):
	if "IDENTITY_P" in template:
		return "IDENTITY_P"
	if "IDENTITY_A" in template:
		return "IDENTITY_A"
	else:
		return "IDENTITY_S"

def load_templates(template_filename):
    if template_filename.endswith('.tsv'):
        df = pd.read_csv(template_filename,sep='\t')
    else:
        df = pd.read_csv(template_filename)
    #Apply add_placeholder to create a new column from the "case_templ" column
    df['Placeholder'] = df['case_templ'].apply(add_placeholder)
    return df


def load_terms(terms_filename,sep='\t'):
    if terms_filename.endswith('.tsv'):
        df = pd.read_csv(terms_filename,sep='\t')
    else:
        df = pd.read_csv(terms_filename)
    return df




def create_stimuli_sentences(template_filename,terms_filename):
    df_template = load_templates(template_filename)
    df_terms = load_terms(terms_filename)
    df = df_template.merge(df_terms,on='Placeholder')
    df['Text'] = df.apply(lambda row: row['case_templ'].replace('[' + row['Placeholder'] + ']',row['Term']), axis=1)
    return df

def run_perspective(df):
    results = []
    for i,row in df.iterrows():
        scores = get_perspective_scores(row['Text'])
        results.append(scores)
        print(i)
    return results

def main():
    template_filename = "../data/hatecheck-dogwhistles/hateful_identity_only_templates.csv"
    terms_filename = "../data/hatecheck-dogwhistles/terms_to_test.tsv"
    results_dir = '../results/hatecheck-dogwhistles/'
    if not os.path.exists(results_dir):
        os.mkdir(results_dir)
    result_filename = os.path.join(results_dir,'perspective_scores_hateful_identity_only_templates.tsv')
    

    df = create_stimuli_sentences(template_filename,terms_filename)
    results = run_perspective(df)
    df_result = pd.DataFrame(results).merge(df,on='Text',how='inner')
    df_result.to_csv(result_filename,sep='\t')
        
  
    

if __name__ == "__main__":
    main()
