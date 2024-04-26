from flask import Flask, request, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import docx2txt
from flask.cli import with_appcontext
import openai
import random
from flask import session
import os
from dotenv import load_dotenv

load_dotenv()  # This loads the environment variables from the .env file

OPEN_API_KEY = os.getenv('OPEN_API_KEY')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hola.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'docx'}
db = SQLAlchemy(app)

openai.api_key = OPEN_API_KEY

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

class Team(db.Model):
    TeamID = db.Column(db.Integer, primary_key=True)
    TeamMembers = db.Column(db.String(1000), nullable = False)

class User(db.Model):
    ufid = db.Column(db.String(100), primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    # This line remains unchanged, the relationship will use the foreign key defined in Rating
    rating = db.relationship('Rating', backref='user', uselist=False, lazy='joined')

class Rating(db.Model):
    ufid = db.Column(db.String(100), db.ForeignKey('user.ufid'), primary_key=True)
    average_rating = db.Column(db.Float)
    selected_skills = db.Column(db.String)

    def __repr__(self):
        return f"<Rating {self.ufid}, Average Rating: {self.average_rating}, Skills: {self.selected_skills}>"

# Initialize database creation, this should be called at an appropriate place in your application setup
with app.app_context():
    db.create_all()
    
    

    
CSS_STYLES = '''
<style>
body {
    background-color: #f8f9fa;
    font-family: Arial, sans-serif;
    margin: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}

.container {
    font-family: Arial, sans-serif;
    text-align: center;
    max-width: 600px;
    margin: 20px auto;
    background-color: #ffffff;
    padding: 20px;
    border-radius: 8px;
    border: 15px solid #20b696;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    color: #000;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.skills-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr); /* Creates a grid with 3 columns */
    gap: 10px; /* Space between grid items */
    text-align: left; /* Aligns the text to the left within each grid item */
    width: 100%;
    max-width: 540px; /* Adjust based on container size or preference */
}

button, .btn-primary {
    background-color: #20b696;
    color: white;
    border: none;
    padding: 10px 24px;
    margin-top: 20px;
    cursor: pointer;
    border-radius: 4px;
}

button:hover, .btn-primary:hover {
    background-color: #377569;
}
.slider {
    position: relative;
    width: 100%;
    overflow: hidden;
}

.slide {
    width: 100%;
    position: absolute;
    left: 0;
    transition: all 0.5s ease;
}

</style>
'''

# Login Page
LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Page</title>
    <style>
        body { background-color: #f8f9fa; color: #343a40; font-family: Arial, sans-serif; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .container { max-width: 700px; margin: 0 auto; padding: 50px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); text-align: center; background-color: #fff; border: 10px solid #20b696; }
        h1 { color: #000000; margin-bottom: 20px; }
        .input-container { margin-bottom: 15px; display: flex; align-items: center; }
        .input-container input[type="text"] { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 3px; }
        .button-container { text-align: center; }
        button { width: 100px; padding: 10px; background-color: #20b696; border: none; color: #fff; border-radius: 3px; cursor: pointer; margin-top: 15px; }
        button:hover { background-color: #377569; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Login Page</h1>
        <form id="loginForm" method="post" action="/">
            <div class="input-container">
                <input type="text" id="username" name="username" required placeholder="Enter First and Last Name">
            </div>
            <div class="input-container">
                <input type="text" id="ufid" name="ufid" required placeholder="Enter UFID">
            </div>
            <div class="button-container">
                <button type="submit">Login</button>
            </div>
        </form>
    </div>
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        ufid = request.form.get('ufid')
        user = User.query.filter_by(username=username, ufid=ufid).first()
        if user:
            session['ufid'] = user.ufid
            return redirect(url_for('upload_file', user_ufid=user.ufid, new_user=False))
        else:
            new_user = User(username=username, ufid=ufid)
            db.session.add(new_user)
            db.session.commit()
            session['ufid'] = new_user.ufid
            return redirect(url_for('upload_file', user_ufid=new_user.ufid, new_user=True))
    return render_template_string(LOGIN_HTML)


# Upload Page
UPLOAD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Resume</title>
    ''' + CSS_STYLES + '''
</head>
<body>
    <div class="container">
        <h1>{{ message }}</h1>
        <form method="post" enctype="multipart/form-data">
            <form method="post" enctype="multipart/form-data">
      <div class="file-upload">
          <button class="file-upload-btn" type="button" onclick="document.getElementById('fileInput').click();">Choose File</button>
          <input id="fileInput" type="file" name="file" style="display: none;" onchange="document.getElementById('filename').innerHTML = this.files[0].name">
      </div>
      <span id="filename">&nbsp; No file chosen</span>
      <br>
      <button type="submit" class="btn-primary">Extract Skills</button>
    </form>
        
        
        
    </div>
</body>
</html>

'''

TEXT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Extracted Skills</title>
    ''' + CSS_STYLES + '''
</head>
<body class="body">
    <div class="container">
        <h1>Extracted Skills from Resume</h1>
        <form id="skills-form" method="post" action="/submit_skills">
            <div class="skills-grid" id="skills-grid">
                {% for skill in skills %}
                <div class="skill-item">
                    <input type="checkbox" id="skill_{{ loop.index }}" name="skills" value="{{ skill }}">
                    <label for="skill_{{ loop.index }}">{{ skill }}</label>
                </div>
                {% endfor %}
            </div>
            <div>
                <input type="text" id="newSkillInput" placeholder="Enter new skill">
                <button type="button" onclick="addSkill()">Add Skill</button>
            </div>
            <button type="submit" class="btn-primary">Submit Skills</button>
        </form>
        <a href="/" class="btn-success">Upload another resume</a>
    </div>
    <script>
        let skillIndex = {{ skills|length + 1 }};
        
        function addSkill() {
            const skillValue = document.getElementById('newSkillInput').value.trim();
            if (!skillValue) {
                alert('Please enter a skill name.');
                return;
            }

            const grid = document.getElementById('skills-grid');
            const newSkillDiv = document.createElement('div');
            newSkillDiv.className = 'skill-item';
            
            const newSkillInput = document.createElement('input');
            newSkillInput.type = 'checkbox';
            newSkillInput.id = 'skill_' + skillIndex;
            newSkillInput.name = 'skills';
            newSkillInput.value = skillValue;
            
            const newSkillLabel = document.createElement('label');
            newSkillLabel.htmlFor = 'skill_' + skillIndex;
            newSkillLabel.textContent = skillValue;
            
            newSkillDiv.appendChild(newSkillInput);
            newSkillDiv.appendChild(newSkillLabel);
            
            grid.appendChild(newSkillDiv);
            
            document.getElementById('newSkillInput').value = ''; // Clear the input field
            skillIndex++;
        }
    </script>
</body>
</html>
'''

SELECTED_SKILLS_TEMPLATE = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Selected Skills</title>
     <style>
        body {{
            background-color: #f8f9fa;
            font-family: Arial, sans-serif;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }}

        .container {{
            font-family: Arial, sans-serif;
            text-align: center;
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            border: 15px solid #20b696;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            color: #000;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr); /* Creates a grid with 3 columns */
            gap: 10px; /* Space between grid items */
            text-align: left; /* Aligns the text to the left within each grid item */
            width: 100%;
            max-width: 540px; /* Adjust based on container size or preference */
        }}

        button, .btn-primary {{
            background-color: #20b696;
            color: white;
            border: none;
            padding: 10px 24px;
            margin-top: 20px;
            cursor: pointer;
            border-radius: 4px;
        }}

        button:hover, .btn-primary:hover {{
            background-color: #377569;
        }}

        .slide {{
            display: none; /* Initially hide all slides */
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Selected Skills</h1>
        <ul>
            {{% for skill in selected_skills %}}
            <li>{{{{ skill }}}}</li>
            {{% endfor %}}
        </ul>
        <h1>Skill Assessment Questionnaire</h1>
        <form method="post" action="/feedback_skills">
            {{% for skill, qs in questions.items() %}}
            <h3>{{{{ skill }}}} Questions</h3>
            <div class="slider" id="slider_{{{{ skill }}}}">
                {{% for question in qs %}}
                <div class="slide">
                    <p>Q{{{{ loop.index }}}}: {{{{ question }}}}</p>
                    <textarea name="answer_{{{{ skill }}}}_{{{{ loop.index }}}}" rows="4"></textarea>
                </div>
                {{% endfor %}}
            </div>
            <button type="button" onclick="nextSlide('slider_{{{{ skill }}}}')">Next Question</button>
            {{% endfor %}}
            <br>
            <button type="submit" class="btn-primary">Submit</button>
        </form>
    </div>
    <script>
        function nextSlide(sliderId) {{
            let slider = document.getElementById(sliderId);
            let slides = slider.getElementsByClassName('slide');
            let currentIndex = Array.from(slides).findIndex(slide => slide.style.display === 'block');
            if (currentIndex === -1) {{ currentIndex = 0; }}
            slides[currentIndex].style.display = 'none';
            let nextIndex = (currentIndex + 1) % slides.length;
            slides[nextIndex].style.display = 'block';
        }}

        document.addEventListener('DOMContentLoaded', function () {{
            let sliders = document.getElementsByClassName('slider');
            Array.from(sliders).forEach(slider => {{
                let firstSlide = slider.getElementsByClassName('slide')[0];
                if (firstSlide) firstSlide.style.display = 'block';
            }});
        }});
    </script>
</body>
</html>
'''

FEEDBACK_TEMPLATE = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Feedback</title>
    {CSS_STYLES}
</head>
<body>
    <div class="container">
        <h1>Feedback</h1>
        <ul>
            {{% for index, fb in feedback.items() %}}
            <li>
                <p>Answer: {{{{ fb.answer }}}}</p>
                <p>Feedback: {{{{ fb.feedback }}}}</p>
            </li>
            {{% endfor %}}
        </ul>
        <p>Average Rating: {{{{ average_rating }}}}</p>
        <a href="/" class="btn-success">Go Back</a>
    </div>
</body>
</html>
'''

DISPLAY_SKILLS = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Skills Display</title>
</head>
<body>
    <h1>Skills List</h1>
    <ul>
        {{% for skill in skills %}}
            <li>{{{{ skill.name }}}}: {{{{ skill.score }}}}</li>
        {{% endfor %}}
    </ul>
</body>
</html>
'''
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(file_path):
    # Extract text from .docx file
    text = docx2txt.process(file_path)
    return text


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    user_ufid = request.args.get('user_ufid')
    new_user = request.args.get('new_user', 'False') == 'True'  # Convert query parameter to boolean
    user = User.query.get(user_ufid)
    
    if not user:
        return redirect(url_for('login'))  # Redirect to login if no user found
    
    if not user:
        return redirect(url_for('login'))  # Redirect to login if no user found

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(file_path)
            
            text = extract_text(file_path)
            # Split the text into skills assuming they are comma-separated
            skills = [skill.strip() for skill in text.split(',')]
            # Display extracted skills as checkboxes
            return render_template_string(TEXT_TEMPLATE, skills=skills)
            #return "Resume Uploaded Successfully!"
            
    message = "Upload your Resume" if new_user else "Re-upload your Resume"
    return render_template_string(UPLOAD_HTML, message=message)

def generate_questions(topics):
    questions = {}
    for skill in topics:
        levels = ['beginner', 'intermediate', 'advanced']
        skill_questions = []  # Ensure this is a list of questions
        for level in levels:
            prompt = f"Generate a {level} question related to {skill}."
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.5,
                max_tokens=50
            )
            skill_questions.append(response.choices[0].message['content'].strip())
        questions[skill] = skill_questions  # Assigning a list of questions to each skill
    return questions



def verify_answers(answers):
    feedback = {}
    for i, answer in answers.items():
        prompt = f"Review this answer for accuracy and relevance: {answer}. Rate its correctness on a scale from 1 to 5 where 1 indicates completely incorrect, 5 indicates completely correct, and 2-4 indicate varying degrees of partial correctness. Assess based on relevance, accuracy, and completeness. Provide a numerical rating only."
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            temperature=0,
            max_tokens=20
        )
        generated_response = response.choices[0].message['content'].strip()
        feedback[i] = {'answer': answer, 'feedback': generated_response}
    return feedback

def calculate_average_rating(feedback):
    total_ratings = 0
    num_responses = len(feedback)
    
    for item in feedback.values():
        rating = int(item['feedback'])
        total_ratings += rating
    
    average_rating = total_ratings / num_responses if num_responses > 0 else 0
    average_rating = "{:.2f}".format(average_rating)
    
    return average_rating


@app.route('/submit_skills', methods=['POST'])
def generate_questionnaire():
    selected_skills = request.form.getlist('skills')
    session['selected_skills'] = selected_skills
    questions = generate_questions(selected_skills)
    return render_template_string(SELECTED_SKILLS_TEMPLATE, questions=questions, selected_skills=selected_skills)

@app.route('/feedback_skills', methods=['POST'])
def verification_answers():
    if request.method == 'POST':
        answers = {key: request.form.get(key) for key in request.form if key.startswith('answer')}
        feedback = verify_answers(answers)
        average_rating = calculate_average_rating(feedback)
        skills = session.get('selected_skills')
        ufid = session.get('ufid')  # Retrieve UFID from session

        if not ufid:
            return "User identification missing.", 400

        skills_str = ', '.join(skills)
        rating = Rating.query.get(ufid)

        if rating:
            # Update the existing rating
            rating.average_rating = average_rating
            rating.selected_skills = skills_str
        else:
            # No existing rating found, create a new one
            rating = Rating(ufid=ufid, average_rating=average_rating, selected_skills=skills_str)
            db.session.add(rating)
        
        db.session.commit()

        return redirect(url_for('match_teams'))

    return "Invalid request", 400


@app.route('/match_teams')
def match_teams():
    #users = User.query.join(Rating).order_by(Rating.average_rating.desc()).all()
    users = Rating.query.all()
    
    Team.query.delete()
    #for team in teams:
    
    num_teams = len(users)//4   #Team size write it in the denominator
    if num_teams == 0:
        return "error': 'No teams defined", 400

    # Initialize team data for balancing
    team_data = {i: {'members': [], 'total_skill': 0.0} for i in range(1, num_teams+1)}

    print(team_data)
    # Distribute users ensuring all are assigned
    for user in users:
        # Sort teams by total skill ascending to find the least cumulative skill
        least_team = min(team_data.items(), key=lambda t: (t[1]['total_skill'], t[0]))
        least_team[1]['members'].append(user.ufid)
        least_team[1]['total_skill'] += user.average_rating
    #print("#")
    # Update the database with the new team members
    for team_id, data in team_data.items():
        team = Team(TeamID = team_id, TeamMembers = '')
        x = []
        for i in range(len(data['members'])):
            x.append(str(data['members'][i]))
        #team.TeamMembers = ','.join(data['members'])
        team.TeamMembers = ','.join(x)
        y = Team.query.get(team_id)
        if y:
            y.TeamMembers = ','.join(x)
        else:
            db.session.add(team)
    db.session.commit()

    return redirect(url_for('list_teams'))



TEAM_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team List</title>
    ''' + CSS_STYLES + '''
</head>
<body>
    <div class="container">
        <h1>Teams and Members</h1>
        <ul>
            {% for team in teams %}
                <li>
                    <strong>Team ID:</strong> {{ team.TeamID }}<br>
                    <strong>Members:</strong> 
                    <ul>
                        {% for member in team.TeamMembers %}
                            <li>{{ member }}</li>
                        {% endfor %}
                    </ul>
                </li>
            {% endfor %}
        </ul>
        <a href="/">Back to Home</a>
    </div>
</body>
</html>
'''

@app.route('/teams')
def list_teams():
    # Fetch all teams
    teams = Team.query.all()
    # Fetch all users and create a dictionary mapping UFIDs to usernames
    users = User.query.all()
    user_dict = {user.ufid: user.username for user in users}

    # Prepare data to return: replace UFIDs in teams with corresponding usernames
    team_data = []
    for team in teams:
        # Split the TeamMembers field into UFIDs and lookup usernames
        member_ids = team.TeamMembers.split(',')
        member_names = [user_dict.get(ufid, 'Unknown User') for ufid in member_ids]
        team_data.append({
            'TeamID': team.TeamID,
            'TeamMembers': member_names
        })

    return render_template_string(TEAM_TEMPLATE, teams = team_data)



if __name__ == '__main__':
    app.run(debug=True)