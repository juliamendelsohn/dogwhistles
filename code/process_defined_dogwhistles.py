import pandas as pd 
import os
import string
import difflib

# Function that takes in the gpt-3 definitions for dogwhistles (json lines file) and converts to .tsv for evaluation
def convert_gpt3_definitions_to_tsv(infile,outfile):
    df = pd.read_json(infile,lines=True)
    dogwhistles = []
    for i,row in df.iterrows():
        template_prompt_pieces = row['Prompt'].split('[X]')
        dogwhistle = row['Text'].replace(template_prompt_pieces[0],'').replace(template_prompt_pieces[1],'').strip('"').strip()
        dogwhistles.append(dogwhistle)
    df['Dogwhistle'] = dogwhistles
    df['Truncated Response'] = [x.split('\n')[0] for x in df['Responses']]
    df['Responses'] = [x.replace('\n','').replace('\t','').replace('\r','') for x in df['Responses']]
    df = df.sort_values(by='Dogwhistle')
    df.to_csv(outfile,sep='\t')


def main():
    infile = "../defining/missing_generations2_jan2023.jsonl"
    outfile = "../results/defining/missing_generations2_definitions_jan2023.tsv"
    convert_gpt3_definitions_to_tsv(infile,outfile)


if __name__ == "__main__":
    main()
