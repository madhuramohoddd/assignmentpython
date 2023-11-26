from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from bson import ObjectId
from bson import json_util
import json

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/your_database_name'  # Update with your MongoDB connection URI
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this to a secure secret key
mongo = PyMongo(app)
jwt = JWTManager(app)


from uuid import uuid4

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400

    # Check if user already exists
    existing_user = mongo.db.users.find_one({'username': username})

    if existing_user:
        # Update existing user data (or handle as needed)
        return jsonify({'message': 'User already exists. Consider updating user data.'}), 409

    # Generate custom _id
    user_id = str(uuid4())

    user_data = {'_id': user_id, 'username': username, 'password': password}
    mongo.db.users.insert_one(user_data)

    return jsonify({'message': 'Registration successful!'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400

    user = mongo.db.users.find_one({'username': username})

    if not user or user['password'] != password:
        return jsonify({'message': 'Invalid username or password'}), 401

    #access_token = create_access_token(identity=username)
    # Create JWT token with the username as identity
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200

    
from flask_jwt_extended import get_jwt_identity

@app.route('/api/welcome', methods=['POST'])
@jwt_required()
def welcome():
    # Retrieve the username from the JWT token
    username = get_jwt_identity()

    # Save data to MongoDB
    user_data = {"name": username}
    mongo.db.users.insert_one(user_data)

    return jsonify({'message': f'Welcome, {username}! Data stored successfully.'}), 200




class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

from flask import jsonify

@app.route('/api/retrieve', methods=['GET'])
# #@jwt_required()
def retrieve_data():
    print("Entered retrieve_data function")  # Add print statements like this

    # Retrieve data from MongoDB, including _id
    data = list(mongo.db.users.find({}, {"_id": 1, "name": 1}))

    print("Data retrieved:", data)  # Add print statements like this

    # Convert ObjectId to string during JSON serialization
    json_data = JSONEncoder().encode(data)

    # Deserialize JSON data to a Python object and use jsonify
    response_data = json.loads(json_data)
    response = jsonify({'data': response_data})

    print("JSON Data:", json_data)  # Add print statements like this

    return response


@app.route('/api/edit/<user_id>', methods=['PUT'])
@jwt_required()
def edit_data(user_id):
    # Update data in MongoDB
    user_name = request.json.get('name')
    result = mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'name': user_name}})
    
    if result.modified_count == 1:
        return jsonify({'message': 'Data updated successfully.'}), 200
    else:
        return jsonify({'message': 'Data not found or not modified.'}), 404
    

    
@app.route('/api/delete/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_data(user_id):
    # Delete data from MongoDB
    result = mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    
    if result.deleted_count == 1:
        return jsonify({'message': 'Data deleted successfully.'}), 200
    else:
        return jsonify({'message': 'Data not found or not deleted.'}), 404

if __name__ == '__main__':
    app.run(debug=True)

   
