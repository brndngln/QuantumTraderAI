
from transformers import pipeline
from googletrans import Translator

translator = Translator()
sentiment_pipeline = pipeline("sentiment-analysis")

def analyze_foreign_news(texts, target_lang='en'):
    combined = []
    for text in texts:
        translated = translator.translate(text, dest=target_lang).text
        sentiment = sentiment_pipeline(translated)[0]
        combined.append({"original": text, "translated": translated, "sentiment": sentiment})
    return combined
