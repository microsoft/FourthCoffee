#!/usr/bin/env python
from importlib import import_module
import os
import cv2
from flask import Flask, render_template, Response, request, url_for, redirect
from sqlConnector import SqlConnector
import mysql.connector
import socket

app = Flask(__name__)

dbenabled = os.environ.get("DBENABLED")


if dbenabled:
    mydb = mysql.connector.connect(
        host=os.environ.get('DBHOST'),
        user=os.environ.get('DBUSER'),
        password=os.environ.get('DBSECRET'),
        database=os.environ.get('DBNAME')
   )


dbserver = os.environ.get('DBHOST')
servername = socket.gethostname()

@app.route('/')
def index():
    """Fourth Coffee Point-Of-Sale"""
    
    cameras_enabled = False
    if os.environ.get('CAMERAS_ENABLED'):
        cameras_enabled = os.environ.get('CAMERAS_ENABLED') == 'True'
    
    head_title = "Fourth Coffee"
    if os.environ.get('HEAD_TITLE'):
        head_title = os.environ.get('HEAD_TITLE')

    holiday_season = False
    
    if os.environ.get('NEW_CATEGORY'):
        holiday_season = os.environ.get('NEW_CATEGORY') == 'True'

    season = ""
    if os.environ.get("SEASON"):
        season = os.environ.get("SEASON")

    if dbenabled:
        mydb2 = mysql.connector.connect(
            host=os.environ.get('DBHOST'),
            user=os.environ.get('DBUSER'),
            password=os.environ.get('DBSECRET'),
            database=os.environ.get('DBNAME')
        )
        cur2 = mydb2.cursor()
        productlist = []
        query = "SELECT * from fourthcoffeedb.products"
        cur2.execute(query)
        for item in cur2.fetchall():
            productlist.append({
                'id': item[0],
                'name': item[1],
                'price': item[2],
                'currentInventory': item[3],
                'photolocation': item[4]
            })
        cur2.close()
    
    if season == "Winter":
        return render_template('winterdb.html' if dbenabled else 'index2.html', productlist=productlist, head_title = head_title, cameras_enabled = cameras_enabled, dbserver=dbserver, servername=servername)
    elif season == "Summer":
        return render_template('summerdb.html' if dbenabled else 'index.html', productlist=productlist, head_title = head_title, cameras_enabled = cameras_enabled, dbserver=dbserver, servername=servername)
    else:
        return render_template('indexdb.html' if dbenabled else 'index.html', productlist=productlist, head_title = head_title, cameras_enabled = cameras_enabled, dbserver=dbserver, servername=servername)
    
    #return render_template('index3.html', productlist=productlist, dbserver=dbserver, servername=servername)
    #return render_template('index3.html' if dbenabled else 'index.html', productlist=productlist, head_title = head_title, cameras_enabled = cameras_enabled, dbserver=dbserver, servername=servername)
    #return render_template('index.html' if holiday_season else 'index2.html', head_title = head_title, cameras_enabled = cameras_enabled)

@app.route('/inventory')
def inventory():
    mydb2 = mysql.connector.connect(
    host=os.environ.get('DBHOST'),
    user=os.environ.get('DBUSER'),
    password=os.environ.get('DBSECRET'),
    database=os.environ.get('DBNAME')
    )
    try:
        cur2 = mydb2.cursor()
        inventorylist = []
        query = "SELECT * from fourthcoffeedb.products"
        cur2.execute(query)
        for item in cur2.fetchall():
            inventorylist.append({
                'id': item[0],
                'name': item[1],
                'price': item[2],
                'currentInventory': item[3]
            })
        cur2.close()
        return render_template('inventory.html', inventorylist=inventorylist)
    except Exception as e:
        return "Error querying items: " + str(e)

@app.route('/addPurchase',methods = ['POST'])
def addPurchase():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json; charset=UTF-8'):
        json = request.get_json()
        sqlDb = SqlConnector()
        successful = sqlDb.addPurchase(json['ProductId'])
        if(successful):
            return "Ok"
        else:
            return "Error processing request"
    else:
        return 'Content-Type not supported!'

@app.route('/video_feed/<feed>')
def video_feed(feed):
    return Response(gen_frames(feed),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/add_item', methods=['POST'])
def add_item():
    try:
        # Get item information from request data
        name = request.form['name']
        quantity = int(request.form['quantity'])
        capacity = int(request.form['capacity'])

        # Insert item into database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO inventory (name, quantity, capacity) VALUES (%s, %s, %s)", (name, quantity, capacity))
        mysql.connection.commit()
        cur.close()

        # Return success message
        return "Item added successfully."
    except Exception as e:
        # Handle errors
        return "Error adding item: " + str(e)

@app.route('/update_item', methods=['POST'])
def update_item():
    cur = mydb.cursor()
    try:
        # Get item information from request data
        item_id = int(request.form['id'])
        name = request.form['name']
        price = float(request.form['price'])

        # Update item in database  
        cur.execute("UPDATE products SET Name=%s, price=%s WHERE id=%s", (name, price, item_id))
        mydb.commit()
        cur.close()

        # Return success message
        return "Item updated successfully."
    except Exception as e:
        # Handle errors
        return "Error updating item: " + str(e)

@app.route('/delete_item', methods=['POST'])
def delete_item():
    try:
        # Get item ID from request data
        item_id = int(request.form['id'])

        # Delete item from database
        cur = mydb.cursor()
        cur.execute("DELETE FROM products WHERE id=%s", (item_id,))
        mydb.commit()
        cur.close()

        # Return success message
        return "Item deleted successfully."
    except Exception as e:
        # Handle errors
        return "Error deleting item: " + str(e)

def gen_frames(source):
    """Video streaming frame capture function."""
    baseUrl = "rtsp://localhost:554/media/" 
    if os.environ.get('CAMERAS_BASEURL'):
        baseUrl = str(os.environ['CAMERAS_BASEURL'])

    cap = cv2.VideoCapture(baseUrl + source)  # capture the video from the live feed

    while True:
        # # Capture frame-by-frame. Return boolean(True=frame read correctly. )
        success, frame = cap.read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, debug=True)
