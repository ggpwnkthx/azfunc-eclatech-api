from azure.storage.blob import BlobClient, ContainerClient
from .sql import AzSQLEngine

def regenerate_cetas(blob_conn_str, blob_container_name, sql_server, sql_database, sql_table, sql_select):
    # use blob states
    error_blob_client = BlobClient.from_connection_string(
        conn_str=blob_conn_str,
        container_name=blob_container_name,
        blob_name=f"{sql_table}/triggers/error"
    )
        
    finish_blob_client = BlobClient.from_connection_string(
        conn_str=blob_conn_str,
        container_name=blob_container_name,
        blob_name=f"{sql_table}/triggers/finished"
    )
    
    # clean up data files
    container_client = ContainerClient.from_connection_string(
        conn_str=blob_conn_str,
        container_name=blob_container_name
    )
    for blob in container_client.list_blobs(name_starts_with=f"{sql_table}/data/"):
        container_client.delete_blob(blob)
    for blob in container_client.list_blobs(name_starts_with=f"{sql_table}/data"):
        container_client.delete_blob(blob)
        
    # recreate CETAS
    sql_engine = AzSQLEngine(sql_server,sql_database)
    try:
        sql_engine.execute(f"""
            IF  EXISTS (
                SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'{sql_table}') 
                AND 
                type in (N'U')
            )
            DROP EXTERNAL TABLE [{sql_table}]
            ;
            CREATE EXTERNAL TABLE {sql_table}
            WITH (
                DATA_SOURCE = [sa_esquireonspot],
                LOCATION = '/{blob_container_name}/{sql_table}/data',
                FILE_FORMAT = Parquet
            ) AS
            {sql_select};
        """)
    except Exception as e:
        error_blob_client.upload_blob(str(e.__dict__['orig']), overwrite=True)
        return

    finish_blob_client.upload_blob("izak wuz eer", overwrite=True)