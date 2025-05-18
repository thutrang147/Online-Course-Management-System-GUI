from utils.db_connector import create_connection
from mysql.connector import Error

def add_course(name, description, instructor_id):
    """Add a new course to the Courses table."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor() as cursor:
            print(f"Adding course: {name}, {description}, instructor_id={instructor_id}")
            query = "INSERT INTO Courses (CourseName, CourseDescription, InstructorID) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, description, instructor_id))
            connection.commit()
            return cursor.lastrowid
    except Error as e:
        print(f"Error adding course: {e}")
        return None
    finally:
        connection.close()

def get_course_by_id(course_id):
    """Retrieve a course by its ID."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Courses WHERE CourseID = %s"
            cursor.execute(query, (course_id,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error retrieving course: {e}")
        return None
    finally:
        connection.close()

def update_course_info(course_id, name=None, description=None, instructor_id=None):
    """Update course information."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            updates = []
            params = []
            if name:
                updates.append("CourseName = %s")
                params.append(name)
            if description:
                updates.append("CourseDescription = %s")
                params.append(description)
            if instructor_id:
                updates.append("InstructorID = %s")
                params.append(instructor_id)
            if not updates:
                return False
            params.append(course_id)
            query = f"UPDATE Courses SET {', '.join(updates)} WHERE CourseID = %s"
            cursor.execute(query, params)
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error updating course: {e}")
        return False
    finally:
        connection.close()

def list_all_courses():
    """Retrieve all courses with instructor names."""
    connection = create_connection()
    if not connection:
        return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT C.*, I.InstructorName 
                FROM Courses C 
                LEFT JOIN Instructors I ON C.InstructorID = I.InstructorID
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        print(f"Error listing courses: {e}")
        return []
    finally:
        connection.close()

def get_courses_by_instructor(instructor_id):
    """Retrieve all courses by an instructor."""
    connection = create_connection()
    if not connection:
        return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Courses WHERE InstructorID = %s"
            cursor.execute(query, (instructor_id,))
            return cursor.fetchall()
    except Error as e:
        print(f"Error retrieving courses: {e}")
        return []
    finally:
        connection.close()

def list_courses_with_details():
    """List all courses with instructor details and enrollment count."""
    connection = create_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
            SELECT c.CourseID, c.CourseName, c.CourseDescription as Description, c.InstructorID,
                   i.InstructorName, 
                   (SELECT COUNT(*) FROM Enrollments WHERE CourseID = c.CourseID) as EnrollmentCount
            FROM Courses c
            LEFT JOIN Instructors i ON c.InstructorID = i.InstructorID
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        print(f"Error listing courses with details: {e}")
        return []
    finally:
        connection.close()

def list_active_courses():
    """List all active courses (having at least one enrollment)."""
    connection = create_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
            SELECT c.CourseID, c.CourseName, c.CourseDescription, c.InstructorID,
                   i.InstructorName, 
                   COUNT(e.EnrollmentID) as EnrollmentCount
            FROM Courses c
            LEFT JOIN Instructors i ON c.InstructorID = i.InstructorID
            JOIN Enrollments e ON c.CourseID = e.CourseID
            GROUP BY c.CourseID
            HAVING EnrollmentCount > 0
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        print(f"Error listing active courses: {e}")
        return []
    finally:
        connection.close()

def get_featured_courses(limit=3):
    """Get a limited number of featured courses for the homepage."""
    connection = create_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
            SELECT c.CourseID, c.CourseName, c.CourseDescription, c.InstructorID,
                   i.InstructorName
            FROM Courses c
            LEFT JOIN Instructors i ON c.InstructorID = i.InstructorID
            ORDER BY c.CourseID DESC  -- Newest courses first
            LIMIT %s
            """
            cursor.execute(query, (limit,))
            return cursor.fetchall()
    except Error as e:
        print(f"Error getting featured courses: {e}")
        return []
    finally:
        connection.close()

def get_recommended_courses(learner_id, limit=3):
    """Get recommended courses for a learner based on their enrollments."""
    connection = create_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Get courses that the learner is not enrolled in
            query = """
            SELECT c.CourseID, c.CourseName, c.CourseDescription, c.InstructorID,
                   i.InstructorName
            FROM Courses c
            LEFT JOIN Instructors i ON c.InstructorID = i.InstructorID
            WHERE c.CourseID NOT IN (
                SELECT CourseID FROM Enrollments WHERE LearnerID = %s
            )
            LIMIT %s
            """
            cursor.execute(query, (learner_id, limit))
            return cursor.fetchall()
    except Error as e:
        print(f"Error getting recommended courses: {e}")
        return []
    finally:
        connection.close()

def delete_course(course_id):
    """Delete a course from the Courses table."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            query = "DELETE FROM Courses WHERE CourseID = %s"
            cursor.execute(query, (course_id,))
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error deleting course: {e}")
        return False
    finally:
        connection.close()

def search_courses(search_term):
    """Search courses by name, description, instructor name or ID."""
    connection = create_connection()
    if not connection:
        return []
    
    search_pattern = f'%{search_term}%'
    
    try:
        try:
            course_id = int(search_term)
            id_search = True
        except ValueError:
            id_search = False
            
        with connection.cursor(dictionary=True) as cursor:
            if id_search:
                query = """
                    SELECT c.CourseID, c.CourseName, c.CourseDescription as Description, 
                           i.InstructorID, i.InstructorName
                    FROM Courses c
                    LEFT JOIN Instructors i ON c.InstructorID = i.InstructorID
                    WHERE c.CourseID = %s 
                       OR c.CourseName LIKE %s
                       OR c.CourseDescription LIKE %s
                       OR i.InstructorName LIKE %s
                    ORDER BY c.CourseName
                """
                cursor.execute(query, (course_id, search_pattern, search_pattern, search_pattern))
            else:
                query = """
                    SELECT c.CourseID, c.CourseName, c.CourseDescription as Description, 
                           i.InstructorID, i.InstructorName
                    FROM Courses c
                    LEFT JOIN Instructors i ON c.InstructorID = i.InstructorID
                    WHERE c.CourseName LIKE %s
                       OR c.CourseDescription LIKE %s
                       OR i.InstructorName LIKE %s
                    ORDER BY c.CourseName
                """
                cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            return cursor.fetchall()
    except Error as e:
        print(f"Error searching courses: {e}")
        return []
    finally:
        connection.close()
