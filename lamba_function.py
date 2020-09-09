import json
import boto3
import os
import sys
import csv

from datetime import date
from datetime import datetime
import re
import argparse 
import time
global reduced_item


tempPath = '/tmp'
region = 'eu-west-2'

ec2 = boto3.client('ec2', region_name=region)

##
# Convert to string keeping encoding in mind...
##
def to_string(s):
    try:
        return str(s)
    except:
        #Change the encoding type if needed
        return s.encode('utf-8')
        

def reduce_item(key, value):
    global reduced_item
    ##print('key: & value:',key,value)
    ##print('Reduced Item:', reduced_item)
    
    ##print("debug", reduced_item)
    #Reduction Condition 1
    if type(value) is list:
        i=0
        for sub_item in value:
            reduce_item(key+'_'+to_string(i), sub_item)
            i=i+1

    #Reduction Condition 2
    elif type(value) is dict:
        sub_keys = value.keys()
        for sub_key in sub_keys:
            reduce_item(key+'_'+to_string(sub_key), value[sub_key])

    #Base Condition
    else:
        reduced_item[to_string(key)] = to_string(value)

    ## debug print('Reduced Item:', reduced_item)
    return(reduced_item)


def json_func():
    response = ec2.describe_instances()
    ##print("RESPONSE" , response)
    json_string = json.dumps(response, default=str)
    
    
    with open('/tmp/instances-v1.json', 'w') as file:
        json.dump(json_string, file)
        content="String content to write to a new S3 file"
        s3 = boto3.resource('s3')
        object = s3.Object('bucketname', 'instances-v1.json')
        object.put(Body=json_string)   
        file.close()
        
 
def lambda_handler(event, context):
        global reduced_item
        json_func()   

        #Reading arguments
        node = 'Reservations'
        json_file_path = '/tmp/instances-v1.json'
        csv_file_path = '/tmp/instances-v1.csv'

        with open(json_file_path, 'r') as fp:
            json_value = fp.read()
            ##raw_data = json.loads(json_value)
            response = ec2.describe_instances()
            ##raw_data = json_string = json.dumps(response, default=str)
            raw_data = response
            ##print('Raw JSON',raw_data)
            fp.close()
            data_to_be_processed = raw_data[node]

        ##try:
           ## data_to_be_processed = raw_data[node]
          ##  print('dtbp try:',data_to_be_processed[node])
        ##except:
            ##data_to_be_processed = raw_data[node]
           ## print('dtbpi except:',data_to_be_processed[node])
            
        processed_data = []
        header = []
        for item in data_to_be_processed:
            reduced_item = {}
            ##print('ITEM',item)
            reduce_item(node, item)
            print(reduced_item.keys())
            header += reduced_item.keys()

            processed_data.append(reduced_item)

        print('header:',header)
        header = list(set(header))
        print('header:',header)
        ##print(data_to_be_processed)
        header.sort()

        with open(csv_file_path, 'w+') as f:
            writer = csv.DictWriter(f, header, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for row in processed_data:
                writer.writerow(row)
                print('debug2',row)
                
        print ("Just completed writing csv file with %d columns" % len(header))
                
        s3 = boto3.resource('s3')
        BUCKET = s3.Bucket('bucketname')
        #s3.upload_file(csv_file_path,my_bucket,'instances-v1.csv')
        #s3.Bucket(BUCKET).upload_file("/tmp/instances-v1.csv", "instances-v1.csv")
        object = s3.Object('bucketname', 'instances-v1.csv')
        object.put(Body=open(csv_file_path,'rb'))   
        

         
        return {    
    
            'statusCode': 200,
           'body': json.dumps('Lambda complete!')
    }
