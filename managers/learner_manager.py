from utils.db_connector import create_connection
from mysql.connector import Error
import bcrypt

def add_learner(name, email, phone, password):
    """Add a new learner with user account."""
    from managers import user_manager
    
    connection = create_connection()
    if not connection:
        return None
    
    try:
        connection.start_transaction()
        
        user_id = user_manager.create_user(email, password, 'learner')
        
        if not user_id:
            connection.rollback()
            print("Failed to create user account")
            return None
        
        with connection.cursor() as cursor:
            query = "INSERT INTO Learners (UserID, LearnerName, PhoneNumber) VALUES (%s, %s, %s)"
            cursor.execute(query, (user_id, name, phone))
            learner_id = cursor.lastrowid
            
        connection.commit()
        return learner_id
        
    except Error as e:
        connection.rollback()
        print(f"Error adding learner: {e}")
        return None
    finally:
        connection.close()

def get_learner_by_id(learner_id):
    """Get learner information by ID including email."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            # JOIN with Users to get email
            query = """
                SELECT l.LearnerID, l.LearnerName, u.Email, l.PhoneNumber, l.UserID
                FROM Learners l
                JOIN Users u ON l.UserID = u.UserID
                WHERE l.LearnerID = %s
            """
            cursor.execute(query, (learner_id,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error retrieving learner: {e}")
        return None
    finally:
        connection.close()

def get_learner_by_email(email):
    """Get learner details by email."""
    connection = create_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # fix the query to use the correct table and join
            query = """
                SELECT L.* 
                FROM Learners L 
                JOIN Users U ON L.UserID = U.UserID 
                WHERE U.Email = %s
            """
            cursor.execute(query, (email,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error getting learner by email: {e}")
        return None
    finally:
        connection.close()

def get_learner_by_user_id(user_id):
    """Get learner details by UserID."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Learners WHERE UserID = %s"
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error getting learner by user ID: {e}")
        return None
    finally:
        connection.close()

def update_learner_info(learner_id, name=None, phone=None, email=None):
    """Update learner information."""
    connection = create_connection()
    if not connection:
        return False
    
    try:
        connection.start_transaction()
        
        # Update learner table
        learner_updates = []
        learner_params = []
        
        if name:
            learner_updates.append("LearnerName = %s")
            learner_params.append(name)
            
        if phone:
            learner_updates.append("PhoneNumber = %s")
            learner_params.append(phone)
            
        if learner_updates:
            learner_params.append(learner_id)
            learner_query = f"UPDATE Learners SET {', '.join(learner_updates)} WHERE LearnerID = %s"
            
            with connection.cursor() as cursor:
                cursor.execute(learner_query, learner_params)
        
        # Update email in Users table if needed
        if email:
            # Get the UserID from Learners table
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT UserID FROM Learners WHERE LearnerID = %s", (learner_id,))
                result = cursor.fetchone()
                
                if result and 'UserID' in result:
                    user_id = result['UserID']
                    cursor.execute("UPDATE Users SET Email = %s WHERE UserID = %s", (email, user_id))
        
        connection.commit()
        return True
        
    except Error as e:
        connection.rollback()
        print(f"Error updating learner: {e}")
        return False
    finally:
        connection.close()

def list_all_learners():
    """Get all learners with their information including email."""
    connection = create_connection()
    if not connection:
        return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            # join with Users to get email
            query = """
                SELECT l.LearnerID, l.LearnerName, u.Email, l.PhoneNumber
                FROM Learners l
                JOIN Users u ON l.UserID = u.UserID
                ORDER BY l.LearnerName
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        print(f"Error retrieving learners: {e}")
        return []
    finally:
        connection.close()

def delete_learner(learner_id):
    """Delete a learner and their user account."""
    connection = create_connection()
    if not connection:
        return False
    
    try:
        connection.start_transaction()
        
        # Get the UserID first
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT UserID FROM Learners WHERE LearnerID = %s", (learner_id,))
            result = cursor.fetchone()
            
            if not result or 'UserID' not in result:
                connection.rollback()
                return False
                
            user_id = result['UserID']
            
            # Delete related records first
            # Delete lecture views
            cursor.execute("DELETE FROM LectureViews WHERE LearnerID = %s", (learner_id,))
            
            # Delete enrollments
            cursor.execute("DELETE FROM Enrollments WHERE LearnerID = %s", (learner_id,))
            
            # Delete from Learners table
            cursor.execute("DELETE FROM Learners WHERE LearnerID = %s", (learner_id,))
            
            # Then delete the User record
            cursor.execute("DELETE FROM Users WHERE UserID = %s", (user_id,))
            
        connection.commit()
        return True
        
    except Error as e:
        connection.rollback()
        print(f"Error deleting learner: {e}")
        return False
    finally:
        connection.close()

def check_password(learner_id, password):
    """Check if the provided password matches the stored password for the learner."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor(dictionary=True) as cursor:
            # fix the query to use the correct table and join
            query = """
                SELECT U.Password 
                FROM Users U
                JOIN Learners L ON U.UserID = L.UserID
                WHERE L.LearnerID = %s
            """
            cursor.execute(query, (learner_id,))
            result = cursor.fetchone()
            if result and result['Password'] == password:
                return True
            return False
    except Error as e:
        print(f"Error checking password: {e}")
        return False
    finally:
        connection.close()

def update_password(learner_id, new_password):
    """Update the password for the learner."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            query = "UPDATE Learners SET Password = %s WHERE LearnerID = %s"
            cursor.execute(query, (new_password, learner_id))
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error updating password: {e}")
        return False
    finally:
        connection.close()

def get_learner_courses(learner_id):
    """Retrieve all courses for a specific learner."""
    connection = create_connection()
    if not connection:
        return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT Courses.CourseID, Courses.CourseName
                FROM Enrollments
                JOIN Courses ON Enrollments.CourseID = Courses.CourseID
                WHERE Enrollments.LearnerID = %s
            """
            cursor.execute(query, (learner_id,))
            return cursor.fetchall()
    except Error as e:
        print(f"Error retrieving learner courses: {e}")
        return []
    finally:
        connection.close()

def enroll_in_course(learner_id, course_id):
    """Enroll a learner in a specific course."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            query = "INSERT INTO Enrollments (LearnerID, CourseID) VALUES (%s, %s)"
            cursor.execute(query, (learner_id, course_id))
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error enrolling in course: {e}")
        return False
    finally:
        connection.close()

def unenroll_from_course(learner_id, course_id):
    """Unenroll a learner from a specific course and delete all lecture views."""
    connection = create_connection()
    if not connection:
        return False
    
    try:
        connection.start_transaction()
        
        with connection.cursor() as cursor:
            # Delete lecture views for this course
            cursor.execute("""
                DELETE lv FROM LectureViews lv
                JOIN Lectures l ON lv.LectureID = l.LectureID
                WHERE lv.LearnerID = %s AND l.CourseID = %s
            """, (learner_id, course_id))
            
            # Delete enrollment
            cursor.execute("DELETE FROM Enrollments WHERE LearnerID = %s AND CourseID = %s", 
                          (learner_id, course_id))
            
            if cursor.rowcount > 0:
                connection.commit()
                return True
            else:
                connection.rollback()
                return False
                
    except Error as e:
        if connection:
            connection.rollback()
        print(f"Error unenrolling from course: {e}")
        return False
    finally:
        if connection:
            connection.close()

def get_learner_progress(learner_id, course_id):
    """Retrieve the progress of a learner in a specific course."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT Progress
                FROM CourseProgress
                WHERE LearnerID = %s AND CourseID = %s
            """
            cursor.execute(query, (learner_id, course_id))
            return cursor.fetchone()
    except Error as e:
        print(f"Error retrieving learner progress: {e}")
        return None
    finally:
        connection.close()

def update_learner_progress(learner_id, course_id, progress):
    """Update the progress of a learner in a specific course."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE CourseProgress
                SET Progress = %s
                WHERE LearnerID = %s AND CourseID = %s
            """
            cursor.execute(query, (progress, learner_id, course_id))
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error updating learner progress: {e}")
        return False
    finally:
        connection.close()

def search_learners(search_term):
    """Search learners by ID, name or email."""
    connection = create_connection()
    if not connection:
        return []
    
    search_pattern = f'%{search_term}%'
    
    try:
        try:
            learner_id = int(search_term)
            id_search = True
        except ValueError:
            id_search = False
        
        with connection.cursor(dictionary=True) as cursor:
            if id_search:
                query = """
                    SELECT l.LearnerID, l.LearnerName, u.Email, l.PhoneNumber
                    FROM Learners l
                    JOIN Users u ON l.UserID = u.UserID
                    WHERE l.LearnerID = %s OR l.LearnerName LIKE %s OR u.Email LIKE %s
                    ORDER BY l.LearnerName
                """
                cursor.execute(query, (learner_id, search_pattern, search_pattern))
            else:
                query = """
                    SELECT l.LearnerID, l.LearnerName, u.Email, l.PhoneNumber
                    FROM Learners l
                    JOIN Users u ON l.UserID = u.UserID
                    WHERE l.LearnerName LIKE %s OR u.Email LIKE %s
                    ORDER BY l.LearnerName
                """
                cursor.execute(query, (search_pattern, search_pattern))
                
            return cursor.fetchall()
    except Error as e:
        print(f"Error searching learners: {e}")
        return []
    finally:
        connection.close()