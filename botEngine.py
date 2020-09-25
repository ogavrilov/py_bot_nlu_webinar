import codecs
import random
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC


class botEngineClass:

    def __init__(self, botconfigfilename=None, dialogsfilename=None):
        self.bot_alowable_probe_value = 0.1
        self.stats = {'intent': 0, 'generative': 0, 'fails': 0}
        self.__prepareBotConfig__(botconfigfilename)
        self.__prepareBotDialogs__(dialogsfilename)

    @staticmethod
    def __clearText__(text):
        text = text.lower()
        alphabet = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя0123456789- abcdefghijklmnopqrstuvwxyz'
        result = ''
        for c in text:
            if c in alphabet:
                result += c
        return result

    def __prepareBotConfig__(self, botconfigfilename):
        if botconfigfilename:
            with codecs.open(botconfigfilename, 'r', 'utf-8-sig') as fileHandle:
                filetext = fileHandle.read()
                self.bot_config = eval(filetext)
            # prepare dataset for model study
            dataset = []
            for intent, intent_data in self.bot_config['intents'].items():
                for example in intent_data['examples']:
                    dataset.append([example, intent])
            corpus = [text for text, intent in dataset]
            y = [intent for text, intent in dataset]
            # prepare vectors from dataset
            self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3))
            x = self.vectorizer.fit_transform(corpus)
            # prepare model and study
            self.clf = SVC(probability=True)
            self.clf.fit(x, y)

    def __prepareBotDialogs__(self, dialogsfilename):
        self.search_dataset = {}
        if dialogsfilename:
            with codecs.open(dialogsfilename, 'r', 'utf-8-sig') as fileHandle:
                content = fileHandle.read()
            blocks = content.split('\n\n')
            dataset = []
            questions = set()
            for block in blocks:
                replicas = block.split('\n')[:2]
                if len(replicas) == 2:
                    question = self.__clearText__(replicas[0][2:])
                    answer = replicas[1][2:]
                    if question and answer and question not in questions:
                        questions.add(question)
                        dataset.append([question, answer])
            # prepare search dataset (all words)
            search_dataset = {}
            for question, answer in dataset:
                words = question.split(' ')
                for word in words:
                    if word not in search_dataset:
                        search_dataset[word] = []
                    search_dataset[word].append((question, answer))
            # prepare search dataset (rare words)
            self.search_dataset = {
                word: word_dataset
                for word, word_dataset in search_dataset.items()
                if len(word_dataset) < 1000
            }

    def get_intent(self, text):
        proba_list = self.clf.predict_proba(self.vectorizer.transform([text]))[0]
        max_proba = max(proba_list)
        # print(text, self.clf.predict(self.vectorizer.transform([text])), max_proba)
        if max_proba > self.bot_alowable_probe_value:
            index = list(proba_list).index(max_proba)
            return self.clf.classes_[index]

    def get_response_by_intent(self, intent):
        phrases = self.bot_config['intents'][intent]['responses']
        return random.choice(phrases)

    def get_response_generatively(self, text):
        text = self.__clearText__(text)
        if not text:
            return
        words = text.split(' ')
        words_dataset = set()
        for word in words:
            if word in self.search_dataset:
                words_dataset |= set(self.search_dataset[word])
        scores = []
        for question, answer in words_dataset:
            if abs(len(text) - len(question)) / len(question) < 0.4:
                distance = nltk.edit_distance(text, question)
                score = distance / len(question)
                if score < 0.4:
                    scores.append([score, question, answer])
        if scores:
            return min(scores, key=lambda s: s[0])[2]

    def get_failure_phrase(self):
        phrases = self.bot_config['failure_phrases']
        return random.choice(phrases)

    def get_answer(self, request):
        # NLU
        intent = self.get_intent(request)

        # Генерация ответа
        if intent:
            self.stats['intent'] += 1
            return self.get_response_by_intent(intent)

        response = self.get_response_generatively(request)
        if response:
            self.stats['generative'] += 1
            return response

        self.stats['fails'] += 1
        return self.get_failure_phrase()
