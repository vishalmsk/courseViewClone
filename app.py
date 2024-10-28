from pytz import timezone
import pytz
from flask import Flask, Response, render_template, request, jsonify, make_response, url_for
from config import Config
from extension import db
from flask_migrate import Migrate
from email_validator import validate_email, EmailNotValidError
from flask_mail import Mail, Message

app = Flask(__name__)
# Direct configuration for Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'mitrmedia3@gmail.com'
app.config['MAIL_PASSWORD'] = 'nczustsbcycmxpyo'
app.config['MAIL_DEFAULT_SENDER'] = 'mitrmedia3@gmail.com'

mail = Mail(app)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

from models import User, Course, UserAction

with app.app_context():
    db.create_all()


def url_for_with_prefix(endpoint, **values):
    prefix = '/cornelsen'
    original_url = url_for(endpoint, **values)
    return prefix + original_url



@app.route('/data')
def data():
    courses = Course.query.all()
    return render_template('data.html', courses=courses)



@app.route('/')
def index():
    email = request.cookies.get('user_email')
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            # Record the visit
            action = UserAction(action='visited_site', user_id=user.id)
            db.session.add(action)
            db.session.commit()
    # Group courses by style
    courses = Course.query.all()
    courses_by_style = {}
    for course in courses:
        courses_by_style.setdefault(course.style, []).append(course)
    return render_template(
        'index.html',
        courses_by_style=courses_by_style,
        email_provided=bool(email),
        url_for_with_prefix=url_for_with_prefix
    )



@app.route('/submit', methods=['POST'])
def submit():
    data = request.json

    subject = 'New Contact Us Submission'
    body_html = f"""
    <html>
        <body>
            <h2>New Contact Us Submission</h2>
            <p><b>Name:</b> {data['first_name']} {data['last_name']}</p>
            <p><b>Email:</b> {data['email']}</p>
            <p><b>Company:</b> {data['company_name']}</p>
            <p><b>Message:</b> {data['message']}</p>
            <p>This request has come from <b>demos.mitrmedia.com/klett</b>.</p>
        </body>
    </html>
    """

    # Send email to sales team
    msg = Message(subject, recipients=['sam@mitrmedia.com'])
    msg.body = "This is a plain text backup for email clients that don't render HTML."
    msg.html = body_html

    try:
        # Send the email
        mail.send(msg)
        return jsonify({"success": True, "message": "Email sent successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
      

@app.route('/submit_email', methods=['POST'])
def submit_email():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required.'}), 400
    try:
        # Validate email
        valid = validate_email(email)
        email = valid.email
    except EmailNotValidError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email)
        db.session.add(user)
        db.session.commit()
    # Record the visit
    action = UserAction(action='submitted_email', user_id=user.id)
    db.session.add(action)
    db.session.commit()
    response = make_response(jsonify({'status': 'success'}))
    response.set_cookie('user_email', email, max_age=30*24*60*60)  # 30 days
    return response

@app.route('/record_course_view', methods=['POST'])
def record_course_view():
    data = request.get_json()
    course_id = data.get('course_id')
    email = request.cookies.get('user_email')
    if not email or not course_id:
        return jsonify({'status': 'error', 'message': 'Invalid data.'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found.'}), 404
    action = UserAction(action='viewed_course', user_id=user.id, course_id=course_id)
    db.session.add(action)
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/get_course_url', methods=['POST'])
def get_course_url():
    data = request.get_json()
    course_id = data.get('course_id')
    course = Course.query.get(course_id)

    if course:
        course_url = course.course_url

        # Check if the course URL points to a local build
        if course_url.startswith('build'):
            # Use `url_for_with_prefix` to generate the correct URL to serve the local build files
            course_url = url_for_with_prefix('static', filename=course_url)

        return jsonify({'status': 'success', 'course_url': course_url})
    else:
        return jsonify({'status': 'error', 'message': 'Course not found'}), 404




# import requests

# @app.route('/get_course_url/<int:course_id>', methods=['GET'])
# def get_course_url(course_id):
#     course = Course.query.get(course_id)
    
#     if course:
#         course_url = course.course_url  # Get the external URL from the database
        
#         # Proxy the request
#         try:
#             # Fetch the external content
#             resp = requests.get(course_url)
            
#             # Check if the external content was successfully fetched
#             if resp.status_code == 200:
#                 # Exclude certain headers like 'content-encoding' that could cause issues
#                 excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
#                 headers = [(name, value) for (name, value) in resp.headers.items() if name.lower() not in excluded_headers]
                
#                 # Return the external content with the original headers
#                 return Response(resp.content, resp.status_code, headers)
#             else:
#                 return jsonify({'status': 'error', 'message': 'Failed to fetch the external course URL'}), 500
#         except requests.RequestException as e:
#             return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500
#     else:
#         return jsonify({'status': 'error', 'message': 'Course not found'}), 404



from collections import Counter
from sqlalchemy.sql import func

# ... [existing code] ...
@app.route('/dashboard')
def dashboard():
    # Implement authentication here (omitted for brevity)
    users = User.query.all()
    courses = Course.query.all()
    user_course_views = {}
    ist = timezone('Asia/Kolkata')

    # Analytics Data
    total_users = User.query.count()
    total_courses = Course.query.count()

    # Most viewed course
    course_view_counts = db.session.query(
        UserAction.course_id, func.count(UserAction.course_id)
    ).filter(
        UserAction.action == 'viewed_course'
    ).group_by(
        UserAction.course_id
    ).order_by(func.count(UserAction.course_id).desc()).first()

    if course_view_counts:
        course_id, views = course_view_counts
        course = Course.query.get(course_id)
        most_viewed_course = {
            'title': course.title,
            'views': views
        }
    else:
        most_viewed_course = None

    for user in users:
        course_views = {}
        for course in courses:
            # Get all timestamps when the user viewed the course
            actions = UserAction.query.filter_by(
                user_id=user.id, course_id=course.id, action='viewed_course'
            ).order_by(UserAction.timestamp.desc()).all()
            timestamps = []
            for action in actions:
                # If the timestamp is naive, assume it's in UTC and localize it
                if action.timestamp.tzinfo is None:
                    utc_timestamp = pytz.utc.localize(action.timestamp)
                else:
                    utc_timestamp = action.timestamp
                ist_timestamp = utc_timestamp.astimezone(ist)
                timestamps.append(ist_timestamp)
            course_views[course.id] = timestamps if timestamps else None
        # Handle user.created_at similarly
        if user.created_at.tzinfo is None:
            utc_created_at = pytz.utc.localize(user.created_at)
        else:
            utc_created_at = user.created_at
        ist_created_at = utc_created_at.astimezone(ist)
        user_course_views[user.id] = {
            'signup_date': ist_created_at,
            'course_views': course_views
        }

    return render_template(
        'dashboard.html',
        users=users,
        courses=courses,
        user_course_views=user_course_views,
        total_users=total_users,
        total_courses=total_courses,
        most_viewed_course=most_viewed_course
    )

@app.route('/get_courses', methods=['GET'])
def get_courses():
    style = request.args.get('style')
    if style:
        courses = Course.query.filter_by(style=style).all()
    else:
        courses = Course.query.all()

    course_list = [
        {
            'id': course.id,
            'title': course.title,
            'thumbnail_url': course.thumbnail_url,
            'style': course.style
        }
        for course in courses
    ]
    return jsonify({'status': 'success', 'courses': course_list})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
