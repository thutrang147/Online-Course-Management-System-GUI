# SQL Project: Online Course Management System

This is a comprehensive online course management system built with Flask and MySQL. The system provides different interfaces for learners, instructors, and administrators to manage courses, track progress, and interact with educational content.

## Prerequisites

- Python 3.8 or higher
- MySQL server
- MySQL Workbench (optional)
- pip (Python package manager)

## Setup Instructions

### Database Setup

1. Login to MySQL:
   ```bash
   mysql -u root -p
   ```

2. Run the SQL setup script:
   ```bash
   mysql -u root -p < /path/to/SQL_Project/sql/SQLProject.sql
   ```

3. **Test Database Connection**
   After setting up the database, you can test the connection using the MySQL client. You can log in with the `admin_app_user` user created in the SQL setup file:
   ```bash
   mysql -u admin_app_user -p -D onlinecourse
   ```
   If you see the MySQL prompt without errors, your connection is successful.

### Application Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd SQL_Project
   ```

2. **Set Up Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   Start the application:
   ```bash
   python main.py
   ```

5. **Access the Application**
   Open your web browser and go to [http://localhost:5000](http://localhost:5000) to use the Online Course Management System.

## Default User Account
   After setting up the database, you can use the following default user accounts to log in. These are automatically inserted into the database during setup.

   - **Administrator**
      - Username: `admin@system.com`
      - Password: `admin`

   - **Instructor**
      - Username: `dumbledore@edu.example.com`
      - Password: `instructor`

   - **Learner**
      - Username: `alice@example.com`
      - Password: `admin`

   > **Note:** You can modify or add user accounts directly in the application through sign up or have them created by the admin.

## Troubleshooting

- **ModuleNotFoundError**: Ensure the project root is added to the `PYTHONPATH`:
  ```bash
  export PYTHONPATH=/path/to/SQL_Project:$PYTHONPATH
  ```

- **Database Connection Issues**: Verify your database credentials in `config.py` or environment variables.

## License

This project is licensed under the MIT License.