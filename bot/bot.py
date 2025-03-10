# -*- coding: utf-8 -*-
"""bot.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1h926xNrzAiQFPBb1wyAI2x3MMumj6bRx
"""

! pip install aiogram scikit-learn gensim numpy requests
! wget https://raw.githubusercontent.com/vifirsanova/compling/main/tasks/task3/faq.json

import json
import requests
import asyncio
import numpy as np
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ContentType
from aiogram.fsm.storage.memory import MemoryStorage
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import Word2Vec

# Импортируем необходимые модули
from aiogram import Bot, Dispatcher, types  # Основные классы для работы с ботом
import logging  # Логирование для отслеживания работы бота
import asyncio  # Модуль для работы с асинхронным кодом
import sys  # Используется для работы с системными вызовами

# Токен API бота (его нужно заменить на реальный токен, полученный у BotFather)
API_TOKEN = "token"

# Настраиваем логирование, чтобы видеть информацию о работе бота в консоли
logging.basicConfig(level=logging.INFO)
# Создаем объект диспетчера, который управляет входящими сообщениями и командами
dp = Dispatcher()

bot = Bot(token=API_TOKEN)

# Загружаем json

# Загружаем json
faq_url = "https://raw.githubusercontent.com/vifirsanova/compling/main/tasks/task3/faq.json"
faq_data = requests.get(faq_url).json()["faq"]

faq_questions = [item["question"] for item in faq_data]
faq_answers = [item["answer"] for item in faq_data]

"""tf-idf"""

# TF-IDF преобразование
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(faq_questions)

# Запрос пользователя
query = "Где мой заказ?"

# Преобразуем запрос в вектор
query_vec = vectorizer.transform([query])

# Вычисляем косинусное сходство
similarities = cosine_similarity(query_vec, tfidf_matrix)

# Ищем индекс наиболее близкого вопроса на основе косинусного сходства
best_match_idx = similarities.argmax()
best_question = faq_questions[best_match_idx]
best_answer = faq_answers[best_match_idx]

# Выводим результат
print(f"Вопрос: {best_question}")
print(f"Ответ: {best_answer}")

"""word2vec"""

# Подгружаем Word2Vec
sentences = [q.split() for q in faq_questions]
word2vec_model = Word2Vec(sentences, vector_size=100, window=5, min_count=1, workers=4)

# Функция для усреднения векторов слов в вопросе
def sentence_vector(sentence, model):
    words = sentence.split()
    vectors = [model.wv[word] for word in words if word in model.wv]
    return np.mean(vectors, axis=0) # Берем среднее значение по всем векторам, чтобы одно предложение представлял один вектор

# Векторизуем вопросы
faq_vectors = np.array([sentence_vector(q, word2vec_model) for q in faq_questions])

# Образец запроса пользователя
query = "Где мой заказ?"
query_vector = sentence_vector(query, word2vec_model).reshape(1, -1)

# Оценка косинусного сходства
similarities = cosine_similarity(query_vector, faq_vectors)
best_match_idx = similarities.argmax()
best_answer = faq_answers[best_match_idx]

print(f"Вопрос: {faq_questions[best_match_idx]}")
print(f"Ответ: {best_answer}")

"""Функция сравнения и выбора лучшего ответа для бота"""

# Функция выбора ответа
def get_best_answer(query):
    query_vec_tfidf = vectorizer.transform([query])
    similarities_tfidf = cosine_similarity(query_vec_tfidf, tfidf_matrix)
    best_match_idx_tfidf = similarities_tfidf.argmax()

    query_vec_w2v = sentence_vector(query, word2vec_model).reshape(1, -1)
    similarities_w2v = cosine_similarity(query_vec_w2v, faq_vectors)
    best_match_idx_w2v = similarities_w2v.argmax()

    if best_match_idx_tfidf == best_match_idx_w2v:
        return faq_answers[best_match_idx_tfidf]

    best_match_idx = best_match_idx_tfidf if similarities_tfidf.max() > similarities_w2v.max() else best_match_idx_w2v
    return faq_answers[best_match_idx]

    """ Функция get_best_answer(query) выбирает наиболее подходящий ответ на вопрос пользователя, сравнивая два метода """

query = "Когда доставят мой заказ?"
print(get_best_answer(query))

"""Кнопки"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создаём кнопки
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="О компании")],
        [KeyboardButton(text="Пожаловаться")]
    ],
    resize_keyboard=True
)

# Обрабатываем команды
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Я бот, отвечающий на вопросы. Выберите кнопку или задайте свой вопрос.", reply_markup=kb)

@dp.message(lambda message: message.text == "О компании")
async def about_company(message: Message):
    await message.answer("Наша компания занимается доставкой товаров по всей стране.")

@dp.message(lambda message: message.text == "Пожаловаться")
async def complain(message: Message):
    await message.answer("Отправьте изображение с жалобой.")

@dp.message(lambda message: message.document)
async def handle_photo(message: Message):
    photo = message.document
    file_size = photo.file_size
    file_name = photo.file_name

    await message.answer(f"Название файла: {file_name}\nРазмер файла: {file_size} байт")
    await message.answer("Ваш запрос передан специалисту.")

# Обработка вопросов
@dp.message()
async def handle_question(message: Message):
    user_question = message.text
    answer = get_best_answer(user_question)
    await message.answer(answer)

# Запуск бота
async def main():
    bot = Bot(token=API_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    await main()