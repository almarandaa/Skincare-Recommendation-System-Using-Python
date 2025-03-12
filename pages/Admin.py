import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import pickle

def create_admin_db():
    conn = sqlite3.connect('admin.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_admin_users(username, password):
    conn = sqlite3.connect('admin.db')
    c = conn.cursor()

    # Enkripsi password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        c.execute('INSERT INTO admin_users (username, password) VALUES (?, ?)', (username, hashed_password.decode('utf-8')))
        conn.commit()
        print(f"User {username} successfully added.")
    except sqlite3.IntegrityError:
        print(f"User {username} already exists.")
    finally:
        conn.close()

create_admin_db()
# Tambahkan pengguna admin dengan username dan password Anda
add_admin_users('Admin', 'password')


def login_admin(username, password):
    conn = sqlite3.connect('admin_users.db')
    c = conn.cursor()
    c.execute('SELECT password FROM admin_users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()

    if result:
        hashed_password = result[0]
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    return False

# buat database dan tabel
def create_new_db():
    conn = sqlite3.connect('product.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS product (
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            type TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_new_db()

# Fungsi untuk membuat koneksi database
def get_db_connection():
    conn = sqlite3.connect('product.db')
    return conn

# Fungsi CRUD
def add_product(name, category, type):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO product (name, category, type) VALUES (?, ?, ?)', (name, category, type))
    conn.commit()
    conn.close()

def view_products():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM product')
    products = c.fetchall()
    conn.close()
    return products

def update_product(old_name, new_name, category, type):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE product SET name = ?, category = ?, type = ? WHERE name = ?', (new_name, category, type, old_name))
    conn.commit()
    conn.close()

def delete_product(name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM product WHERE name = ?', (name,))
    conn.commit()
    conn.close()


# Halaman login
def login_page():
    st.title("Admin Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if login_admin(username, password):
            st.success("Login Successfull!")
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['page'] = 'crud'  # Set page to CRUD
        else:
            st.error("Invalid username or password")

# Halaman CRUD Admin
def admin_crud_page():
    st.title("Skincare Recommendation Management")
    st.write(f"Hello, {st.session_state['username']}! You are logged in.")

    # Add Product
    st.subheader("Add New Product")

    category_options = ["Facial Wash", "Mask", "Moisturizer", "Sunscreen", "Toner"]
    skin_options = ["Normal", "Dry", "Oily", "Sensitive", "Combination"]

    new_name = st.text_input('Product Name')
    new_category = st.selectbox('Category', category_options)
    new_type = st.selectbox('Skin Type', skin_options)

    if st.button('Add Product'):
        add_product(new_name, new_category, new_type)
        st.success('Product successfully added!')

    # View Products
    st.subheader("Product List")
    product = view_products()
    df_products = pd.DataFrame(product, columns=['Name', 'Category', 'Type'])
    st.table(df_products)
    
    # Update Product
    st.subheader('Update Product')
    old_name = st.text_input('Current Product Name')
    update_name = st.text_input('New Product Name')
    update_category = st.selectbox('New Category', category_options)
    update_type = st.selectbox('New Skin Type', skin_options)

    if st.button('Update Product'):
        if old_name and update_name:
            update_product(old_name, update_name, update_category, update_type)
        st.success(f'Product "{old_name}" successfully updated to "{update_name}"!')
    else:
        st.error('Please enter both the current and new product names.')

    # Delete Product
    st.subheader('Delete Product')
    delete_name = st.text_input('Product Name to Delete')

    if st.button('Delete Product'):
        delete_product(delete_name)
        st.success('Product successfully deleted!')


# Setup initial state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'

# Streamlit application logic
if st.session_state['logged_in']:
    if st.session_state['page'] == 'crud':
        admin_crud_page()  # Display CRUD admin page if logged in
else:
    login_page()  # Display login page if not logged in

if st.button('Logout'):
    st.session_state['logged_in'] = False
    st.session_state['page'] = 'login'
 
