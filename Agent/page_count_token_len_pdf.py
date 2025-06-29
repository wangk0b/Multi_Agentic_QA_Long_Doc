import os
import PyPDF2
#import numpy as np
from tqdm import tqdm
import glob

def getPageCount(pdf_file):

	pdfFileObj = open(pdf_file, 'rb')
	pdfReader = PyPDF2.PdfReader(pdfFileObj)
	pages = len(pdfReader.pages)
	return pages

def extractData(pdf_file, page):

	pdfFileObj = open(pdf_file, 'rb')
	pdfReader = PyPDF2.PdfReader(pdfFileObj)
	pageObj = pdfReader.pages[page]
	data = pageObj.extract_text()
	return data

def getWordCount(data):

	data=data.split()
	return len(data)

def word_count(filename):
		
		pdfFile = filename
	
		# check if the specified file exists or not
		try:
			if os.path.exists(pdfFile):
				print("file found!")
		except OSError as err:
			print(err.reason)
			exit(1)


		# get the word count in the pdf file
		totalWords = 0
		numPages = getPageCount(pdfFile)
		for i in tqdm(range(numPages),desc = 'pages'):
			text = extractData(pdfFile, i)
			totalWords+=getWordCount(text)
		

		return totalWords,numPages



'''
doc_len = []
token_len = []
filenames = glob.glob("/eph/nvme0/azureml/cr/j/479ecd8aad9c4b8cb47681f1aeeb796c/exe/wd/eng_bio/STEM_BOOKs/*.pdf")
for i in tqdm(filenames,desc="EDA"):
		word,page = word_count(i)
		doc_len.append(page)
		token_len.append(word)
doc_len = np.array(doc_len)
token_len = np.array(token_len)
np.save('doc_len.npy',doc_len)
np.save('token_len.npy',token_len)
'''