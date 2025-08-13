from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List
from ....core.config import config

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Основное меню пользователя"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="📊 Моя статистика"))
    builder.add(KeyboardButton(text="🔢 Расчет намазов"))
    builder.add(KeyboardButton(text="➕ Отметить намазы"))
    builder.add(KeyboardButton(text="🥗 Расчет постов"))
    builder.add(KeyboardButton(text="🥗 Отметить посты"))
    builder.add(KeyboardButton(text="⚙️ Настройки"))
    builder.add(KeyboardButton(text="ℹ️ Помощь"))
    
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup(resize_keyboard=True)

def get_moderator_menu_keyboard() -> ReplyKeyboardMarkup:
    """Меню модератора"""
    builder = ReplyKeyboardBuilder()
    
    # Обычные функции пользователя
    builder.add(KeyboardButton(text="📊 Моя статистика"))
    builder.add(KeyboardButton(text="🔢 Расчет намазов"))
    builder.add(KeyboardButton(text="➕ Отметить намазы"))
    builder.add(KeyboardButton(text="🥗 Расчет постов"))
    builder.add(KeyboardButton(text="🥗 Отметить посты"))
    
    # Функции модератора
    builder.add(KeyboardButton(text="📈 Общая статистика"))
    builder.add(KeyboardButton(text="📢 Рассылка"))
    
    builder.add(KeyboardButton(text="⚙️ Настройки"))
    builder.add(KeyboardButton(text="ℹ️ Помощь"))
    
    builder.adjust(3, 2, 2, 2)
    
    return builder.as_markup(resize_keyboard=True)

def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Меню администратора"""
    builder = ReplyKeyboardBuilder()
    
    # Обычные функции пользователя
    builder.add(KeyboardButton(text="📊 Моя статистика"))
    builder.add(KeyboardButton(text="🔢 Расчет намазов"))
    builder.add(KeyboardButton(text="➕ Отметить намазы"))
    builder.add(KeyboardButton(text="🥗 Расчет постов"))
    builder.add(KeyboardButton(text="🥗 Отметить посты"))
    
    # Функции модератора
    builder.add(KeyboardButton(text="📈 Общая статистика"))
    builder.add(KeyboardButton(text="📢 Рассылка"))
    
    # Функции администратора
    
    builder.add(KeyboardButton(text="⚙️ Настройки"))
    builder.add(KeyboardButton(text="ℹ️ Помощь"))
    builder.add(KeyboardButton(text="👥 Управление админами"))
    
    builder.adjust(3, 2, 2, 2, 1)
    
    return builder.as_markup(resize_keyboard=True)