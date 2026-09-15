import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle

print("Dataset load ho raha hai...")
data = pd.read_csv('dataset.csv')

X = data['url']
y = data['label']

print("Model train ho raha hai...")
vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 3))
X_vectorized = vectorizer.fit_transform(X)

model = LogisticRegression()
model.fit(X_vectorized, y)

pickle.dump(model, open('phishing_model.pkl', 'wb'))
pickle.dump(vectorizer, open('vectorizer.pkl', 'wb'))

print("✅ Model successfully train ho gaya!")
print("Files save ho gayi: phishing_model.pkl, vectorizer.pkl")
