import os 
import pandas as pd
import importlib
definergpt3 = importlib.import_module("definer-gpt3")
from collections import Counter


def process_metadata(metadata_file):
    df_metadata = pd.read_csv(metadata_file,sep='\t')
    df_metadata = df_metadata[df_metadata['should_include']==True]
    df_metadata['surface_case_norm'] = df_metadata['Prompt Forms'].str.lower()
    return df_metadata


def combine_evaluations(eval_files):
    df_all = []
    for eval_file in eval_files:
        new_df = pd.read_csv(eval_file,sep='\t')
        new_df = new_df[['Prompt','Dogwhistle Definition','Spelling',
        'Provided Definition', 'Secret Cue', 'Text', 'Responses', 'Dogwhistle',
        'Truncated Response', 'Overt', 'Covert']]
        df_all.append(new_df)
    df = pd.concat(df_all)
    df['surface_case_norm'] = df['Dogwhistle'].str.lower()
    df = df[(df['Spelling'].isna()) | (df['Spelling']=='dogwhistle')]
    df['Dogwhistle Definition'].fillna('',inplace=True)
    return df

def filter_excluded_terms(df_eval,df_metadata):
    surface_forms_to_include = set(df_metadata[df_metadata['should_include']==True]['surface_case_norm'])
    df_eval = df_eval[df_eval['surface_case_norm'].isin(surface_forms_to_include)]
    return df_eval



def make_template_for_missing_generations(missing_generation,df_prompts):
    new_entry = {}
    term = missing_generation['Dogwhistle']
    new_entry['Dogwhistle Definition'] = missing_generation['Dogwhistle Definition']
    new_entry['Secret Cue'] = missing_generation['Secret Cue']
    new_entry['Dogwhistle'] = term
    new_entry['Provided Definition'] = True if missing_generation['Dogwhistle Definition']!='' else False
    new_entry['Spelling'] = 'dogwhistle'



    prompt_template = df_prompts[(df_prompts['Provided Definition']==new_entry['Provided Definition']) &
    (df_prompts['Secret Cue']==new_entry['Secret Cue'])]['Prompt'].values[0]

    new_entry['Prompt'] = new_entry['Dogwhistle Definition'] + ' ' + prompt_template
    new_entry['Prompt'] = new_entry['Prompt'].strip()
    
    if term.startswith('using') or (term.startswith('the') and term not in ['the Fed','the Rothschilds','the goyim know']):
        new_entry['Text'] = new_entry['Prompt'].replace('[X]',term)
    else:
        new_entry['Text'] = new_entry['Prompt'].replace('[X]',f'"{term}"')    
    return new_entry
    
   




def find_missing_generations(df_metadata,df_eval):
    surface_forms_to_include = set(df_metadata[df_metadata['should_include']==True]['surface_case_norm'])
    definitions = list(df_eval['Dogwhistle Definition'].unique())
    secret_cues = list(df_eval['Secret Cue'].unique())
    terms = list(df_metadata['Prompt Forms'].unique())

    df = df_metadata.merge(df_eval,on='surface_case_norm',how='inner')
    
    missing_generation_list = []
    for definition in definitions:
        for secret_cue in secret_cues:
            for term in terms:
                matches = len(df[(df['Dogwhistle Definition']==definition) & 
                (df['Secret Cue']==secret_cue) & 
                (df['Prompt Forms']==term)])
                if matches==0:
                    missing_generation = {}
                    missing_generation['Dogwhistle Definition'] = definition
                    missing_generation['Secret Cue'] = secret_cue
                    missing_generation['Dogwhistle'] = term
                    missing_generation_list.append(missing_generation)

    return missing_generation_list

def write_missing_generations_to_file(missing_generation_list,df_prompts,outfile):
    new_entries = []
    for missing_generation in missing_generation_list:
        new_entry = make_template_for_missing_generations(missing_generation,df_prompts)
        new_entries.append(new_entry)
    df_new_entries = pd.DataFrame(new_entries)
    print(df_new_entries)
    df_new_entries.to_csv(outfile,sep='\t',index=False)



def main():

    eval_files = ['../results/defining/evaluation_aug2022.tsv',
    '../results/defining/evaluation_jan2023.tsv',
    '../results/defining/evaluation2_jan2023.tsv',
    '../results/defining/evaluation3_jan2023.tsv']

    df_metadata = process_metadata('../data/defining/all_surface_forms.tsv')
    df_eval = combine_evaluations(eval_files)
    df_eval = filter_excluded_terms(df_eval,df_metadata)
    df = df_metadata.merge(df_eval,on='surface_case_norm',how='inner')
    df = df.drop_duplicates(subset=['surface_case_norm','Dogwhistle Definition','Secret Cue'],keep='first')
    df.to_csv('../results/defining/all_evaluations_jan2023.tsv',sep='\t')
    print(df)
    # prompts_filename = '../data/defining/prompts.tsv'
    # df_prompts = pd.read_csv(prompts_filename,sep='\t')

    # missing_generation_list = find_missing_generations(df_metadata,df_eval)
    # outfile = '../defining/missing_prompts2_jan2023.tsv'
    # write_missing_generations_to_file(missing_generation_list,df_prompts,outfile)
 
   





    
    



if __name__ == "__main__":
    main()
