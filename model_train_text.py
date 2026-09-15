import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle

print("Text dataset load ho raha hai...")
data = pd.read_csv('dataset_text.csv')

X = data['text']
y = data['label']

print("Text model train ho raha hai...")
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
X_vectorized = vectorizer.fit_transform(X)

model = LogisticRegression()
model.fit(X_vectorized, y)

pickle.dump(model, open('text_model.pkl', 'wb'))
pickle.dump(vectorizer, open('text_vectorizer.pkl', 'wb'))

print("✅ Text model successfully train ho gaya!")
