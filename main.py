from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import os
from functools import wraps

# Import managers
from managers import auth_manager, user_manager, learner_manager, instructor_manager
from managers import course_manager, lecture_manager, enrollment_manager

app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict.get('UserID') or user_dict.get('user_id') or user_dict.get('id')
        self.email = user_dict.get('Email') or user_dict.get('email')
        self.role = user_dict.get('Role') or user_dict.get('role')
        self.password = user_dict.get('Password') or user_dict.get('password')

@login_manager.user_loader
def load_user(user_id):
    user_dict = user_manager.get_user_by_id(int(user_id))
    if not user_dict:
        return None
    return User(user_dict)

# Role-based access control
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# === ROUTE DEFINITIONS ===

# Home Page
@app.route('/')
def index():
    # Get featured courses for display
    featured_courses = course_manager.get_featured_courses()
    return render_template('index.html', courses=featured_courses)

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user_dict = auth_manager.authenticate(email, password)
        
        if not user_dict:
            flash('Incorrect email or password!', 'danger')
            return render_template('login.html')
        
        user = User(user_dict)
        login_user(user)
        # Set UserID in session for later use (e.g., password change)
        session['UserID'] = user.id
        # Lưu role vào session
        role = user_dict.get('Role', user_dict.get('role'))
        session['role'] = role
        
        # Lấy entity_id dựa trên role
        if role == 'learner':
            learner = learner_manager.get_learner_by_email(email)
            if learner:
                session['entity_id'] = learner['LearnerID']
                print(f"Debug - Learner ID set to: {learner['LearnerID']}")
        elif role == 'instructor':
            instructor = instructor_manager.get_instructor_by_email(email)
            if instructor:
                session['entity_id'] = instructor['InstructorID']
        
        flash(f'Login successful!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        phone = request.form.get('phone', '')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
            
        # Check if email already exists
        if not user_manager.is_email_unique(email):
            flash('This email is already registered.', 'danger')
            return render_template('register.html')
        
        # Create new learner (only learners can self-register)
        learner_id = learner_manager.add_learner(name, email, phone, password)
        
        if learner_id:
            flash('Registration successful! You can log in now.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again later.', 'danger')
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have successfully logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        # Implementation for password reset (would involve sending email)
        flash('If the account exists, we have sent password reset instructions to your email.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

# User Dashboard - redirects to appropriate role dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'learner':
        return redirect(url_for('learner_dashboard'))
    elif role == 'instructor':
        return redirect(url_for('instructor_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Unknown role.', 'danger')
        return redirect(url_for('logout'))

# === LEARNER ROUTES ===
@app.route('/learner')
@login_required
@role_required(['learner'])
def learner_dashboard():
    learner_id = session.get('entity_id')
    print(f"Debug - Learner dashboard - learner_id from session: {learner_id}")
    
    learner = learner_manager.get_learner_by_id(learner_id)
    print(f"Debug - Learner data: {learner}")
    
    # Get enrolled courses with progress
    enrolled_courses = enrollment_manager.get_enrollments_by_learner(learner_id)
    print(f"Debug - Enrolled courses count: {len(enrolled_courses) if enrolled_courses else 0}")
    print(f"Debug - Enrolled courses data: {enrolled_courses}")
    
    # Get recommended courses
    recommended_courses = course_manager.get_recommended_courses(learner_id)
    
    return render_template('learner/dashboard.html', 
                           learner=learner,
                           enrolled_courses=enrolled_courses,
                           recommended_courses=recommended_courses)

@app.route('/learner/courses')
@login_required
@role_required(['learner'])
def learner_courses():
    learner_id = session.get('entity_id')
    search_term = request.args.get('search', '')
    
    if search_term:
        
        enrolled_courses = enrollment_manager.search_learner_enrollments(learner_id, search_term)
    else:
        
        enrolled_courses = enrollment_manager.get_enrollments_by_learner(learner_id)
        
    return render_template('learner/courses.html', courses=enrolled_courses, search=search_term)

@app.route('/learner/course/<int:course_id>')
@login_required
@role_required(['learner'])
def learner_course_detail(course_id):
    learner_id = session.get('entity_id')
    if not learner_id:
        flash('Session expired. Please log in again.', 'danger')
        return redirect(url_for('login'))

    # Get all enrollments for this learner
    enrollments = enrollment_manager.get_enrollments_by_learner(learner_id)
    # Find the enrollment for this course
    enrollment = None
    if enrollments:
        for e in enrollments:
            if e['CourseID'] == course_id:
                enrollment = e
                break

    if not enrollment:
        flash('You’re not enrolled in this course.', 'warning')
        return redirect(url_for('learner_courses'))

    course = course_manager.get_course_by_id(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('learner_courses'))

    lectures = lecture_manager.get_lectures_with_view_status(learner_id, course_id)
    if lectures is None:
        lectures = []

    return render_template('learner/course_detail.html',
                           course=course,
                           lectures=lectures,
                           enrollment=enrollment)

@app.route('/learner/lecture/<int:lecture_id>')
@login_required
@role_required(['learner'])
def learner_view_lecture(lecture_id):
    learner_id = session.get('entity_id')
    lecture = lecture_manager.get_lecture_by_id(lecture_id)
    
    if not lecture:
        flash('Lecture does not exist.', 'danger')
        return redirect(url_for('learner_courses'))
    
    # Check if enrolled in the course
    course_id = lecture['CourseID']
    enrollment = enrollment_manager.get_enrollment(learner_id, course_id)
    if not enrollment:
        flash('You do not have permission to view this lecture.', 'warning')
        return redirect(url_for('learner_courses'))
    
    # Mark lecture as viewed
    enrollment_manager.mark_lecture_viewed(learner_id, lecture_id)
    
    return render_template('learner/view_lecture.html', lecture=lecture)

@app.route('/learner/profile', methods=['GET', 'POST'])
@login_required
@role_required(['learner'])
def learner_profile():
    learner_id = session.get('entity_id')
    learner = learner_manager.get_learner_by_id(learner_id)
    
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        # not using email here as it is not editable
        success = learner_manager.update_learner_info(learner_id, name=name, phone=phone)
        
        if success:
            flash('Your personal information has been updated.', 'success')
        else:
            flash('Failed to update information.', 'danger')
            
        return redirect(url_for('learner_profile'))
    learner = learner_manager.get_learner_by_id(learner_id)
    return render_template('learner/profile.html', learner=learner)

@app.route('/learner/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('New passwords do not match!', 'danger')
            return redirect(url_for('change_password'))
            
        user_id = session.get('UserID')
        print('User id:',user_id)
        user = user_manager.get_user_by_id(user_id)
        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('change_password'))
        if not (user['Password'] == current_password or check_password_hash(user['Password'], current_password)):
            flash('Current password is incorrect!', 'danger')
            return redirect(url_for('change_password'))
            
        success = user_manager.update_password(user_id, new_password)
        
        if success:
            flash('Password has been changed successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Password change failed.', 'danger')
            
    return render_template('change_password.html')

@app.route('/courses')
def browse_courses():
    search_term = request.args.get('search', '')
    
    if search_term:
        courses = course_manager.search_courses(search_term)
    else:
        courses = course_manager.list_courses_with_details()
        
    print(f"Debug - Courses count: {len(courses) if courses else 0}")
    if courses and len(courses) > 0:
        print(f"Debug - First course: {courses[0]}")
    return render_template('courses.html', courses=courses, search=search_term)

@app.route('/course/<int:course_id>')
def course_details(course_id):
    course = course_manager.get_course_by_id(course_id)
    if not course:
        flash('The course does not exist.', 'danger')
        return redirect(url_for('browse_courses'))
        
    # Get instructor
    instructor = None
    if course.get('InstructorID'):
        instructor = instructor_manager.get_instructor_by_id(course['InstructorID'])
        
    # Get lectures (only titles)
    lectures = lecture_manager.get_lectures_by_course(course_id)
    
    # Check if user is enrolled
    is_enrolled = False
    if current_user.is_authenticated:
        if current_user.role == 'learner':  
            learner_id = session.get('entity_id')
            enrollment = enrollment_manager.get_enrollment(learner_id, course_id)
            is_enrolled = enrollment is not None
    
    return render_template('course_details.html', 
                          course=course, 
                          instructor=instructor, 
                          lectures=lectures,
                          is_enrolled=is_enrolled)

@app.route('/enroll/<int:course_id>')
@login_required
@role_required(['learner'])
def enroll_course(course_id):
    learner_id = session.get('entity_id')
    
    # Check if already enrolled
    enrollment = enrollment_manager.get_enrollment(learner_id, course_id)
    if enrollment:
        flash('You have already enrolled in this course.', 'info')
        return redirect(url_for('course_details', course_id=course_id))
    
    # Enroll
    success = enrollment_manager.enroll_learner(learner_id, course_id)
    
    if success:
        flash('Course enrollment successful!', 'success')
    else:
        flash('Course enrollment failed.', 'danger')
        
    return redirect(url_for('course_details', course_id=course_id))

@app.route('/unenroll/<int:course_id>')
@login_required
@role_required(['learner'])
def unenroll_course(course_id):
    learner_id = session.get('entity_id')
    
    # Check if user is enrolled in this course
    enrollment = enrollment_manager.get_enrollment(learner_id, course_id)
    if not enrollment:
        flash('You are not enrolled in this course.', 'warning')
        return redirect(url_for('learner_courses'))
    
    # Unenroll
    success = learner_manager.unenroll_from_course(learner_id, course_id)
    
    if success:
        flash('You have successfully unenrolled from this course.', 'success')
    else:
        flash('Failed to unenroll from the course.', 'danger')
        
    return redirect(url_for('learner_courses'))

# === INSTRUCTOR ROUTES ===
@app.route('/instructor')
@login_required
@role_required(['instructor'])
def instructor_dashboard():
    instructor_id = session.get('entity_id')
    instructor = instructor_manager.get_instructor_by_id(instructor_id)
    
    # Get assigned courses
    courses = course_manager.get_courses_by_instructor(instructor_id)
    
    # Get enrollment statistics
    enrollment_stats = {}
    for course in courses:
        course_id = course['CourseID']
        enrollments = enrollment_manager.get_enrollments_by_course(course_id)
        enrollment_stats[course_id] = len(enrollments) if enrollments else 0
    print(f"Debug - Enrollment stats: {enrollment_stats}")
    return render_template('instructor/dashboard.html', 
                          instructor=instructor,
                          courses=courses,
                          enrollment_stats=enrollment_stats)

# The route below can be redundant 
@app.route('/instructor/courses')
@login_required
@role_required(['instructor'])
def instructor_courses():
    instructor_id = session.get('entity_id')
    courses = course_manager.get_courses_by_instructor(instructor_id)
    return render_template('instructor/courses.html', courses=courses)

@app.route('/instructor/course/<int:course_id>')
@login_required
@role_required(['instructor'])
def instructor_course_detail(course_id):
    instructor_id = session.get('entity_id')
    
    # Check if course belongs to instructor
    course = course_manager.get_course_by_id(course_id)
    if not course or course.get('InstructorID') != instructor_id:
        flash('You do not have permission to manage this course.', 'warning')
        return redirect(url_for('instructor_courses'))
    
    # Get lectures
    lectures = lecture_manager.get_lectures_by_course(course_id)
    
    # Get detailed learner progress using get_course_progress_summary
    enrollments = enrollment_manager.get_course_progress_summary(course_id)
    
    return render_template('instructor/course_detail.html', 
                          course=course,
                          lectures=lectures,
                          enrollments=enrollments)

@app.route('/instructor/lecture/add/<int:course_id>', methods=['GET', 'POST'])
@login_required
@role_required(['instructor'])
def instructor_add_lecture(course_id):
    instructor_id = session.get('entity_id')
    
    # Check if course belongs to instructor
    course = course_manager.get_course_by_id(course_id)
    if not course or course.get('InstructorID') != instructor_id:
        flash('You do not have permission to add lectures to this course.', 'warning')
        return redirect(url_for('instructor_courses'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        lecture_id = lecture_manager.add_lecture(course_id, title, content)
        
        if lecture_id:
            flash('Lecture added successfully!', 'success')
            return redirect(url_for('instructor_course_detail', course_id=course_id))
        else:
            flash('Failed to add lecture.', 'danger')
    
    return render_template('instructor/add_lecture.html', course=course)

@app.route('/instructor/lecture/view/<int:lecture_id>')
@login_required
@role_required(['instructor'])
def instructor_view_lecture(lecture_id):
    lecture = lecture_manager.get_lecture_by_id(lecture_id)
    course = course_manager.get_course_by_id(lecture['CourseID'])
    return render_template('instructor/view_lecture.html', lecture=lecture, course=course)

@app.route('/instructor/lecture/<int:lecture_id>', methods=['GET', 'POST'])
@login_required
@role_required(['instructor'])
def instructor_edit_lecture(lecture_id):
    instructor_id = session.get('entity_id')
    lecture = lecture_manager.get_lecture_by_id(lecture_id)
    if not lecture:
        flash('Lecture does not exist.', 'danger')
        return redirect(url_for('instructor_courses'))
    course_id = lecture['CourseID']
    course = course_manager.get_course_by_id(course_id)
    if not course or course.get('InstructorID') != instructor_id:
        flash('You do not have permission to edit this lecture.', 'warning')
        return redirect(url_for('instructor_courses'))

    if request.method == 'POST':
        if 'delete' in request.form:
            # Handle lecture deletion
            success = lecture_manager.delete_lecture(lecture_id)
            if success:
                flash('Lecture deleted successfully!', 'success')
                return redirect(url_for('instructor_course_detail', course_id=course_id))
            else:
                flash('Failed to delete the lecture.', 'danger')
        else:
            # Handle lecture update
            title = request.form['title']
            content = request.form['content']
            success = lecture_manager.update_lecture_content(lecture_id, title=title, content=content)
            if success:
                flash('Lecture updated successfully!', 'success')
                return redirect(url_for('instructor_course_detail', course_id=course_id))
            else:
                flash('Failed to update the lecture.', 'danger')
    return render_template('instructor/edit_lecture.html', lecture=lecture, course=course)

@app.route('/instructor/course/<int:course_id>/students')
@login_required
@role_required(['instructor'])
def instructor_course_students(course_id):
    # Check if course belongs to this instructor
    instructor_id = session.get('entity_id')
    course = course_manager.get_course_by_id(course_id)
    
    if not course or course['InstructorID'] != instructor_id:
        flash('You do not have permission to view students for this course.', 'danger')
        return redirect(url_for('instructor_dashboard'))
    
    # Get enrollments for this course
    enrollments = enrollment_manager.get_detailed_enrollments_by_course(course_id)
    
    return render_template('instructor/course_students.html', 
                          course=course, 
                          enrollments=enrollments)

@app.route('/instructor/profile', methods=['GET', 'POST'])
@login_required
@role_required(['instructor'])
def instructor_profile():
    instructor_id = session.get('entity_id')
    instructor = instructor_manager.get_instructor_by_id(instructor_id)
    
    if request.method == 'POST':
        name = request.form['name']
        expertise = request.form['expertise']
        
        success = instructor_manager.update_instructor_info(
            instructor_id, name=name, expertise=expertise)
        
        if success:
            flash('Personal information has been updated.', 'success')
        else:
            flash('Failed to update information.', 'danger')
            
        return redirect(url_for('instructor_profile'))
        
    return render_template('instructor/profile.html', instructor=instructor)

# === ADMIN ROUTES ===
@app.route('/admin')
@login_required
@role_required(['admin'])
def admin_dashboard():
    learner_count = len(learner_manager.list_all_learners())
    instructor_count = len(instructor_manager.list_all_instructors())
    course_count = len(course_manager.list_all_courses())
    enrollment_count = enrollment_manager.get_enrollment_count()
    
    recent_enrollments = enrollment_manager.get_recent_enrollments(10)
    
    return render_template('admin/dashboard.html',
                          learner_count=learner_count,
                          instructor_count=instructor_count,
                          course_count=course_count,
                          enrollment_count=enrollment_count,
                          recent_enrollments=recent_enrollments)

@app.route('/admin/learners')
@login_required
@role_required(['admin'])
def admin_learners():
    search_term = request.args.get('search', '')
    
    if search_term:
        learners = learner_manager.search_learners(search_term)
    else:
        learners = learner_manager.list_all_learners()
        
    return render_template('admin/learners.html', learners=learners, search=search_term)

@app.route('/admin/learner/<int:learner_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_learner_detail(learner_id):
    learner = learner_manager.get_learner_by_id(learner_id)

    if not learner:
        flash('Learner does not exist.', 'danger')
        return redirect(url_for('admin_learners'))

    if request.method == 'POST':
        if 'delete' in request.form:
            # Handle learner deletion
            success = learner_manager.delete_learner(learner_id)
            if success:
                flash('Learner deleted successfully!', 'success')
                return redirect(url_for('admin_learners'))
            else:
                flash('Failed to delete learner.', 'danger')
                return redirect(url_for('admin_learner_detail', learner_id=learner_id))
        else:
            # Handle update
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']

            success = learner_manager.update_learner_info(
                learner_id, name=name, email=email, phone=phone)

            if success:
                flash('Learner information updated successfully!', 'success')
            else:
                flash('Failed to update learner information.', 'danger')

            return redirect(url_for('admin_learner_detail', learner_id=learner_id))

    # Get all enrollments for this learner (with course progress)
    learner_courses = enrollment_manager.get_enrollments_by_learner(learner_id)
    # Get all enrollments (for the list below, if you want to keep it)
    enrollments = enrollment_manager.get_enrollments_by_learner(learner_id)

    return render_template('admin/learner_detail.html',
                           learner=learner,
                           learner_courses=learner_courses,
                           enrollments=enrollments)

@app.route('/admin/instructors')
@login_required
@role_required(['admin'])
def admin_instructors():
    search_term = request.args.get('search', '')
    
    if search_term:
        instructors = instructor_manager.search_instructors(search_term)
    else:
        instructors = instructor_manager.list_all_instructors()
        
    return render_template('admin/instructors.html', instructors=instructors, search=search_term)

@app.route('/admin/instructor/<int:instructor_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_instructor_detail(instructor_id):
    instructor = instructor_manager.get_instructor_by_id(instructor_id)
    if not instructor:
        flash('Instructor does not exist.', 'danger')
        return redirect(url_for('admin_instructors'))

    if request.method == 'POST':
        if 'delete' in request.form:
            # Handle instructor deletion
            success = instructor_manager.delete_instructor(instructor_id)
            if success:
                flash('Instructor deleted successfully!', 'success')
                return redirect(url_for('admin_instructors'))
            else:
                flash('Failed to delete instructor.', 'danger')
                return redirect(url_for('admin_instructor_detail', instructor_id=instructor_id))
        else:
            # Handle update
            name = request.form['name']
            email = request.form['email']
            expertise = request.form['expertise']

            success = instructor_manager.update_instructor_info(
                instructor_id, name=name, email=email, expertise=expertise
            )

            if success:
                flash('Instructor information updated successfully!', 'success')
            else:
                flash('Failed to update instructor information.', 'danger')
            return redirect(url_for('admin_instructor_detail', instructor_id=instructor_id))

    return render_template('admin/instructor_detail.html', instructor=instructor)

@app.route('/admin/courses')
@login_required
@role_required(['admin'])
def admin_courses():
    search_term = request.args.get('search', '')
    
    if search_term:
        courses = course_manager.search_courses(search_term)
    else:
        courses = course_manager.list_all_courses()
        
    return render_template('admin/courses.html', courses=courses, search=search_term)

@app.route('/admin/course/<int:course_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_course_detail(course_id):
    course = course_manager.get_course_by_id(course_id)
    
    if not course:
        flash('Course does not exist.', 'danger')
        return redirect(url_for('admin_courses'))
    
    if request.method == 'POST':
        if 'delete' in request.form:
            # Handle course deletion
            success = course_manager.delete_course(course_id)
            if success:
                flash('Course deleted successfully!', 'success')
                return redirect(url_for('admin_courses'))
            else:
                flash('Failed to delete course.', 'danger')
                return redirect(url_for('admin_course_detail', course_id=course_id))
        else:
            # Handle update
            name = request.form['name']
            description = request.form['description']
            instructor_id = request.form.get('instructor', '')
            
            if instructor_id == '':
                instructor_id = None
            else:
                instructor_id = int(instructor_id)
                
            success = course_manager.update_course_info(
                course_id, name=name, description=description, instructor_id=instructor_id)
            
            if success:
                flash('Course information updated successfully!', 'success')
            else:
                flash('Failed to update course information.', 'danger')
                
            return redirect(url_for('admin_course_detail', course_id=course_id))
        
    instructors = instructor_manager.list_all_instructors()
    lectures = lecture_manager.get_lectures_by_course(course_id)
    
    return render_template('admin/course_detail.html', 
                          course=course,
                          instructors=instructors,
                          lectures=lectures)

# Add to main.py

@app.route('/admin/lecture/<int:lecture_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_edit_lecture(lecture_id):
    lecture = lecture_manager.get_lecture_by_id(lecture_id)
    if not lecture:
        flash('Lecture does not exist.', 'danger')
        return redirect(url_for('admin_courses'))
    course_id = lecture.get('CourseID')
    course = course_manager.get_course_by_id(course_id)
    if not course:
        flash('Course does not exist.', 'danger')
        return redirect(url_for('admin_courses'))

    if request.method == 'POST':
        if 'delete' in request.form:
            success = lecture_manager.delete_lecture(lecture_id)
            if success:
                flash('Lecture deleted successfully!', 'success')
                return redirect(url_for('admin_course_detail', course_id=course_id))
            else:
                flash('Failed to delete the lecture.', 'danger')
                return redirect(url_for('admin_edit_lecture', lecture_id=lecture_id))
        else:
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            if not title or not content:
                flash('Title and content are required.', 'danger')
            else:
                success = lecture_manager.update_lecture_content(lecture_id, title=title, content=content)
                if success:
                    flash('Lecture updated successfully!', 'success')
                    return redirect(url_for('admin_course_detail', course_id=course_id))
                else:
                    flash('Failed to update the lecture.', 'danger')
    return render_template('admin/edit_lecture.html', lecture=lecture, course=course)

@app.route('/admin/lecture/view/<int:lecture_id>')
@login_required
@role_required(['admin'])
def admin_view_lecture(lecture_id):
    lecture = lecture_manager.get_lecture_by_id(lecture_id)
    if not lecture:
        flash('Lecture does not exist.', 'danger')
        return redirect(url_for('admin_courses'))
    course = course_manager.get_course_by_id(lecture['CourseID'])
    return render_template('admin/view_lecture.html', lecture=lecture, course=course)

@app.route('/admin/lecture/add/<int:course_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_add_lecture(course_id):
    course = course_manager.get_course_by_id(course_id)
    if not course:
        flash('Course does not exist.', 'danger')
        return redirect(url_for('admin_courses'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash('Title and content are required.', 'danger')
        else:
            lecture_id = lecture_manager.add_lecture(course_id, title, content)
            if lecture_id:
                flash('Lecture added successfully!', 'success')
                return redirect(url_for('admin_course_detail', course_id=course_id))
            else:
                flash('Failed to add lecture.', 'danger')
    return render_template('admin/add_lecture.html', course=course)

@app.route('/admin/reports')
@login_required
@role_required(['admin'])
def admin_reports():
    instructor_workload = instructor_manager.get_all_instructors_workload()
    active_courses = course_manager.list_active_courses()
    
    return render_template('admin/reports.html',
                          instructor_workload=instructor_workload,
                          active_courses=active_courses)

@app.route('/admin/add-learner', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_add_learner():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        if not user_manager.is_email_unique(email):
            flash('Email already exists in the system!', 'danger')
            return render_template('admin/add_learner.html')
        
        learner_id = learner_manager.add_learner(name, email, phone, password)
        
        if learner_id:
            flash(f'Successfully added learner {name}!', 'success')
            return redirect(url_for('admin_learners'))
        else:
            flash('Failed to add learner.', 'danger')
    
    return render_template('admin/add_learner.html')

@app.route('/admin/add-instructor', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_add_instructor():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        expertise = request.form['expertise']
        password = request.form['password']
        
        if not user_manager.is_email_unique(email):
            flash('Email already exists in the system!', 'danger')
            return render_template('admin/add_instructor.html')
        
        instructor_id = instructor_manager.add_instructor(name, expertise, email, password)
        
        if instructor_id:
            flash(f'Successfully added instructor {name}!', 'success')
            return redirect(url_for('admin_instructors'))
        else:
            flash('Failed to add instructor.', 'danger')
    
    return render_template('admin/add_instructor.html')

@app.route('/admin/add-course', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_add_course():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        instructor_id = request.form.get('instructor', '')
        print(f"Adding course: {name}, {description}, instructor_id={instructor_id}")
        if instructor_id == '':
            instructor_id = None
        else:
            instructor_id = int(instructor_id)
        course_id = course_manager.add_course(name, description, instructor_id)
        
        if course_id:
            flash(f'Successfully added course {name}!', 'success')
            return redirect(url_for('admin_courses'))
        else:
            flash('Failed to add course.', 'danger')
    
    instructors = instructor_manager.list_all_instructors()
    
    return render_template('admin/add_course.html', instructors=instructors)

@app.route('/admin/course_summary/select', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_course_summary_select():
    courses = course_manager.list_all_courses()
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        if course_id:
            return redirect(url_for('admin_course_summary', course_id=course_id))
        else:
            flash('Please select a course.', 'warning')
    return render_template('admin/course_summary_select.html', courses=courses)

@app.route('/admin/course_summary/<int:course_id>')
@login_required
@role_required(['admin'])
def admin_course_summary(course_id):
    course = course_manager.get_course_by_id(course_id)
    if not course:
        flash('Course does not exist.', 'danger')
        return redirect(url_for('admin_course_summary_select'))
    summary = enrollment_manager.get_course_progress_summary(course_id)
    return render_template('admin/course_summary.html', course=course, summary=summary)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')