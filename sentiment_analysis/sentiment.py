import pandas as pd
import numpy as np
import joblib
import spacy
import time

from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import accuracy_score, f1_score, classification_report

def load_data():
    print("🔹 Loading and preprocessing data...")
    df = pd.read_csv('preprocessed_reviews.csv')
    df.dropna(inplace=True)
    label_encoder = LabelEncoder()
    df['label'] = label_encoder.fit_transform(df['sentiment'])
    joblib.dump(label_encoder, 'label_encoder.pkl')
    return df, label_encoder

def compute_weights(y):
    print("🔹 Computing class weights...")
    class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y), y=y)
    weight_dict = dict(enumerate(class_weights))
    print("Class Weights:", weight_dict)
    return weight_dict

def train_with_cv(X, y, param_grid):
    print("🔹 Starting cross-validation with GridSearch...")
    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    acc_list, f1_list = [], []

    for fold, (train_idx, test_idx) in enumerate(kf.split(X, y)):
        print(f"\n🔸 Fold {fold + 1}")
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer()),
            ('svm', LinearSVC(class_weight='balanced', max_iter=10000))
        ])

        grid = GridSearchCV(pipeline, param_grid, cv=2, scoring='f1_macro', n_jobs=-1)
        grid.fit(X_train, y_train)

        best_model = grid.best_estimator_
        y_pred = best_model.predict(X_test)

        print(f"Best Params: {grid.best_params_}")
        print(classification_report(y_test, y_pred))

        acc_list.append(accuracy_score(y_test, y_pred))
        f1_list.append(f1_score(y_test, y_pred, average='macro'))

    print("\n✅ Average Accuracy:", np.mean(acc_list))
    print("✅ Average F1 Score:", np.mean(f1_list))

def train_final_model(X, y):
    print("\n🔹 Training final model on full dataset...")
    final_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=10000)),
        ('svm', LinearSVC(class_weight='balanced', C=1, max_iter=10000))
    ])
    final_pipeline.fit(X, y)
    joblib.dump(final_pipeline, 'svm_tfidf_pipeline.pkl')
    print("✅ Final model saved to svm_tfidf_pipeline.pkl")

def main():
    start_time = time.time()

    df, _ = load_data()
    X_all, y_all = df['clean_text'], df['label']
    compute_weights(y_all)

    param_grid = {
        'tfidf__ngram_range': [(1, 1), (1, 2)],
        'tfidf__max_features': [5000, 10000],
        'svm__C': [0.5, 1]
    }

    train_with_cv(X_all, y_all, param_grid)
    train_final_model(X_all, y_all)

    print(f"\n⏱️ Total training time: {round((time.time() - start_time) / 60, 2)} minutes")

if __name__ == "__main__":
    main()


# ======================================= << RESULT FROM TERMINAL >> =======================================

# $ python sentiment.py 
# 🔹 Loading and preprocessing data...
# 🔹 Computing class weights...
# Class Weights: {0: np.float64(5.461618180472278), 1: np.float64(3.087135714136279), 2: np.float64(0.40112648796174727)}
# 🔹 Starting cross-validation with GridSearch...

# 🔸 Fold 1
# Best Params: {'svm__C': 0.5, 'tfidf__max_features': 10000, 'tfidf__ngram_range': (1, 2)}
#               precision    recall  f1-score   support

#            0       0.61      0.67      0.64      1801
#            1       0.46      0.46      0.46      3187
#            2       0.94      0.94      0.94     24525

#     accuracy                           0.87     29513
#    macro avg       0.67      0.69      0.68     29513
# weighted avg       0.87      0.87      0.87     29513


# 🔸 Fold 2
# Best Params: {'svm__C': 0.5, 'tfidf__max_features': 10000, 'tfidf__ngram_range': (1, 2)}
#               precision    recall  f1-score   support

#            0       0.61      0.68      0.64      1802
#            1       0.46      0.44      0.45      3186
#            2       0.94      0.94      0.94     24525

#     accuracy                           0.87     29513
#    macro avg       0.67      0.69      0.68     29513
# weighted avg       0.87      0.87      0.87     29513


# 🔸 Fold 3
# Best Params: {'svm__C': 0.5, 'tfidf__max_features': 10000, 'tfidf__ngram_range': (1, 2)}
#               precision    recall  f1-score   support

#            0       0.62      0.68      0.65      1801
#            1       0.45      0.45      0.45      3186
#            2       0.94      0.93      0.94     24525

#     accuracy                           0.87     29512
#    macro avg       0.67      0.69      0.68     29512
# weighted avg       0.87      0.87      0.87     29512


# 🔸 Fold 4
# Best Params: {'svm__C': 0.5, 'tfidf__max_features': 10000, 'tfidf__ngram_range': (1, 2)}
#               precision    recall  f1-score   support

#            0       0.61      0.69      0.65      1801
#            1       0.47      0.45      0.46      3187
#            2       0.94      0.94      0.94     24524

#     accuracy                           0.87     29512
#    macro avg       0.67      0.69      0.68     29512
# weighted avg       0.87      0.87      0.87     29512


# 🔸 Fold 5
# Best Params: {'svm__C': 0.5, 'tfidf__max_features': 10000, 'tfidf__ngram_range': (1, 2)}
#               precision    recall  f1-score   support

#            0       0.63      0.69      0.65      1801
#            1       0.46      0.46      0.46      3187
#            2       0.94      0.93      0.94     24524

#     accuracy                           0.87     29512
#    macro avg       0.68      0.69      0.68     29512
# weighted avg       0.87      0.87      0.87     29512


# ✅ Average Accuracy: 0.8680148031856838
# ✅ Average F1 Score: 0.6806491385208163

# 🔹 Training final model on full dataset...
# ✅ Final model saved to svm_tfidf_pipeline.pkl

# ⏱️ Total training time: 12.42 minutes