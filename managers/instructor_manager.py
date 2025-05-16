from utils.db_connector import create_connection
from mysql.connector import Error

def add_instructor(name, expertise, email, password):
    """Add a new instructor with user account."""
    from managers import user_manager
    
    connection = create_connection()
    if not connection:
        return None
    
    try:
        connection.start_transaction()
        
        # 1. Create user account first
        user_id = user_manager.create_user(email, password, 'instructor')
        if not user_id:
            connection.rollback()
            return None
        
        # 2. Create instructor profile
        with connection.cursor() as cursor:
            query = "INSERT INTO Instructors (InstructorName, Expertise, Email, UserID) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (name, expertise, email, user_id))
            instructor_id = cursor.lastrowid
            
        connection.commit()
        return instructor_id
        
    except Error as e:
        connection.rollback()
        print(f"Error adding instructor: {e}")
        return None
    finally:
        connection.close()

def get_instructor_by_id(instructor_id):
    """Retrieve an instructor by their ID."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Instructors WHERE InstructorID = %s"
            cursor.execute(query, (instructor_id,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error retrieving instructor: {e}")
        return None
    finally:
        connection.close()

def update_instructor_info(instructor_id, name=None, expertise=None, email=None):
    """Update instructor information."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            updates = []
            params = []
            if name:
                updates.append("InstructorName = %s")
                params.append(name)
            if expertise:
                updates.append("Expertise = %s")
                params.append(expertise)
            if email:
                updates.append("Email = %s")
                params.append(email)
            if not updates:
                return False
            params.append(instructor_id)
            query = f"UPDATE Instructors SET {', '.join(updates)} WHERE InstructorID = %s"
            cursor.execute(query, params)
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error updating instructor: {e}")
        return False
    finally:
        connection.close()

def list_all_instructors():
    """Retrieve all instructors."""
    connection = create_connection()
    if not connection:
        return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Instructors"
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        print(f"Error listing instructors: {e}")
        return []
    finally:
        connection.close()

def delete_instructor(instructor_id):
    """Delete an instructor by their ID."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            query = "DELETE FROM Instructors WHERE InstructorID = %s"
            cursor.execute(query, (instructor_id,))
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error deleting instructor: {e}")
        return False
    finally:
        connection.close()

def get_instructor_by_email(email):
    """Retrieve an instructor by their email."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Instructors WHERE Email = %s"
            cursor.execute(query, (email,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error retrieving instructor: {e}")
        return None
    finally:
        connection.close()

def check_password(instructor_id, password):
    """Check if the provided password matches the stored password for the instructor."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            query = "SELECT Password FROM Instructors WHERE InstructorID = %s"
            cursor.execute(query, (instructor_id,))
            result = cursor.fetchone()
            if result and result['Password'] == password:
                return True
            return False
    except Error as e:
        print(f"Error checking password: {e}")
        return False
    finally:
        connection.close()

def update_password(instructor_id, new_password):
    """Update the password for the instructor."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            query = "UPDATE Instructors SET Password = %s WHERE InstructorID = %s"
            cursor.execute(query, (new_password, instructor_id))
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error updating password: {e}")
        return False
    finally:
        connection.close()

def get_instructor_by_user_id(user_id):
    """Retrieve an instructor by their User ID."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Instructors WHERE UserID = %s"
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error retrieving instructor by user ID: {e}")
        return None
    finally:
        connection.close()

def get_all_instructors_workload():
    """Get workload statistics for all instructors."""
    connection = create_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
            SELECT i.InstructorID, i.InstructorName, i.Expertise,
                   COUNT(DISTINCT c.CourseID) as CourseCount,
                   COUNT(DISTINCT e.LearnerID) as LearnerCount,
                   COUNT(DISTINCT l.LectureID) as LectureCount
            FROM Instructors i
            LEFT JOIN Courses c ON i.InstructorID = c.InstructorID
            LEFT JOIN Enrollments e ON c.CourseID = e.CourseID
            LEFT JOIN Lectures l ON c.CourseID = l.CourseID
            GROUP BY i.InstructorID
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        print(f"Error getting instructor workload: {e}")
        return []
    finally:
        connection.close()
