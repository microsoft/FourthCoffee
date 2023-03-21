#!/usr/bin/env python
from importlib import import_module
import os
import cv2
from flask import Flask, render_template, Response, request, url_for, redirect, session
from flask_session import Session
from sqlConnector import SqlConnector
import mysql.connector
import socket
import secrets
import mysql.connector
from mysql.connector import pooling
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config["SESSION PERMANENT"] = False
app.config['SESSION_TYPE'] = "filesystem"
Session(app)


dbconfig = {
    "pool_name": "mypool",
    "pool_size": 20,
    "host": os.environ.get('DBHOST'),
    "user": os.environ.get('DBUSER'),
    "password": os.environ.get('DBSECRET'),
    "database": os.environ.get('DBNAME')
}

cnxpool = pooling.MySQLConnectionPool(**dbconfig)


dbserver = os.environ.get('DBHOST')
storeid = os.environ.get('STOREID')
servername = socket.gethostname()
dbenabled = 1


@app.route('/reset')
def reset():
    session.clear()
    return 'Session reset'

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

    cnx = cnxpool.get_connection()
    cur = cnx.cursor()
    productlist = []
    query = "SELECT * from fourthcoffeedb.products"
    cur.execute(query)
    for item in cur.fetchall():
        productlist.append({
            'produtctid': item[0],
            'name': item[1],
            'price': item[2],
            'currentInventory': item[3],
            'photolocation': item[4]
        })
    cur.close()

    if season == "Winter":
        return render_template('winterdb.html', productlist=productlist, head_title = head_title, cameras_enabled = cameras_enabled, dbserver=dbserver, servername=servername)
    elif season == "Summer":
        return render_template('summerdb.html', productlist=productlist, head_title = head_title, cameras_enabled = cameras_enabled, dbserver=dbserver, servername=servername)
    else:
        return render_template('indexdb.html', productlist=productlist, head_title = head_title, cameras_enabled = cameras_enabled, dbserver=dbserver, servername=servername)
    
    #return render_template('index3.html', productlist=productlist, dbserver=dbserver, servername=servername)
    #return render_template('index3.html' if dbenabled else 'index.html', productlist=productlist, head_title = head_title, cameras_enabled = cameras_enabled, dbserver=dbserver, servername=servername)
    #return render_template('index.html' if holiday_season else 'index2.html', head_title = head_title, cameras_enabled = cameras_enabled)

@app.route('/inventory')
def inventory():
    try:
        cnx = cnxpool.get_connection()
        cur = cnx.cursor()
        inventorylist = []
        query = "SELECT * from fourthcoffeedb.products"
        cur.execute(query)
        for item in cur.fetchall():
            inventorylist.append({
                'id': item[0],
                'name': item[1],
                'price': item[2],
                'currentInventory': item[3]
            })
        cur.close()
        cnx.close()
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
        cnx = cnxpool.get_connection()
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO inventory (name, quantity, capacity) VALUES (%s, %s, %s)", (name, quantity, capacity))
        mysql.connection.commit()
        cur.close()
        cnx.close()

        # Return success message
        return "Item added successfully."
    except Exception as e:
        # Handle errors
        return "Error adding item: " + str(e)
    
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    # Get the product ID and quantity from the form data
    product_id = request.form['product_id']
    product_name = request.form['product_name']
    product_price = request.form['product_price']
    quantity = 1

    # Create a new cart item with the product data and quantity
    item = {
        'id': product_id,
        'quantity': quantity,
        'name': product_name,
        'price': product_price
    }

    # Add the item to the shopping cart session
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(item)

    # Redirect back to the homepage
    return redirect('/')

@app.route('/cart')
def cart():
    # Get the cart data from the session
    summary = {}
    cart = session.get('cart', [])
    for item in cart:
        id = item['id']
        quantity = item['quantity']
        if id in summary:
            summary[id] += quantity
        else:
            summary[id] = quantity
    # print (summary)
    # Render the shopping cart template with the cart data
    return render_template('cart.html', cart=cart)

@app.route('/checkout')
def checkout():
    cnx = cnxpool.get_connection()
    cur = cnx.cursor()
    cart = session.get('cart', [])
    orderDate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    jsoncart = json.dumps(cart)
    query = "INSERT INTO Orders (orderDate, orderdetails, storeId) VALUES ('{}', '{}', {})".format(orderDate, jsoncart, storeid)
    cur.execute(query)
    ordernumber = cur.lastrowid
    cnx.commit()
    cur.close()
    cnx.close()
    session.clear()
    return render_template('checkout.html', ordernumber=ordernumber)


@app.route('/update_item', methods=['POST'])
def update_item():
    cnx = cnxpool.get_connection()
    cur = cnx.cursor()
    try:
        # Get item information from request data
        item_id = int(request.form['id'])
        name = request.form['name']
        price = float(request.form['price'])

        # Update item in database  
        cur.execute("UPDATE products SET Name=%s, price=%s WHERE id=%s", (name, price, item_id))
        cnx.commit()
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
        cnx = cnxpool.get_connection()
        cur = cnx.cursor()
        cur.execute("DELETE FROM products WHERE id=%s", (item_id,))
        cnx.commit()
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
