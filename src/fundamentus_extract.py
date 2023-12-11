# importing libraries
from bs4 import *
import pandas as pd
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import datetime as dt
from datetime import datetime,date,time
from html.parser import HTMLParser
import locale
import time
import re
import logging
import objects
import boto3
import io
from pathlib import Path
from dotenv import load_dotenv

# Setting up variables
credentials = objects.aws_connection(profile="admin").account

today = dt.date.today()  

'''This variable YearMonthDateFolder is to standardize the S3 bucket, 
it defines yyyy/mm/dd as key when writing files.
'''         
YearMonthDateFolder = objects.folderpath(
    year = str(today.year),
    month = str(today.month).zfill(2),
    day = str(today.day).zfill(2))

'''
logging.basicConfig is for set which level of information will be displayed
and the file name
'''
logging.basicConfig(
    
        level=logging.INFO,
        handlers=[logging.FileHandler("fundamentus.log", mode='w'),logging.StreamHandler()],
        format="%(message)s -  %(funcName)s - %(filename)s - %(asctime)s"
        )
    
def Fundamentus_ELT():  
     
    '''
    
    This function fetches all rows from https://www.fundamentus.com.br/resultado.php
    buffers it into pandas dataframe and then writes it into S3 bucket.
    
    '''
    
    url = 'https://www.fundamentus.com.br/resultado.php'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}
    
    logging.info('URL and headers defined')
    
    req = Request(url, headers = headers)
    response = urlopen(req)
    html = response.read()

    logging.info('Parsing file with BeautifulSoup')
    
    soup = BeautifulSoup(html, 'html.parser')    
    
    colunas_names = [col.getText() for col in soup.find('table', {'id': 'resultado'}).find('thead').findAll('th')]
    colunas = {i: col.getText() for i, col in enumerate(soup.find('table', {'id': 'resultado'}).find('thead').findAll('th'))}

    dados = pd.DataFrame(columns=colunas_names)
    
    logging.info('Iterating over php table rows')
    for i in range(len(soup.find('table', {'id': 'resultado'}).find('tbody').findAll('tr'))):
        linha = soup.find('table', {'id': 'resultado'}).find('tbody').findAll('tr')[i].getText().split('\n')[1:]
        inserir_linha = pd.DataFrame(linha).T.rename(columns=colunas)
        dados = pd.concat([dados, inserir_linha], ignore_index=True)
    
    '''
    Here starts the variables setting to upload the file into S3 bucket
    
    '''
    bucket = objects.folder_builder(
    sourcelayer='landing',
    targetlayer='processed',
    storageOption='s3').storage_selector
    logging.info('Variable bucket ready')
    
    client = boto3.client('s3',
                        aws_access_key_id=credentials['aws_access_key_id'],
                        aws_secret_access_key=credentials['aws_secret_access_key']
                        )
    logging.info('Connection ready to be used')
    
    # df = pd.read_csv(f,sep=';',encoding='Windows-1252')
    buffer=io.StringIO()
    dados.to_csv(buffer,sep=';',encoding='utf-8',index=None)
    
    client.put_object(ACL='private',
            Body=buffer.getvalue(),
            Bucket=bucket['source_bucket'],
            Key=f'{YearMonthDateFolder}fundamentus_historico.csv')
        
    return logging.info('File was successfully uploaded to s3 bucket')       


