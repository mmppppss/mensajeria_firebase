import flask
from flask import Flask, render_template, request, redirect, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, auth, db

session={}
app = Flask(__name__)

cred = credentials.Certificate('./credenciales.json')
firebase_app = firebase_admin.initialize_app(cred,{
    'databaseURL': 'https://mensajeria-c2f1f-default-rtdb.firebaseio.com/'
    })

@app.route('/', methods=["GET"])
def home():
    if 'user_uid' in session:
        return render_template('chat.html', username=session['username'])  
    return redirect(url_for('login')) 

@app.route('/registrarse', methods=['GET', 'POST'])
def registrarse():
    if request.method == 'GET':
        return render_template("registro.html")
    elif request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]
        username = request.form["username"] 
        try:
            user = auth.create_user(
                email=email,
                password=password
            )
            ref = db.reference('users')
            ref.child(user.uid).set({
                'username': username,
                'email': email
            })

            # Guardar el nombre en la sesión
            session['user_uid'] = user.uid
            session['username'] = username
            return redirect(url_for('login'))  
        except Exception as e:
            return f"Error al crear usuario: {str(e)}"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            id_token = data.get('idToken')

            if not id_token:
                return jsonify({'error': 'ID Token no proporcionado'}), 400

            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid'] 
            user = auth.get_user(uid)
            ref = db.reference('users')
            user_data = ref.child(uid).get()

            if user_data and 'username' in user_data:
                username = user_data['username']
            else:
                username = user.email
            session['user_uid'] = user.uid
            session['username'] = username
            print(username)
            return jsonify({'message': 'Autenticación exitosa'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return render_template("login.html")


@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    message = data.get('message')
    user = data.get('user')
    if not message or not user:
        return jsonify({'error': 'Faltan campos'}), 400

    ref = db.reference('messages')
    ref.push({
        'user': user,
        'message': message
    })
    return jsonify({'success': True})

@app.route('/get_messages', methods=['GET'])
def get_messages():
    ref = db.reference('messages')
    messages = ref.get()
    if messages:
        return jsonify(messages)
    return jsonify([])


if __name__ == '__main__':
    app.run(debug=True)

