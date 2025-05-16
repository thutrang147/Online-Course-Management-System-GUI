from utils.db_connector import create_connection
from mysql.connector import Error

def enroll_learner(learner_id, course_id):
    """Enroll a learner in a course."""
    connection = create_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Check if already enrolled
            check_query = "SELECT 1 FROM Enrollments WHERE LearnerID = %s AND CourseID = %s"
            cursor.execute(check_query, (learner_id, course_id))
            if cursor.fetchone():
                return True  # Already enrolled
            
            # Insert enrollment record
            query = "INSERT INTO Enrollments (LearnerID, CourseID, EnrollmentDate) VALUES (%s, %s, NOW())"
            cursor.execute(query, (learner_id, course_id))
            connection.commit()
            print(f"Debug - Enrolled learner {learner_id} in course {course_id}")
            return True
    except Error as e:
        print(f"Error enrolling learner: {e}")
        return False
    finally:
        connection.close()

def get_enrollments_by_learner(learner_id):
    """Get all enrollments for a specific learner with course details and progress."""
    connection = create_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
            SELECT e.EnrollmentID, e.CourseID, e.LearnerID, e.EnrollmentDate,
                   c.CourseName, c.CourseDescription,
                   i.InstructorName,
                   (SELECT COUNT(*) FROM Lectures WHERE CourseID = c.CourseID) as TotalLectures,
                   (SELECT COUNT(*) FROM LectureViews lv 
                    JOIN Lectures l ON lv.LectureID = l.LectureID
                    WHERE lv.LearnerID = e.LearnerID AND l.CourseID = e.CourseID) as CompletedLectures
            FROM Enrollments e
            JOIN Courses c ON e.CourseID = c.CourseID
            LEFT JOIN Instructors i ON c.InstructorID = i.InstructorID
            WHERE e.LearnerID = %s
            """
            cursor.execute(query, (learner_id,))
            enrollments = cursor.fetchall()
            
            print(f"Debug - SQL query executed for learner_id={learner_id}, found {len(enrollments)} enrollments")
            
            # Calculate progress percentage for each enrollment
            for enrollment in enrollments:
                total = enrollment['TotalLectures']
                completed = enrollment['CompletedLectures']
                if total > 0:
                    enrollment['ProgressPercentage'] = round((completed / total) * 100)
                else:
                    enrollment['ProgressPercentage'] = 0
                    
            return enrollments
    except Error as e:
        print(f"Error getting enrollments for learner: {e}")
        return []
    finally:
        connection.close()

def get_enrollments_by_course(course_id):
    """Get all enrollments for a specific course with learner details."""
    connection = create_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
            SELECT e.EnrollmentID, e.CourseID, e.LearnerID, e.EnrollmentDate,
                   l.LearnerName, l.Email,
                   (SELECT COUNT(*) FROM Lectures WHERE CourseID = e.CourseID) as TotalLectures,
                   (SELECT COUNT(*) FROM LectureViews lv 
                    JOIN Lectures lec ON lv.LectureID = lec.LectureID
                    WHERE lv.LearnerID = e.LearnerID AND lec.CourseID = e.CourseID) as CompletedLectures
            FROM Enrollments e
            JOIN Learners l ON e.LearnerID = l.LearnerID
            WHERE e.CourseID = %s
            """
            cursor.execute(query, (course_id,))
            enrollments = cursor.fetchall()
            
            # Calculate progress percentage for each enrollment
            for enrollment in enrollments:
                total = enrollment['TotalLectures']
                completed = enrollment['CompletedLectures']
                if total > 0:
                    enrollment['ProgressPercentage'] = round((completed / total) * 100)
                else:
                    enrollment['ProgressPercentage'] = 0
                    
            return enrollments
    except Error as e:
        print(f"Error getting enrollments for course: {e}")
        return []
    finally:
        connection.close()

def get_enrollment(learner_id, course_id):
    """Check if a learner is enrolled in a specific course."""
    connection = create_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
            SELECT EnrollmentID, LearnerID, CourseID, EnrollmentDate
            FROM Enrollments
            WHERE LearnerID = %s AND CourseID = %s
            """
            cursor.execute(query, (learner_id, course_id))
            return cursor.fetchone()
    except Error as e:
        print(f"Error checking enrollment: {e}")
        return None
    finally:
        connection.close()

def get_enrollment_count():
    """Get the total number of enrollments."""
    connection = create_connection()
    if not connection:
        return 0
    
    try:
        with connection.cursor() as cursor:
            query = "SELECT COUNT(*) FROM Enrollments"
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
    except Error as e:
        print(f"Error getting enrollment count: {e}")
        return 0
    finally:
        connection.close()

def get_recent_enrollments(limit=10):
    """Get recent enrollments with learner and course details."""
    connection = create_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
            SELECT e.EnrollmentID, e.LearnerID, e.CourseID, e.EnrollmentDate,
                   l.LearnerName, c.CourseName
            FROM Enrollments e
            JOIN Learners l ON e.LearnerID = l.LearnerID
            JOIN Courses c ON e.CourseID = c.CourseID
            ORDER BY e.EnrollmentDate DESC
            LIMIT %s
            """
            cursor.execute(query, (limit,))
            return cursor.fetchall()
    except Error as e:
        print(f"Error getting recent enrollments: {e}")
        return []
    finally:
        connection.close()

def update_enrollment_status(enrollment_id, status):
    """Update the completion status of an enrollment."""
    connection = create_connection()
    if not connection:
        return False
    try:
        with connection.cursor() as cursor:
            query = "UPDATE Enrollments SET CompletionStatus = %s WHERE EnrollmentID = %s"
            cursor.execute(query, (status, enrollment_id))
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error updating enrollment status: {e}")
        return False
    finally:
        connection.close()

def mark_lecture_viewed(learner_id, lecture_id):
    """Mark a lecture as viewed by a learner."""
    connection = create_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # Check if already viewed
            check_query = "SELECT 1 FROM LectureViews WHERE LearnerID = %s AND LectureID = %s"
            cursor.execute(check_query, (learner_id, lecture_id))
            if cursor.fetchone():
                return True  # Already marked as viewed
                
            # Insert view record
            query = "INSERT INTO LectureViews (LearnerID, LectureID, ViewDate) VALUES (%s, %s, NOW())"
            cursor.execute(query, (learner_id, lecture_id))
            connection.commit()
            return True
    except Error as e:
        print(f"Error marking lecture as viewed: {e}")
        return False
    finally:
        connection.close()

def get_learner_progress(enrollment_id):
    """Retrieve progress for an enrollment."""
    connection = create_connection()
    if not connection:
        return None
    try:
        with connection.cursor(dictionary=True) as cursor: # add EnrollmentDate, EnrollmentID
            query = """
                SELECT 
                    E.EnrollmentID,
                    E.LearnerID, 
                    E.CourseID, 
                    E.EnrollmentDate, 
                    E.CompletionStatus, 
                    E.ProgressPercentage, 
                    COUNT(DISTINCT LV.LectureID) AS ViewedLectures, 
                    COUNT(DISTINCT L.LectureID) AS TotalLectures
                FROM Enrollments E
                LEFT JOIN LectureViews LV ON E.LearnerID = LV.LearnerID
                LEFT JOIN Lectures L ON E.CourseID = L.CourseID
                WHERE E.EnrollmentID = %s
                GROUP BY E.LearnerID, E.CourseID, E.CompletionStatus, E.ProgressPercentage
            """
            cursor.execute(query, (enrollment_id,))
            return cursor.fetchone()
    except Error as e:
        print(f"Error retrieving progress: {e}")
        return None
    finally:
        connection.close()

def get_course_progress_summary(course_id: int):
    """
    Retrieves a progress summary for all learners enrolled in a specific course
    by calling the GenerateCompletionSummary stored procedure.
    Returns:
        A list of dictionaries, where each dictionary represents a learner's
        enrollment and progress in that course. Returns an empty list on error.
        Example item: {'LearnerName': 'Alice', 'CourseName': 'Python Intro', 
                       'EnrollmentDate': datetime.date(2024, 1, 5), 
                       'CompletionStatus': 'In Progress', 'ProgressPercentage': 50}
    """
    connection = create_connection()
    if not connection:
        return []

    summary_data = []
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Call the stored procedure
            cursor.callproc('GenerateCompletionSummary', (course_id,))
            
            # Stored procedures that return result sets need to be handled by iterating over stored_results()
            # MySQL Connector/Python returns one result set per SELECT statement in the SP.
            # Your SP has one SELECT.
            for result_set in cursor.stored_results():
                summary_data = result_set.fetchall() # fetchall() from the result_set object
                break # Assuming only one result set from this SP
            
    except Error as e:
        print(f"Error generating course completion summary for course ID {course_id}: {e}")
        # summary_data remains []
    finally:
        if connection and connection.is_connected():
            connection.close()
    return summary_data

def get_all_enrollments_detailed():
    """
    Retrieves all enrollment records, including learner names and course names.
    Returns:
        list: A list of dictionaries, where each dictionary represents an enrollment
              and includes 'EnrollmentID', 'LearnerName', 'CourseName', 'EnrollmentDate',
              'CompletionStatus', and 'ProgressPercentage'.
              Returns an empty list if no enrollments are found or an error occurs.
        Example item:
            {
                'EnrollmentID': 1, 
                'LearnerName': 'Alice Wonderland', 
                'CourseName': 'Introduction to Python', 
                'EnrollmentDate': datetime.date(2024, 1, 5), 
                'CompletionStatus': 'In Progress', 
                'ProgressPercentage': 50
            }
    """
    connection = create_connection()
    if not connection:
        return []

    enrollments_data = []
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = """
                SELECT 
                    E.EnrollmentID,
                    L.LearnerName,
                    C.CourseName,
                    E.EnrollmentDate,
                    E.CompletionStatus,
                    E.ProgressPercentage,
                    E.LearnerID,  -- Included for potential further use if needed
                    E.CourseID    -- Included for potential further use if needed
                FROM Enrollments E
                JOIN Learners L ON E.LearnerID = L.LearnerID
                JOIN Courses C ON E.CourseID = C.CourseID
                ORDER BY E.EnrollmentDate DESC, L.LearnerName ASC, C.CourseName ASC;
            """
            cursor.execute(query)
            enrollments_data = cursor.fetchall()
            
    except Error as e:
        print(f"Error retrieving all detailed enrollments: {e}")
        # enrollments_data remains []
    finally:
        if connection and connection.is_connected():
            connection.close()
    return enrollments_data

def get_enrollment_logs():
    """
    Retrieves all enrollment log records, including associated learner and course names.
    Returns:
        Returns an empty list if no logs are found or an error occurs.
        Example item:
            {
                'LogID': 1,
                'EnrollmentID': 101, # Could be None if original enrollment was deleted
                'LearnerName': 'Alice Wonderland', # Could be None if original learner was deleted
                'CourseName': 'Introduction to Python', # Could be None if original course was deleted
                'LogTime': datetime.datetime(2024, 1, 5, 10, 0, 0), # Timestamp object
                'ActionType': 'Enrollment Created'
            }
    """
    connection = create_connection()
    if not connection:
        return []

    logs_data = []
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Join EnrollmentLogs with Learners and Courses to get names.
            # Use LEFT JOINs because LearnerID or CourseID in EnrollmentLogs
            # might be NULL if the original entities were deleted (due to ON DELETE SET NULL).
            query = """
                SELECT 
                    EL.LogID,
                    EL.EnrollmentID,
                    L.LearnerName,    -- Fetched via LEFT JOIN
                    C.CourseName,     -- Fetched via LEFT JOIN
                    EL.LogTime,
                    EL.ActionType
                FROM EnrollmentLogs EL
                LEFT JOIN Learners L ON EL.LearnerID = L.LearnerID
                LEFT JOIN Courses C ON EL.CourseID = C.CourseID
                ORDER BY EL.LogTime DESC, EL.LogID DESC; -- Show newest logs first
            """
            cursor.execute(query)
            logs_data = cursor.fetchall()
            
    except Error as e:
        print(f"Error retrieving enrollment logs: {e}")
        # logs_data remains []
    finally:
        if connection and connection.is_connected():
            connection.close()
    return logs_data