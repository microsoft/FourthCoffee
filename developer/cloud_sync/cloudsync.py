import mysql.connector
from azure.cosmos import CosmosClient
import time
import os

# MySQL connection settings
server = os.environ.get('DBHOST')
database = os.environ.get('DBNAME')
username = os.environ.get('DBUSER')
password = os.environ.get('DBSECRET')
sync_interval = 120 #In seconds

#Azure CosmosDB settings
endpoint = os.environ.get('COSMOSENDPOINT')
key = os.environ.get('COSMOSKEY')
database_name = os.environ.get('COSMOSDB')
container_name = os.environ.get('COSMOSCONTAINER')

# Connect to MySQL
cnxn = mysql.connector.connect(user=username, password=password, host=server, database=database)
cursor = cnxn.cursor()

# Connect to Azure Cosmos DB
client = CosmosClient(endpoint, key)
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

while True:
    # Get all records with cloudSynced = 0
    query = "SELECT * FROM Orders WHERE cloudSynced = 0"
    cursor.execute(query)
    rows = cursor.fetchall()

    # Sync each record to Azure Cosmos DB and set cloudSynced to True
    for row in rows:
        document = {
            'id': str(row[0]),
            'orderDate': str(row[1]),
            'orderdetails': row[2],
            'storeId': str(row[3]),
            'cloudSynced': True
        }
        container.upsert_item(document)
        query = "UPDATE Orders SET cloudSynced = 1 WHERE orderID = " + str(row[0])
        print("Order ID:",row[0],"synced to cloud")
        cursor.execute(query)
        cnxn.commit()

    # Wait for 2 minutes before syncing again
    time.sleep(sync_interval)
