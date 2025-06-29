import glob
import json
import argparse

parser = argparse.ArgumentParser(description='DIR')

parser.add_argument('--dir', 
                type=str, 
                )

args = parser.parse_args()
filename = args.dir

def concate_json(file_path:str,name:str):
    files = glob.glob(f'{file_path}/*.json')
    data = []
    for j in files:
     try:
        with open(j) as f:
            data += json.load(f)
     except:
         continue
    with open(f'user_logs/{name}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    

if __name__ == "__main__":
   
   concate_json(filename,filename.split("/")[-1])
            