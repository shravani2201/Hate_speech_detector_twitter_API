import os
from flask import *
from flask_mysqldb import MySQL
import MySQLdb as mdb
import re
import pickle
import numpy as np
import pandas as pd
import re
import string
import tensorflow as tf
from tensorflow import keras
from keras.preprocessing.sequence import pad_sequences
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

app = Flask(__name__,template_folder="templates",static_folder="static")

app.secret_key = 'secret@1234'

mydbConn = mdb.connect(
  host="localhost",
  user="root",
  password="shobhana",
  database="hate_speech_project"
)
curr = mydbConn.cursor(mdb.cursors.DictCursor)
mydb = MySQL(app)

loaded_model = tf.keras.models.load_model('hate_ml_model.h5')

with open('tokenizer.pkl', 'rb') as tokenizer_file:
    tokenizer = pickle.load(tokenizer_file)

@app.route('/')
@app.route('/login',methods=['GET','POST'])
def login():
    print(request.method)
    print(request.form)
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        print(email, password)
        # curr =  mysql.connector.cursor(mdb.cursors.DictCursor)
        curr.execute(
            'SELECT * FROM users WHERE email = % s \
            AND password = % s', (email, password, ))
        users = curr.fetchone()
        print("Users:", users)
        if users:
            session['loggedin'] = True
            session['id'] = users['id']
            session['username'] = users['username']
            username = session['username']
            msg = 'Logged in successfully !'
            curr.execute("SELECT * FROM ml_table where username = %s", (username,))
            datatuple = curr.fetchall()
            data=[]
            for i in range(len(datatuple)):
                data.append(datatuple[i])
            print(data)

            curr.execute("SELECT COUNT(id) from ml_table where username = %s",(username,))
            count = curr.fetchone()
            count = count['COUNT(id)']
            print(count)

            curr.execute("select count(hate) from ml_table where hate = 1 and username = %s",(username,))
            count1 = curr.fetchone()
            count1 = count1['count(hate)']

            curr.execute("select count(`Not_hate`) from ml_table where `Not_hate` = 1 and username = %s",(username,))
            count2 = curr.fetchone()
            count2 = count2['count(`Not_hate`)']

            
            curr.execute("SELECT hate FROM ml_table WHERE username = %s", (username,))
            data1 = curr.fetchall()
            print(data1)
            hate_count = 0
            not_hate_count = 0
            for row in data1:
                if row['hate'] == 1:
                    hate_count += 1
                else:
                        not_hate_count += 1
            
            if not len(datatuple):
                pie_chart_image_path = "static/new_user.jpeg"
                chart_path = "static/new_user.jpeg"
                bar_graph_path="static/new_user.jpeg"
                return render_template('dash.html', msg=msg, data=data, count=count,count1=count1,count2=count2,pie_chart_image=pie_chart_image_path,chart_path=chart_path,bar_path=bar_graph_path)
            else:

                # Create the pie chart
                plt.figure(figsize=(5, 3.5))
                labels = ["Hate", "Not_hate"]
                values = [hate_count, not_hate_count]
                colors = ["#ff9999", "#66b3ff"]
                plt.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
                plt.title("Hate vs Not_hate Pie Chart")

                # Save the pie chart image to the 'static' folder
                pie_chart_image_path = os.path.join('static', 'pie_chart.png')
                plt.savefig(pie_chart_image_path)
                plt.figure(figsize=(4, 3.5))
                labels1 = ["Hate (1)", "No Hate (0)"]
                values1 = [hate_count, not_hate_count]
                colors1 = ['red', 'blue']

                plt.bar(labels1, values1, color=colors1)
                plt.title('Hate Distribution')
                plt.xlabel('Hate Value')
                plt.ylabel('Count')

                # Save the bar chart image to a file
                bar_graph_path="static/hate_bar.png"
                plt.savefig("static/hate_bar.png")

                curr.execute("SELECT id, prediction FROM ml_table WHERE username = %s", (username,))
                data2 = curr.fetchall()
                if data2:
                    id = []  # Create an empty list to store the id values
                    for record in data2:
                        id.append(record['id'])
                    prediction = []  # Create an empty list to store the prediction values
                    for record in data2:
                        prediction.append(record['prediction'])
                if id and prediction:
                    # Create a line chart
                    plt.figure(figsize=(5, 3.5))
                    plt.plot(id, prediction, marker='o', linestyle='-', color='b')
                    plt.title('Predictions')
                    plt.xlabel('id')
                    plt.ylabel('Predictions')

                    # Save the chart as a PNG image
                    chart_path = "static/line_chart.png"
                    plt.savefig(chart_path)

       
            return render_template('dash.html', msg=msg, data=data, count=count,count1=count1,count2=count2,pie_chart_image=pie_chart_image_path,chart_path=chart_path,bar_path=bar_graph_path )
            msg = 'Incorrect username / password !'
    return render_template('hate.html',msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    print("Hey in regiser: ")
    print(request.method)
    print(request.form)
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        #cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curr.execute(
            'SELECT * FROM users WHERE username = % s', (username, ))
        users = curr.fetchone()
        if users:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'name must contain only characters and numbers !'
        else:
            curr.execute('INSERT INTO users VALUES (NULL, % s, % s, % s)',(username, password, email,))
            mydbConn.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('hate.html', msg=msg)


@app.route("/home")
def home():
    print("HEYEEEEEEEEE")
    if 'loggedin' in session:
        curr.execute("SELECT * FROM ml_table")
        data = curr.fetchall()
        # print(data)
        import array
        data = array.array('i', data)
        print(data)
        
        return render_template("dash.html", data=data)
    
    return redirect(url_for('login'))



maxlen = 50

def preprocess_text(text):
    text = re.sub(r'[^\w\s]', '', text)
    text = text.lower()
    return text

tweet_text = " "

@app.route("/predict", methods=['GET','POST'])
def predict():
    if request.method == 'POST':
        input_text = request.form.get('input_text')
        tweet_text = input_text
        if not input_text:
            return render_template("dash.html")


        input_text = preprocess_text(input_text)

        input_sequence = np.array(tokenizer.texts_to_sequences([input_text]))
        input_sequence = pad_sequences(input_sequence, padding='post', maxlen=maxlen)

        prediction = loaded_model.predict(input_sequence)
        print(prediction)

        Cutoff = 0.005

        plt.figure(figsize=(8, 4))
        plt.bar(["Prediction", "Cutoff Threshold"], [prediction[0][0], Cutoff], color=["blue", "red"])
        plt.xlabel("Category")
        plt.ylabel("Probability")
        plt.title("Prediction vs. Cutoff Threshold")
        plt.savefig('static/bar_graph.png')

        if prediction >= Cutoff:
            result = "Hate"
            hate_value = 1
            not_hate_value = 0
        else:
            result = "Not_hate"
            hate_value = 0
            not_hate_value = 1

        if "username" in session:
            user_name = session["username"]

        prediction_float = float(prediction)


        curr.execute('SELECT username FROM users WHERE username = %s', (user_name,))
        user_data = curr.fetchone()

        if user_data:
                username = user_data['username']
                curr.execute('INSERT INTO ml_table (username, Post, Hate, `Not_hate`,Prediction) VALUES (%s, %s, %s, %s,%s)',
                             (username, input_text, hate_value, not_hate_value,prediction_float*100))
                mydbConn.commit()
       
        return render_template('result.html', input_text=input_text, prediction=prediction*100, result=result, cutoff=Cutoff)
    return redirect(url_for('home'))
ck = ""
cs = ""
ak = ""
aks = ""
@app.route('/keys', methods=['POST'])
def keys():
    global ck,cs,ak,aks
    ck = request.form['consumer_key']
    cs = request.form['consumer_secret']
    ak = request.form['access_token']
    aks = request.form['access_token_secret']
    if not (ck or cs or ak or aks):
        return render_template("Keys.html")
    return render_template("tweet_detect.html")

@app.route('/post_on_twitter', methods=['POST'])
def post_on_twitter():
    global tweet_text
    if request.method == 'POST':
        input_text = request.form.get('input_text')
        tweet_text = input_text
        if not input_text:
            return render_template("tweet_detect.html")


        input_text = preprocess_text(input_text)

        input_sequence = np.array(tokenizer.texts_to_sequences([input_text]))
        input_sequence = pad_sequences(input_sequence, padding='post', maxlen=maxlen)

        prediction = loaded_model.predict(input_sequence)
        print(prediction)
        global Cutoff

        Cutoff = 0.50

        plt.figure(figsize=(8, 4))
        plt.bar(["Prediction", "Cutoff Threshold"], [prediction[0][0], Cutoff], color=["blue", "red"])
        plt.xlabel("Category")
        plt.ylabel("Probability")
        plt.title("Prediction vs. Cutoff Threshold")
        plt.savefig('static/bar_graph.png')

        if prediction >= Cutoff:
            result = "Hate"
            hate_value = 1
            not_hate_value = 0
        else:
            result = "Not_hate"
            hate_value = 0
            not_hate_value = 1

        if "username" in session:
            user_name = session["username"]

        prediction_float = float(prediction)


        curr.execute('SELECT username FROM users WHERE username = %s', (user_name,))
        user_data = curr.fetchone()

        if user_data:
                username = user_data['username']
                curr.execute('INSERT INTO ml_table (username, Post, Hate, `Not_hate`,Prediction) VALUES (%s, %s, %s, %s,%s)',
                             (username, input_text, hate_value, not_hate_value,prediction_float*100))
                mydbConn.commit()
       
        return render_template('resultnew.html', input_text=input_text, prediction=prediction*100, result=result, cutoff=Cutoff)
    

@app.route('/post', methods=['POST'])
def post():
    post_or_not = request.form.get('post_or_not')
    if post_or_not == "YES":
        import tweepy
        Twitter_consumer_key = ck
        Twitter_consumer_secret = cs
        Twitter_access_token = ak
        Twitter_access_token_secret = aks

        client = tweepy.Client(consumer_key=Twitter_consumer_key,
                            consumer_secret=Twitter_consumer_secret,
                            access_token=Twitter_access_token,
                            access_token_secret=Twitter_access_token_secret
                            )

        response = client.create_tweet(text=tweet_text)

        #response = client.get_home_timeline()
        print(response)
        username = session['username']
        curr.execute("SELECT * FROM ml_table where username = %s", (username,))
        datatuple = curr.fetchall()
        data=[]
        for i in range(len(datatuple)):
            data.append(datatuple[i])
        print(data)

        curr.execute("SELECT COUNT(id) from ml_table where username = %s",(username,))
        count = curr.fetchone()
        count = count['COUNT(id)']
        print(count)

        curr.execute("select count(hate) from ml_table where hate = 1 and username = %s",(username,))
        count1 = curr.fetchone()
        count1 = count1['count(hate)']

        curr.execute("select count(`Not_hate`) from ml_table where `Not_hate` = 1 and username = %s",(username,))
        count2 = curr.fetchone()
        count2 = count2['count(`Not_hate`)']
        curr.execute("SELECT hate FROM ml_table WHERE username = %s", (username,))
        data1 = curr.fetchall()
        print(data1)
        hate_count = 0
        not_hate_count = 0
        for row in data1:
            if row['hate'] == 1:
                hate_count += 1
            else:
                    not_hate_count += 1

        plt.figure(figsize=(5, 3.5))
        labels = ["Hate", "Not_hate"]
        values = [hate_count, not_hate_count]
        colors = ["#ff9999", "#66b3ff"]
        plt.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
        plt.title("Hate vs Not_hate Pie Chart")

        # Save the pie chart image to the 'static' folder
        pie_chart_image_path = os.path.join('static', 'pie_chart.png')
        plt.savefig(pie_chart_image_path)
        plt.figure(figsize=(4, 3.5))
        labels1 = ["Hate (1)", "No Hate (0)"]
        values1 = [hate_count, not_hate_count]
        colors1 = ['red', 'blue']

        plt.bar(labels1, values1, color=colors1)
        plt.title('Hate Distribution')
        plt.xlabel('Hate Value')
        plt.ylabel('Count')

        bar_graph_path="static/hate_bar.png"
        # Save the bar chart image to a file
        plt.savefig("static/hate_bar.png")


        curr.execute("SELECT id, prediction FROM ml_table WHERE username = %s", (username,))
        data2 = curr.fetchall()
        if data2:
            id = []  # Create an empty list to store the id values
            for record in data2:
                id.append(record['id'])
            prediction = []  # Create an empty list to store the prediction values
            for record in data2:
                prediction.append(record['prediction'])
        if id and prediction:
            # Create a line chart
            plt.figure(figsize=(5, 3.5))
            plt.plot(id, prediction, marker='o', linestyle='-', color='b')
            plt.title('Predictions')
            plt.xlabel('id')
            plt.ylabel('Predictions')

            # Save the chart as a PNG image
            chart_path = "static/line_chart.png"
            plt.savefig(chart_path)

        return render_template('dash.html', data=data, count=count,count1=count1,count2=count2,pie_chart_image=pie_chart_image_path,chart_path=chart_path,bar_path=bar_graph_path )

    else: 
        username = session['username']
        curr.execute("SELECT * FROM ml_table where username = %s", (username,))
        datatuple = curr.fetchall()
        data=[]
        for i in range(len(datatuple)):
            data.append(datatuple[i])
        print(data)

        curr.execute("SELECT COUNT(id) from ml_table where username = %s",(username,))
        count = curr.fetchone()
        count = count['COUNT(id)']
        print(count)

        curr.execute("select count(hate) from ml_table where hate = 1 and username = %s",(username,))
        count1 = curr.fetchone()
        count1 = count1['count(hate)']

        curr.execute("select count(`Not_hate`) from ml_table where `Not_hate` = 1 and username = %s",(username,))
        count2 = curr.fetchone()
        count2 = count2['count(`Not_hate`)']
        curr.execute("SELECT hate FROM ml_table WHERE username = %s", (username,))
        data1 = curr.fetchall()
        print(data1)
        hate_count = 0
        not_hate_count = 0
        for row in data1:
            if row['hate'] == 1:
                hate_count += 1
            else:
                    not_hate_count += 1

        plt.figure(figsize=(5, 3.5))
        labels = ["Hate", "Not_hate"]
        values = [hate_count, not_hate_count]
        colors = ["#ff9999", "#66b3ff"]
        plt.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
        plt.title("Hate vs Not_hate Pie Chart")

        # Save the pie chart image to the 'static' folder
        pie_chart_image_path = os.path.join('static', 'pie_chart.png')
        plt.savefig(pie_chart_image_path)
        plt.figure(figsize=(4, 3.5))
        labels1 = ["Hate (1)", "No Hate (0)"]
        values1 = [hate_count, not_hate_count]
        colors1 = ['red', 'blue']

        plt.bar(labels1, values1, color=colors1)
        plt.title('Hate Distribution')
        plt.xlabel('Hate Value')
        plt.ylabel('Count')

        bar_graph_path="static/hate_bar.png"
        # Save the bar chart image to a file
        plt.savefig("static/hate_bar.png")


        curr.execute("SELECT id, prediction FROM ml_table WHERE username = %s", (username,))
        data2 = curr.fetchall()
        if data2:
            id = []  # Create an empty list to store the id values
            for record in data2:
                id.append(record['id'])
            prediction = []  # Create an empty list to store the prediction values
            for record in data2:
                prediction.append(record['prediction'])
        if id and prediction:
            # Create a line chart
            plt.figure(figsize=(5, 3.5))
            plt.plot(id, prediction, marker='o', linestyle='-', color='b')
            plt.title('Predictions')
            plt.xlabel('id')
            plt.ylabel('Predictions')

            # Save the chart as a PNG image
            chart_path = "static/line_chart.png"
            plt.savefig(chart_path)
        return render_template('dash.html', data=data, count=count,count1=count1,count2=count2,pie_chart_image=pie_chart_image_path,chart_path=chart_path,bar_path=bar_graph_path )

    


if(__name__ == "__main__"):
    app.run(debug=True)