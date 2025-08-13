-- 1. Создаем новую таблицу с правильной структурой
CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    gender TEXT,
    childbirth_count INTEGER DEFAULT 0,
    childbirths TEXT DEFAULT '[]',
    hyde_periods TEXT DEFAULT '[]',
    nifas_lengths TEXT DEFAULT '[]',
    birth_date DATE,
    city TEXT,
    role TEXT DEFAULT 'user',
    is_registered BOOLEAN DEFAULT FALSE,
    prayer_start_date DATE,
    adult_date DATE,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Копируем данные из старой таблицы в новую
INSERT INTO users_new (
    telegram_id, username, gender, birth_date, city, role, 
    is_registered, prayer_start_date, adult_date, 
    last_activity, created_at, updated_at
)
SELECT 
    telegram_id, username, gender, birth_date, city, role, 
    is_registered, prayer_start_date, adult_date, 
    last_activity, created_at, updated_at
FROM users;

-- 3. Удаляем старую таблицу
DROP TABLE users;

-- 4. Переименовываем новую таблицу
ALTER TABLE users_new RENAME TO users;

-- 5. Пересоздаем индексы
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);