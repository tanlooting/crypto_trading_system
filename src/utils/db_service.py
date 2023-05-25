from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class DBService:
    def __init__(self, auth_config, logger):
        self.username = auth_config['mdb_username']
        self.password = auth_config['mdb_password']
        self.cluster = auth_config['mdb_cluster']
        
        self.uri = f"mongodb+srv://{self.username}:{self.password}@{self.cluster}.7oor9py.mongodb.net/?retryWrites=true&w=majority"
        self.logger = logger
    
    def connect(self):
        try:
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            self.logger.info('Successful connection to database!')
            return self.client
        except Exception as e:
            self.logger.info("unsuccessful connection to database.")
            return None
    
    def ping(self):
        try:
            self.client.admin.command('ping')
            self.logger.info("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)
        
        
    def get_database(self, db_name):
        self.db = self.client[db_name]
        return self.db
    
    def disconnect(self):
        self.client.close()
