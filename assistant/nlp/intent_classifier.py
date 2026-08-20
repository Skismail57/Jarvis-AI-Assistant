import json
import re
import string
import os
import joblib
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score


class IntentClassifier:
    def __init__(self, model_dir: str = None, intents_path: str = None):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.model_dir = model_dir or os.path.join(self.base_dir, "models")
        self.intents_path = intents_path or os.path.join(self.base_dir, "data", "intents.json")
        self.model_path = os.path.join(self.model_dir, "intent_classifier.pkl")
        self.intents_data_path = os.path.join(self.model_dir, "intents_data.pkl")

        self.pipeline = None
        self.intents = None
        self.label_encoder = None
        self.classes_ = None

        os.makedirs(self.model_dir, exist_ok=True)
        self._download_nltk_data()
        self._load_or_train()

    def _download_nltk_data(self):
        resource_map = {
            "punkt": "tokenizers/punkt",
            "stopwords": "corpora/stopwords",
            "wordnet": "corpora/wordnet",
            "punkt_tab": "tokenizers/punkt_tab",
            "omw-1.4": "corpora/omw-1.4"
        }
        for res, path in resource_map.items():
            try:
                nltk.data.find(path)
            except LookupError:
                try:
                    nltk.download(res, quiet=True)
                except Exception:
                    pass

    @staticmethod
    def preprocess_text(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"https?://\S+|www\.\S+", "", text)
        text = re.sub(r"<.*?>", "", text)
        text = re.sub(r"[%s]" % re.escape(string.punctuation), "", text)
        text = re.sub(r"\n", "", text)
        text = re.sub(r"\w*\d\w*", "", text)

        try:
            tokens = word_tokenize(text)
            stop_words = set(stopwords.words("english"))
            lemmatizer = WordNetLemmatizer()
            tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words and token.isalpha()]
            text = " ".join(tokens)
        except Exception:
            pass
        return text

    def _load_intents(self):
        with open(self.intents_path, "r", encoding="utf-8") as f:
            self.intents = json.load(f)

        texts = []
        labels = []
        self.response_map = {}

        for item in self.intents:
            intent = item["intent"]
            self.response_map[intent] = item.get("responses", [])
            for pattern in item["patterns"]:
                texts.append(pattern)
                labels.append(intent)

        self.classes_ = sorted(set(labels))
        self.label_to_idx = {label: i for i, label in enumerate(self.classes_)}
        self.idx_to_label = {i: label for i, label in enumerate(self.classes_)}

        return texts, labels

    def _build_pipeline(self):
        return Pipeline([
            ("tfidf", TfidfVectorizer(
                preprocessor=self.preprocess_text,
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True,
                min_df=1
            )),
            ("clf", LogisticRegression(
                C=10.0,
                max_iter=2000,
                solver="lbfgs",
                random_state=42,
                class_weight="balanced"
            ))
        ])

    def _train(self):
        texts, labels = self._load_intents()
        labels_idx = [self.label_to_idx[l] for l in labels]

        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels_idx, test_size=0.15, random_state=42, stratify=labels_idx
        )

        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True,
                min_df=1
            )),
            ("clf", LogisticRegression(
                C=10.0,
                max_iter=2000,
                solver="lbfgs",
                random_state=42,
                class_weight="balanced"
            ))
        ])

        self.pipeline.fit(texts, labels_idx)

        y_pred = self.pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"[IntentClassifier] Training complete. Accuracy: {acc:.4f}")
        print(f"[IntentClassifier] Params: ngram_range=(1,2), C=10.0, solver=lbfgs")

        joblib.dump(self.pipeline, self.model_path)
        joblib.dump({
            "classes_": self.classes_,
            "label_to_idx": self.label_to_idx,
            "idx_to_label": self.idx_to_label,
            "response_map": self.response_map,
            "intents": self.intents
        }, self.intents_data_path)

    def _load_or_train(self):
        if os.path.exists(self.model_path) and os.path.exists(self.intents_data_path):
            try:
                self.pipeline = joblib.load(self.model_path)
                data = joblib.load(self.intents_data_path)
                self.classes_ = data["classes_"]
                self.label_to_idx = data["label_to_idx"]
                self.idx_to_label = data["idx_to_label"]
                self.response_map = data["response_map"]
                self.intents = data["intents"]
                print("[IntentClassifier] Loaded trained model from disk.")
                return
            except Exception as e:
                print(f"[IntentClassifier] Failed to load model, retraining: {e}")
        self._train()

    def predict(self, text: str, top_k: int = 3):
        if self.pipeline is None:
            raise RuntimeError("Model not loaded or trained.")

        probs = self.pipeline.predict_proba([text])[0]
        top_indices = np.argsort(probs)[::-1][:top_k]

        results = []
        for idx in top_indices:
            label = self.idx_to_label[idx]
            prob = float(probs[idx])
            results.append({
                "intent": label,
                "confidence": prob,
                "responses": self.response_map.get(label, [])
            })
        return results

    def get_intent(self, text: str, threshold: float = 0.3):
        predictions = self.predict(text, top_k=1)
        if not predictions:
            return None
        top = predictions[0]
        if top["confidence"] < threshold:
            return {"intent": "unknown", "confidence": top["confidence"], "responses": []}
        return top

    def retrain(self):
        self._train()
