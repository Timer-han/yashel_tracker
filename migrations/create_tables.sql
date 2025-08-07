-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    gender TEXT,
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

-- Таблица намазов
CREATE TABLE IF NOT EXISTS prayers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    prayer_type TEXT NOT NULL,
    total_missed INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, prayer_type)
);

-- Таблица истории намазов
CREATE TABLE IF NOT EXISTS prayer_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    prayer_type TEXT NOT NULL,
    action TEXT NOT NULL,
    amount INTEGER NOT NULL,
    previous_value INTEGER NOT NULL,
    new_value INTEGER NOT NULL,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Таблица администраторов
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    role TEXT NOT NULL,
    added_by INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_prayers_user_id ON prayers(user_id);
CREATE INDEX IF NOT EXISTS idx_prayer_history_user_id ON prayer_history(user_id);
CREATE INDEX IF NOT EXISTS idx_admins_telegram_id ON admins(telegram_id);