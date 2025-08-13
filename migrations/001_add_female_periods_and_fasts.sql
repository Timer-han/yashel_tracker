-- migrations/001_add_female_periods_and_fasts.sql

-- Добавляем новые столбцы в таблицу users (только если их еще нет)
ALTER TABLE users ADD COLUMN childbirth_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN childbirths TEXT DEFAULT '[]';
ALTER TABLE users ADD COLUMN hyde_periods TEXT DEFAULT '[]';
ALTER TABLE users ADD COLUMN nifas_lengths TEXT DEFAULT '[]';

-- Создаем новую таблицу пользователей без ненужных полей
CREATE TABLE IF NOT EXISTS users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    gender TEXT,
    birth_date DATE,
    city TEXT,
    role TEXT DEFAULT 'user',
    is_registered BOOLEAN DEFAULT FALSE,
    prayer_start_date DATE,
    adult_date DATE,
    childbirth_count INTEGER DEFAULT 0,
    childbirths TEXT DEFAULT '[]',
    hyde_periods TEXT DEFAULT '[]',
    nifas_lengths TEXT DEFAULT '[]',
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Копируем данные из старой таблицы (если новая таблица пуста)
INSERT OR IGNORE INTO users_new (
    id, telegram_id, username, gender, birth_date, city, role, 
    is_registered, prayer_start_date, adult_date, childbirth_count,
    childbirths, hyde_periods, nifas_lengths, last_activity, created_at, updated_at
)
SELECT 
    id, telegram_id, username, gender, birth_date, city, role,
    is_registered, prayer_start_date, adult_date,
    COALESCE(childbirth_count, 0),
    COALESCE(childbirths, '[]'),
    COALESCE(hyde_periods, '[]'),
    COALESCE(nifas_lengths, '[]'),
    last_activity, created_at, updated_at
FROM users;

-- Переименовываем таблицы
DROP TABLE IF EXISTS users_old;
ALTER TABLE users RENAME TO users_old;
ALTER TABLE users_new RENAME TO users;

-- Создаем таблицу для постов
CREATE TABLE IF NOT EXISTS fasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fast_type TEXT NOT NULL,
    total_missed INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
    UNIQUE(user_id, fast_type)
);

-- Создаем таблицу истории постов
CREATE TABLE IF NOT EXISTS fast_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fast_type TEXT NOT NULL,
    action TEXT NOT NULL,
    amount INTEGER NOT NULL,
    previous_value INTEGER NOT NULL,
    new_value INTEGER NOT NULL,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
);

-- Индексы для новых таблиц
CREATE INDEX IF NOT EXISTS idx_fasts_user_id ON fasts(user_id);
CREATE INDEX IF NOT EXISTS idx_fast_history_user_id ON fast_history(user_id);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id_new ON users(telegram_id);