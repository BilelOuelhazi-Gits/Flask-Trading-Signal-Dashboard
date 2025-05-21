import time
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import json
from datetime import datetime
from bson import json_util


app = Flask(__name__)
app.secret_key = "supersecretkey"

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client.MySignal  # Connecting to the MySignal database
users_collection = db.users
signals_collection = db.trading_signals



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        phone_number = request.form['phone_number']

        if not username or not email or not password or not confirm_password or not phone_number:
            flash('Please fill in all the fields', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        existing_user = users_collection.find_one(
            {"$or": [{"username": username}, {"email": email}, {"phone_number": phone_number}]})

        if existing_user:
            flash('Username, email, or phone number already exists', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "phone_number": phone_number,
            "role": "user"  # Default role
        }

        users_collection.insert_one(user)

        flash('Registration successful', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({"username": username})

        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = username

            # Redirect user to the appropriate dashboard based on their role
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'super admin':
                return redirect(url_for('superadmin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/user/dashboard')
def user_dashboard():
    if 'logged_in' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        if user and user['role'] == 'user':
            # Retrieve all saved signals for the user
            user_signals = db.user_signals.find({"user_id": user['_id']})
            saved_signals = []
            for saved_signal in user_signals:
                # Find the original signal from signals_collection
                original_signal = signals_collection.find_one({"_id": saved_signal['signal_id']})
                if original_signal:
                    # Determine win/loss status of the saved signal based on the original signal
                    if original_signal['win_status'] is not None:  # Check if win status is determined
                        if original_signal['win_status']:
                            win_loss_status = 'Win'
                        else:
                            win_loss_status = 'Loss'
                    else:
                        win_loss_status = 'Undetermined'  # Set status as undetermined if original signal's win status is undetermined

                    # Extract asset, date, and pips difference
                    asset = original_signal['asset']
                    date = original_signal['created_at']
                    pips_difference = original_signal.get('pips_difference', None)

                    saved_signals.append({
                        "asset": asset,
                        "date": date,
                        "win_loss_status": win_loss_status,
                        "pips_difference": pips_difference
                    })
            return render_template('user_dashboard.html', username=username, saved_signals=saved_signals)
    flash('You need to log in as a user first', 'error')
    return redirect(url_for('login'))


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'logged_in' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        if user and user['role'] == 'admin':
            users = users_collection.find()
            signals = signals_collection.find()
            return render_template('admin_dashboard.html', username=username, users=users, signals=signals)
    flash('You need to log in as an admin first', 'error')
    return redirect(url_for('login'))


@app.route('/admin/add_signal', methods=['POST'])
def admin_add_signal():
    if 'logged_in' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        if user and user['role'] == 'admin':

            asset = request.form['asset']
            type_ = request.form['type']
            entry_price = float(request.form['entry_price'])
            stop_loss = float(request.form['stop_loss'])
            take_profit = [float(tp) for tp in request.form.getlist('take_profit')]
            risk_level = request.form['risk_level']

            current_time = datetime.now()


            signal = {
                "asset": asset,
                "type": type_,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_level": risk_level,
                "created_at": current_time,  # Add current time to the signal
                "win_status": None  # Initialize win_status to None
            }

            signals_collection.insert_one(signal)
            flash('Trading signal added successfully', 'success')
            return redirect(url_for('admin_dashboard'))
    flash('You need to log in as an admin first', 'error')
    return redirect(url_for('login'))




@app.route('/admin/update_win_status/<signal_id>', methods=['POST'])
def admin_update_win_status(signal_id):
    # Check if the user is logged in and is an admin
    if 'logged_in' not in session:
        flash('You need to log in as an admin first', 'error')
        return redirect(url_for('login'))

    username = session['username']
    user = users_collection.find_one({"username": username})

    if not user or user['role'] != 'admin':
        flash('You need to log in as an admin first', 'error')
        return redirect(url_for('login'))

    # Get the win status and selected take profit level from the form
    win_status = request.form.get('win_status')
    take_profit_level = int(request.form.get('take_profit_level'))

    # Validate the win status
    if win_status not in ('true', 'false'):
        flash('Invalid win status', 'error')
        return redirect(url_for('admin_dashboard'))

    # Find the signal by ID
    signal = signals_collection.find_one({"_id": ObjectId(signal_id)})

    if not signal:
        flash('Signal not found', 'error')
        return redirect(url_for('admin_dashboard'))

    # Extract necessary signal details
    entry_price = signal['entry_price']
    take_profit = signal['take_profit'][take_profit_level]

    # Determine the pip multiplier based on the currency pair
    is_jpy_pair = 'JPY' in signal['asset']
    pip_multiplier = 100 if is_jpy_pair else 10000

    # Calculate the pips difference based on the selected take profit level
    if win_status == 'true':
        pips_difference = (take_profit - entry_price) * pip_multiplier
    else:
        pips_difference = (signal['stop_loss'] - entry_price) * pip_multiplier

    # Update the signal document in the database with the win status and pips difference
    signals_collection.update_one(
        {"_id": ObjectId(signal_id)},
        {"$set": {"win_status": win_status, "pips_difference": pips_difference}}
    )

    flash('Win status and pips difference updated successfully', 'success')
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/delete_signal/<signal_id>', methods=['POST'])
def admin_delete_signal(signal_id):
    if 'logged_in' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        if user and user['role'] == 'admin':
            signals_collection.delete_one({"_id": ObjectId(signal_id)})
            flash('Signal deleted successfully', 'success')
            return redirect(url_for('admin_dashboard'))
    flash('You need to log in as an admin first', 'error')
    return redirect(url_for('login'))




def generate_signals():
    latest_signal = None  # Variable to store the latest emitted signal

    while True:
        signals = list(signals_collection.find().sort([("_id", -1)]))

        # Check if the latest signal has changed
        if signals and signals[0] != latest_signal:
            latest_signal = signals[0]
            for signal in signals:
                entry_price = signal['entry_price']
                pips_difference = 0

                # Determine if the pair involves JPY to set the multiplier
                is_jpy_pair = 'JPY' in signal['asset']
                pip_multiplier = 100 if is_jpy_pair else 10000

                if signal['win_status'] == 'true':
                    # Assuming the first take profit level is the target when winning
                    pips_difference = (signal['take_profit'][0] - entry_price) * pip_multiplier
                elif signal['win_status'] == 'false':
                    # Stop loss level is the target when losing
                    pips_difference = (signal['stop_loss'] - entry_price) * pip_multiplier

                signal['pips_difference'] = pips_difference

            yield f'data: {json.dumps(signals, default=str)}\n\n'

        time.sleep(5)  # Poll every 5 seconds


@app.route('/stream_signals')
def stream_signals():
    def generate():
        latest_signal = None

        while True:
            signals = list(signals_collection.find().sort([("_id", -1)]))

            if signals and signals[0] != latest_signal:
                latest_signal = signals[0]
                yield f"data: {json.dumps(signals, default=json_util.default)}\n\n"

            time.sleep(5)

    return Response(generate(), mimetype="text/event-stream")



@app.route('/save_signal/<signal_id>', methods=['POST'])
def save_signal(signal_id):
    if 'logged_in' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})

        if user and user['role'] == 'user':
            entry_price = float(request.form['entry_price'])
            stop_loss = float(request.form['stop_loss'])
            take_profit = [float(request.form[f'take_profit_{tp_index}']) for tp_index in range(len(request.form)) if f'take_profit_{tp_index}' in request.form]

            # Add current time
            current_time = datetime.now()

            modified_signal = {
                "user_id": user['_id'],
                "signal_id": ObjectId(signal_id),
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "saved_at": current_time  # Add current time when the signal is saved
            }

            user_signals_collection = db.user_signals
            user_signals_collection.update_one(
                {"user_id": user['_id'], "signal_id": ObjectId(signal_id)},
                {"$set": modified_signal},
                upsert=True
            )

            flash('Signal saved successfully', 'success')
            return redirect(url_for('user_dashboard'))

    flash('You need to log in first', 'error')
    return redirect(url_for('login'))

@app.route('/admin/add_user', methods=['POST'])
def admin_add_user():
    if 'logged_in' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        if user and user['role'] == 'admin':
            # Retrieve form data
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            phone_number = request.form['phone_number']
            role = request.form['role']

            # Check for existing user
            existing_user = users_collection.find_one(
                {"$or": [{"username": username}, {"email": email}, {"phone_number": phone_number}]})

            if existing_user:
                flash('Username, email, or phone number already exists', 'error')
            else:
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                user = {
                    "username": username,
                    "email": email,
                    "password": hashed_password,
                    "phone_number": phone_number,
                    "role": role
                }
                users_collection.insert_one(user)
                flash('User added successfully', 'success')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/edit_user/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']
        role = request.form['role']

        # Update user information
        users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {
            "username": username,
            "email": email,
            "phone_number": phone_number,
            "role": role
        }})
        flash('User updated successfully', 'success')

        return redirect(url_for('admin_dashboard'))
    else:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        return render_template('edit_user.html', user=user)


@app.route('/admin/delete_user/<user_id>', methods=['POST'])
def admin_delete_user(user_id):
    users_collection.delete_one({"_id": ObjectId(user_id)})
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/superadmin/dashboard')
def superadmin_dashboard():
    if 'logged_in' in session:
        username = session['username']
        user = users_collection.find_one({"username": username})
        if user and user['role'] == 'super admin':
            return render_template('super_admin_dashboard.html', username=username)
    flash('You need to log in as a super admin first', 'error')
    return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)