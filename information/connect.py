from pymongo import MongoClient
import os
MONGO_URI = str(os.getenv('MONGO_URI'))
client = MongoClient(MONGO_URI)
db = client['bookshop']
users_collection = db['users']
books_collection = db['books']
borrowed_books = db['book_user']