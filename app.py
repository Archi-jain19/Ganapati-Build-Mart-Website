import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from flask_cors import CORS  # Import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
application = app

# Database connection details (maintained for compatibility)
db_config = db.MYSQL_CONFIG

CORS(app)
# Secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', 'ganapati-build-mart-production-secret-2025')

# Number of products to display per page
PRODUCTS_PER_PAGE = 12


# Route for the home page
@app.route('/')
def home():
    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT name, url FROM brands")
    brands = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('index.html', brands=brands)

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO contact_inquiries (name, email, subject, message) VALUES (%s, %s, %s, %s)",
                (name, email, subject, message)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Thank you for reaching out! Your message has been sent successfully.", "success")
        except Exception as e:
            flash(f"Error submitting message: {e}", "error")

        return redirect(url_for('contact'))

    return render_template('contact.html')


# Shop route with filters, sorting, and pagination
@app.route('/shop', methods=['GET'])
def shop():
    try:
        # Get query parameters for sorting, filtering, and pagination
        sort_by = request.args.get('sort', 'product_name')
        if sort_by not in ['product_name', 'category', 'brand', 'id']:
            sort_by = 'product_name'
        sort_order = request.args.get('order', 'ASC').upper()
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'ASC'

        category = request.args.get('category', '')
        brand = request.args.get('brand', '')
        try:
            current_page = max(1, int(request.args.get('page', 1)))
        except (ValueError, TypeError):
            current_page = 1
        
        # Calculate the offset for pagination
        offset = (current_page - 1) * PRODUCTS_PER_PAGE
        
        # Create the base SQL query for filtered products
        query = "SELECT id, product_name, category, brand, description, image_url FROM products"
        
        # Apply category filter if provided
        filters = []
        filter_params = []
        if category:
            filters.append("category = %s")
            filter_params.append(category)
        if brand:
            filters.append("brand = %s")
            filter_params.append(brand)
        
        if filters:
            query += " WHERE " + " AND ".join(filters)
        
        # Apply sorting
        query += f" ORDER BY {sort_by} {sort_order}"
        
        # Apply pagination (LIMIT and OFFSET)
        query += f" LIMIT {PRODUCTS_PER_PAGE} OFFSET {offset}"
        
        # Connect to the database
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(query, tuple(filter_params) if filter_params else None)
        products = cursor.fetchall()

        # Get total number of filtered products for pagination
        count_query = "SELECT COUNT(*) FROM products"
        if filters:
            count_query += " WHERE " + " AND ".join(filters)
        
        cursor.execute(count_query, tuple(filter_params) if filter_params else None)
        row = cursor.fetchone()
        total_products = row['COUNT(*)'] if row else 0
        total_pages = (total_products // PRODUCTS_PER_PAGE) + (1 if total_products % PRODUCTS_PER_PAGE else 0)
        if total_pages == 0:
            total_pages = 1
        
        # Get all categories and brands to populate the filter dropdowns
        cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
        categories = cursor.fetchall()
        
        cursor.execute("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND brand != ''")
        brands = cursor.fetchall()

        return render_template('shop.html', products=products, sort_by=sort_by, sort_order=sort_order, category=category, brand=brand, categories=categories, brands=brands, total_pages=total_pages, current_page=current_page)
    
    except Exception as e:
        return f"Error connecting to database: {e}"
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/admin/products', methods=['GET'])
def admin_products():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        # Define products per page
        PRODUCTS_PER_PAGE = 12
        
        # Get query parameters for sorting, filtering, and pagination
        sort_by = request.args.get('sort', 'product_name')
        if sort_by not in ['product_name', 'category', 'brand', 'id']:
            sort_by = 'product_name'
        sort_order = request.args.get('order', 'ASC').upper()
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'ASC'

        category = request.args.get('category', '')
        brand = request.args.get('brand', '')
        try:
            current_page = max(1, int(request.args.get('page', 1)))
        except (ValueError, TypeError):
            current_page = 1
        
        # Calculate the offset for pagination
        offset = (current_page - 1) * PRODUCTS_PER_PAGE
        
        # Create the base SQL query for filtered products
        query = "SELECT id, product_name, category, brand, description, image_url FROM products"
        
        # Apply category filter if provided
        filters = []
        filter_params = []
        if category:
            filters.append("category = %s")
            filter_params.append(category)
        if brand:
            filters.append("brand = %s")
            filter_params.append(brand)
        
        if filters:
            query += " WHERE " + " AND ".join(filters)
        
        # Apply sorting
        query += f" ORDER BY {sort_by} {sort_order}"
        
        # Apply pagination (LIMIT and OFFSET)
        query += f" LIMIT {PRODUCTS_PER_PAGE} OFFSET {offset}"
        
        # Connect to the database
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(query, tuple(filter_params) if filter_params else None)
        products = cursor.fetchall()

        # Get total number of filtered products for pagination
        count_query = "SELECT COUNT(*) FROM products"
        if filters:
            count_query += " WHERE " + " AND ".join(filters)
        
        cursor.execute(count_query, tuple(filter_params) if filter_params else None)
        row = cursor.fetchone()
        total_products = row['COUNT(*)'] if row else 0
        total_pages = (total_products // PRODUCTS_PER_PAGE) + (1 if total_products % PRODUCTS_PER_PAGE else 0)
        if total_pages == 0:
            total_pages = 1
        
        # Get all categories and brands to populate the filter dropdowns
        cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
        categories = cursor.fetchall()
        
        cursor.execute("SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND brand != ''")
        brands = cursor.fetchall()

        return render_template('admin.html', products=products, sort_by=sort_by, sort_order=sort_order, category=category, brand=brand, categories=categories, brands=brands, total_pages=total_pages, current_page=current_page)
    
    except Exception as e:
        return f"Error connecting to database: {e}"
    
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Handling form submission for adding a product
            if 'add_product' in request.form:
                product_name = request.form.get('product_name')
                category = request.form.get('category')
                image_url = request.form.get('image_url')
                description = request.form.get('description')
                
                # Basic validation
                if not all([product_name, category]):
                    flash('Product name and category are required', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                # Handle new category
                if category == 'new':
                    new_category = request.form.get('new_category')
                    if not new_category:
                        flash('New category name is required', 'error')
                        return redirect(url_for('admin_dashboard'))
                    category = new_category
                
                # Insert product into the database
                cursor.execute("""INSERT INTO products (product_name, category, image_url, description) 
                                VALUES (%s, %s, %s, %s)""", 
                                (product_name, category, image_url, description))
                connection.commit()
                flash('Product added successfully', 'success')
                return redirect(url_for('admin_dashboard'))
            
            # Handling the edit form submission
            elif 'edit_product' in request.form:
                product_id = request.form.get('product_id')
                product_name = request.form.get('product_name')
                category = request.form.get('category')
                image_url = request.form.get('image_url')
                description = request.form.get('description')
                
                # Basic validation
                if not all([product_id, product_name, category]):
                    flash('Product ID, name, and category are required', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                # Handle new category
                if category == 'new':
                    new_category = request.form.get('new_category')
                    if not new_category:
                        flash('New category name is required', 'error')
                        return redirect(url_for('admin_dashboard'))
                    category = new_category
                
                # Update product in the database
                cursor.execute("""
                    UPDATE products
                    SET product_name = %s, category = %s, image_url = %s, description = %s
                    WHERE id = %s
                """, (product_name, category, image_url, description, product_id))
                connection.commit()
                flash('Product updated successfully', 'success')
                return redirect(url_for('admin_dashboard'))

        # Handle "edit" via query parameters
        product_to_edit = None
        if 'edit' in request.args:
            product_id = request.args.get('edit')
            # Validate product_id
            if product_id and product_id.isdigit():
                cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
                product_to_edit = cursor.fetchone()
                if not product_to_edit:
                    flash('Product not found', 'error')

        # Handle "delete" via query parameters
        if 'delete' in request.args:
            product_id = request.args.get('delete')
            # Validate product_id
            if product_id and product_id.isdigit():
                # Confirm the product exists before deleting
                cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
                if cursor.fetchone():
                    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
                    connection.commit()
                    flash('Product deleted successfully', 'success')
                else:
                    flash('Product not found', 'error')
                return redirect(url_for('admin_dashboard'))

        # Fetch all products to display in the table
        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        products = cursor.fetchall()
        
        # Fetch unique categories for the dropdown
        cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
        categories = cursor.fetchall()
        
        return render_template('new.html', 
                               products=products, 
                               product_to_edit=product_to_edit,
                               categories=categories)
                             
    except Exception as err:
        flash(f"Database error: {err}", 'error')
        return redirect(url_for('admin_dashboard'))
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Fetch user details from DB
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        # Verify the password
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['user_id'] = user.get('id')
            session['user_name'] = user.get('name')
            return redirect(url_for('admin_products'))
        else:
            message = "Invalid credentials. (Hint: username 'admin', password 'admin123')"
            return render_template('login.html', message=message)

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'logged_in' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))  # Redirect to login page if not logged in
    
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        
        # Generate hashed password
        hashed_password = generate_password_hash(password)
        
        # Store the hashed password in the database
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (username, password, name) VALUES (%s, %s, %s)", (username, hashed_password, name))
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect(url_for('get_customers'))

    return render_template('register.html')



@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the session
    session.clear()
    return redirect(url_for('home'))



@app.route('/api/products', methods=['GET'])
def api_products():
    """API endpoint to get all products in JSON format"""
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, product_name, category, brand, description, image_url FROM products")
        products = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['GET'])
def get_customers():
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        customers = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # Check if the request wants JSON (API call) or HTML (browser request)
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'customers': customers
            })
        else:
            # Render the HTML template with the customers data
            return render_template(
                'customer.html',
                customers=customers,
                title="Customer Management"
            )
            
    except Exception as e:
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': str(e)}), 400
        else:
            return f"Error: {str(e)}", 400


@app.route('/api/users/<int:id>', methods=['POST'])
def save_customer(id):
    try:
        # Get the new name and email from the request
        data = request.json or {}
        new_name = data.get('name')
        new_email = data.get('email')
        
        # Connect to the database
        connection = db.get_connection()
        cursor = connection.cursor()

        # Update the user in the database
        update_query = """
            UPDATE users
            SET name = %s, username = %s
            WHERE id = %s
        """
        cursor.execute(update_query, (new_name, new_email, id))
        connection.commit()
        cursor.close()
        connection.close()

        # Return success response
        return jsonify({'message': 'Customer updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/new_user')
def new():
    return render_template('register.html')


@app.route('/api/delete_customer/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        # Connect to the database
        connection = db.get_connection()
        cursor = connection.cursor()

        # Delete the customer from the database
        delete_query = """
            DELETE FROM users
            WHERE id = %s
        """
        cursor.execute(delete_query, (customer_id,))
        connection.commit()
        affected = cursor.rowcount
        cursor.close()
        connection.close()

        # Check if any row was affected
        if affected > 0:
            return jsonify({'message': 'Customer deleted successfully'}), 200
        else:
            return jsonify({'error': 'Customer not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/brands')
def brand():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)  
    
    cursor.execute("SELECT id, name, name AS brand, url FROM brands")
    brands = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('brands.html', brands=brands)


# Add a new brand
@app.route('/brands/add', methods=['POST'])
def add_brand():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    name = request.form['name']
    url = request.form['url']

    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO brands (name, url) VALUES (%s, %s)", (name, url))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('brand'))  


# Delete a brand
@app.route('/brands/delete/<int:brand_id>')
def delete_brand(brand_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM brands WHERE id = %s", (brand_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('brand'))  


if __name__ == '__main__':
    print("Starting Ganapati Build Mart Flask Server on http://127.0.0.1:5000 ...")
    app.run(debug=True, host='127.0.0.1', port=5000)
