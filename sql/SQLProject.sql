DROP DATABASE IF EXISTS OnlineCourses;
CREATE DATABASE OnlineCourses;
USE OnlineCourses;

-- ============================================================================
-- USER MANAGEMENT TABLE
-- Central table for user authentication and role management.
-- ============================================================================
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Email VARCHAR(100) UNIQUE NOT NULL,    -- Unique email for login
    Password VARCHAR(100) NOT NULL,        -- User's password (plaintext for this project)
    Role ENUM('learner', 'instructor', 'admin') NOT NULL, -- User's role in the system
    LastLogin DATETIME NULL,               -- Timestamp of the last login
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp of user creation
);

-- ============================================================================
-- CORE TABLE DEFINITIONS
-- Defines tables for learners, instructors, courses, lectures,
-- enrollments, lecture views, and enrollment logs.
-- ============================================================================

-- Learners Table: Manages specific learner profile information, linked to a User.
CREATE TABLE Learners (
    LearnerID INT AUTO_INCREMENT PRIMARY KEY, -- This LearnerID is still used as FK in Enrollments, LectureViews
    UserID INT UNIQUE NOT NULL,              -- Foreign Key to Users table, ensures one User is one Learner
    LearnerName VARCHAR(100) NOT NULL,       -- Learner's full name (Required)
    PhoneNumber VARCHAR(20) UNIQUE,          -- Learner's phone number (Unique, Optional)
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Instructors Table: Manages specific instructor profile information, linked to a User.
CREATE TABLE Instructors (
    InstructorID INT AUTO_INCREMENT PRIMARY KEY, -- This InstructorID is still used as FK in Courses
    UserID INT UNIQUE NOT NULL,              -- Foreign Key to Users table, ensures one User is one Instructor
    InstructorName VARCHAR(100) NOT NULL,    -- Instructor's full name (Required)
    Expertise VARCHAR(100),                 -- Instructor's area of expertise (Optional)
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Courses Table: Manages course information.
CREATE TABLE Courses (
    CourseID INT AUTO_INCREMENT PRIMARY KEY,
    CourseName VARCHAR(100) NOT NULL,
    CourseDescription TEXT,
    InstructorID INT,                       -- References Instructors.InstructorID
    FOREIGN KEY (InstructorID) REFERENCES Instructors(InstructorID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- Lectures Table: Manages lecture content within courses.
CREATE TABLE Lectures (
    LectureID INT AUTO_INCREMENT PRIMARY KEY,
    CourseID INT NOT NULL,
    Title VARCHAR(200) NOT NULL,
    Content TEXT,
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Enrollments Table: Manages learner enrollments in courses and tracks progress.
CREATE TABLE Enrollments (
    EnrollmentID INT AUTO_INCREMENT PRIMARY KEY,
    LearnerID INT NOT NULL,                  -- References Learners.LearnerID
    CourseID INT NOT NULL,                   -- References Courses.CourseID
    EnrollmentDate DATE NOT NULL,
    CompletionStatus ENUM('Not Started', 'In Progress', 'Completed') DEFAULT 'Not Started' NOT NULL,
    ProgressPercentage TINYINT UNSIGNED DEFAULT 0 NOT NULL,
    FOREIGN KEY (LearnerID) REFERENCES Learners(LearnerID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- LectureViews Table: Records which lectures a learner has viewed.
CREATE TABLE LectureViews (
    LearnerID INT NOT NULL,                  -- References Learners.LearnerID
    LectureID INT NOT NULL,                  -- References Lectures.LectureID
    ViewDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (LearnerID, LectureID),
    FOREIGN KEY (LearnerID) REFERENCES Learners(LearnerID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (LectureID) REFERENCES Lectures(LectureID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Enrollment Log Table: Records enrollment events for auditing purposes.
CREATE TABLE EnrollmentLogs (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    EnrollmentID INT NULL,
    LearnerID INT NULL,
    CourseID INT NULL,
    LogTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ActionType VARCHAR(50) DEFAULT 'Enrollment Created' NOT NULL,
    FOREIGN KEY (EnrollmentID) REFERENCES Enrollments(EnrollmentID) ON DELETE SET NULL,
    FOREIGN KEY (LearnerID) REFERENCES Learners(LearnerID) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID) ON DELETE SET NULL ON UPDATE CASCADE
);

-- ============================================================================
-- INDEXES
-- Creates indexes to improve query performance.
-- ============================================================================
CREATE INDEX idx_Users_Email ON Users(Email);                      -- Speeds up login and email uniqueness checks.
CREATE INDEX idx_CourseName ON Courses(CourseName);                -- Speeds up searching courses by name.
CREATE INDEX idx_Enrollments_LearnerID ON Enrollments(LearnerID);   -- Speeds up finding enrollments for a specific learner.
CREATE INDEX idx_Enrollments_CourseID ON Enrollments(CourseID);    -- Speeds up finding enrollments for a specific course.
CREATE INDEX idx_Lectures_CourseID ON Lectures(CourseID);          -- Speeds up finding lectures for a specific course.

-- ============================================================================
-- VIEWS
-- Creates views to provide simplified perspectives on the data.
-- ============================================================================

-- View: Shows learner's course enrollment details, progress, and email.
CREATE VIEW LearnerCourseProgress AS
SELECT
    L.LearnerName,
    U.Email AS LearnerEmail, -- Learner's email from Users table
    C.CourseName,
    E.EnrollmentDate,
    E.CompletionStatus,
    E.ProgressPercentage
FROM Enrollments E
JOIN Learners L ON E.LearnerID = L.LearnerID
JOIN Users U ON L.UserID = U.UserID -- Join with Users to get Email
JOIN Courses C ON E.CourseID = C.CourseID;

-- View: Shows the teaching load (number of courses) and email for each instructor.
CREATE VIEW InstructorTeachingLoad AS
SELECT
    I.InstructorName,
    U.Email AS InstructorEmail, -- Instructor's email from Users table
    COUNT(C.CourseID) AS NumberOfCourses
FROM Instructors I
JOIN Users U ON I.UserID = U.UserID -- Join with Users to get Email
LEFT JOIN Courses C ON I.InstructorID = C.InstructorID
GROUP BY I.InstructorID, I.InstructorName, U.Email;

-- ============================================================================
-- USER DEFINED FUNCTIONS
-- Defines custom functions for reusable calculations.
-- ============================================================================

-- Function: Calculates the completion rate for a learner in a specific course.
DELIMITER $$
CREATE FUNCTION CalculateCompletionRate(p_learner_id INT, p_course_id INT)
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total_lectures INT DEFAULT 0;
    DECLARE viewed_lectures INT DEFAULT 0;
    DECLARE completion_rate DECIMAL(5,2) DEFAULT 0.00;
    SELECT COUNT(*) INTO total_lectures FROM Lectures WHERE CourseID = p_course_id;
    SELECT COUNT(DISTINCT LV.LectureID) INTO viewed_lectures
    FROM LectureViews LV JOIN Lectures L ON LV.LectureID = L.LectureID
    WHERE LV.LearnerID = p_learner_id AND L.CourseID = p_course_id;
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

-- Procedure: Enrolls a learner into a course, preventing duplicates.
DELIMITER //
CREATE PROCEDURE EnrollLearner(IN p_learner_id INT, IN p_course_id INT)
BEGIN
    IF NOT EXISTS (SELECT 1 FROM Enrollments WHERE LearnerID = p_learner_id AND CourseID = p_course_id) THEN
        INSERT INTO Enrollments (LearnerID, CourseID, EnrollmentDate, CompletionStatus, ProgressPercentage)
        VALUES (p_learner_id, p_course_id, CURDATE(), 'Not Started', 0);
    ELSE
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Learner is already enrolled in this course.';
    END IF;
END //
DELIMITER ;

-- Procedure: Generates a summary report of course completion status for a specific course, including learner email.
DELIMITER //
CREATE PROCEDURE GenerateCompletionSummary(IN p_course_id INT)
BEGIN
    SELECT
        L.LearnerName, U.Email AS LearnerEmail, -- Learner's email
        C.CourseName, E.EnrollmentDate, E.CompletionStatus, E.ProgressPercentage
    FROM Enrollments E
    JOIN Learners L ON E.LearnerID = L.LearnerID
    JOIN Users U ON L.UserID = U.UserID -- Join with Users to get Email
    JOIN Courses C ON E.CourseID = C.CourseID
    WHERE E.CourseID = p_course_id
    ORDER BY L.LearnerName;
END //
DELIMITER ;

-- ============================================================================
-- TRIGGERS
-- Defines triggers for automatic actions based on data changes.
-- ============================================================================

-- Trigger: Logs a new enrollment record into EnrollmentLogs after insertion.
DELIMITER //
CREATE TRIGGER LogNewEnrollment AFTER INSERT ON Enrollments
FOR EACH ROW BEGIN INSERT INTO EnrollmentLogs (EnrollmentID, LearnerID, CourseID) VALUES (NEW.EnrollmentID, NEW.LearnerID, NEW.CourseID); END //
DELIMITER ;

-- Trigger: Ensures that a lecture view date is not earlier than the enrollment date.
DELIMITER $$
CREATE TRIGGER CheckViewDateAfterEnrollment BEFORE INSERT ON LectureViews
FOR EACH ROW BEGIN
    DECLARE enroll_date DATE;
    SELECT EnrollmentDate INTO enroll_date FROM Enrollments E JOIN Lectures L ON E.CourseID = L.CourseID WHERE E.LearnerID = NEW.LearnerID AND L.LectureID = NEW.LectureID LIMIT 1;
    IF DATE(NEW.ViewDate) < enroll_date THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ViewDate must be on or after EnrollmentDate'; END IF;
END$$
DELIMITER ;

-- Trigger: Automatically updates the enrollment progress after a new lecture view is inserted.
DELIMITER $$
CREATE TRIGGER UpdateEnrollmentProgress AFTER INSERT ON LectureViews
FOR EACH ROW BEGIN
    DECLARE v_course_id INT; DECLARE v_completion_rate DECIMAL(5,2); DECLARE v_completion_status ENUM('Not Started', 'In Progress', 'Completed');
    SELECT CourseID INTO v_course_id FROM Lectures WHERE LectureID = NEW.LectureID;
    SET v_completion_rate = CalculateCompletionRate(NEW.LearnerID, v_course_id);
    IF v_completion_rate = 100.00 THEN SET v_completion_status = 'Completed'; ELSEIF v_completion_rate > 0.00 THEN SET v_completion_status = 'In Progress'; ELSE SET v_completion_status = 'Not Started'; END IF;
    UPDATE Enrollments SET ProgressPercentage = v_completion_rate, CompletionStatus = v_completion_status WHERE LearnerID = NEW.LearnerID AND CourseID = v_course_id;
END$$
DELIMITER ;

-- ============================================================================
-- DATABASE SECURITY & ADMINISTRATION
-- Creates database users and grants specific privileges.
-- ============================================================================
DROP USER IF EXISTS 'readonly_learner'@'%';
CREATE USER 'readonly_learner'@'%' IDENTIFIED BY 'studentPass123!';
GRANT SELECT ON OnlineCourses.Users TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.Learners TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.Instructors TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.Courses TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.Lectures TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.Enrollments TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.LectureViews TO 'readonly_learner'@'%';
GRANT SELECT ON OnlineCourses.LearnerCourseProgress TO 'readonly_learner'@'%';
GRANT EXECUTE ON FUNCTION OnlineCourses.CalculateCompletionRate TO 'readonly_learner'@'%';
GRANT EXECUTE ON PROCEDURE OnlineCourses.EnrollLearner TO 'readonly_learner'@'%';

DROP USER IF EXISTS 'admin_app_user'@'%';
CREATE USER 'admin_app_user'@'%' IDENTIFIED BY 'complexAdminPass456!';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Users TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Learners TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Instructors TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Courses TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Lectures TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.Enrollments TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.LectureViews TO 'admin_app_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON OnlineCourses.EnrollmentLogs TO 'admin_app_user'@'%';
GRANT SELECT ON OnlineCourses.LearnerCourseProgress TO 'admin_app_user'@'%';
GRANT SELECT ON OnlineCourses.InstructorTeachingLoad TO 'admin_app_user'@'%';
GRANT EXECUTE ON FUNCTION OnlineCourses.CalculateCompletionRate TO 'admin_app_user'@'%';
GRANT EXECUTE ON PROCEDURE OnlineCourses.EnrollLearner TO 'admin_app_user'@'%';
GRANT EXECUTE ON PROCEDURE OnlineCourses.GenerateCompletionSummary TO 'admin_app_user'@'%';

FLUSH PRIVILEGES;

-- ============================================================================
-- SAMPLE DATA INSERTION
-- Populates the tables with sample data. Order is important due to FKs.
-- Passwords for sample users are set to their role name for simplicity in this project.
-- In a real application, passwords MUST BE HASHED.
-- ============================================================================

-- 1. Insert Admin User
INSERT INTO Users (Email, Password, Role) VALUES 
('admin@system.com', 'admin', 'admin');

-- 2. Insert Sample Users (for Learners)
INSERT INTO Users (Email, Password, Role) VALUES
('alice@example.com', 'learner', 'learner'), ('bob@example.com', 'learner', 'learner'),
('charlie@example.com', 'learner', 'learner'), ('diana@example.com', 'learner', 'learner'),
('ethan@example.com', 'learner', 'learner'), ('fiona@example.com', 'learner', 'learner'),
('caesar@example.com', 'learner', 'learner'), ('hermione@example.com', 'learner', 'learner'),
('indy@example.com', 'learner', 'learner'), ('bond@example.com', 'learner', 'learner');

-- 3. Insert Sample Users (for Instructors)
INSERT INTO Users (Email, Password, Role) VALUES
('dumbledore@edu.example.com', 'instructor', 'instructor'), ('ada@edu.example.com', 'instructor', 'instructor'),
('miyagi@edu.example.com', 'instructor', 'instructor'), ('curie@edu.example.com', 'instructor', 'instructor'),
('turing@edu.example.com', 'instructor', 'instructor'), ('mcgonagall@edu.example.com', 'instructor', 'instructor'),
('holmes@edu.example.com', 'instructor', 'instructor'), ('goodall@edu.example.com', 'instructor', 'instructor'),
('docbrown@edu.example.com', 'instructor', 'instructor'), ('snape@edu.example.com', 'instructor', 'instructor');

-- 4. Insert into Learners, linking to UserID
INSERT INTO Learners (UserID, LearnerName, PhoneNumber) VALUES
((SELECT UserID FROM Users WHERE Email = 'alice@example.com'), 'Alice Wonderland', '0901234001'),
((SELECT UserID FROM Users WHERE Email = 'bob@example.com'), 'Bob The Builder', '0901234002'),
((SELECT UserID FROM Users WHERE Email = 'charlie@example.com'), 'Charlie Chaplin', '0901234003'),
((SELECT UserID FROM Users WHERE Email = 'diana@example.com'), 'Diana Prince', '0901234004'),
((SELECT UserID FROM Users WHERE Email = 'ethan@example.com'), 'Ethan Hunt', '0901234005'),
((SELECT UserID FROM Users WHERE Email = 'fiona@example.com'), 'Fiona Shrek', '0901234006'),
((SELECT UserID FROM Users WHERE Email = 'caesar@example.com'), 'Gaius Julius Caesar', '0901234007'),
((SELECT UserID FROM Users WHERE Email = 'hermione@example.com'), 'Hermione Granger', '0901234008'),
((SELECT UserID FROM Users WHERE Email = 'indy@example.com'), 'Indiana Jones', '0901234009'),
((SELECT UserID FROM Users WHERE Email = 'bond@example.com'), 'James Bond', '0901234010');

-- 5. Insert into Instructors, linking to UserID
-- Note: InstructorIDs will be 1, 2, 3... based on insertion order here.
INSERT INTO Instructors (UserID, InstructorName, Expertise) VALUES
((SELECT UserID FROM Users WHERE Email = 'dumbledore@edu.example.com'), 'Prof. Dumbledore', 'Advanced Magic'), -- Assumed InstructorID = 1
((SELECT UserID FROM Users WHERE Email = 'ada@edu.example.com'), 'Dr. Ada Lovelace', 'Computer Science'),          -- Assumed InstructorID = 2
((SELECT UserID FROM Users WHERE Email = 'miyagi@edu.example.com'), 'Mr. Miyagi', 'Karate Fundamentals'),       -- Assumed InstructorID = 3
((SELECT UserID FROM Users WHERE Email = 'curie@edu.example.com'), 'Ms. Marie Curie', 'Physics & Chemistry'),      -- Assumed InstructorID = 4
((SELECT UserID FROM Users WHERE Email = 'turing@edu.example.com'), 'Dr. Alan Turing', 'Cryptography & AI'),       -- Assumed InstructorID = 5
((SELECT UserID FROM Users WHERE Email = 'mcgonagall@edu.example.com'), 'Prof. Minerva McGonagall', 'Transfiguration'),-- Assumed InstructorID = 6
((SELECT UserID FROM Users WHERE Email = 'holmes@edu.example.com'), 'Mr. Sherlock Holmes', 'Deductive Reasoning'),-- Assumed InstructorID = 7
((SELECT UserID FROM Users WHERE Email = 'goodall@edu.example.com'), 'Ms. Jane Goodall', 'Primatology'),         -- Assumed InstructorID = 8
((SELECT UserID FROM Users WHERE Email = 'docbrown@edu.example.com'), 'Dr. Emmett Brown', 'Temporal Mechanics'),  -- Assumed InstructorID = 9
((SELECT UserID FROM Users WHERE Email = 'snape@edu.example.com'), 'Prof. Severus Snape', 'Potions Master');    -- Assumed InstructorID = 10

-- 6. Insert Courses (Using hardcoded InstructorIDs based on assumed insertion order above)
INSERT INTO Courses (CourseName, CourseDescription, InstructorID) VALUES
('Introduction to Python', 'Learn Python basics, data types, and control flow.', 2), -- Dr. Ada Lovelace
('SQL for Beginners', 'Master fundamental SQL queries for data manipulation.', 2),      -- Dr. Ada Lovelace
('Web Design Basics', 'Build and style simple web pages using HTML5 and CSS3.', 5),       -- Dr. Alan Turing
('Introduction to AI', 'An overview of core AI concepts and algorithms.', 5),            -- Dr. Alan Turing
('Relational Database Design', 'Learn database design principles, normalization, and ER modeling.', 2), -- Dr. Ada Lovelace
('Data Analysis with Python', 'Using Pandas and NumPy for data exploration.', 7),       -- Mr. Sherlock Holmes
('JavaScript Essentials', 'Understand JavaScript basics for dynamic web pages.', 5),      -- Dr. Alan Turing
('User Interface Design', 'Fundamentals of creating intuitive user interfaces.', 8),    -- Ms. Jane Goodall
('Cybersecurity Fundamentals', 'Basic concepts of digital threats and defenses.', 5),    -- Dr. Alan Turing
('The Art of Deduction', 'Sharpen your observation and logical reasoning skills.', 7);    -- Mr. Sherlock Holmes

-- 7. Insert Lectures
INSERT INTO Lectures (CourseID, Title, Content) VALUES
(1, 'Python Environment Setup', 'Installing Python and setting up your IDE.'), (1, 'Variables and Data Types', 'Integers, Floats, Strings, Booleans.'), (1, 'Basic Operators', 'Arithmetic, Comparison, Logical operators.'),
(2, 'Introduction to Databases', 'What are databases? Relational model basics.'), (2, 'SELECT Queries', 'Using SELECT, FROM, WHERE to retrieve data.'), (2, 'Filtering Data', 'Using AND, OR, IN, BETWEEN, LIKE.'),
(3, 'HTML Fundamentals', 'Tags, Attributes, Basic page structure.'), (3, 'CSS Basics', 'Selectors, Properties, Colors, Fonts.'),
(4, 'What is Artificial Intelligence?', 'History, Goals, Branches of AI.'), (4, 'Types of Machine Learning', 'Supervised, Unsupervised, Reinforcement Learning.'),
(5, 'The Relational Model Revisited', 'Keys (Primary, Foreign), Relationships.'), (5, 'Normalization (1NF, 2NF, 3NF)', 'Reducing data redundancy.');

-- 8. Enroll Learners into Courses
-- LearnerID here refers to Learners.LearnerID, which auto-increments from 1
INSERT INTO Enrollments (LearnerID, CourseID, EnrollmentDate) VALUES
(1, 1, '2024-01-05'), (1, 2, '2024-01-10'), (2, 1, '2024-01-15'), (2, 3, '2024-01-20'),
(3, 4, '2024-02-01'), (4, 5, '2024-02-05'), (5, 6, '2024-02-10'), (6, 2, '2024-02-15'),
(7, 7, '2024-03-01'), (8, 8, '2024-03-05'), (9, 9, '2024-03-10'), (10, 10, '2024-03-15'),
(1, 5, '2024-02-08');

-- 9. Record some lecture views
INSERT INTO LectureViews (LearnerID, LectureID, ViewDate) VALUES
(1, 1, '2024-01-11 10:00:00'), (1, 2, '2024-01-12 14:30:00'),
(2, 1, '2024-01-19 11:00:00'),
(3, 9, '2024-02-06 16:00:00'), (3, 10, '2024-02-07 10:00:00'),
(4, 11, '2024-02-11 08:30:00'), (4, 12, '2024-02-12 11:45:00');

-- ============================================================================
-- TEST QUERIES (Commented out - for manual verification)
-- ============================================================================
/*
-- Verify user creation and linking
SELECT U.UserID, U.Email, U.Role, L.LearnerName, I.InstructorName
FROM Users U
LEFT JOIN Learners L ON U.UserID = L.UserID
LEFT JOIN Instructors I ON U.UserID = I.UserID;

-- Verify LearnerCourseProgress View with Email
SELECT * FROM LearnerCourseProgress WHERE LearnerName = 'Alice Wonderland';

-- Verify InstructorTeachingLoad View with Email
SELECT * FROM InstructorTeachingLoad WHERE InstructorName = 'Dr. Ada Lovelace';

-- Test login (conceptually, Python would do this)
SELECT UserID, Role, Password FROM Users WHERE Email = 'alice@example.com';
-- Then Python would compare entered password 'learner' with stored 'learner'

-- Other test queries remain largely the same
SELECT CalculateCompletionRate(1, 1) AS Alice_Python_Rate;
CALL GenerateCompletionSummary(1);
SELECT * FROM EnrollmentLogs ORDER BY LogTime DESC LIMIT 5;
INSERT INTO LectureViews (LearnerID, LectureID, ViewDate) VALUES (1, 3, NOW()); -- Alice views last Python lecture
SELECT * FROM LearnerCourseProgress WHERE LearnerName = 'Alice Wonderland' AND CourseName = 'Introduction to Python';
CALL EnrollLearner(1, 1); -- Test duplicate enrollment
*/
