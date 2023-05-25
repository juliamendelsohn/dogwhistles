import pandas as pd
from tqdm import tqdm
import argparse
import json
import re
import os

def compile_regex_patterns(regexfile):
    regex_list = pd.read_csv(regexfile,sep='\t')['Regex'].tolist()
     #Welfare and order are relevant but they are used in too many irrelevant contexts
    regex_list = [r"\b" + regex + r"\b" for regex in regex_list if regex != 'order']
    regex_str = r"(" + '|'.join(regex_list) + r")"
    return regex_str

def get_regexes_from_speeches(speechpath,pattern,outdir,jsonformat):
    if os.path.isdir(speechpath):
        speechfiles = [os.path.join(speechpath,x) for x in os.listdir(speechpath)]
    elif os.path.isfile(speechpath):
        speechfiles = [speechpath]
    else:
        raise Exception(f'Input path {speechpath} is not a file or directory')
    
    for speechfile in speechfiles:
        print(speechfile)
        outfile = os.path.join(outdir,os.path.basename(speechfile))
        try:
            num_lines = sum(1 for line in open(speechfile,'r'))
        except:
            num_lines = sum(1 for line in open(speechfile,'rb'))
        with open(speechfile,'r',encoding='utf-8',errors='ignore') as f_in, open(outfile,'w') as f_out:
            for line in tqdm(f_in,total=num_lines):
                m = re.search(pattern,line.lower())
                if m != None:
                    if jsonformat:
                        speech_info = json.loads(line)
                    else:
                        speech_info = {}
                        speech_info['speech_id'] = line.split('|')[0]
                        speech_info['text'] = ''.join(line.split('|')[1:])

                    speech_info['dogwhistles'] = re.findall(pattern,speech_info['text'].lower())
                    json_str = json.dumps(speech_info) + '\n'
                    f_out.write(json_str)


def main():
    parser = argparse.ArgumentParser(description="Argument parser for extracting dogwhistles")
    parser.add_argument('--regexfile',action='store',default='/net/nfs2.mosaic/juliam/dogwhistle/data/racial_dogwhistle_regexes.tsv')
    parser.add_argument('--speechpath',action='store',default='/net/nfs2.mosaic/juliam/dogwhistle/data/congressionalSpeeches/raw/')
    parser.add_argument('--outdir',action='store',default='/net/nfs2.mosaic/juliam/dogwhistle/data/congressionalSpeeches/raw_with_racial_dogwhistle/')
    parser.add_argument('--jsonformat',action='store_true')
    args = parser.parse_args()
    regexfile = args.regexfile
    speechpath = args.speechpath
    outdir = args.outdir
    jsonformat = args.jsonformat

    if not os.path.exists(outdir):
        os.mkdir(outdir)

    pattern = compile_regex_patterns(regexfile)
    get_regexes_from_speeches(speechpath,pattern,outdir,jsonformat)




if __name__ == "__main__":
    main()