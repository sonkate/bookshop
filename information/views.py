from django.shortcuts import render
from .connect import users_collection, books_collection, borrowed_books
from bson.objectid import ObjectId
from bson import json_util
from datetime import datetime
from django.http import JsonResponse
from django.http import QueryDict
import json


# Create your views here.
# Home page
def home(request):
    # users_collection.insert_one(
    #     {
    #         "name": "son",
    #         "email": "son@gmail.com",
    #         "lib_code": "JEMSOW",
    #         "pwd": "son123",
    #         "phone_num": "091234233123",
    #         "avatar": "",
    #     }
    # )

    # books_collection.insert_one(
    #     {
    #         "pub_date": "12/01/2002",
    #         "publisher": "NXB TPHCM",
    #         "desc": "This is book desc",
    #         "total_page": 200,
    #         "rating": 5.6,
    #         "genre": "science",
    #         "author": "John Thomas",
    #         "name": "Environment and Human",
    #         "total_quantity": 10,
    #         "available": 7,
    #     }
    # )
    count = books_collection.count_documents({})
    response = {"data": {"count": count}, "message": "successful"}
    return JsonResponse(response, status=200)


def get_book_by_id(request):
    response = {}
    if request.method == "GET":
        if request.GET.get("id"):
            book = books_collection.find_one({"_id": ObjectId(request.GET.get("id"))})
            if book:
                book["_id"] = str(book["_id"])
                response = {"data": book, "message": "successful"}
            else: 
                return JsonResponse({"Error": "No book founded"}, status=400)
    return JsonResponse(response, status=200)

def return_book(request):
    if request.method == "POST":
        body = request.body.decode("utf-8")
        data = json.loads(body)

        userId = data.get('userId')
        bookId = data.get('bookId')
        
        borrowed_book = borrowed_books.find_one({"bookId": bookId, "userId": userId}) if (ObjectId.is_valid(bookId) and ObjectId.is_valid(userId)) else None 

        if borrowed_book and borrowed_book["status"]=='borrowing':
            result = borrowed_books.update_one({"_id": borrowed_book["_id"]}, { "$set": { "status": "returned" } })
        
            if result:
                # check pelnaty fee
                day_exceed = (datetime.now().date() - datetime.fromisoformat(borrowed_book["due_date"]).date()).days
                # update number of book available
                books_collection.update_one({"_id": ObjectId(bookId)}, {'$inc': {'available': 1}})
                return JsonResponse({'message': 'Book return successfully.', "data": {'Late days': abs(day_exceed) if day_exceed < 0 else 0}}, status=200)

        return JsonResponse({'error': 'This user does not borrow this book before or Wrong Id'}, status=400)
        
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def place_book(request):
    if request.method == "POST":
        body = request.body.decode("utf-8")
        data = json.loads(body)

        userId = data.get('userId')
        bookId = data.get('bookId')

        # check date
        try:
            due_date = datetime.strptime(data.get('due_date'), "%Y-%m-%d")
            due_date = due_date.replace(hour=23, minute=59, second=59)

            due_date_iso_format = due_date.isoformat()
        except:
            return JsonResponse({'error': 'Error date time format (Please send under form "yyyy-mm-dd" - "2023-12-31")'}, status=400)

        data_row = {
            "userId": userId,
            "bookId": bookId,
            "due_date": due_date_iso_format,
            "start_date": datetime.now().isoformat(),
            "status": "borrowing",
        }

        book = books_collection.find_one({"_id": ObjectId(bookId)}) if ObjectId.is_valid(bookId) else None
        user = users_collection.find_one({"_id": ObjectId(userId)}) if ObjectId.is_valid(userId) else None
        # Check if book is available
        if(book.get('available') == 0):
            return JsonResponse({'error': 'All books are currently borrowed.'}, status=409)
        
        borrowed_book = borrowed_books.find_one({"bookId": bookId, "userId": userId})

        # case: the book was not borrowed before
        if user and book and borrowed_book is None:
            result = borrowed_books.insert_one(data_row)
        
            if result.inserted_id:
                # update number of book available
                books_collection.update_one({"_id": ObjectId(bookId)}, {'$inc': {'available': -1}})
                return JsonResponse({'message': 'Book placed successfully'}, status = 200)
            
        # case this book was returned
        if borrowed_book is not None and borrowed_book['status'] == 'returned':
            borrowed_books.update_one({"_id": borrowed_book["_id"]}, { "$set": { "status": "borrowing","due_date": due_date_iso_format, "start_date": datetime.now().isoformat(),  } })
            # update number of book available
            books_collection.update_one({"_id": ObjectId(bookId)}, {'$inc': {'available': -1}})
            return JsonResponse({'message': 'Book placed successfully'}, status=200)
        # case this book is borrowing
        elif borrowed_books is not None and borrowed_book['status'] == 'borrowing':
            return JsonResponse({'error': 'This book was borrowed'}, status=409)

        return JsonResponse({'error': 'Failed to insert book placement'}, status=409)
        
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def add_book_wishlist(request):
    if request.method == "POST":
        body = request.body.decode("utf-8")
        data = json.loads(body)
        userId = data.get('userId')
        bookId = data.get('bookId')

        book = books_collection.find_one({"_id": ObjectId(bookId)}) if ObjectId.is_valid(bookId) else None
        user = users_collection.find_one({"_id": ObjectId(userId)}) if ObjectId.is_valid(userId) else None
        if book and user:
            users_collection.update_one({"_id": ObjectId(userId)}, {'$addToSet': {'wishlist': ObjectId(bookId)}})
            return JsonResponse({'message': 'Add book to wishlist successfully'}, status=200)
        return JsonResponse({'error': 'Check userId or bookId'}, status=409)
        
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def remove_book_wishlist(request):
    if request.method == "POST":
        body = request.body.decode("utf-8")
        data = json.loads(body)
        userId = data.get('userId')
        bookId = data.get('bookId')

        book = books_collection.find_one({"_id": ObjectId(bookId)}) if ObjectId.is_valid(bookId) else None
        user = users_collection.find_one({"_id": ObjectId(userId)}) if ObjectId.is_valid(userId) else None
        if book and user:
            users_collection.update_one({"_id": ObjectId(userId)}, {'$pull': {'wishlist': ObjectId(bookId)}})
            return JsonResponse({'message': 'Remove book from wishlist successfully'}, status=200)
        return JsonResponse({'error': 'Check userId or bookId'}, status=409)
        
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def get_book(request):
    if request.method == "GET":
        data = []
        if request.GET.get("searched"):
            searched = request.GET.get("searched")
            data = books_collection.find({"$or":[{"name":  {"$regex":searched}}, {"genre": {"$regex":searched}}]})
        else:
            data = books_collection.find({})
        data = json.loads(json_util.dumps(data))
        data_res = []
        for ele in data:
            data_res += [ele]
        response = {"data": data_res, "message": "successful"}
        return JsonResponse(response, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def get_placed_list(request, id):
    if request.method == "GET":
        # case: check valid userId
        if not ObjectId.is_valid(id):
            return JsonResponse({'error': 'Wrong Id'}, status=409)
        user = users_collection.find_one({"_id" : ObjectId(id)})

        # case: check existed user
        if user:
            data = borrowed_books.find({"userId" : id})
            placed_books = json.loads(json_util.dumps(data))

            # case: no book borrowed before
            if len(list(placed_books))==0:
                return JsonResponse({'data': '' ,'message': 'Placed list is empty'}, status=200)
            
            # case: normal list
            data = books_collection.find({"$or": [{'_id': ObjectId(item['bookId'])} for item in placed_books]})
            matching_books = json.loads(json_util.dumps(data))
            for book in matching_books:
                book['id'] = str(book['_id']['$oid'])
                del book['_id']

            combined_list = []
            for item in placed_books:
                book_id = item['bookId']
                matching_book = next((book for book in matching_books if book['id'] == book_id), None)
                if matching_book:
                    del item['userId']
                    del item['_id']
                    del item['bookId']
                    item.update(matching_book)
                    combined_list.append(item)
            data = [item for item in combined_list if item['status'] == 'borrowing']

            #check final length of data after being eliminated 
            if len(data) == 0:
                return JsonResponse({'data': '' ,'message': 'Placed list is empty'}, status=200)
            return JsonResponse({'data': data ,'message': 'success'}, status=200)

        else:
            return JsonResponse({'error': 'User id is not exist'}, status=409)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
            

def get_wishlist(request, id):
    if request.method == "GET":
        if not ObjectId.is_valid(id):
            return JsonResponse({'error': 'Wrong Id'}, status=409)
        user = users_collection.find_one({"_id" : ObjectId(id)})
        if user:
            data = json.loads(json_util.dumps(user))
            wishlist = data['wishlist'] if 'wishlist' in data else []
            if len(wishlist) == 0:
                return JsonResponse({'data': wishlist ,'message': 'Wishlist is empty'}, status=200)
            data = books_collection.find({"$or": [{'_id': ObjectId(item['$oid'])} for item in wishlist]})
            data = json.loads(json_util.dumps(data))
            data_res = []
            for ele in data:
                data_res += [ele]
            return JsonResponse({'data':data_res ,'message': 'Get wishlist successfully'}, status=200)
        else:
            return JsonResponse({'error': 'User id is not exist'}, status=409)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def sign_up(request):
    if request.method == "POST":
        body = request.body.decode("utf-8")
        data = json.loads(body)

        phone_num = data.get("phone_num")
        avatar = data.get("avatar")

        new_user = {
            "name": data.get("name"),
            "email": data.get("email"),
            "lib_code": data.get("lib_code"),
            "pwd": data.get("password"),
            "phone_num": phone_num if phone_num else "",
            "avatar": avatar if avatar else "",
        }

        if new_user.get("name") and new_user.get("email") and new_user.get("lib_code") and new_user.get("pwd"):
            invalid_email = users_collection.find_one({"email": new_user.get("email")})
            if invalid_email:
                return JsonResponse({"error": "Email has been used"}, status=409)
            
            result = users_collection.insert_one(new_user)

            if result.inserted_id:
                return JsonResponse({"message": "Created account successfully"})

        return JsonResponse({"error": "Failed to create new account"}, status=404)
        
    return JsonResponse({"error": "Invalid request method"}, status=405)

def sign_in(request):
    print(request)
    if request.method == "POST":
        body = request.body.decode("utf-8")
        data = json.loads(body)

        login = users_collection.find_one({"email": data.get("email"), "pwd": data.get("password")})

        if login:
            return JsonResponse({	
                "message": "Logged in successfully",
                "data": {"id": str(login.get("_id")), "name": login.get("name")}
            })

        return JsonResponse({"error": "Invalid username or password"}, status=404)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
    
def get_user_info(request, id):
    if request.method == "GET":     
        user = users_collection.find_one({"_id": ObjectId(id)})
        
        if user:
            return JsonResponse({
                "message": "User found",
                "data": {
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "password": user.get("pwd"),
                    "lib_code": user.get("lib_code"),
                    "phone_num": user.get("phone_num"),
                    "avatar": user.get("avatar")
                }
            })
        return JsonResponse({"error": "User not found"}, status=404)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def update_user_info(request):
    if request.method == "POST":
        body = request.body.decode("utf-8")
        data = json.loads(body)

        updated_user = {}
        user = users_collection.find_one({"_id": ObjectId(data.get("id"))})
        data.pop("id")

        if user:
            # and name and email and pwd and lib_code
            if not data.get("name"):
                data["name"] = user.get("name")
            if not data.get("password"):
                data["pwd"] = user.get("pwd")
            else:
                data["pwd"] = data.pop("password")
            if not data.get("lib_code"):
                data["lib_code"] = user.get("lib_code")
            if not data.get("phone_num"):
                data["phone_num"] = user.get("phone_num")
            if not data.get("avatar"):
                data["avatar"] = user.get("avatar")
            if not data.get("email"):
                data["email"] = user.get("email")
            else: 
                email = data.get("email")
                if email != user.get("email"):
                    invalid_email = users_collection.find_one({"email": email})
                    if invalid_email:
                        return JsonResponse({"error": "New email has been used"}, status=409)
            change = {"$set": data}
            result = users_collection.update_one(user, change)
            
            if result:
                return JsonResponse({"message": "Updated successfully"})
		
        return JsonResponse({"error": "Invalid user id"}, status=404)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def get_borrow_history(request, id):
    if request.method == "GET":
        user = users_collection.find_one({"_id": ObjectId(id)})
        books = []

        if user:
            records = borrowed_books.find({"userId": id}, {"userId": 0}, limit=10)
            for record in records:
                books += [record]
                name = books_collection.find_one({"_id": ObjectId(str(record.get("bookId")))})
                books[-1]["_id"] = str(books[-1]["_id"])
                books[-1]["due_date"] = books[-1]["due_date"][0:10]
                books[-1]["start_date"] = books[-1]["start_date"][0:10]
                books[-1]["name"] = name.get("name")
            return JsonResponse({"message": "History found", "history": books})
        
        return JsonResponse({"error": "User not found"}, status=404)
        
    return JsonResponse({"error": "Invalid request method"}, status=405)
