DROP DATABASE IF EXISTS OnlineCourses;
CREATE DATABASE OnlineCourses;
USE OnlineCourses;

-- ============================================================================
-- TABLE DEFINITIONS (Based on Section 2 Design)
-- Defines the core tables for learners, instructors, courses, lectures,
-- enrollments, and lecture views. Includes constraints and referential integrity.
-- ============================================================================

-- Learners Table: Manages learner information.
CREATE TABLE Learners (
    LearnerID INT AUTO_INCREMENT PRIMARY KEY,
    LearnerName VARCHAR(100) NOT NULL,       -- Learner's full name (Required)
    Email VARCHAR(100) UNIQUE NOT NULL,      -- Learner's email (Unique, Required)
    PhoneNumber VARCHAR(20) UNIQUE,          -- Learner's phone number (Unique, Optional)
    UserID INT UNIQUE,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- Instructors Table: Manages instructor information.
CREATE TABLE Instructors (
    InstructorID INT AUTO_INCREMENT PRIMARY KEY,
    InstructorName VARCHAR(100) NOT NULL,    -- Instructor's full name (Required)
    Expertise VARCHAR(100),                 -- Instructor's area of expertise (Optional)
    Email VARCHAR(100) UNIQUE NOT NULL,      -- Instructor's email (Unique, Required)
    UserID INT UNIQUE,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- Courses Table: Manages course information.
CREATE TABLE Courses (
    CourseID INT AUTO_INCREMENT PRIMARY KEY,
    CourseName VARCHAR(100) NOT NULL,        -- Course title (Required)
    CourseDescription TEXT,                 -- Detailed description of the course (Optional)
    InstructorID INT,                       -- Assigned instructor (Optional, allows flexibility)
    FOREIGN KEY (InstructorID) REFERENCES Instructors(InstructorID)
        ON DELETE SET NULL  -- If instructor is deleted, set InstructorID to NULL in Courses
        ON UPDATE CASCADE   -- If InstructorID changes, update it in Courses
);

-- Lectures Table: Manages lecture content within courses.
CREATE TABLE Lectures (
    LectureID INT AUTO_INCREMENT PRIMARY KEY,
    CourseID INT NOT NULL,                   -- Associated course (Required)
    Title VARCHAR(200) NOT NULL,             -- Lecture title (Required)
    Content TEXT,                           -- Lecture content (Optional)
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
        ON DELETE CASCADE   -- If a course is deleted, its lectures are also deleted
        ON UPDATE CASCADE   -- If CourseID changes, update it in Lectures
);

-- Enrollments Table: Manages learner enrollments in courses and tracks progress.
CREATE TABLE Enrollments (
    EnrollmentID INT AUTO_INCREMENT PRIMARY KEY,
    LearnerID INT NOT NULL,                  -- Enrolled learner (Required)
    CourseID INT NOT NULL,                   -- Enrolled course (Required)
    EnrollmentDate DATE NOT NULL,            -- Date of enrollment (Required)
    CompletionStatus ENUM('Not Started', 'In Progress', 'Completed') DEFAULT 'Not Started' NOT NULL, -- Course completion status
    ProgressPercentage TINYINT UNSIGNED DEFAULT 0 NOT NULL, -- Completion percentage (0-100)
    FOREIGN KEY (LearnerID) REFERENCES Learners(LearnerID)
        ON DELETE CASCADE   -- If a learner is deleted, their enrollments are also deleted
        ON UPDATE CASCADE,  -- If LearnerID changes, update it in Enrollments
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
        ON DELETE CASCADE   -- If a course is deleted, its enrollments are also deleted
        ON UPDATE CASCADE   -- If CourseID changes, update it in Enrollments
);

-- LectureViews Table: Records which lectures a learner has viewed.
CREATE TABLE LectureViews (
    LearnerID INT NOT NULL,
    LectureID INT NOT NULL,
    ViewDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Date and time the lecture was viewed (Required)
    PRIMARY KEY (LearnerID, LectureID),     -- Ensures one view record per learner per lecture
    FOREIGN KEY (LearnerID) REFERENCES Learners(LearnerID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (LectureID) REFERENCES Lectures(LectureID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Enrollment Log Table: Records enrollment events for auditing purposes.
CREATE TABLE EnrollmentLogs (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    EnrollmentID INT NULL,                     -- Reference to the enrollment record (allows NULL if enrollment is deleted)
    LearnerID INT NULL,                        -- Allows NULL if learner is deleted
    CourseID INT NULL,                         -- Allows NULL if course is deleted
    LogTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Time of the log entry
    ActionType VARCHAR(50) DEFAULT 'Enrollment Created' NOT NULL, -- Type of action logged
    FOREIGN KEY (EnrollmentID) REFERENCES Enrollments(EnrollmentID) ON DELETE SET NULL, -- Keep log even if enrollment deleted
    FOREIGN KEY (LearnerID) REFERENCES Learners(LearnerID) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID) ON DELETE SET NULL ON UPDATE CASCADE
);

-- ============================================================================
-- INDEXES
-- Creates indexes to improve query performance.
-- ============================================================================
CREATE INDEX idx_CourseName ON Courses(CourseName);                -- Speeds up searching courses by name.
CREATE INDEX idx_Enrollments_LearnerID ON Enrollments(LearnerID);   -- Speeds up finding enrollments for a specific learner.
CREATE INDEX idx_Enrollments_CourseID ON Enrollments(CourseID);    -- Speeds up finding enrollments for a specific course.
CREATE INDEX idx_Lectures_CourseID ON Lectures(CourseID);          -- Speeds up finding lectures for a specific course.

-- ============================================================================
-- VIEWS
-- Creates views to provide simplified perspectives on the data.
-- Corresponds to Section 3.4 implementation.
-- ============================================================================

-- View: Shows learner's course enrollment details and progress.
CREATE VIEW LearnerCourseProgress AS
SELECT
    l.LearnerName,
    c.CourseName,
    e.EnrollmentDate,
    e.CompletionStatus,
    e.ProgressPercentage
FROM Enrollments e
JOIN Learners l ON e.LearnerID = l.LearnerID
JOIN Courses c ON e.CourseID = c.CourseID;

-- View: Shows the teaching load (number of courses) for each instructor.
CREATE VIEW InstructorTeachingLoad AS
SELECT
    i.InstructorName,
    COUNT(c.CourseID) AS NumberOfCourses
FROM Instructors i
LEFT JOIN Courses c ON i.InstructorID = c.InstructorID -- Use LEFT JOIN to include instructors with no courses
GROUP BY i.InstructorID, i.InstructorName;

-- ============================================================================
-- USER DEFINED FUNCTIONS
-- Defines custom functions for reusable calculations.
-- Note: Function is defined before the SP/Trigger that might use it.
-- ============================================================================

-- Calculates the completion rate for a learner in a specific course.
DELIMITER $$
CREATE FUNCTION CalculateCompletionRate(p_learner_id INT, p_course_id INT)
RETURNS DECIMAL(5,2) -- Returns a decimal percentage (e.g., 95.50)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total_lectures INT DEFAULT 0;
    DECLARE viewed_lectures INT DEFAULT 0;
    DECLARE completion_rate DECIMAL(5,2) DEFAULT 0.00;

    -- Get total number of lectures in the course
    SELECT COUNT(*) INTO total_lectures
    FROM Lectures
    WHERE CourseID = p_course_id;

    -- Get number of unique lectures viewed by the learner in that course
    SELECT COUNT(DISTINCT LV.LectureID) INTO viewed_lectures
    FROM LectureViews LV
    JOIN Lectures L ON LV.LectureID = L.LectureID
    WHERE LV.LearnerID = p_learner_id AND L.CourseID = p_course_id;

    -- Calculate rate, avoiding division by zero
    IF total_lectures > 0 THEN
        SET completion_rate = ROUND((viewed_lectures / total_lectures) * 100, 2);
    END IF;

    RETURN completion_rate;
END$$
DELIMITER ;

-- ============================================================================
-- STORED PROCEDURES
-- Defines stored procedures to encapsulate reusable logic.
-- ============================================================================

-- Enrolls a learner into a course, preventing duplicates.
DELIMITER //
CREATE PROCEDURE EnrollLearner(IN p_learner_id INT, IN p_course_id INT)
BEGIN
    -- Check if the learner is already enrolled
    IF NOT EXISTS (SELECT 1 FROM Enrollments WHERE LearnerID = p_learner_id AND CourseID = p_course_id) THEN
        INSERT INTO Enrollments (LearnerID, CourseID, EnrollmentDate, CompletionStatus, ProgressPercentage)
        VALUES (p_learner_id, p_course_id, CURDATE(), 'Not Started', 0);
    ELSE
        -- Signal an error if already enrolled
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Learner is already enrolled in this course.';
    END IF;
END //
DELIMITER ;

-- Procedure: Generates a summary report of course completion status for a specific course.
DELIMITER //
CREATE PROCEDURE GenerateCompletionSummary(IN p_course_id INT)
BEGIN
    SELECT
        l.LearnerName,
        c.CourseName,
        e.EnrollmentDate,
        e.CompletionStatus,
        e.ProgressPercentage
    FROM Enrollments e
    JOIN Learners l ON e.LearnerID = l.LearnerID
    JOIN Courses c ON e.CourseID = c.CourseID
    WHERE e.CourseID = p_course_id -- Filter by the specified course
    ORDER BY l.LearnerName;
END //
DELIMITER ;

-- ============================================================================
-- TRIGGERS
-- Defines triggers for automatic actions based on data changes.
-- ============================================================================


-- Logs a new enrollment record into EnrollmentLogs after insertion.
DELIMITER //
CREATE TRIGGER LogNewEnrollment AFTER INSERT ON Enrollments
FOR EACH ROW
BEGIN
    INSERT INTO EnrollmentLogs (EnrollmentID, LearnerID, CourseID)
    VALUES (NEW.EnrollmentID, NEW.LearnerID, NEW.CourseID);
END //
DELIMITER ;

-- Ensures that a lecture view date is not earlier than the enrollment date.
DELIMITER $$
CREATE TRIGGER CheckViewDateAfterEnrollment
BEFORE INSERT ON LectureViews
FOR EACH ROW
BEGIN
    DECLARE enroll_date DATE;

    -- Get the enrollment date for the learner in the course containing this lecture
    SELECT EnrollmentDate INTO enroll_date
    FROM Enrollments E
    JOIN Lectures L ON E.CourseID = L.CourseID
    WHERE E.LearnerID = NEW.LearnerID AND L.LectureID = NEW.LectureID
    LIMIT 1; -- Assumes learner enrolls only once per course

    -- Compare the date part of the view date with the enrollment date
    IF DATE(NEW.ViewDate) < enroll_date THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ViewDate must be on or after EnrollmentDate';
    END IF;
END$$
DELIMITER ;


-- Trigger: Automatically updates the enrollment progress after a new lecture view is inserted.

DELIMITER $$
CREATE TRIGGER UpdateEnrollmentProgress AFTER INSERT ON LectureViews
FOR EACH ROW
BEGIN
    DECLARE v_course_id INT;
    DECLARE v_completion_rate DECIMAL(5,2);
    DECLARE v_completion_status ENUM('Not Started', 'In Progress', 'Completed');

    -- Get the CourseID for the lecture just viewed
    SELECT CourseID INTO v_course_id
    FROM Lectures
    WHERE LectureID = NEW.LectureID;

    -- Calculate the new completion rate using the function
    SET v_completion_rate = CalculateCompletionRate(NEW.LearnerID, v_course_id);

    -- Determine the new completion status based on the rate
    IF v_completion_rate = 100.00 THEN
        SET v_completion_status = 'Completed';
    ELSEIF v_completion_rate > 0.00 THEN
        SET v_completion_status = 'In Progress';
    ELSE
        SET v_completion_status = 'Not Started';
    END IF;

    -- Update the corresponding enrollment record
    UPDATE Enrollments
    SET
        ProgressPercentage = v_completion_rate,
        CompletionStatus = v_completion_status
    WHERE
        LearnerID = NEW.LearnerID AND CourseID = v_course_id;
END$$
DELIMITER ;

-- ============================================================================
-- DATABASE SECURITY & ADMINISTRATION
-- Creates database users and grants specific privileges.
-- ============================================================================

-- Read-only user for learner-facing applications.
DROP USER IF EXISTS 'readonly_learner'@'%';
CREATE USER 'readonly_learner'@'%' IDENTIFIED BY 'studentPass123!';
-- Grant specific SELECT permissions
GRANT SELECT ON OnlineCourses.Learners TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.Instructors TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.Courses TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.Lectures TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.Enrollments TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.LectureViews TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.LearnerCourseProgress TO 'readonly_learner'@'%';
-- Grant EXECUTE permission on necessary functions/procedures
GRANT EXECUTE ON FUNCTION OnlineCourses.CalculateCompletionRate TO 'readonly_learner'@'%';
GRANT EXECUTE ON PROCEDURE OnlineCourses.EnrollLearner TO 'readonly_learner'@'%'; -- If learners self-enroll

-- Administrative user for management applications.
DROP USER IF EXISTS 'admin_app_user'@'%';
CREATE USER 'admin_app_user'@'%' IDENTIFIED BY 'complexAdminPass456!';
-- Grant specific DML and SELECT permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Learners TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Instructors TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Courses TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Lectures TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Enrollments TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.LectureViews TO 'admin_app_user'@'%';
GRANT SELECT ON OnlineCourses.EnrollmentLogs TO 'admin_app_user'@'%'; -- Read-only on logs
-- Grant SELECT on views
GRANT SELECT ON OnlineCourses.LearnerCourseProgress TO 'admin_app_user'@'%';
GRANT SELECT ON OnlineCourses.InstructorTeachingLoad TO 'admin_app_user'@'%';
-- Grant EXECUTE on necessary functions/procedures
GRANT EXECUTE ON FUNCTION OnlineCourses.CalculateCompletionRate TO 'admin_app_user'@'%';
GRANT EXECUTE ON PROCEDURE OnlineCourses.EnrollLearner TO 'admin_app_user'@'%';
GRANT EXECUTE ON PROCEDURE OnlineCourses.GenerateCompletionSummary TO 'admin_app_user'@'%';

-- Apply the privilege changes
FLUSH PRIVILEGES;

-- ============================================================================
-- SAMPLE DATA INSERTION
-- Populates the tables with sample data for testing.
-- ============================================================================

-- Insert Learners
INSERT INTO Learners (LearnerName, Email, PhoneNumber) VALUES
('Alice Wonderland', 'alice@example.com', '0901234001'), ('Bob The Builder', 'bob@example.com', '0901234002'),
('Charlie Chaplin', 'charlie@example.com', '0901234003'), ('Diana Prince', 'diana@example.com', '0901234004'),
('Ethan Hunt', 'ethan@example.com', '0901234005'), ('Fiona Shrek', 'fiona@example.com', '0901234006'),
('Gaius Julius Caesar', 'caesar@example.com', '0901234007'), ('Hermione Granger', 'hermione@example.com', '0901234008'),
('Indiana Jones', 'indy@example.com', '0901234009'), ('James Bond', 'bond@example.com', '0901234010');

-- Insert Instructors
INSERT INTO Instructors (InstructorName, Expertise, Email) VALUES
('Prof. Dumbledore', 'Advanced Magic', 'dumbledore@edu.example.com'), ('Dr. Ada Lovelace', 'Computer Science', 'ada@edu.example.com'),
('Mr. Miyagi', 'Karate Fundamentals', 'miyagi@edu.example.com'), ('Ms. Marie Curie', 'Physics & Chemistry', 'curie@edu.example.com'),
('Dr. Alan Turing', 'Cryptography & AI', 'turing@edu.example.com'), ('Prof. Minerva McGonagall', 'Transfiguration', 'mcgonagall@edu.example.com'),
('Mr. Sherlock Holmes', 'Deductive Reasoning', 'holmes@edu.example.com'), ('Ms. Jane Goodall', 'Primatology', 'goodall@edu.example.com'),
('Dr. Emmett Brown', 'Temporal Mechanics', 'docbrown@edu.example.com'), ('Prof. Severus Snape', 'Potions Master', 'snape@edu.example.com');

-- Insert Courses (Includes instructor name comments for readability)
INSERT INTO Courses (CourseName, CourseDescription, InstructorID) VALUES
('Introduction to Python', 'Learn Python basics, data types, and control flow.', 2), -- Ada Lovelace
('SQL for Beginners', 'Master fundamental SQL queries for data manipulation.', 2), -- Ada Lovelace
('Web Design Basics', 'Build and style simple web pages using HTML5 and CSS3.', 5), -- Alan Turing
('Introduction to AI', 'An overview of core AI concepts and algorithms.', 5), -- Alan Turing
('Relational Database Design', 'Learn database design principles, normalization, and ER modeling.', 2), -- Ada Lovelace
('Data Analysis with Python', 'Using Pandas and NumPy for data exploration.', 7), -- Sherlock Holmes
('JavaScript Essentials', 'Understand JavaScript basics for dynamic web pages.', 5), -- Alan Turing
('User Interface Design', 'Fundamentals of creating intuitive user interfaces.', 8), -- Jane Goodall
('Cybersecurity Fundamentals', 'Basic concepts of digital threats and defenses.', 5), -- Alan Turing
('The Art of Deduction', 'Sharpen your observation and logical reasoning skills.', 7); -- Sherlock Holmes

-- Insert Lectures
INSERT INTO Lectures (CourseID, Title, Content) VALUES
-- Course 1: Python (ID: 1) - 3 lectures
(1, 'Python Environment Setup', 'Installing Python and setting up your IDE.'),
(1, 'Variables and Data Types', 'Integers, Floats, Strings, Booleans.'),
(1, 'Basic Operators', 'Arithmetic, Comparison, Logical operators.'),
-- Course 2: SQL (ID: 2) - 3 lectures
(2, 'Introduction to Databases', 'What are databases? Relational model basics.'),
(2, 'SELECT Queries', 'Using SELECT, FROM, WHERE to retrieve data.'),
(2, 'Filtering Data', 'Using AND, OR, IN, BETWEEN, LIKE.'),
-- Course 3: Web Design (ID: 3) - 2 lectures
(3, 'HTML Fundamentals', 'Tags, Attributes, Basic page structure.'),
(3, 'CSS Basics', 'Selectors, Properties, Colors, Fonts.'),
-- Course 4: AI (ID: 4) - 2 lectures
(4, 'What is Artificial Intelligence?', 'History, Goals, Branches of AI.'),
(4, 'Types of Machine Learning', 'Supervised, Unsupervised, Reinforcement Learning.'),
-- Course 5: DB Design (ID: 5) - 2 lectures
(5, 'The Relational Model Revisited', 'Keys (Primary, Foreign), Relationships.'),
(5, 'Normalization (1NF, 2NF, 3NF)', 'Reducing data redundancy.');

-- Enroll Learners into Courses (Using direct INSERT with fixed dates)
-- NOTE: Inserting into Enrollments will trigger 'LogNewEnrollment'
INSERT INTO Enrollments (LearnerID, CourseID, EnrollmentDate, CompletionStatus, ProgressPercentage) VALUES
(1, 1, '2024-01-05', 'Not Started', 0), -- Alice, Python
(1, 2, '2024-01-10', 'Not Started', 0), -- Alice, SQL
(2, 1, '2024-01-15', 'Not Started', 0), -- Bob, Python
(2, 3, '2024-01-20', 'Not Started', 0), -- Bob, Web Design
(3, 4, '2024-02-01', 'Not Started', 0), -- Charlie, AI
(4, 5, '2024-02-05', 'Not Started', 0), -- Diana, DB Design
(5, 6, '2024-02-10', 'Not Started', 0), -- Ethan, Data Analysis
(6, 2, '2024-02-15', 'Not Started', 0), -- Fiona, SQL
(7, 7, '2024-03-01', 'Not Started', 0), -- Gaius, JavaScript
(8, 8, '2024-03-05', 'Not Started', 0), -- Hermione, UI/UX
(9, 9, '2024-03-10', 'Not Started', 0), -- Indiana, Cybersecurity
(10, 10, '2024-03-15', 'Not Started', 0), -- James, Deduction
(1, 5, '2024-02-08', 'Not Started', 0); -- Alice, DB Design (Enroll after Diana)

-- Record some lecture views
-- NOTE: Inserting into LectureViews triggers 'CheckViewDateAfterEnrollment' AND 'UpdateEnrollmentProgress'
-- Alice (Learner 1), Python Course (Course 1, Enrolled '2024-01-05', Lecture IDs: 1, 2, 3)
INSERT INTO LectureViews (LearnerID, LectureID, ViewDate) VALUES (1, 1, '2024-01-11 10:00:00'); 
INSERT INTO LectureViews (LearnerID, LectureID, ViewDate) VALUES (1, 2, '2024-01-12 14:30:00'); 
-- Bob (Learner 2), Python Course (Course 1, Enrolled '2024-01-15', Lecture IDs: 1, 2, 3)
INSERT INTO LectureViews (LearnerID, LectureID, ViewDate) VALUES (2, 1, '2024-01-19 11:00:00'); 
-- Charlie (Learner 3), AI Course (Course 4, Enrolled '2024-02-01', Lecture IDs: 9, 10)
INSERT INTO LectureViews (LearnerID, LectureID, ViewDate) VALUES (3, 9, '2024-02-06 16:00:00'); 
INSERT INTO LectureViews (LearnerID, LectureID, ViewDate) VALUES (3, 10, '2024-02-07 10:00:00'); 
-- Diana (Learner 4), DB Design Course (Course 5, Enrolled '2024-02-05', Lecture IDs: 11, 12)
INSERT INTO LectureViews (LearnerID, LectureID, ViewDate) VALUES (4, 11, '2024-02-11 08:30:00'); 
INSERT INTO LectureViews (LearnerID, LectureID, ViewDate) VALUES (4, 12, '2024-02-12 11:45:00');

-- ============================================================================
-- USER MANAGEMENT
-- Creates a Users table for authentication and authorization.
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(100) NOT NULL,
    Role ENUM('learner', 'instructor', 'admin') NOT NULL,
    LastLogin DATETIME NULL
);


ALTER TABLE Learners ADD COLUMN UserID INT UNIQUE,
ADD FOREIGN KEY (UserID) REFERENCES Users(UserID);

ALTER TABLE Instructors ADD COLUMN UserID INT UNIQUE,
ADD FOREIGN KEY (UserID) REFERENCES Users(UserID);

-- Insert sample users
INSERT INTO Users (Email, Password, Role) 
VALUES ('admin@system', 'admin', 'admin');

-- Tạo user cho các Learners và Instructors đã có
INSERT INTO Users (Email, Password, Role)
SELECT Email, 'learner', 'learner' 
FROM Learners;

INSERT INTO Users (Email, Password, Role)
SELECT Email, 'instructor', 'instructor'
FROM Instructors;

-- Liên kết UserID
UPDATE Learners L
JOIN Users U ON L.Email = U.Email
SET L.UserID = U.UserID;

UPDATE Instructors I
JOIN Users U ON I.Email = U.Email
SET I.UserID = U.UserID;

GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Users TO 'admin_app_user'@'%';



