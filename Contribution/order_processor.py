
import json
import sqlite3


DB_PATH = "orders.db"


def calculate_discount(price, discount_percent):
    """
    Calculate final price after discount.

    Example:
    price = 1000
    discount = 10%

    final_price = 900
    """

    # Calculate discounted price.
    final_price = price - (price * discount_percent / 100)

    # Return final price.
    return final_price


def save_order(customer_name, email, product, price, discount_percent):
    """
    Save order into database.

    FLOW:
    1. Open database connection
    2. Calculate final price
    3. Create SQL query
    4. Execute query
    5. Commit changes
    6. Close connection
    """

    # Open SQLite database connection.
    connection = sqlite3.connect(DB_PATH)

    # Create cursor object for executing SQL queries.
    cursor = connection.cursor()

    # Calculate discounted price.
    final_price = calculate_discount(price, discount_percent)

   

    query = f"""
    INSERT INTO orders (customer_name, email, product, final_price)
    VALUES ('{customer_name}', '{email}', '{product}', {final_price})
    """

    # Execute SQL query.
    cursor.execute(query)

    # Save changes permanently.
    connection.commit()

    # Close database connection.
    connection.close()

    # Return success message.
    return "Order saved successfully"


def process_order(order_json):
    """
    Main function that processes customer order.

    FLOW:
    1. Convert JSON string to Python dictionary
    2. Extract values
    3. Validate values
    4. Save order into database
    5. Return result
    """

    # Convert JSON string into Python dictionary.
    order = json.loads(order_json)

    # Extract customer name from JSON.
    customer_name = order["customer_name"]

    # Extract email from JSON.
    email = order["email"]

    # Extract product name from JSON.
    product = order["product"]

    # Extract product price from JSON.
    price = order["price"]

    # Extract discount percentage.
    discount_percent = order["discount_percent"]

    # Basic validation check.
    if price < 0:
        return "Invalid price"

    

    # Save order into database.
    result = save_order(
        customer_name,
        email,
        product,
        price,
        discount_percent,
    )

    # Return final result.
    return result



sample_order = """
{
    "customer_name": "John",
    "email": "john@example.com",
    "product": "AI Course",
    "price": 1000,
    "discount_percent": 10
}
"""



print(process_order(sample_order))