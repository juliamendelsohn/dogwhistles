import argparse
import json
import random
import os
import pandas as pd
import re
from utils import gpt3_completion, write_items
import random

def load_prompts(prompts_dir):
    df_prompts = pd.read_csv(os.path.join(prompts_dir,'prompts.tsv'),sep='\t')
    df_prompts.columns = columns=['Prompt','Prompt Type','Seed']
    prompt_types = set(df_prompts['Prompt Type'])
    prompt_info = {}
    prompt_info['prompts'] = df_prompts['Prompt']
    prompt_info['definitions'] = pd.read_csv(os.path.join(prompts_dir,'definitions.tsv'),sep='\t')['Definition']
    if 'Ideology' in prompt_types:
        prompt_info['ideology'] = pd.read_csv(os.path.join(prompts_dir,'ideologies.tsv'),sep='\t')['Ideology']
    if 'Country' in prompt_types:
        prompt_info['country'] = pd.read_csv(os.path.join(prompts_dir,'countries_small.tsv'),sep='\t')['Country']
        prompt_info['demonym'] = pd.read_csv(os.path.join(prompts_dir,'countries_small.tsv'),sep='\t')['Adjectival']
    if 'Target Group' in prompt_types:
        prompt_info['target'] = pd.read_csv(os.path.join(prompts_dir,'targets_immigrant.tsv'),sep='\t')['Target']
    return prompt_info

def compile_prompts(prompt_info):
    all_prompts = []
    for p,prompt in enumerate(prompt_info['prompts']):            
        for spelling in ['dogwhistle', 'dog-whistle','dog whistle']:
            match = re.search("\[([A-Z]+)\]", prompt)
            if match:
                category = match.group(0).replace("[","").replace("]","").lower()
                category_variants = list(prompt_info[category])                
                for variant in category_variants:
                    specific_group_prompt = prompt.replace(match.group(0),variant)
                    for d,definition in enumerate(prompt_info['definitions']):
                        new_prompt = {}
                        new_prompt['Prompt'] = definition + '\n' + specific_group_prompt + '\n' + '1.'
                        new_prompt['Prompt'] = new_prompt['Prompt'].replace('dogwhistle',spelling)
                        new_prompt['Prompt Id'] = p
                        new_prompt['Category'] = category
                        new_prompt['Variant'] = variant
                        new_prompt['Definition'] = d
                        new_prompt['Spelling'] = spelling
                        all_prompts.append(new_prompt)


            else:
                for d,definition in enumerate(prompt_info['definitions']):
                    new_prompt = {}
                    new_prompt['Prompt'] = definition + '\n' + prompt + '\n' + '1.'
                    new_prompt['Prompt'] = new_prompt['Prompt'].replace('dogwhistle',spelling)
                    new_prompt['Prompt Id'] = p
                    new_prompt['Category'] = 'generic'
                    new_prompt['Variant'] = 'generic'
                    new_prompt['Definition Id'] = d
                    new_prompt['Spelling'] = spelling
                    all_prompts.append(new_prompt)
    return all_prompts


def main(output_file, gpt3_version, num_generations, seed):
    random.seed(seed)
    prompts_dir = '/net/nfs2.mosaic/juliam/dogwhistle/data/Prompts0'
    prompt_info = load_prompts(prompts_dir)
    all_prompts = compile_prompts(prompt_info)
    all_prompts = [p for p in all_prompts if p['Category'] in ['target']]
    print(len(all_prompts))
    with open(output_file,'w') as f:
        for i,prompt in enumerate(all_prompts):
            if i % 100 == 0: print(i)
            res = prompt.copy()
            text = prompt['Prompt']
            gpt3_response = gpt3_completion(text, gpt3_version, max_tokens=256,
                                                        temperature=0.7, logprobs=1, echo=False,
                                                        num_outputs=num_generations, top_p=1,
                                                        best_of=num_generations)
            res['responses'] = [r['text'] for r in gpt3_response['choices']]
            json.dump(res,f)
            f.write('\n')



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Script to surface dogwhistles with GPT-3')

    # Required Parameters
    parser.add_argument('--output_file', type=str, help='File to output',default='/net/nfs2.mosaic/juliam/dogwhistle/surfacing/target_immigrant_prompt0.jsonl')
    parser.add_argument('--gpt3_version', type=str, help='text-davinci-002', default="text-davinci-002")
    parser.add_argument('--num_generations', type=int, help='No. of gpt3 generations', default=5)
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
