import sys 
sys.path.append(r'C:\Users\SALA443\Desktop\Projetos\Dados_B3 - teste\CVM\airflow')
sys.path.append(r"C:\Users\SALA443\Desktop\Projetos\Dados_B3 - teste\Transform\CVM_env\Lib\site-packages")
# print (sys.path)
import datetime
from datetime import date
import zipfile
import requests
from bs4 import BeautifulSoup
import re
import os
import logging
import boto3
import pandas as pd
from botocore.exceptions import ClientError
from pathlib import Path
from dotenv import load_dotenv
import io


dotenv_path = Path(r'/workspaces/DadosAbertosGOV/src/.env')
load_dotenv(dotenv_path=dotenv_path)
print(dotenv_path)

today = datetime.date.today()   
'''output example: 2023/11/23/'''



'''
This script aims to build the local enviroment to receive files from 
CVM DFPs and then save it into S3 bucket.
You can navigate over the script using the commented tags as bellow:
1-Folder set up
2-Getting DFP zip files
3-Convert to csv
4-Writting it into S3 bucket  
'''
# 1-Folder set up
class folderpath():
    """This object builds folder structure to store daily data 
    within year-month-date
    """
    def __init__(self,year:str,month:str,day:str):
        
        self.year = year
        self.month = month
        self.day = day

    @property
    def daily(self) -> str:
        return f"{self.year}/{self.month}/{self.day}"
    
    def __str__(self) -> str:
        return f"{self.year}/{self.month}/{self.day}/"
    
YearMonthDateFolder = folderpath(year = str(today.year),month = str(today.month).zfill(2),day = str(today.day).zfill(2))

class s3path():
    """This object builds folder structure of S3 datalake
    """
    def __init__(self,innerpath:str):        
        self.innerpath = innerpath
        
    @property   
    def fullpath(self) -> str:
        if self.innerpath == 'landing':
            return "landing"
            
        elif self.innerpath == 'processed':
            return "processed"
            
        elif self.innerpath == 'consume':
            
            return "consume"
        elif self.innerpath == 'enriched':
            return "enriched"
            
        else:
            return "caminho inexistente"          
       
class transform():
    
    def ToRaw(file:str):
        """
        This method extracts zip files from a given folder and stores inside 
        another given folder
        """
        landing=s3path(innerpath='landing').fullpath
        processed=s3path(innerpath='processed').fullpath
        folder=folderpath(
            year = str(datetime.date.today().year),
            month = str(datetime.date.today().month).zfill(2),
            day = str(datetime.date.today().day).zfill(2))
        
        # with zipfile.ZipFile(f"{s3path(innerpath='landing').fullpath}/{folderpath(year = str(datetime.date.today().year),month = str(datetime.date.today().month).zfill(2),day = str(datetime.date.today().day).zfill(2))}/{file}", 'r') as zip_ref:
        with zipfile.ZipFile(f"{landing}/{folder}/{file}", 'r') as zip_ref:
            zip_ref.extractall(f"{processed}/{folder}")

class aws_s3_buckets():
    def __init__(self,innerpath:str):        
        self.innerpath = innerpath
        
    @property   
    def fullpath(self) -> str:
        if self.innerpath == 'landing':
            return "de-okkus-landing-dev-727477891012"
        elif self.innerpath == 'processed':
            return "de-okkus-processed-dev-727477891012"
        elif self.innerpath == 'consume':
            return "de-okkus-consume-dev-727477891012"
        elif self.innerpath == 'silver':
            return "de-okkus-silver-dev-727477891012"
        elif self.innerpath == 'scripts':
            return "de-okkus-scripts-dev-727477891012"
        else:
            return "caminho inexistente"  
        
class aws_connection():
    def __init__(self,profile:str):
        self.profile = profile
    @property
    def account(self) -> dict:
        
        if self.profile == "admin":
            return {"aws_access_key_id":os.getenv("aws_access_key_id"),
                    "aws_secret_access_key":os.getenv("aws_secret_access_key"),
                    "aws_region":os.getenv("aws_region")}
        else:
            return {"aws_access_key_id":os.getenv("excepetion_aws_access_key_id"),
                    "aws_secret_access_key":os.getenv("excepetion_aws_secret_access_key"),
                    "aws_region":os.getenv("excepetion_aws_region")}

# Variable credentials receives the attributes of aws_connection class
# which gets the credentials of .env file
credentials = aws_connection(profile='admin').account     
client = boto3.client('s3',
                aws_access_key_id=credentials['aws_access_key_id'],
                aws_secret_access_key=credentials['aws_secret_access_key']
                )

class folder_builder():
    '''
    This class aims to build the right folder struture for S3 and local directories
    
    The attributes of this class are:
    sourcelayer: can be ['landing','processed','consume'] 
    targetlayer: can be ['landing','processed','consume']
    storageOption: can be ['s3','local_dev']
       
    Output is a dictionary which has:
    source_bucket:sourcelayer
    target_bucket:targetlayer
    
    storage_selector is the method's name which performs the standarization of the folder 
    example:
    layer = folder_builder(sourcelayer='landing',targetlayer='processed',storageOption='s3').storage_selector    
    print(layer['source_bucket'])     
    '''
    
    def __init__(self,sourcelayer:str,targetlayer:str,storageOption:str):

        self.sourcelayer = sourcelayer
        self.targetlayer = targetlayer
        self.storageOption = storageOption
       
    @property
    def storage_selector(self) -> dict:
        if self.storageOption == 'local_dev':
            return {'source_bucket':f'local_dev/{self.sourcelayer}/',
                    'target_bucket':f'local_dev/{self.targetlayer}/',
                    'key':f'{YearMonthDateFolder}/'}
        
        if self.storageOption == 's3':
            return {'source_bucket':f'de-okkus-{self.sourcelayer}-dev-727477891012',
                    'target_bucket':f'de-okkus-{self.targetlayer}-dev-727477891012',
                    'key':f'{YearMonthDateFolder}'}




  
#     def transfer(self):
            
#         bucket_x_key = files_IO(storageOption=self.storageOption,sourcelayer=self.sourcelayer,targetlayer=self.targetlayer).sourcelayerMode
#         Bucket = bucket_x_key['Bucket'] 
#         Key = bucket_x_key['Key'] 
#         data = client.get_object(Bucket=Bucket,Key=Key)
        
#         df = pd.read_csv(data['Body'],sep=';',encoding='utf-8')
#         df[f'loaded_to{self.sourcelayer}_date'] = date.today()
#         df[f'loaded_to{self.sourcelayer}_time'] = datetime.now().time()
#         buffer = io.StringIO()
        
#         bucket_x_key = files_IO(storageOption=self.storageOption,sourcelayer=self.sourcelayer,targetlayer=self.targetlayer).targetlayer
#         Bucket = bucket_x_key['Bucket'] 
#         Key = bucket_x_key['Key'] 
#         df.to_csv(buffer,encoding='utf-8',sep=';')    
        
#         client.put_object(
#                 ACL='private',
#                 Body=buffer.getvalue(),
#                 Bucket=f'de-okkus-{self.targetlayer}-dev-727477891012',
#                 Key=f'{YearMonthDateFolder}{self.filename}')

# x = files_IO(
#     sourcelayer='landing',
#     targetlayer='processed',
#     filename='cad_cia_aberta.csv',
#     storageOption='s3').transfer

# files_IO.transfer()
# bucketKey = files_IO(storageOption='s3',layer='processed').layerMode
# print(bucketKey['Bucket'])
# print(bucketKey['Key'])

            
            
        
        # credentials = aws_connection(profile="admin").account
        # # url = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv'
        # df = pd.read_csv(self.source,sep=';',encoding='Windows-1252')
        # buffer = io.StringIO()
        # df.to_csv(buffer,encoding='utf-8',sep=';')
        # # rawData = io.StringIO(urlData.decode('ISO 8859-1'))
        # client = boto3.client('s3',aws_access_key_id=credentials['aws_access_key_id'],
        #                         aws_secret_access_key=credentials['aws_secret_access_key']
        #                         )    

        # client.put_object(ACL='private',
        #             Body=buffer.getvalue(),
        #             Bucket='de-okkus-landing-dev-727477891012',
        #             Key=f'{self.folderStructure}cad_cia_aberta.csv')      
    # @property
    # def conn(self):        
    #     return aws_connection(os.getenv("aws_access_key_id"),os.getenv("aws_secret_access_key"),os.getenv("aws_region"))  
    # @property
    # def credentials(self):
        
        
        
    #     self.aws_access_key_id       = os.getenv("aws_access_key_id"),
    #     self.aws_secret_access_key   = os.getenv("aws_secret_access_key"),
    #     self.aws_region              = os.getenv("aws_region") 
        
    #     return self.aws_access_key_id

# ends settings from folder structure and s3 buckets path
# credentials = aws_connection(profile="admin").account
# print (credentials['aws_access_key_id'])
# print (credentials['aws_region'])


# def FindDREfiles(param:str) -> list:
#     """
#     Finds and Lists all files that matches with DRE
#     """
#     FileList = []
#     for file in os.listdir(ProcessedZone):
        
#         if re.findall(param,file):
            
#             FileList.append(file)
           
#     return FileList

# def ReadDREFilesTransformAndSaveAsParquet():

#     fileList = FindDREfiles('DRE')

#     for file in fileList[:]:  
#         foldername = f"{str(file).strip('.csv')}/"
#         schema = dre
#         df = pd.read_csv(f'{ProcessedZone}{file}',delimiter=';',encoding='ISO-8859-1')
#         df['Transform_Date'] = pd.to_datetime('today').to_datetime64()
#         os.makedirs(f"{ConsumeZone}{foldername}",exist_ok=True)
#         file = str(file).strip('.csv')
#         df.to_parquet(f"{ConsumeZone}{foldername}{file}_{pd.to_datetime('today').date()}.parquet",engine='pyarrow',partition_cols='DT_INI_EXERC')
#         file = None
#     return None