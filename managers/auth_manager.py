from managers import learner_manager, instructor_manager, user_manager

def authenticate(email, password):
    user = user_manager.get_user_by_email(email)
    if not user or user['Password'] != password:
        return None
    
    # update last login
    user_manager.update_last_login(user['UserID'])
    
    # Find the corresponding ID from the Learners/Instructors table
    entity_id = None
    if user['Role'] == 'learner':
        learner = learner_manager.get_learner_by_user_id(user['UserID'])
        entity_id = learner['LearnerID'] if learner else None
    elif user['Role'] == 'instructor':
        instructor = instructor_manager.get_instructor_by_user_id(user['UserID'])
        entity_id = instructor['InstructorID'] if instructor else None
    elif user['Role'] == 'admin':
        entity_id = 0  # Admin doesnt need ID from other tables
        
    return {
        'role': user['Role'],
        'id': entity_id,
        'email': email,
        'user_id': user['UserID']
    }




