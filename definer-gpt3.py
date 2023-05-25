import argparse
import json
import random
import os
import pandas as pd
import re
from utils import gpt3_completion, write_items
import random

def load_prompts(prompts_dir,prompts_filename='prompts.tsv',definitions_filename='definitions.tsv'):
    df_prompts = pd.read_csv(os.path.join(prompts_dir,prompts_filename),sep='\t')
    df_prompts.columns = columns=['Prompt','Provided Definition','Secret Cue']
    definitions_list = pd.read_csv(os.path.join(prompts_dir,definitions_filename),sep='\t')['Definition']
    definitions_list = list(definitions_list)  
    print(definitions_list)
    #spelling_list = ['dogwhistle','dog-whistle','dog whistle']
    spelling_list = ['dogwhistle']
    all_entries = []
    for i,row in df_prompts.iterrows():
        if row['Provided Definition'] == True:
            for definition in definitions_list:
                for spelling in spelling_list:
                    new_entry = {}
                    definition_variant = definition.replace('dogwhistle',spelling)
                    new_prompt = definition_variant + ' ' + row['Prompt']
                    new_entry['Prompt'] = new_prompt
                    new_entry['Dogwhistle Definition'] = definition
                    new_entry['Spelling'] = spelling
                    new_entry['Provided Definition'] = row['Provided Definition']
                    new_entry['Secret Cue'] = row['Secret Cue']
                    all_entries.append(new_entry)
        else:   
            new_entry = {}
            new_entry['Prompt'] = row['Prompt']
            new_entry['Dogwhistle Definition'] = ''
            new_entry['Spelling'] = ''
            new_entry['Provided Definition'] = row['Provided Definition']
            new_entry['Secret Cue'] = row['Secret Cue']
            all_entries.append(new_entry)
    return pd.DataFrame(all_entries)


def add_dogwhistles_to_prompts(df_prompts,prompts_dir,dogwhistle_filename,col_name='Term'):
    df_dogwhistles = pd.read_csv(os.path.join(prompts_dir,dogwhistle_filename),sep='\t')
    df_phrases = df_dogwhistles[df_dogwhistles['add_quotes']==True][col_name]
    df_symbols = df_dogwhistles[df_dogwhistles['add_quotes']==False][col_name]
    all_prompts = []
    for i,row in df_prompts.iterrows():
        for phrase in df_phrases:
            new_entry = row.to_dict()
            new_entry['Dogwhistle'] = phrase
            new_entry['Text'] = row['Prompt'].replace('[X]',f'"{phrase}"')
            all_prompts.append(new_entry)
        for symbol in df_symbols:
            new_entry = row.to_dict()
            new_entry['Dogwhistle'] = symbol
            new_entry['Text'] = row['Prompt'].replace('[X]',symbol)
            all_prompts.append(new_entry)
    df = pd.DataFrame(all_prompts)
    return df
        

def main(output_file, gpt3_version, num_generations, seed):
    random.seed(seed)
    prompts_dir = '../data/defining'
    # df_prompts = load_prompts(prompts_dir)
    # dogwhistle_filename = 'dogwhistles_to_define_jan2023.tsv'
    # df = add_dogwhistles_to_prompts(df_prompts,prompts_dir,dogwhistle_filename,col_name='surface_form')
    df = pd.read_csv('../defining/missing_prompts2_jan2023.tsv',sep='\t')
    with open(output_file,'w') as f:
        for i,row in df.iterrows():
            print(i / len(df))
            text = row['Text']
            new_entry = row.to_dict()
            gpt3_response = gpt3_completion(text, gpt3_version, max_tokens=256,
                                                        temperature=0.0, logprobs=1, echo=False,
                                                        num_outputs=num_generations, top_p=1,
                                                        best_of=num_generations)
            new_entry['Responses'] = [r['text'] for r in gpt3_response['choices']]
            if num_generations == 1:
                new_entry['Responses'] = new_entry['Responses'][0]
            json.dump(new_entry,f)
            f.write('\n')



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Script to surface dogwhistles with GPT-3')

    # Required Parameters
    parser.add_argument('--output_file', type=str, help='File to output',default='../defining/missing_generations2_jan2023.jsonl')
    parser.add_argument('--gpt3_version', type=str, help='text-davinci-002', default="text-davinci-002")
    parser.add_argument('--num_generations', type=int, help='No. of gpt3 generations', default=1)
    parser.add_argument('--seed', type=int, default=31555)

    args = parser.parse_args()
    print('====Input Arguments====')
    print(json.dumps(vars(args), indent=2, sort_keys=True))
    print("=======================")
    main(
        args.output_file,
        args.gpt3_version,
        args.num_generations,
        args.seed
    )
