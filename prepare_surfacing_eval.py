import os
import sys
import json
from collections import Counter
import pandas as pd 


def consolidate_variants(category,variant):
    if category == 'target' and variant == 'liberal':
        return 'anti-liberal'
    if category == 'target' and variant == 'conservative':
        return 'anti-conservative'
    if variant in ['liberal','far-left','leftist']:
        return 'liberal'
    if variant in ['conservative','far-right']:
        return 'conservative'
    if variant in ['Black','African-American','anti-Black','racist']:
        return 'anti-Black'
    if variant in ['Latino', 'Hispanic', 'anti-Latino', 'anti-Hispanic']:
        return 'anti-Latino'
    if variant in ['Native', 'Native American', 'anti-Native']:
        return 'anti-Native'
    if variant in ['Asian', 'anti-Asian']:
        return 'anti-Asian'
    if variant in ['Jewish','antisemitic','anti-Semitic']:
        return 'antisemitic'
    if variant in ['Christian', 'religious']:
        return 'religious'
    if variant in ['Muslim','Islamophobic']:
        return 'Islamophobic'
    if variant in ['gay','homophobic','lesbian','queer']:
        return 'homophobic'
    if variant in ['bisexual','biphobic']:
        return 'biphobic'
    if variant in ['trans', 'transgender', 'transphobic']:
        return 'transphobic'
    if variant in ['poor','classist']:
        return 'classist'
    if variant in ['alt-right', 'white supremacist']:
        return 'white supremacist'
    else:
        return variant


def load_file(filename):
    all_dogwhistles = []
    overall_dogwhistle_counts = Counter()
    with open(filename, 'r') as f:
        for line in f:
            d = json.loads(line)
            category = d['Category']
            variant = d['Variant']
            consolidated_variant = consolidate_variants(category,variant)
            for dogwhistle in d['response_counter_cleaned']:
                freq = d['response_counter_cleaned'][dogwhistle]
                all_dogwhistles.append((category,variant,consolidated_variant,dogwhistle,freq))
                overall_dogwhistle_counts[dogwhistle] += freq
    return all_dogwhistles,overall_dogwhistle_counts


def prepare_dataframes(all_dogwhistles,overall_dogwhistle_counts,generations_per_variant,threshold = 0.03):
    num_generations_df = pd.DataFrame.from_dict(generations_per_variant,orient='index').reset_index()
    num_generations_df.columns = ['variant group','num_generations']

    overall_counts_df = pd.DataFrame.from_dict(overall_dogwhistle_counts,orient='index').reset_index()
    overall_counts_df.columns = ['dogwhistle','overall count']
    dogwhistle_df =  pd.DataFrame(all_dogwhistles, columns=['category','variant', 'variant group', 'dogwhistle','count in variant'])

    counts_by_variant_group = dogwhistle_df.groupby(['variant group','dogwhistle']).sum().reset_index()
    counts_by_variant_group.columns = ['variant group','dogwhistle','count in variant group']
    counts_by_variant_group = counts_by_variant_group.merge(num_generations_df,on='variant group')
    counts_by_variant_group['percent of variant group generations'] = counts_by_variant_group['count in variant group']/counts_by_variant_group['num_generations']
    df_for_precision = counts_by_variant_group[counts_by_variant_group['percent of variant group generations'] >= threshold]
    df_for_precision = df_for_precision.sort_values(by=['percent of variant group generations'],ascending=False)

    dogwhistle_df = dogwhistle_df.merge(overall_counts_df, on='dogwhistle')
    dogwhistle_df = dogwhistle_df.merge(counts_by_variant_group, on=['variant group','dogwhistle']).sort_values(by='variant group')
    return dogwhistle_df,df_for_precision

def load_generation_counts(filename):
    generations_per_variant = Counter()
    with open(filename, 'r') as f:
        for line in f:
            d = json.loads(line)
            category = d['Category']
            variant = d['Variant']
            consolidated_variant = consolidate_variants(category,variant)
            generations_per_variant[consolidated_variant] += len(d['responses'])
    return generations_per_variant

def main():
    surfaced_dogwhistle_file = '/home/juliame/dogwhistle/results/surfacing/prompt0_cleaned.jsonl'
    raw_generations_file = '/home/juliame/dogwhistle/surfacing/prompt0.jsonl'
    out_dir = '/home/juliame/dogwhistle/results/surfacing/eval'
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    all_dogwhistles,overall_dogwhistle_counts = load_file(surfaced_dogwhistle_file)
    generations_per_variant = load_generation_counts(raw_generations_file)
    dogwhistle_df,df_for_precision = prepare_dataframes(all_dogwhistles,overall_dogwhistle_counts,generations_per_variant)
    
    dogwhistle_df.to_csv(os.path.join(out_dir,'df_for_recall.tsv'),sep='\t',index=False)
    df_for_precision.to_csv(os.path.join(out_dir,'df_for_precision.tsv'),sep='\t',index=False)

if __name__ == '__main__':
    main()