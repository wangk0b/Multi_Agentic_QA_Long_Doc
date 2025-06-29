from pdf2image import convert_from_path
from openai import AzureOpenAI, OpenAI
import base64
from typing import List, Any, Dict, Callable
import os
from tqdm import tqdm
import glob
#import google.generativeai as genai
from page_count_token_len_pdf import getPageCount
import json
import argparse
import time


parser = argparse.ArgumentParser(description='DIR')

parser.add_argument('--dir', 
                type=str, 
                )
parser.add_argument('--round', 
                type=int, 
                )
parser.add_argument('--n_q', 
                type=int, 
                )
parser.add_argument('--chunk', 
                type=int, 
                )
parser.add_argument('--overlap', 
                type=int, 
                )
parser.add_argument('--save_ocr', 
                type=bool, 
                default=False
                )
args = parser.parse_args()
filename = args.dir
round = args.round
chunk = args.chunk
n_q = args.n_q
overlap = args.overlap
save_ocr = args.save_ocr
#create chatgpt api
#GPT Client
client = AzureOpenAI(
    azure_endpoint="https://allam-swn-gpt-01.openai.azure.com/",
    api_version="2024-02-15-preview",
    api_key='Your API'
)
###########
####Create Gemini1.5 pro
#GOOGLE_API_KEY = 'AIzaSyAQk6DSaCRDwH9ob4Dcru_8owOil-SjQLM'
#genai.configure(api_key=GOOGLE_API_KEY)
#####



####read system prompts
with open("Agent/prompt/sys_q_new.txt", 'r') as f:
    sys_prompt_q = f.read()

with open("Agent/prompt/sys_prompt_a.txt", 'r') as f:
    sys_prompt_a = f.read()

with open("Agent/prompt/sys_j_new.txt", 'r') as f:
    sys_prompt_j = f.read()

with open("Agent/prompt/sys_prompt_e.txt", 'r') as f:
    sys_prompt_e = f.read()

with open("Agent/prompt/sys_prompt_evidence.txt", 'r') as f:
    sys_prompt_evidence = f.read()

with open("Agent/prompt/sys_prompt_ocr.txt", 'r') as f:
    sys_prompt_ocr = f.read()
####


#def gempro_apply_chat_template(prompt:str,filename:str,index:List[int]) -> List[Any]:
#    '''
#    template for Gemini-1.5 pro with images
#    '''
#    images = [genai.upload_file(filename+f'/image{i}.jpg') for i in range(index[0],index[1],1)]
#    messages=[prompt]+images        
#    return messages


'''
def get_gemini_response(messages:List[Any],sys_prompt:str) -> str:
  model = genai.GenerativeModel('gemini-1.5-pro-latest',system_instruction = sys_prompt)
  response = model.generate_content(messages)
  return response.text
'''

def get_gpt_response(messages:List[Dict]) -> str:
    while True:
        try:
            response = client.chat.completions.create(
            model="gpt-4o-900ptu",
            messages=messages,
            temperature=0.0,
            max_tokens=4096,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
            )
            response = response.choices[0].message.content
            break
        except:
            time.sleep(5)
            continue
    return response

def gpt_apply_chat_template_IT(prompt:str,sys_prompt:str,encoded_images:List[str]) -> List[Dict]:
    '''
    template for chatgpt with images
    '''
    message_content = [{"type": "text", "text": prompt}]
    if len(encoded_images) > 0:
        for encoded_image in encoded_images:
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
            })
    messages=[
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": message_content},
        {"role":"assistant","content":""}
    ]
    return messages

#base64 image encoding for chatgpt input
def encode_images_to_base64(image_paths: List[str]) -> List[str]:
    encoded_images = []
    for image_path in tqdm(image_paths,desc="Encode to base64"):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            encoded_images.append(encoded_string)
    return encoded_images

def convert_pdf_to_jpg(pdf_path:str,output_dir:str) -> Any:
    image_paths = []
    images = convert_from_path(pdf_path)
    p_len = len(images)
    for iter, image in enumerate(tqdm(images,desc="PDF to JPG")):
        image = image.convert('RGB')
        image.save(f"{output_dir}/image{iter}.jpg",'JPEG')
        image_paths.append(f"{output_dir}/image{iter}.jpg")
    return p_len, image_paths

#OCR agent
def run_ocr_on_images(encoded_images: List[str], ocr_filename:str, LLM_Engine: Callable = get_gpt_response, LLM_Template: Callable = gpt_apply_chat_template_IT) -> None:
    """
    This function takes a group of images and returns a str
    with OCR extracted texts and any additional metadata.
    """
    sys_prompt = sys_prompt_ocr
    prompt = 'Please perform OCR for the given images.'
    #convert pdf to list of PIL objects
    ocr_results = ''
    for iter,encoded_image in enumerate(tqdm(encoded_images, desc="OCR")):
    #formulate template
    #get response
        messages = LLM_Template(prompt,sys_prompt,[encoded_image])
        response = LLM_Engine(messages)
        ocr_results = f"\n\nHere starts ######Content of page {iter}: \n\n" + response
        with open(ocr_filename, "a") as f:
           f.write(ocr_results)

 
#get layout with Yolo v11 object detection maybe a bit additional
def run_yolo_on_images(image_folder: str, output_dir: str, Layout_Engine: str = "yolo11n.pt") -> None:
    """
    This function takes a group of images and returns YOLO detected objects.
    """
    #batch detection
    os.system(f'yolo predict model={Layout_Engine} source={image_folder} device=0 project={output_dir}')
    return None


def group_images(encoded_images:List[str], group_size: int = chunk, overlap: int = overlap) -> List[List[str]]:
    """
    Groups images into lists of `group_size` with `overlap` images overlapping
    between successive groups. Image with Yolo layouts
    """
    groups = []
    start_end = []
    i = 0
    for i in range(0,len(encoded_images),group_size - overlap):
      if (i+group_size) < len(encoded_images):
        chunk = encoded_images[i:(i+group_size)]
        start_end.append([i,i+group_size])
      else:
        chunk = encoded_images[i:]
        start_end.append([i,len(encoded_images)])
      groups.append(chunk)
    return groups,start_end


def run_question_proposal(encoded_images: List[str],OCR: str, Q_list: str = '', Feedback: str = '', Q_num: int = n_q, LLM_Engine: Callable = get_gpt_response, LLM_Template: Callable = gpt_apply_chat_template_IT) -> str:
    """
    Proposes questions based on the group of images
    """
    sys_prompt = sys_prompt_q
    if len(Feedback) > 0:
        prompt = f"Based on the provided images, the one-to-one OCR results of these images:\n {OCR} \n, the Proposed Questions:\n {Q_list} \n and Feebacks regarding the Q&As: \n {Feedback} \n. Propose harder questions and replace the Q&A pairs where the attempted answers are correct and keep the Q&A pairs where the attempted answers are wrong. The total number of Q&A pairs should be {Q_num} (the same as before)."
    else:
        prompt = f"Based on the provided images and the one-to-one OCR results of these images: \n {OCR}, \n come up with {Q_num} of high-quality questions with more emphasis on cross-two-image and cross-multi(three or more)-image questions.."
    messages = LLM_Template(prompt,sys_prompt,encoded_images)
    response = LLM_Engine(messages)
    return response

def run_extract_question(Q_List:str,LLM_Engine: Callable = get_gpt_response, LLM_Template: Callable = gpt_apply_chat_template_IT) -> str:
    sys_prompt = sys_prompt_e
    prompt = f'Extract questions from the provided Q&A pairs {Q_List}'
    messages = LLM_Template(prompt,sys_prompt,[])
    reponse = LLM_Engine(messages)
    return reponse
    

def run_question_answering(Q_List: str, encoded_images:List[str], LLM_Engine: Callable = get_gpt_response, LLM_Template: Callable = gpt_apply_chat_template_IT) -> str:
    """
    Answering questions based on the group of images
    """
    sys_prompt = sys_prompt_a
    prompt = f"Based on the provided images, Please answer the questions listed in the bullet points:\n {Q_List}."
    messages = LLM_Template(prompt,sys_prompt,encoded_images)
    response = LLM_Engine(messages)
    return response


def run_judge(encoded_images:List[str],OCR: str, Q_List: str, A_List: str, LLM_Engine: Callable = get_gpt_response, LLM_Template: Callable = gpt_apply_chat_template_IT) -> str:
    """
    Judge on the Q&As based on the group of images
    """
    sys_prompt = sys_prompt_j
    prompt = f"Based on the provided questions: {Q_List} \n and answers: {A_List} \n, please comprehensively evaluate and analyze each Q&A pair based on the provided images and their one-to-one OCR results:\n {OCR}."
    messages = LLM_Template(prompt,sys_prompt,encoded_images)
    response = LLM_Engine(messages)
    return response
    

def get_groups(filename:str, output_dir:str, ocr_file:str, sep:str) -> Any:
   _,image_paths = convert_pdf_to_jpg(filename,output_dir)
   encoded_images = encode_images_to_base64(image_paths)
   for url in image_paths:
        os.system(f'rm {url}')
   grouped_images,start_end_index = group_images(encoded_images)
   if not os.path.exists(ocr_file):
        print('---Calling OCR Agent---')
        run_ocr_on_images(encoded_images,ocr_file) 
        print('Agent OCR: Task Complete') 
   #print(start_end_index)
   f = open(ocr_file,"r")
   text = f.read().strip().split(sep)
   text = text[1:]
   os.system(f'rm {ocr_file}')
   return text, grouped_images, start_end_index, encoded_images 

def run_first_round(ocr_text: str, encode:List[str] ) -> Any:
       print('Starting with the first round')
       print('---Calling Agent 1 for Question Generation---')
       q_list = run_question_proposal(encode,ocr_text)
       #print(q_list)
       print('---Agent 1: Task complete---')
       print('---Calling Agent 2 to parse the Q&A pairs---')
       q_a = run_extract_question(q_list)
       #print(q_a)
       print('---Agent 2: Task complete---')
       print('---Calling Agent 3 for answers to the proposed questions---')
       a_list = run_question_answering(q_a,encode)
       print('---Agent 3: Task complete---')
       print('---Calling Agent 4 for feedbacks on the Q&A pairs---')
       feedback = run_judge(encode,ocr_text,q_list,a_list)
       print('---Agent 4: Task complete---')
       #print(feedback)
       return q_list, feedback

def run_debate( encode:List[str],ocr_text:str, Q_list:str, Feedback:str, n_round:int = round) -> str:
    for i in tqdm(range(0,n_round),desc="Debating"):
       print('---Debate Start---')
       print(f'---Round {i}---')
       print('---Calling Agent 1 for Question Rebuttal---')
       q_list = run_question_proposal(encode,ocr_text,Q_list,Feedback)
       #print(q_list)
       print('---Agent 1: Task complete---')
       print('---Calling Agent 2 to parse the Q&A pairs---')
       q_a = run_extract_question(q_list)
       print(q_a)
       print('---Agent 2: Task complete---')
       print('---Calling Agent 3 for answers to the proposed questions---')
       a_list = run_question_answering(q_a,encode)
       print('---Agent 3: Task complete---')
       print('---Calling Agent 4 for feedbacks on the Q&A pairs---')
       feedback = run_judge(encode,ocr_text,q_list,a_list)
       print('---Agent 4: Task complete---')
       Q_list = q_list
       Feedback = feedback
       #print(feedback)
       if 'questions proposed are excellent' in feedback:
          return feedback
    return Feedback
       

def run_evidence_validate(encode:List[str],ocr_text:str, feedback:str, bookname:str, length:int,LLM_Engine: Callable = get_gpt_response, LLM_Template: Callable = gpt_apply_chat_template_IT) -> str:
    print('---Calling Agent 5 for Evidence Validation---')
    sys_prompt = sys_prompt_evidence
    prompt = f'Please validate the evidence pages and sources of the following Q&A pairs: \n {feedback} \n based on the given images with bookname: {bookname} and length: {length} and OCR results: \n {ocr_text}'
    messages = LLM_Template(prompt,sys_prompt,encode)
    response = LLM_Engine(messages)
    print('---Agent 5: Task complete---')
    return response

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

    sep = 'Here starts ######'

   #for filename in tqdm(file, desc="Processing Books"):
    page = getPageCount(filename)
    if page < 400:
        output_dir = "Books/"+filename.split('/')[-1].split(".")[0]
        print(f"Process {output_dir}")
        os.system(f'mkdir {output_dir}')
        ocr_file = f"{output_dir}/ocr_result.txt"
        text, grouped_images, start_end_index, encoded_all = get_groups(filename,output_dir,ocr_file,sep)
        if not save_ocr:
            os.system(f'rm -r {output_dir}')
        name = output_dir.split("/")[-1]
        count = 0
        for encode,index in tqdm(zip(grouped_images,start_end_index), total= len(grouped_images),desc ="Handling Groups"):
            #index = start_end_index[1]
            count_start = index[0]
            count_end = index[1]
            ocr_text = ""
            #encode = grouped_images[1]
            for i in range(count_start,count_end,1):
                    ocr_text += text[i]+"\n\n"
            q_list, feedback = run_first_round(ocr_text,encode)
            if 'questions proposed are excellent' in feedback:
                q_final = run_evidence_validate(encode,ocr_text,feedback,bookname=name,length=page)
            else:
                feedback = run_debate(encode,ocr_text,q_list,feedback,n_round=round)
                q_final = run_evidence_validate(encode,ocr_text,feedback,bookname=name,length=page)
            #print(q_final)
            os.system(f'mkdir QA_English/{name}')
            with open(f"QA_English/{name}/QA_{name}.txt", "w") as f:
                f.write(q_final)
                os.system(f'mv QA_English/{name}/QA_{name}.txt QA_English/{name}/QA_{name}_{count}.json')
            count += 1
        concate_json(f"QA_English/{name}",name)      
     