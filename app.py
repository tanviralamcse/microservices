import boto3
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
table = dynamodb.Table('itsawsAdminCredential')
posts_table = dynamodb.Table('Projects')

API_BASE_URL = 'https://g2bxonwzo4.execute-api.eu-central-1.amazonaws.com/deployed'

# Function to get admin credentials from DynamoDB
def get_admin_credentials(username):
    try:
        response = table.get_item(Key={'username': username})
        admin = response.get('Item', None)
        if admin:
            return admin['username'], admin['password']
        else:
            return None, None
    except Exception as e:
        print(f"Error retrieving credentials: {e}")
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
        print(f"Error fetching posts: {e}")
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
            print(f"Error creating post: {e}")
            flash('Error creating post. Please try again later.', 'danger')

        return redirect(url_for('dashboard'))

    # In case of GET request, we pass an empty post object to avoid errors in the template
    post = {'title': '', 'description': '', 'image': ''}

    return render_template('create_post.html', post=post)


# Route to view a specific post by projectId
@app.route('/admin/posts/<string:projectId>')
def view_post(projectId):
    try:
        # Fetch the post from DynamoDB using the projectId
        response = posts_table.get_item(Key={'projectId': projectId})
        post = response.get('Item', None)

        if not post:
            flash('Post not found.', 'danger')
            return redirect(url_for('dashboard'))

    except Exception as e:
        print(f"Error fetching post: {e}")
        flash('Error fetching post details.', 'danger')
        return redirect(url_for('dashboard'))

    # Render the view_post.html template with the post data
    return render_template('view_post.html', post=post)


# Route to edit a post
@app.route('/admin/posts/<string:projectId>/edit', methods=['GET', 'POST'])
def edit_post(projectId):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image_link = request.form['image']

        # Prepare data for update
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
            print(f"Error updating post: {e}")
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
    # Validate and process the incoming data
    title = data.get('title')
    description = data.get('description')
    github_link = data.get('image')  # 'image' represents the GitHub link

    # Update the post in DynamoDB
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


@app.route('/admin/posts/<string:projectId>/delete', methods=['POST'])
def delete_post(projectId):
    try:
        # Delete the post from the DynamoDB using the projectId
        response = posts_table.delete_item(
            Key={'projectId': projectId}
        )
        flash('Post deleted successfully!', 'success')
    except Exception as e:
        print(f"Error deleting post: {e}")
        flash('Error deleting post. Please try again.', 'danger')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)