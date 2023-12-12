import sys 
sys.path.append(r'C:\Users\SALA443\Desktop\Projetos\Dados_B3 - teste\CVM\airflow')
sys.path.append(r"C:\Users\SALA443\Desktop\Projetos\Dados_B3 - teste\Transform\CVM_env\Lib\site-packages")
# print (sys.path)
import datetime as dt
from datetime import datetime,date,time
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
import uuid

dotenv_path = Path(r'/workspaces/app/.env')
load_dotenv(dotenv_path=dotenv_path)
# print(dotenv_path)

logging.basicConfig(
    
        level=logging.INFO,
        handlers=[logging.FileHandler("dadoseconomicos.log", mode='w'),logging.StreamHandler()],
        format="%(message)s -  %(funcName)s - %(filename)s - %(asctime)s"
        )

today = dt.date.today()    
'''output example: 2023/11/23/'''

sep = {'standard':';','altered':','}
encoding = {'standard':'utf-8','altered':'Windows-1252'}

tags = {'ppl_fundamentus':'S3|Fundamentus|B3'}

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
    
YearMonthDateFolder = folderpath(
    year = str(today.year),
    month = str(today.month).zfill(2),
    day = str(today.day).zfill(2)
    )

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
    '''
    This class performs the aws connection, by fetching 
    credentials within .env file.
    '''
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
# credentials = aws_connection(profile='admin').account     
# client = boto3.client('s3',
#                 aws_access_key_id=credentials['aws_access_key_id'],
#                 aws_secret_access_key=credentials['aws_secret_access_key']
#                 )

# credentials = aws_connection(profile='admin').account

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

class data_transfer():
    bucket = dict
    identity = str
    def __init__(self,
                 source:str,
                 target:str,
                 provider:str,
                 profile:str,
                 file:object,
                 pipeline=str,
                 pipeline_id=None,
                 tag=None):
        
        self.source         = source
        self.target         = target
        self.provider       = provider
        self.profile        = profile
        self.file           = file
        self.pipeline       = pipeline
        self.pipeline_id    = pipeline_id
        self.tag            = tag
        
        
    @property  
    def path(self) -> dict:
        
        bucket = folder_builder(
            sourcelayer=self.source,
            targetlayer=self.target,
            storageOption=self.provider).storage_selector  
    
        return bucket
    
   
    def transfer(self):
        '''
        This class performs data transfer between S3 buckets and add metadata fields in
        order to better management of the dataflow. The goal of that feature is to provide 
        agility whenever debugging is neeeded.
        Four field are added by default:
            identity: Field which contains the pipeline name and pipeline_id
            loaded_{*Target bucket name}_date: Date of data uploading
            loaded_{*Target bucket name}_time: Time of data uploading
            tags: Tags that are binded to pipeline name
            
        To perform the transfer method, write as bellow:
        
        data_transfer(source='landing',
                target='processed',
                provider='s3',
                profile='admin',
                file=pd.DataFrame(),
                pipeline='ppl_fundamentus').transfer()
                
        This function will get fundametus.csv file from S3 source to target and also will
        add the four metadata fields mentioned before.
        
        '''        
        
        credentials = aws_connection(profile=self.profile).account
        client = boto3.client(self.provider,                              
                              aws_access_key_id=credentials['aws_access_key_id'],
                              aws_secret_access_key=credentials['aws_secret_access_key']
                        )
        
        logging.info(f"AWS connection was establshed by using the profile{self.profile} for aws_connection class")
        
        bucket = data_transfer(
            source=self.source,
            target=self.target,
            provider=self.provider,
            profile=self.profile,
            file=pd.DataFrame(),
            pipeline_id=str()
            ).path

        key = f'{YearMonthDateFolder}fundamentus_historico.csv'

        data = client.get_object(Bucket=bucket['source_bucket'],Key=key)
        self.file = pd.read_csv(data["Body"],sep=sep['standard'],encoding=encoding['standard']) 
        
        # adding new fields
        # self.pipeline = 'ppl_intra_s3'
        self.pipeline_id = uuid.uuid4().hex[:16]
        identity = f"{self.pipeline}_{self.pipeline_id}"
        
        logging.info(f"Adding new metadata fields")
        self.file['identity'] = identity
        self.file[f"loaded_{bucket['target_bucket']}_date"] = date.today()
        self.file[f"loaded_{bucket['target_bucket']}_time"] = datetime.now().time()
        self.file['tags'] = tags[self.pipeline]
        
        buffer = io.StringIO()
        self.file.to_csv(buffer,sep=sep['standard'],encoding=encoding['standard'],index=None)
        logging.info(f"Dataframe was successfully buffered")
                
        client.put_object(ACL='private',
        Body=buffer.getvalue(),
        Bucket=bucket['target_bucket'],
        Key=f'{YearMonthDateFolder}fundamentus_historico.csv')
        logging.info(f"Done! Pipeline ran as {identity} using tags {tags[self.pipeline]}")



