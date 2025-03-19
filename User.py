import pickle
import streamlit as st
import numpy as np
import pandas as pd
import sqlite3
import random
import bcrypt

# Load model and data
model = pickle.load(open('artifacts/model.pkl', 'rb'))
skincare_names = pickle.load(open('artifacts/skincare_names.pkl', 'rb'))
final_rating = pickle.load(open('artifacts/final_rating.pkl', 'rb'))
skincare_pivot = pickle.load(open('artifacts/skincare_pivot.pkl', 'rb'))
skincare_type = pickle.load(open('artifacts/skincare_types.pkl', 'rb'))

st.title('Skincare Recommendation')

# Database setup
def create_main_db():
    conn = sqlite3.connect('main.db')
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
              )
              ''')
    c.execute('''
              CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_id INTEGER,
                    rating INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id)
              )
              ''')
    conn.commit()
    conn.close()

create_main_db()

# Database connection
def get_main_db_connection():
    conn = sqlite3.connect('main.db')
    return conn

def get_product_db_connection():
    conn = sqlite3.connect('product.db')
    return conn

# User authentication
def register_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Check if the username already exists
    existing_user = c.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if existing_user:
        conn.close()
        return False  # Username already exists

    # If username does not exist, proceed with registration
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
    conn.commit()
    conn.close()
    return True  # Registration successful

def login_user(username, password):
    conn = get_main_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
        return user
    else:
        return None

# Rating system
def rate_product(user_id, product_id, rating):
    conn = get_main_db_connection()
    conn.execute('INSERT INTO ratings (user_id, product_id, rating) VALUES (?, ?, ?)',
                 (user_id, product_id, rating))
    conn.commit()
    conn.close()

def get_average_rating(product_id):
    conn = get_main_db_connection()
    avg_rating = conn.execute('SELECT AVG(rating) FROM ratings WHERE product_id = ?', (product_id,)).fetchone()[0]
    conn.close()
    return avg_rating if avg_rating else 0

def get_product_id_by_name(name):
    df = load_data_from_db()  # Memuat data dari database
    filtered_df = df[df['name'] == name]
    
    if not filtered_df.empty:
        return filtered_df.index[0]  # Ambil ID produk dari index DataFrame
    else:
        return None  # Nama produk tidak ditemukan
    
# Load product data
def load_data_from_db():
    conn = get_product_db_connection()
    query = 'SELECT * FROM product'
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def merge_data():
    db_data = load_data_from_db()
    db_product_names = db_data['name'].tolist()
    combined_names = list(set(skincare_names) | set(db_product_names))
    return combined_names, db_data

# Fetch poster
def fetch_poster(suggestion):
    skincare_name = []
    ids_index = []
    poster_url = []

    for skincare_id in suggestion:
        skincare_name.append(skincare_pivot.index[skincare_id])

    for name in skincare_name[0]:
        ids = np.where(final_rating['Product Name'] == name)[0][0]
        ids_index.append(ids)

    for idx in ids_index:
        url = final_rating.iloc[idx]['Image']
        poster_url.append(url)

    return poster_url

# Skincare recommendation
def recommend_skincare(skincare_name):
    skincare_list = []

    combined_names, _ = merge_data()

    if skincare_name not in combined_names:
        st.error("Product not found!")
        return skincare_list, []

    if skincare_name in skincare_pivot.index:
        skincare_id = np.where(skincare_pivot.index == skincare_name)[0][0]
        distance, suggestion = model.kneighbors(skincare_pivot.iloc[skincare_id, :].values.reshape(1, -1), n_neighbors=4)
    else:
        st.error("Recommendation model doesn't contain this product.")
        return skincare_list, []

    poster_url = fetch_poster(suggestion)

    for i in range(len(suggestion)):
        skincare = skincare_pivot.index[suggestion[i]]
    for j in skincare:
        skincare_list.append(j)
    return skincare_list, poster_url

# Main application
combined_names, _ = merge_data()

selected_skincare = st.selectbox("Choose a skincare product", combined_names)

if st.button('Here`s Your Recommendation'):
    recommended_skincare, poster_url = recommend_skincare(selected_skincare)
    num_recommendations = random.randint(2, 6)
    selected_indices = random.sample(range(len(recommended_skincare)), min(num_recommendations, len(recommended_skincare)))
    selected_recommendations = [recommended_skincare[i] for i in selected_indices]
    selected_posters = [poster_url[i] for i in selected_indices]
    num_columns = len(selected_recommendations)
    cols = st.columns(num_columns)

    for idx in range(num_columns):
        with cols[idx]:
            st.text(selected_recommendations[idx])
            if idx < len(selected_posters):
                st.image(selected_posters[idx], use_container_width=True)
            else:
                st.text("No image available")

# Registration
if st.sidebar.checkbox('Register'):
    new_user = st.sidebar.text_input('Username')
    new_password = st.sidebar.text_input('Password', type='password')
    if st.sidebar.button('Register'):
        registration_successful = register_user(new_user, new_password)
        if registration_successful:
            st.sidebar.success("User registered successfully!")
        else:
            st.sidebar.error("Username already exists. Please choose a different username.")

user = None

if st.sidebar.checkbox('Login'):
    username = st.sidebar.text_input('Username')
    password = st.sidebar.text_input('Password', type='password')
    if st.sidebar.button('Login'):
        user = login_user(username, password)
        if user:
            st.sidebar.success(f"Logged in as {user[1]}")
        else:
            st.sidebar.error("Incorrect username or password")

if user:
    st.subheader('Rate a Product')
    product_to_rate = st.selectbox('Select a product', combined_names)
    rating = st.slider('Rate (1-5)', 1, 5, 3)

    if st.button('Submit Rating'):
        product_id = get_product_id_by_name(product_to_rate)
        
        if product_id is not None:
            rate_product(user[0], product_id, rating)
            st.success('Rating submitted!')
        else:
            st.error('Product not found. Please select a valid product.')
else:
    st.warning("Please log in to rate products.")

# Display product table
st.subheader("Skincare Product")
st.dataframe(skincare_type)
