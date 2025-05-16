from utils.db_connector import create_connection
from mysql.connector import Error

def add_lecture(course_id, title, content):
    """Add a new lecture to the Lectures table."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor() as cursor:
            query = "INSERT INTO Lectures (CourseID, Title, Content) VALUES (%s, %s, %s)"
            cursor.execute(query, (course_id, title, content))
            connection.commit()
            return cursor.lastrowid
    except Error as e:
        print(f"Error adding lecture: {e}")
        return None
    finally:
        connection.close()

def get_lecture_by_id(lecture_id):
    """Retrieve a lecture by its ID."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Lectures WHERE LectureID = %s"
            cursor.execute(query, (lecture_id,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error retrieving lecture: {e}")
        return None
    finally:
        connection.close()

def get_lectures_by_course(course_id):
    """Retrieve all lectures for a course, ordered by LectureID."""
    connection = create_connection()
    if not connection:
        return []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Lectures WHERE CourseID = %s ORDER BY LectureID"
            cursor.execute(query, (course_id,))
            return cursor.fetchall()
    except Error as e:
        print(f"Error retrieving lectures: {e}")
        return []
    finally:
        connection.close()

def update_lecture_content(lecture_id, title=None, content=None):
    """Update lecture content."""
    connection = create_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            updates = []
            params = []
            
            if title is not None:
                updates.append("Title = %s")
                params.append(title)
            if content is not None:
                updates.append("Content = %s")
                params.append(content)
                
            if not updates:  # No fields to update
                return True
                
            query = f"UPDATE Lectures SET {', '.join(updates)} WHERE LectureID = %s"
            params.append(lecture_id)
            
            cursor.execute(query, params)
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error updating lecture: {e}")
        return False
    finally:
        connection.close()

def delete_lecture(lecture_id):
    """Delete a lecture from the Lectures table."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            query = "DELETE FROM Lectures WHERE LectureID = %s"
            cursor.execute(query, (lecture_id,))
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error deleting lecture: {e}")
        return False
    finally:
        connection.close()

def get_lectures_with_view_status(learner_id, course_id):
    """Get lectures for a course with view status for a specific learner."""
    connection = create_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
            SELECT l.LectureID, l.CourseID, l.Title, l.Content,
                   CASE WHEN lv.LectureID IS NOT NULL THEN TRUE ELSE FALSE END as Viewed,
                   lv.ViewDate
            FROM Lectures l
            LEFT JOIN LectureViews lv ON l.LectureID = lv.LectureID AND lv.LearnerID = %s
            WHERE l.CourseID = %s
            ORDER BY l.LectureID
            """
            cursor.execute(query, (learner_id, course_id))
            return cursor.fetchall()
    except Error as e:
        print(f"Error getting lectures with view status: {e}")
        return []
    finally:
        connection.close()