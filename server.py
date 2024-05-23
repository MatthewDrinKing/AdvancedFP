import sqlite3
from flask import Flask, request, jsonify

# Initialize the Flask application
app = Flask(__name__)

# Function to get a new SQLite connection and cursor
def get_db():
    conn = sqlite3.connect('orders.db')
    return conn, conn.cursor()

# Create the "orders" table if it doesn't exist
def create_orders_table():
    conn, c = get_db()  # Get a new connection and cursor

    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            quantity INTEGER,
            isfood TEXT,
            Time TEXT,
            venue TEXT,
            total REAL,
            printing_status TEXT,
            fiscal_id TEXT,
            refund_amount REAL,   -- Add this line to create the refund_amount column
            refund_reason TEXT,   -- Add this line to create the refund_reason column
            refund_date TEXT      -- Add this line to create the refund_date column
        )
    ''')

    conn.commit()  # Commit the changes to the database

    conn.close()  # Close the connection


# Route for receiving and storing order data
@app.route('/process-json', methods=['POST'])
def process_json():
    conn, c = get_db()  # Get a new connection and cursor

    order_data = request.get_json()  # Get the order data from the request payload

    # Extract the necessary information from the order_data dictionary
    name = order_data['name'][0]['name']
    price = order_data['name'][0]['price']
    quantity = order_data['name'][0]['quantity']
    isfood = order_data['name'][0]['isfood']
    Time = order_data['Time']
    venue = order_data['venue']
    total = order_data['total']
    order_id = int(order_data['id'])

    # Insert the order into the database
    c.execute('''
        INSERT INTO orders (name, price, quantity, isfood, Time, venue, total, printing_status, fiscal_id, id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, price, quantity, isfood, Time, venue, total, 'new', '', order_id))

    conn.commit()  # Commit the changes to the database

    conn.close()  # Close the connection

    return "Order received and stored successfully"

# Route for retrieving orders for a specific venue
@app.route('/orders/<venue>', methods=['GET'])
def get_orders(venue):
    conn, c = get_db()  # Get a new connection and cursor

    # Query the database for orders with the specified venue and printing_status as "new"
    c.execute('SELECT * FROM orders WHERE venue=? AND printing_status=?', (venue, 'new'))
    orders = c.fetchall()

    # Update the printing_status to "sent" for the retrieved orders
    c.execute('UPDATE orders SET printing_status=? WHERE venue=? AND printing_status=?', ('sent', venue, 'new'))
    conn.commit()

    # Prepare the order data to be sent as a JSON response
    order_data = []
    for order in orders:
        order_dict = {
            'name': order[1],
            'price': order[2],
            'quantity': order[3],
            'isfood': order[4],
            'Time': order[5],
            'venue': order[6],
            'total': order[7],
            'status': order [8],
            'id' : order[0]
        }
        order_data.append(order_dict)

    conn.close()  # Close the connection

    return jsonify(order_data)

# Route for updating an order with fiscal ID
@app.route('/orders/<order_id>/update', methods=['POST'])
def update_order(order_id):
    conn, c = get_db()  # Get a new connection and cursor

    fiscal_id = request.form['fiscal_id']  # Get the fiscal_id from the POST request

    # Update the order's fiscal_id and printing_status in the database
    c.execute('UPDATE orders SET fiscal_id=?, printing_status=? WHERE id=?', (fiscal_id, 'done', order_id))
    conn.commit()  # Commit the changes to the database

    conn.close()  # Close the connection

    return "Order updated successfully"

# Create the "orders" table before running the server
create_orders_table()

# Route for handling refund requests
@app.route('/refundroute', methods=['POST'])
def refund_route():
    conn, c = get_db()

    refund_data = request.get_json()

    order_id = refund_data['id']

    try:
        # Update the status of the order to "pending refund print"
        c.execute('UPDATE orders SET printing_status=? WHERE id=?', ('pending refund print', order_id))
        conn.commit()

        conn.close()
        return "Refund request processed successfully"
    except sqlite3.Error as e:
        print(e)
        return "Error processing refund request"

# Route for retrieving orders pending refund for a specific venue
@app.route('/orders/pending_refund/<venue>', methods=['GET'])
def get_pending_refund_orders(venue):
    conn, c = get_db()

    # Query the database for orders with the specified venue and printing_status as "pending refund print"
    c.execute('SELECT * FROM orders WHERE venue=? AND printing_status=?', (venue, 'pending refund print'))
    refund_orders = c.fetchall()

    # Prepare the refund order data to be sent as a JSON response
    refund_order_data = []
    for order in refund_orders:
        order_dict = {
            'id': order[0],  # Include the order ID in the response
            'name': order[1],
            'price': order[2],
            'quantity': order[3],
            'isfood': order[4],
            'Time': order[5],
            'venue': order[6],
            'total': order[7],
            'fiscal_id': order[8]  # Modify the index to match the correct column
        }
        refund_order_data.append(order_dict)

        # Update the printing_status to "refund sent" for the retrieved orders
        c.execute('UPDATE orders SET printing_status=? WHERE id=?', ('refund sent', order[0]))
        conn.commit()

    conn.close()

    return jsonify(refund_order_data)





# Run the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)