from openai import AzureOpenAI
import base64
from typing import List, Any, Dict, Callable
import os
import argparse
import time

parser = argparse.ArgumentParser(description='Query the math problems with solutions')

parser.add_argument('--dir', 
                    type=str, 
                    )


args = parser.parse_args()
domain_dir = args.dir

#GPT Client
client = AzureOpenAI(
    azure_endpoint="https://allam-swn-gpt-01.openai.azure.com/",
    api_version="2024-02-15-preview",
    api_key='E43WgvXM1er7Hx6chZ6Hc3yWNwuIPxWf2zBZoQZ6A9w3iH3MfTU6JQQJ99BCACI8hq2XJ3w3AAABACOGFaia'
)
###########
####Create Gemini1.5 pro
#GOOGLE_API_KEY = 'AIzaSyAQk6DSaCRDwH9ob4Dcru_8owOil-SjQLM'
#genai.configure(api_key=GOOGLE_API_KEY)
#####

###########
sys_promt_q = '''
Act as an excellent and professional practitioner for this following tasks: 
     1. High-level and in-depth image comprehension, i.e, receives a group of images together with their OCR results and precisely understand the details of each one. 
     2. Given the images and the image path and your profound understandings of the context, come up with reasonable and high-quality questions:
        (1) Here are the detailed question types that can be asked:
                → Questions types
                   	*Factual Recall
		   			*Conceptual Understanding
					*Step-by-step explanation
					*Math or reasoning & problem solving
					*Comparative & prediction analysis
					*Hypothetical reasoning
					*What-IF
					*multi-hop reasoning
					*Data retrieval
					*Image-based question (diagram, table, graph)
					*chat-style question & follow ups
					*Experimental design
					*Argumentation
					*Debugging error
		(2) Strictly use LATEX expressions for math formula and make sure that the LATEX expressions are compatible with json format
        (3) Strictly make sure that the LATEX expressions are compatible with json format for math formula
        (4) Strictly return the questions in the following format and strictly no separations or headers are needed:
           [
            {
            "image": "image_path" (received from user),
            "conversations": [
        	    {
            	"from": "human",
            	"value": "Question 1"
        	    },
        	    {
            	"from": "gpt",
                "value": "Answer to Question 1"
                },
                {
            	"from": "human",
                "value": "Question 2"
                },
                {
            	"from": "gpt",
                "value": "Answer to Question 2"
                },
                ... etc
                ]
            }
        ]
            
'''
#GOOGLE_API_KEY = 'API'
#genai.configure(api_key=GOOGLE_API_KEY)


#def get_gemini_response(messages:List[Any],sys_prompt:str) -> str:
#  model = genai.GenerativeModel('gemini-1.5-pro-latest',system_instruction = sys_prompt)
#  response = model.generate_content(messages)
#  return response.text


#def gempro_apply_chat_template(prompt:str,filename:str) -> List[Any]:
#    '''
#    template for Gemini-1.5 pro with images
#    '''
#    images = [genai.upload_file(filename)]
#    messages=[prompt]+images        
#    return messages

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


def encode_images_to_base64(image_paths: List[str]) -> List[str]:
    encoded_images = []
    for image_path in image_paths:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            encoded_images.append(encoded_string)
    return encoded_images

def run_ocr_on_images(file_path:str, LLM_Engine: Callable = get_gpt_response, LLM_Template: Callable = gpt_apply_chat_template_IT) -> str:
    """
    This function takes a group of images and returns a str
    with OCR extracted texts and any additional metadata.
    """
    sys_prompt = f"You are an excellent and professional image filter. If the image contains very little information strictly return bad. Otherwise, strictly return good"
    prompt = 'Please filter the image given'
    #convert pdf to list of PIL objects
    encoded_images = encode_images_to_base64([file_path])
    messages = LLM_Template(prompt,sys_prompt,encoded_images)
    response = LLM_Engine(messages)
    #ocr_results = response
    #with open(ocr_filename, "w") as f:
    #    f.write(ocr_results)
    return response,encoded_images

    
def run_question_proposal(encoded_images:list[str], image_path:str, Q_num: int = 10, LLM_Engine: Callable = get_gpt_response, LLM_Template: Callable = gpt_apply_chat_template_IT) -> str:
    """
    Proposes questions based on the group of images
    """
    prompt = f"Based on the provided image and the image path: \n {image_path}, \n come up with {Q_num} of high-quality questions. Out of the 10 questions, 5 should come from text in the image and the remaining 5 should come from graphics. Try your best to reach 10 questions."
    messages = LLM_Template(prompt,sys_promt_q,encoded_images)
    response = LLM_Engine(messages)
    return response

def validate_json(ocr_filename:str, json:str, new_file:str, LLM_Engine: Callable = get_gpt_response, LLM_Template: Callable = gpt_apply_chat_template_IT) -> None:
    """
    This function takes a group of jsons and returns a well-formatted json file
    """
    sys_prompt = '''
    You are an excellent and professional json file validator.
        Do the following task:
        1. Revise and improve it to make sure the math symbols, equations in LATEX are compatible with json format
        2. Output only the revised json formatted content. Strictly no headers or separation:
          [
            {
            "image": "image_path" (received from user),
            "conversations": [
        	    {
            	"from": "human",
            	"value": "Question 1"
        	    },
        	    {
            	"from": "gpt",
                "value": "Answer to Question 1"
                },
                {
            	"from": "human",
                "value": "Question 2"
                },
                {
            	"from": "gpt",
                "value": "Answer to Question 2"
                },
                ... etc
                ]
            }
        ]
        '''
    prompt = f'Please validate and revise the json given: {json}'
    #convert pdf to list of PIL objects
    messages = LLM_Template(prompt,sys_prompt,[])
    ocr_results = LLM_Engine(messages)
    with open(ocr_filename, "a") as f:
        f.write(ocr_results)
    os.system(f"mv {ocr_filename} {new_file}")


if __name__ == "__main__":
    print(domain_dir)
    data_dir = domain_dir.split("/")[-2]+"_QA"
    name = domain_dir.split("/")[-1].split(".")[0]
    os.system(f'mkdir {data_dir}')
    image_path = f'english_data/{domain_dir.split("/")[-1]}'
    ocr,encoded = run_ocr_on_images(domain_dir)
    if 'good' in ocr:
        data = run_question_proposal(encoded,image_path)
        validate_json(f"{data_dir}/data_file_{name}.txt",data, f'{data_dir}/data_file_{name}.json')
        #with open(f"{data_dir}/data_file_{name}.txt", "a") as f:
        #    f.write(data)
        #os.system(f'mv {data_dir}/data_file_{name}.txt {data_dir}/data_file_{name}.json')

    