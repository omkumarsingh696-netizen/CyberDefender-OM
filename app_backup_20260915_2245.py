from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pickle
import re
from database import db, User, Complaint, Feedback,QuizResult

app = Flask(__name__)
app.secret_key = 'cyberdefender_om_secret_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cyberdefender.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

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
                 'prize money', 'send money', 'otp', 'bank details']

DANGEROUS_CODE_PATTERNS = [
    (r'<script.*?>.*?</script>', 'XSS Script Tag'),
    (r'SELECT.*FROM.*WHERE', 'SQL Injection'),
    (r'DROP\s+TABLE', 'SQL DROP Table Attack'),
    (r'UNION\s+SELECT', 'SQL Union Attack'),
    (r'eval\s*\(', 'Dangerous eval() function'),
    (r'exec\s*\(', 'Dangerous exec() function'),
    (r'system\s*\(', 'System command execution'),
    (r'rm\s+-rf\s+/', 'Dangerous delete command'),
    (r'<iframe', 'Hidden iframe injection'),
    (r'javascript:', 'JavaScript protocol injection'),
]

def analyze_url(url):
    v = url_vectorizer.transform([url])
    p = url_model.predict(v)[0]
    c = max(url_model.predict_proba(v)[0]) * 100
    w = []
    if re.search(r'\.(xyz|tk|ml|cf|ga)$', url): w.append("Suspicious domain extension")
    if any(word in url.lower() for word in SUSPICIOUS_WORDS): w.append("Contains phishing keywords")
    if url.count('-') > 2: w.append("Too many hyphens in URL")
    if url.startswith('http://'): w.append("Not using secure HTTPS")
    return p, c, w

def analyze_text(text):
    v = text_vectorizer.transform([text])
    p = text_model.predict(v)[0]
    c = max(text_model.predict_proba(v)[0]) * 100
    w = []
    tl = text.lower()
    for phrase in FRAUD_PHRASES:
        if phrase in tl: w.append(f"Suspicious phrase: '{phrase}'")
    if text.count('!') > 2: w.append("Too many exclamation marks")
    if 'http' in tl: w.append("Contains link")
    return p, c, w

def analyze_code(code):
    w = []
    for pattern, name in DANGEROUS_CODE_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE): w.append(f"{name} detected")
    p = 1 if w else 0
    c = 95.0 if w else 90.0
    return p, c, w

def analyze_image(filename):
    w = []
    suspicious_ext = ['.exe', '.bat', '.sh', '.php', '.js']
    ai_hints = ['dalle', 'midjourney', 'stable_diffusion', 'ai_gen', 'generated', 'fake']
    fn = filename.lower()
    for ext in suspicious_ext:
        if fn.endswith(ext): w.append(f"Suspicious file type: {ext}")
    for hint in ai_hints:
        if hint in fn: w.append(f"AI-generated hint: {hint}")
    p = 1 if w else 0
    c = 75.0 if w else 85.0
    return p, c, w


@app.route('/', methods=['GET', 'POST'])
def home():
    result = None
    active_tab = request.form.get('tab', 'url')
    if request.method == 'POST':
        if active_tab == 'url':
            url = request.form.get('url', '')
            if url:
                p, c, w = analyze_url(url)
                result = {'type': 'URL Scanner', 'input': url,
                          'status': 'PHISHING' if p == 1 else 'SAFE',
                          'confidence': round(c, 2), 'warnings': w}
        elif active_tab == 'email':
            email = request.form.get('email', '')
            if email:
                p, c, w = analyze_text(email)
                result = {'type': 'Email Scanner', 'input': email[:200],
                          'status': 'FAKE EMAIL' if p == 1 else 'GENUINE EMAIL',
                          'confidence': round(c, 2), 'warnings': w}
        elif active_tab == 'message':
            msg = request.form.get('message', '')
            if msg:
                p, c, w = analyze_text(msg)
                result = {'type': 'Message Scanner', 'input': msg[:200],
                          'status': 'FRAUD MESSAGE' if p == 1 else 'SAFE MESSAGE',
                          'confidence': round(c, 2), 'warnings': w}
        elif active_tab == 'code':
            code = request.form.get('code', '')
            if code:
                p, c, w = analyze_code(code)
                result = {'type': 'Code Scanner', 'input': code[:200],
                          'status': 'MALICIOUS CODE' if p == 1 else 'SAFE CODE',
                          'confidence': round(c, 2), 'warnings': w}
        elif active_tab == 'image':
            fn = request.form.get('image_name', '')
            if fn:
                p, c, w = analyze_image(fn)
                result = {'type': 'Image Scanner', 'input': fn,
                          'status': 'SUSPICIOUS IMAGE' if p == 1 else 'SAFE IMAGE',
                          'confidence': round(c, 2), 'warnings': w}
    return render_template('index.html', result=result, active_tab=active_tab,
                           logged_in=('user_id' in session),
                           username=session.get('username', ''))


@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'All fields required!'})
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists!'})
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered!'})
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Account created! Please login.'})


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'success': True, 'message': f'Welcome, {username}!', 'username': username})
    return jsonify({'success': False, 'message': 'Invalid credentials!'})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/complaint', methods=['POST'])
def api_complaint():
    data = request.json
    c = Complaint(
        name=data.get('name', ''),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        fraud_type=data.get('fraud_type', ''),
        description=data.get('description', '')
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Complaint submitted! Team will contact you.'})


@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    data = request.json
    f = Feedback(
        name=data.get('name', ''),
        email=data.get('email', ''),
        rating=int(data.get('rating', 5)),
        message=data.get('message', '')
    )
    db.session.add(f)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Thank you for your feedback!'})




@app.route('/quiz-result')
def quiz_result():
    return render_template('quiz_result.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
# ========================================
# PHISHING AWARENESS QUIZ
# ========================================

QUIZ_QUESTIONS = [
    {
        'id': 1,
        'question': 'Ye URL real hai ya fake?',
        'display': 'https://www.instagram.com',
        'type': 'url',
        'options': ['Real', 'Fake'],
        'correct': 'Real',
        'explanation': 'Ye Instagram ka asli official URL hai. "instagram.com" sahi spelling hai aur HTTPS secure hai.'
    },
    {
        'id': 2,
        'question': 'Ye URL real hai ya fake?',
        'display': 'https://www.instagram-login.xyz',
        'type': 'url',
        'options': ['Real', 'Fake'],
        'correct': 'Fake',
        'explanation': 'Ye FAKE hai! "instagram-login.xyz" mein .xyz extension suspicious hai. Asli Instagram ka domain sirf "instagram.com" hai.'
    },
    {
        'id': 3,
        'question': 'Ye email phishing hai ya real?',
        'display': 'Dear User, Your account will be blocked in 24 hours. Click here to verify your password immediately.',
        'type': 'email',
        'options': ['Real', 'Phishing'],
        'correct': 'Phishing',
        'explanation': 'Phishing email ke 3 red flags: (1) Urgency "24 hours", (2) "Click here", (3) Password verify karne ko keh rahe hain. Instagram kabhi password verify nahi maangta email se.'
    },
    {
        'id': 4,
        'question': 'Ye SMS fraud hai ya real?',
        'display': 'Congratulations! You won Rs 50,000 in KBC Lottery. Send your bank details to claim prize.',
        'type': 'sms',
        'options': ['Real', 'Fraud'],
        'correct': 'Fraud',
        'explanation': 'Ye 100% FRAUD hai! Koi bhi lottery prize nahi deta. Bank details maangna = scam. KBC kabhi SMS se lottery nahi bhejta.'
    },
    {
        'id': 5,
        'question': 'Is URL mein kya problem hai?',
        'display': 'https://www.arnazon.com/login',
        'type': 'url',
        'options': ['Kuch nahi, sahi hai', 'Spelling mistake hai (arnazon vs amazon)'],
        'correct': 'Spelling mistake hai (arnazon vs amazon)',
        'explanation': 'Dekho dhyan se: "arnazon" likha hai, "amazon" nahi! Ye typo-squatting attack hai. Attackers aise fake URLs banate hain.'
    },
    {
        'id': 6,
        'question': 'Ye WhatsApp message fraud hai?',
        'display': 'Your WhatsApp will be deactivated today. Forward this message to 10 people to reactivate.',
        'type': 'message',
        'options': ['Real', 'Fraud'],
        'correct': 'Fraud',
        'explanation': 'Ye classic WhatsApp scam hai! WhatsApp kabhi aise message nahi bhejta. Forward karne se kuch nahi hota. Isse ignore karein.'
    },
    {
        'id': 7,
        'question': 'Safe URL kaunsa hai?',
        'display': 'Kaunsa URL safe hai?',
        'type': 'url',
        'options': ['http://www.google.com', 'https://www.google.com'],
        'correct': 'https://www.google.com',
        'explanation': 'HTTPS (S = Secure) wala URL safe hai. HTTP wala insecure hai. Hamesha HTTPS dhundho — padlock icon 🔒 ke saath.'
    },
    {
        'id': 8,
        'question': 'Ye email real hai?',
        'display': 'From: support@amaz0n.com - Your order #12345 is delayed. Pay Rs 50 at this link to reschedule.',
        'type': 'email',
        'options': ['Real', 'Phishing'],
        'correct': 'Phishing',
        'explanation': 'Dekho sender: "amaz0n.com" (zero 0 hai, o nahi). Ye FAKE hai! Asli Amazon ka domain "amazon.com" hai. Paisa maangna = scam.'
    },
    {
        'id': 9,
        'question': 'Ye message fraud hai?',
        'display': 'URGENT: Your ATM card is blocked. Call 9876543210 immediately to unblock.',
        'type': 'sms',
        'options': ['Real', 'Fraud'],
        'correct': 'Fraud',
        'explanation': 'Bank kabhi SMS se ATM block nahi karta. Aur personal number par call karne ko nahi kehta. Ye vishing (voice phishing) attack hai.'
    },
    {
        'id': 10,
        'question': 'Kya Instagram aise email bhejta hai?',
        'display': 'From: security@instagram-verify.com - We detected unusual login. Verify at: http://instagram-verify.com/login',
        'type': 'email',
        'options': ['Haan, real hai', 'Nahi, phishing hai'],
        'correct': 'Nahi, phishing hai',
        'explanation': 'Dekho domain: "instagram-verify.com" — ye asli Instagram nahi hai! Asli Instagram ka domain "instagram.com" hai. Aur HTTP (S nahi) bhi suspicious hai.'
    }
]


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
        
        # Save to database
        result = QuizResult(
            name=name,
            score=score,
            total=total,
            percentage=percentage
        )
        db.session.add(result)
        db.session.commit()
        
        return render_template('quiz_result.html',
                               name=name,
                               score=score,
                               total=total,
                               percentage=percentage,
                               answers=answers)
    
    return render_template('quiz.html', questions=QUIZ_QUESTIONS)


@app.route('/leaderboard')
def leaderboard():
    top_scores = QuizResult.query.order_by(QuizResult.percentage.desc()).limit(10).all()
    return render_template('leaderboard.html', scores=top_scores)
