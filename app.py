from flask import Flask, request, jsonify
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import os

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get(
    'JWT_SECRET_KEY', 'dev-secret-key')

jwt = JWTManager(app)


ships = []
_next_id = 1

users = []
_next_user_id = 1


class User(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))


class ShipSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Email(allow_none=True)
    arrived_at = fields.DateTime(allow_none=True)  # ISO8601


user_schema = User()
ship_schema = ShipSchema()
ships_schema = ShipSchema(many=True)

def find_ship(sid):
    return next((s for s in ships if s['id'] == sid), None)

@app.errorhandler(ValidationError)
def handle_marshmallow(err):
    return jsonify({"errors": err.messages}), 400




@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    if not '@' in email:
        return jsonify({'msg': "not a valid email"}), 400
    if username == 'admin' and password == 'password':
        token = create_access_token(identity=username)
        return jsonify(access_token=token), 200
    return jsonify({"msg": "Bad username/password"}), 401



@app.route('/ships', methods=['GET'])
def get_ships():
    return jsonify(ships_schema.dump(ships)), 200


@app.route('/ships', methods=['POST'])
@jwt_required()
def create_ship():
    global _next_id
    json_data = request.get_json()
    if not json_data:
        return jsonify({"msg": "No input provided"}), 400
    data = ship_schema.load(json_data)
    data['id'] = _next_id


    if not data.get('arrived_at'):
        data['arrived_at'] = datetime.now()
    _next_id += 1
    ships.append(data)
    return jsonify(ship_schema.dump(data)), 201


@app.route('/ships/<int:sid>', methods=['GET'])
def get_ship(sid):
    s = find_ship(sid)
    if not s:
        return jsonify({"msg": "Ship not found"}), 404
    return jsonify(ship_schema.dump(s)), 200



@app.route('/ships/<int:sid>', methods=['PUT'])
@jwt_required()
def update_ship(sid):
    s = find_ship(sid)
    if not s:
        return jsonify({"msg": "Ship not found"}), 404
    json_data = request.get_json() or {}
    # partial=True to allow partial updates
    updated = ship_schema.load(json_data, partial=True)
    s.update(updated)
    return jsonify(ship_schema.dump(s)), 200


@app.route('/ships/<int:sid>', methods=['DELETE'])
@jwt_required()
def delete_ship(sid):
    s = find_ship(sid)
    if not s:
        return jsonify({"msg": "Ship not found"}), 404
    ships.remove(s)
    return jsonify({"msg": "Ship deleted"}), 200


if __name__ == '__main__':
    app.run(debug=True)
