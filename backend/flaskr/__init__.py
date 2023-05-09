import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import json

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_list(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    list = [item.format() for item in selection]
    current_list = list[start:end]

    return current_list

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.app_context().push()
    setup_db(app)

    #Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    CORS(app)

    #Use the after_request decorator to set Access-Control-Allow
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response
    
    #Create an endpoint to handle GET requests for all available categories. 
    @app.route("/categories")
    def retrieve_categories():
        categories = Category.query.all()

        list = {}
        for item in categories:
            list[item.id] = item.type 

        if len(list) == 0:
            abort(404)

        #print(f'{list[0]}')
        return jsonify(
            {
                "success": True,
                "categories": list,
                "total_categories": len(categories),
            }
        )

    """
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route("/questions")
    def retrieve_questions():
        categories = Category.query.all()

        list = {}
        for item in categories:
            list[item.id] = item.type 

        questions = Question.query.all()
        current_questions = paginate_list( request=request,
                                            selection=questions)
        if len(list) == 0 or len(current_questions) == 0:
            abort(404)

        return jsonify({
                "success": True,
                "questions": current_questions,
                "total_questions": len(questions),
                "categories": list,
                "total_categories": len(categories)
            }
        )
    """
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route("/questions/<int:id>", methods=['DELETE'])
    def delete_questions(id):
        question = Question.query.get(id)
        if question != None:
            question.delete()
    
        return jsonify({
                "success": True if question != None else False
            }
        )

    """
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    """
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)
        search = body.get('searchTerm', None)
        try:
            if search:
                questions = Question.query.filter(Question.question.ilike('%{}%'.format(search))).all()
                current_questions = paginate_list( request=request,
                                                selection=questions)
                return jsonify(
                    {
                        "success": True,
                        "questions": current_questions,
                        "total_questions": len(questions)
                    }
                )
            else:
                question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
                question.insert()

                questions = Question.query.filter(Question.category == new_category).all()
                current_questions = paginate_list( request=request, selection=questions)
                return jsonify({
                    'success': True
                })
        except:
            abort(422)

    """
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route("/categories/<int:category_id>/questions")
    def retrieve_categories_questions(category_id):
        category = Category.query.filter(Category.id == category_id).one_or_none()
        
        if category == None:
            abort(404)

        questions = Question.query.filter(Question.category == category_id).all()
        current_questions = paginate_list( request=request,
                                            selection=questions)

        return jsonify({
                "success": True,
                "questions": current_questions,
                "total_questions": len(questions),
                "current_category": category.type,
            }
        )
    """
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def get_next_question():
        body = request.get_json()
        previous_questions = body.get('previous_questions', None)

        quiz_category = body.get('quiz_category')

        questions = Question.query.filter(Question.category == quiz_category['id'] if quiz_category['id'] != 0 else 1==1, Question.id.not_in(previous_questions)).all()
        current_questions = paginate_list( request=request,
                                            selection=questions)
        return jsonify({
                "success": True,
                "question": random.choice(current_questions) if len(questions) > 0 else None
            }
        )       

    """
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify({"success": False, "error": 400, "message": "bad request"}),
            400,
        )

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 405, "message": "method not allowed"}),
            405,
        )
    return app

