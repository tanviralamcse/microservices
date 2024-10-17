import os
import boto3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
import requests

app = Flask(__name__)

# Ensure secret key is loaded from environment variables
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# AWS DynamoDB setup
try:
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_DEFAULT_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
except Exception as e:
    app.logger.error(f"Failed to create DynamoDB resource: {str(e)}")

# Define tables
table = dynamodb.Table('itsawsAdminCredential')
posts_table = dynamodb.Table('Projects')

# API Base URL for CRUD operations
API_BASE_URL = 'https://g2bxonwzo4.execute-api.eu-central-1.amazonaws.com/deployed'

# Function to get admin credentials from DynamoDB
def get_admin_credentials(username):
    try:
        response = table.get_item(Key={'username': username})
        admin = response.get('Item', None)
        return admin['username'], admin['password'] if admin else (None, None)
    except Exception as e:
        return None, None

# Route for admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    admin_username = 'tanvir'
    admin_username, admin_password = get_admin_credentials(admin_username)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == admin_username and password == admin_password:
            session['logged_in'] = True
            session.pop('_flashes', None)  # Clear any flash messages from previous sessions
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

# Route for admin logout
@app.route('/admin/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Route for admin dashboard
@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        response = posts_table.scan(ProjectionExpression='id')
        total_posts = len(response['Items'])

        # Fetch all posts
        response = posts_table.scan()
        posts = response['Items']
    except Exception as e:
        total_posts = 0
        posts = []

    return render_template('dashboard.html', total_posts=total_posts, posts=posts)

# Route to Create a Post
@app.route('/admin/create_post', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image_link = request.form['image']

        post_data = {
            'title': title,
            'description': description,
            'image': image_link
        }

        try:
            response = requests.post(API_BASE_URL + '/post', json=post_data)

            if response.status_code == 201:
                flash('Post created successfully!', 'success')
            else:
                flash('Error creating post. Please try again.', 'danger')

        except Exception as e:
            flash('Error creating post. Please try again later.', 'danger')

        return redirect(url_for('dashboard'))

    post = {'title': '', 'description': '', 'image': ''}
    return render_template('create_post.html', post=post)

# Route to view a specific post by projectId
@app.route('/admin/posts/<string:projectId>')
def view_post(projectId):
    try:
        response = posts_table.get_item(Key={'projectId': projectId})
        post = response.get('Item', None)

        if not post:
            flash('Post not found.', 'danger')
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash('Error fetching post details.', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('view_post.html', post=post)

# Route to edit a post
@app.route('/admin/posts/<string:projectId>/edit', methods=['GET', 'POST'])
def edit_post(projectId):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image_link = request.form['image']

        update_data = {
            'title': title,
            'description': description,
            'image': image_link
        }

        try:
            response = requests.put(f"{API_BASE_URL}/posts/{projectId}", json=update_data)
            if response.status_code == 200:
                flash('Post updated successfully!', 'success')
            else:
                flash(f'Error updating post: {response.text}', 'danger')
        except Exception as e:
            flash('Error updating post. Please try again later.', 'danger')

        return redirect(url_for('dashboard'))

    try:
        response = posts_table.get_item(Key={'projectId': projectId})
        post = response.get('Item', None)

        if not post:
            flash('Post not found.', 'danger')
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash('Error retrieving post data.', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('edit_post.html', post=post)

# Route to handle the update post operation (PUT)
@app.route('/posts/<string:projectId>', methods=['PUT'])
def update_post(projectId):
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    github_link = data.get('image')

    response = posts_table.update_item(
        Key={'projectId': projectId},
        UpdateExpression="SET title = :t, description = :d, image = :g",
        ExpressionAttributeValues={
            ':t': title,
            ':d': description,
            ':g': github_link
        },
        ReturnValues="UPDATED_NEW"
    )

    return jsonify({"message": "Post updated successfully!", "updatedAttributes": response.get('Attributes')}), 200

# Route to delete a post
@app.route('/admin/posts/<string:projectId>/delete', methods=['POST'])
def delete_post(projectId):
    try:
        response = posts_table.delete_item(Key={'projectId': projectId})
        flash('Post deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting post. Please try again.', 'danger')

    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)  # Bind to all interfaces on port 5000

