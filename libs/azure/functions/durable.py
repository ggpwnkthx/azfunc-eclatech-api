import os
import gzip
import json
import os
import uuid
from azure.storage.blob import BlobClient
def createContextStore(starter: str, instance_id: str = None, settings: dict = {}, data: dict = {}):
    if not instance_id:
        instance_id = uuid.uuid4().hex
    
    context = json.loads(starter)
    keyword = f"{context['managementUrls']['id']}"
    for key, value in context['managementUrls'].items():
        context['managementUrls'][key] = value.replace(keyword, instance_id)
    context['taskHubName'] = context['taskHubName'].lower()
    
    # Save context data
    BlobClient.from_connection_string(
        os.environ['AzureWebJobsStorage'],
        f"{context['taskHubName']}-largemessages",
        f"{instance_id}/context.json.gz"
    ).upload_blob(gzip.compress(json.dumps(context).encode('utf8')))
    
    # Save settings data
    BlobClient.from_connection_string(
        os.environ['AzureWebJobsStorage'],
        f"{context['taskHubName']}-largemessages",
        f"{instance_id}/settings.json.gz"
    ).upload_blob(gzip.compress(json.dumps(settings).encode('utf8')))
    
    # Save data
    BlobClient.from_connection_string(
        os.environ['AzureWebJobsStorage'],
        f"{context['taskHubName']}-largemessages",
        f"{instance_id}/data.json.gz"
    ).upload_blob(gzip.compress(json.dumps(data).encode('utf8')))
    
    return context['taskHubName'], instance_id

def getContextStore(taskHubName:str, instance_id:str, storeName:str = 'context'):
    blob_client = BlobClient.from_connection_string(
        os.environ['AzureWebJobsStorage'],
        f"{taskHubName}-largemessages",
        f"{instance_id}/{storeName}.json.gz"
    )
    return json.loads(gzip.decompress(blob_client.download_blob().readall()))

import pandas as pd
from azure.data.tables import TableClient
from azure.durable_functions.models.Task import TaskBase
def getOrchestrationStatus(taskHubName: str, InstanceId: str):
    table = TableClient.from_connection_string(os.environ['AzureWebJobsStorage'], f"{taskHubName}History")
    return pd.DataFrame(
        table.query_entities(
            f"PartitionKey eq '{InstanceId}'",
            select=['EventType','InstanceId'],
            results_per_page=1000
        )
    ).value_counts('EventType').to_dict()
    


import azure.durable_functions as df
def monitor_all_tasks(context: df.DurableOrchestrationContext, tasks: list[TaskBase], results=[]):
    if len(tasks) == 0:
        return results
    
    _results = yield context.task_any(tasks)
    
    results = yield monitor_all_tasks(
        context,
        [
            task 
            for task in tasks 
            if not task.is_completed
        ],
        results + (_results if type(_results) is list else [_results])
    )
    return results