
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pickle
import re
from database import db, User, Complaint, Feedback, QuizResult

app = Flask(__name__)
app.secret_key = 'cyberdefender_om_secret_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cyberdefender.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Load models
url_model = pickle.load(open('phishing_model.pkl', 'rb'))
url_vectorizer = pickle.load(open('vectorizer.pkl', 'rb'))
text_model = pickle.load(open('text_model.pkl', 'rb'))
text_vectorizer = pickle.load(open('text_vectorizer.pkl', 'rb'))

SUSPICIOUS_WORDS = ['login', 'verify', 'update', 'bank', 'free', 'gift',
                    'prize', 'claim', 'secure', 'account', 'password',
                    'kyc', 'win', 'offer', 'recharge', 'urgent', 'blocked',
                    'suspended', 'lottery', 'click here']

FRAUD_PHRASES = ['click here', 'claim now', 'urgent', 'verify your account',
                 'you have won', 'free gift', 'limited time', 'act now',
                 'your account will be blocked', 'update kyc', 'lottery',
                 'prize money', 'send money', 'otp', 'bank details',
                 'aadhaar', 'pan card', 'cvv']

DANGEROUS_CODE_PATTERNS = [
    (r'<script.*?>.*?</script>', 'XSS Script Tag'),
    (r'SELECT.*FROM.*WHERE', 'SQL Injection'),
    (r'DROP\s+TABLE', 'SQL DROP Table Attack'),
    (r'UNION\s+SELECT', 'SQL Union Attack'),
    (r'eval\s*\(', 'Dangerous eval() function'),
    (r'exec\s*\(', 'Dangerous exec() function'),
    (r'system\s*\(', 'System command execution'),
    (r'rm\s+-rf\s+/', 'Dangerous delete command'),
    (r'base64_decode', 'Obfuscated code'),
    (r'<iframe', 'Hidden iframe injection'),
    (r'javascript:', 'JavaScript protocol injection'),
    (r'\.\./\.\./', 'Directory traversal attack'),
    (r'wget\s+http', 'Remote file download'),
    (r'curl\s+http', 'Remote file download'),
]

QUIZ_QUESTIONS = [
    {'id': 1, 'question': 'Ye URL real hai ya fake?', 'display': 'https://www.instagram.com', 'type': 'url',
     'options': ['Real', 'Fake'], 'correct': 'Real',
     'explanation': 'Ye Instagram ka asli official URL hai. HTTPS secure hai.'},
    {'id': 2, 'question': 'Ye URL real hai ya fake?', 'display': 'https://www.instagram-login.xyz', 'type': 'url',
     'options': ['Real', 'Fake'], 'correct': 'Fake',
     'explanation': '.xyz extension suspicious hai. Instagram ka domain sirf instagram.com hai.'},
    {'id': 3, 'question': 'Ye email phishing hai ya real?', 'display': 'Dear User, Your account will be blocked in 24 hours. Click here to verify your password immediately.', 'type': 'email',
     'options': ['Real', 'Phishing'], 'correct': 'Phishing',
     'explanation': 'Urgency + Click here + Password verify = Phishing.'},
    {'id': 4, 'question': 'Ye SMS fraud hai ya real?', 'display': 'Congratulations! You won Rs 50,000 in KBC Lottery. Send your bank details.', 'type': 'sms',
     'options': ['Real', 'Fraud'], 'correct': 'Fraud',
     'explanation': 'Koi bhi lottery prize nahi deta. Bank details maangna = scam.'},
    {'id': 5, 'question': 'Is URL mein kya problem hai?', 'display': 'https://www.arnazon.com/login', 'type': 'url',
     'options': ['Kuch nahi, sahi hai', 'Spelling mistake hai'], 'correct': 'Spelling mistake hai',
     'explanation': '"arnazon" likha hai, "amazon" nahi! Ye typo-squatting attack hai.'},
    {'id': 6, 'question': 'Ye WhatsApp message fraud hai?', 'display': 'Your WhatsApp will be deactivated today. Forward to 10 people to reactivate.', 'type': 'message',
     'options': ['Real', 'Fraud'], 'correct': 'Fraud',
     'explanation': 'WhatsApp kabhi aise message nahi bhejta. Ye classic scam hai.'},
    {'id': 7, 'question': 'Safe URL kaunsa hai?', 'display': 'Kaunsa URL safe hai?', 'type': 'url',
     'options': ['http://www.google.com', 'https://www.google.com'], 'correct': 'https://www.google.com',
     'explanation': 'HTTPS (S = Secure) wala URL safe hai. Hamesha padlock icon dhundho.'},
    {'id': 8, 'question': 'Ye email real hai?', 'display': 'From: support@amaz0n.com - Your order is delayed. Pay Rs 50.', 'type': 'email',
     'options': ['Real', 'Phishing'], 'correct': 'Phishing',
     'explanation': 'Dekho sender: amaz0n.com (zero 0 hai). Ye FAKE hai!'},
    {'id': 9, 'question': 'Ye message fraud hai?', 'display': 'URGENT: Your ATM card is blocked. Call 9876543210 immediately.', 'type': 'sms',
     'options': ['Real', 'Fraud'], 'correct': 'Fraud',
     'explanation': 'Bank kabhi SMS se ATM block nahi karta. Ye vishing attack hai.'},
    {'id': 10, 'question': 'Kya Instagram aise email bhejta hai?', 'display': 'From: security@instagram-verify.com - Verify at: http://instagram-verify.com/login', 'type': 'email',
     'options': ['Haan, real hai', 'Nahi, phishing hai'], 'correct': 'Nahi, phishing hai',
     'explanation': 'Domain "instagram-verify.com" asli Instagram nahi hai. HTTP bhi suspicious hai.'}
]


def analyze_url(url):
    url_vector = url_vectorizer.transform([url])
    prediction = url_model.predict(url_vector)[0]
    confidence = max(url_model.predict_proba(url_vector)[0]) * 100
    warnings = []
    if re.search(r'\.(xyz|tk|ml|cf|ga)$', url):
        warnings.append("Suspicious domain extension")
    if any(word in url.lower() for word in SUSPICIOUS_WORDS):
        warnings.append("Contains phishing keywords")
    if url.count('-') > 2:
        warnings.append("Too many hyphens in URL")
    if url.startswith('http://'):
        warnings.append("Not using secure HTTPS")
    if len(url) > 75:
        warnings.append("URL is unusually long")
    return prediction, confidence, warnings


def analyze_text(text):
    text_vector = text_vectorizer.transform([text])
    prediction = text_model.predict(text_vector)[0]
    confidence = max(text_model.predict_proba(text_vector)[0]) * 100
    warnings = []
    text_lower = text.lower()
    for phrase in FRAUD_PHRASES:
        if phrase in text_lower:
            warnings.append(f"Contains suspicious phrase: '{phrase}'")
    if text.count('!') > 2:
        warnings.append("Too many exclamation marks")
    if re.search(r'\b\d{10}\b', text):
        warnings.append("Contains phone number")
    if 'http' in text_lower:
        warnings.append("Contains link")
    return prediction, confidence, warnings


def analyze_code(code):
    warnings = []
    for pattern, name in DANGEROUS_CODE_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            warnings.append(f"{name} detected")
    prediction = 1 if warnings else 0
    confidence = 95.0 if warnings else 90.0
    return prediction, confidence, warnings


def analyze_image(filename):
    warnings = []
    suspicious_ext = ['.exe', '.bat', '.sh', '.php', '.js']
    ai_hints = ['dalle', 'midjourney', 'stable_diffusion', 'ai_gen', 'generated', 'synthetic', 'fake']
    filename_lower = filename.lower()
    for ext in suspicious_ext:
        if filename_lower.endswith(ext):
            warnings.append(f"Suspicious file type: {ext}")
    for hint in ai_hints:
        if hint in filename_lower:
            warnings.append(f"Filename suggests AI-generated: {hint}")
    if not filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
        warnings.append("Not a standard image format")
    prediction = 1 if warnings else 0
    confidence = 75.0 if warnings else 85.0
    return prediction, confidence, warnings


# ========== MAIN ROUTES ==========

@app.route('/', methods=['GET', 'POST'])
def home():
    result = None
    active_tab = request.form.get('tab', 'url')
    if request.method == 'POST':
        if active_tab == 'url':
            url = request.form.get('url', '')
            if url:
                p, c, w = analyze_url(url)
                result = {'type': 'URL Scanner', 'input': url, 'status': 'PHISHING' if p == 1 else 'SAFE', 'confidence': round(c, 2), 'warnings': w}
        elif active_tab == 'email':
            email = request.form.get('email', '')
            if email:
                p, c, w = analyze_text(email)
                result = {'type': 'Email Scanner', 'input': email[:200], 'status': 'FAKE EMAIL' if p == 1 else 'GENUINE EMAIL', 'confidence': round(c, 2), 'warnings': w}
        elif active_tab == 'message':
            msg = request.form.get('message', '')
            if msg:
                p, c, w = analyze_text(msg)
                result = {'type': 'Message Scanner', 'input': msg[:200], 'status': 'FRAUD MESSAGE' if p == 1 else 'SAFE MESSAGE', 'confidence': round(c, 2), 'warnings': w}
        elif active_tab == 'code':
            code = request.form.get('code', '')
            if code:
                p, c, w = analyze_code(code)
                result = {'type': 'Code Scanner', 'input': code[:200], 'status': 'MALICIOUS CODE' if p == 1 else 'SAFE CODE', 'confidence': round(c, 2), 'warnings': w}
        elif active_tab == 'image':
            filename = request.form.get('image_name', '')
            if filename:
                p, c, w = analyze_image(filename)
                result = {'type': 'Image Scanner', 'input': filename, 'status': 'SUSPICIOUS IMAGE' if p == 1 else 'SAFE IMAGE', 'confidence': round(c, 2), 'warnings': w}
    return render_template('index.html', result=result, active_tab=active_tab)


# ========== AUTH ROUTES ==========

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome {username}!', 'success')
            return redirect(url_for('home'))
        flash('Invalid credentials!', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out!', 'success')
    return redirect(url_for('home'))


@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        c = Complaint(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone'],
            fraud_type=request.form['fraud_type'],
            description=request.form['description']
        )
        db.session.add(c)
        db.session.commit()
        flash('Complaint submitted!', 'success')
        return redirect(url_for('complaint'))
    return render_template('complaint.html')


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        f = Feedback(
            name=request.form['name'],
            email=request.form['email'],
            rating=int(request.form['rating']),
            message=request.form['message']
        )
        db.session.add(f)
        db.session.commit()
        flash('Thank you for feedback!', 'success')
        return redirect(url_for('feedback'))
    return render_template('feedback.html')


# ========== AWARENESS ROUTES ==========

@app.route('/awareness')
def awareness():
    return render_template('awareness.html')


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        name = request.form.get('name', 'Anonymous')
        score = 0
        total = len(QUIZ_QUESTIONS)
        answers = []
        for q in QUIZ_QUESTIONS:
            user_answer = request.form.get(f'q{q["id"]}', '')
            is_correct = (user_answer == q['correct'])
            if is_correct:
                score += 1
            answers.append({
                'question': q['question'],
                'display': q['display'],
                'user_answer': user_answer,
                'correct': q['correct'],
                'is_correct': is_correct,
                'explanation': q['explanation']
            })
        percentage = (score / total) * 100
        result = QuizResult(name=name, score=score, total=total, percentage=percentage)
        db.session.add(result)
        db.session.commit()
        return render_template('quiz_result.html', name=name, score=score, total=total, percentage=percentage, answers=answers)
    return render_template('quiz.html', questions=QUIZ_QUESTIONS)


@app.route('/leaderboard')
def leaderboard():
    scores = QuizResult.query.order_by(QuizResult.percentage.desc()).limit(10).all()
    return render_template('leaderboard.html', scores=scores)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
