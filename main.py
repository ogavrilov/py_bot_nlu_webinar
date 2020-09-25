from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
import random
import nltk
import codecs
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

BOT_CONFIG = {}
with codecs.open('final_config.py', 'r', 'utf-8-sig') as fileHandle:
    filetext = fileHandle.read()
    BOT_CONFIG = eval(filetext)

BOT_ALLOWABLE_PROBA_VALUE = 0.1

# prepare dataset for model study
dataset = []

for intent, intent_data in BOT_CONFIG['intents'].items():
    for example in intent_data['examples']:
        dataset.append([example, intent])

corpus = [text for text, intent in dataset]
y = [intent for text, intent in dataset]

# prepare vectors from dataset
vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3))
X = vectorizer.fit_transform(corpus)

# prepare model and study
clf = SVC(probability=True)
clf.fit(X, y)

# method return intent name by text and model
def get_intent(text):
    proba_list = clf.predict_proba(vectorizer.transform([text]))[0]
    max_proba = max(proba_list)
    print(text, clf.predict(vectorizer.transform([text])), max_proba)
    if max_proba > BOT_ALLOWABLE_PROBA_VALUE:
        index = list(proba_list).index(max_proba)
        return clf.classes_[index]

def get_response_by_intent(intent):
    phrases = BOT_CONFIG['intents'][intent]['responses']
    return random.choice(phrases)

# prepare dialogs for alternate answer algorithm
with codecs.open('dialogs.txt', 'r', 'utf-8') as fileHandle:
    content = fileHandle.read()

blocks = content.split('\n\n')

def clear_text(text):
    text = text.lower()
    alphabet = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя0123456789- '
    result = ''
    for c in text:
        if c in alphabet:
            result += c
    return result

dataset = []
questions = set()

for block in blocks:
    replicas = block.split('\n')[:2]
    if len(replicas) == 2:
        question = clear_text(replicas[0][2:])
        answer = replicas[1][2:]

        if question and answer and question not in questions:
            questions.add(question)
            dataset.append([question, answer])

search_dataset = {}
for question, answer in dataset:
    words = question.split(' ')
    for word in words:
        if word not in search_dataset:
            search_dataset[word] = []
        search_dataset[word].append((question, answer))

search_dataset = {
    word: word_dataset
    for word, word_dataset in search_dataset.items()
    if len(word_dataset) < 1000
}


def get_response_generatively(text):
    text = clear_text(text)
    if not text:
        return
    words = text.split(' ')

    words_dataset = set()
    for word in words:
        if word in search_dataset:
            words_dataset |= set(search_dataset[word])

    scores = []

    for question, answer in words_dataset:
        if abs(len(text) - len(question)) / len(question) < 0.4:
            distance = nltk.edit_distance(text, question)
            score = distance / len(question)
            if score < 0.4:
                scores.append([score, question, answer])

    if scores:
        return min(scores, key=lambda s: s[0])[2]

def get_failure_phrase():
    phrases = BOT_CONFIG['failure_phrases']
    return random.choice(phrases)

stats = {'intent': 0, 'generative': 0, 'fails': 0}

def bot(request):
    # NLU
    intent = get_intent(request)

    # Генерация ответа
    if intent:
        stats['intent'] += 1
        return get_response_by_intent(intent)

    response = get_response_generatively(request)
    if response:
        stats['generative'] += 1
        return response

    stats['fails'] += 1
    return get_failure_phrase()

def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')

def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def use_bot(update, context):
    answer = bot(update.message.text)
    update.message.reply_text(answer)
    print(update.message.text, answer)
    print(stats)
    print()

def main():
    """Start the bot."""
    print('bot start...')
    updater = Updater("1334319003:AAERj4ZihFAN34oX_rxfCjWJfqfciayMCP8", use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, use_bot))

    updater.start_polling()
    updater.idle()

main()