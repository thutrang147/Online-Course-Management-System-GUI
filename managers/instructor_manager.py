from utils.db_connector import create_connection
from mysql.connector import Error
from managers import user_manager
import bcrypt

def add_instructor(name, expertise, email, password):
    """Add a new instructor with user account."""
    connection = create_connection()
    if not connection:
        return None
    
    try:
        connection.start_transaction()
        
        # 1. Create user first
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_id = user_manager.create_user(email, hashed, 'instructor')
        if not user_id:
            connection.rollback()
            print("Failed to create user account")
            return None
            
        # 2. Create instructor profile
        with connection.cursor() as cursor:
            query = "INSERT INTO Instructors (InstructorName, Expertise, UserID) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, expertise, user_id))
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
    """Get instructor information by ID including email."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            # JOIN với Users để lấy email
            query = """
                SELECT i.InstructorID, i.InstructorName, u.Email, i.Expertise, i.UserID
                FROM Instructors i
                JOIN Users u ON i.UserID = u.UserID
                WHERE i.InstructorID = %s
            """
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
        connection.start_transaction()
        
        # Update instructor table
        instructor_updates = []
        instructor_params = []
        
        if name:
            instructor_updates.append("InstructorName = %s")
            instructor_params.append(name)
            
        if expertise:
            instructor_updates.append("Expertise = %s")
            instructor_params.append(expertise)
            
        if instructor_updates:
            instructor_params.append(instructor_id)
            instructor_query = f"UPDATE Instructors SET {', '.join(instructor_updates)} WHERE InstructorID = %s"
            
            with connection.cursor() as cursor:
                cursor.execute(instructor_query, instructor_params)
        
        # Update email in Users table if needed
        if email:
            # Get the UserID from Instructors table
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT UserID FROM Instructors WHERE InstructorID = %s", (instructor_id,))
                result = cursor.fetchone()
                
                if result and 'UserID' in result:
                    user_id = result['UserID']
                    cursor.execute("UPDATE Users SET Email = %s WHERE UserID = %s", (email, user_id))
        
        connection.commit()
        return True
        
    except Error as e:
        connection.rollback()
        print(f"Error updating instructor: {e}")
        return False
    finally:
        connection.close()

def list_all_instructors():
    """Get all instructors with their information including email from Users table."""
    connection = create_connection()
    if not connection:
        return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            # JOIN với Users để lấy email
            query = """
                SELECT i.InstructorID, i.InstructorName, u.Email, i.Expertise
                FROM Instructors i
                JOIN Users u ON i.UserID = u.UserID
                ORDER BY i.InstructorName
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        print(f"Error retrieving instructors: {e}")
        return []
    finally:
        connection.close()

def delete_instructor(instructor_id):
    """Delete an instructor and associated user account."""
    connection = create_connection()
    if not connection:
        return False
    
    try:
        connection.start_transaction()
        
        # Get the UserID first
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT UserID FROM Instructors WHERE InstructorID = %s", (instructor_id,))
            result = cursor.fetchone()
            
            if not result or 'UserID' not in result:
                connection.rollback()
                return False
                
            user_id = result['UserID']
            
            # Delete from Instructors first due to foreign key constraint
            cursor.execute("DELETE FROM Instructors WHERE InstructorID = %s", (instructor_id,))
            
            # Then delete the User (will cascade to delete related data)
            cursor.execute("DELETE FROM Users WHERE UserID = %s", (user_id,))
            
        connection.commit()
        return True
        
    except Error as e:
        connection.rollback()
        print(f"Error deleting instructor: {e}")
        return False
    finally:
        connection.close()

def get_instructor_by_email(email):
    """Get instructor details by email."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            # JOIN với Users để tìm theo email
            query = """
                SELECT i.*
                FROM Instructors i
                JOIN Users u ON i.UserID = u.UserID
                WHERE u.Email = %s
            """
            cursor.execute(query, (email,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error getting instructor by email: {e}")
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
    """Get all instructors with their course count."""
    connection = create_connection()
    if not connection:
        return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT i.InstructorID, i.InstructorName, u.Email,
                       COUNT(c.CourseID) as CourseCount
                FROM Instructors i
                JOIN Users u ON i.UserID = u.UserID
                LEFT JOIN Courses c ON i.InstructorID = c.InstructorID
                GROUP BY i.InstructorID, i.InstructorName, u.Email
                ORDER BY CourseCount DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        print(f"Error retrieving instructor workload: {e}")
        return []
    finally:
        connection.close()
