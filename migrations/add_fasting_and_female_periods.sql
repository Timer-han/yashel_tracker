-- Миграция для добавления поддержки постов и женских периодов

-- 1. Добавляем новые поля в таблицу users
ALTER TABLE users ADD COLUMN fasting_start_date DATE;
ALTER TABLE users ADD COLUMN has_childbirth BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN childbirth_count INTEGER DEFAULT 0;

-- 2. Создаем таблицу для хранения информации о хайд
CREATE TABLE IF NOT EXISTS hayd_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    average_duration INTEGER NOT NULL, -- средняя продолжительность в днях
    period_number INTEGER DEFAULT 0, -- номер периода (0 - общий, 1 - до первых родов, 2 - после первых и т.д.)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, period_number)
);

-- 3. Создаем таблицу для информации о нифас (послеродовой период)
CREATE TABLE IF NOT EXISTS nifas_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    childbirth_number INTEGER NOT NULL, -- номер родов
    childbirth_date DATE NOT NULL,
    nifas_duration INTEGER NOT NULL, -- продолжительность нифаса в днях (макс 40)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, childbirth_number)
);

-- 4. Создаем таблицу для постов
CREATE TABLE IF NOT EXISTS fasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fast_type TEXT NOT NULL, -- 'ramadan', 'shawwal', 'other'
    year INTEGER, -- год для рамадана
    total_missed INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, fast_type, year)
);

-- 5. Создаем таблицу истории постов
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
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- 6. Удаляем ненужные поля из users (сохраняем данные в full_name)
-- Сначала обновляем full_name для тех, у кого его нет
UPDATE users 
SET full_name = COALESCE(full_name, TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')))
WHERE full_name IS NULL OR full_name = '';

-- Создаем новую таблицу без first_name и last_name
CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    full_name TEXT,
    gender TEXT,
    birth_date DATE,
    city TEXT,
    role TEXT DEFAULT 'user',
    is_registered BOOLEAN DEFAULT FALSE,
    prayer_start_date DATE,
    adult_date DATE,
    fasting_start_date DATE,
    has_childbirth BOOLEAN DEFAULT FALSE,
    childbirth_count INTEGER DEFAULT 0,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Копируем данные
INSERT INTO users_new (
    id, telegram_id, username, full_name, gender, birth_date, 
    city, role, is_registered, prayer_start_date, adult_date,
    last_activity, created_at, updated_at
)
SELECT 
    id, telegram_id, username, full_name, gender, birth_date,
    city, role, is_registered, prayer_start_date, adult_date,
    last_activity, created_at, updated_at
FROM users;

-- Удаляем старую таблицу и переименовываем новую
DROP TABLE users;
ALTER TABLE users_new RENAME TO users;

-- Создаем индексы
CREATE INDEX IF NOT EXISTS idx_hayd_info_user_id ON hayd_info(user_id);
CREATE INDEX IF NOT EXISTS idx_nifas_info_user_id ON nifas_info(user_id);
CREATE INDEX IF NOT EXISTS idx_fasts_user_id ON fasts(user_id);
CREATE INDEX IF NOT EXISTS idx_fast_history_user_id ON fast_history(user_id);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);