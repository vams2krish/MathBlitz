-- Reference PostgreSQL schema for managed production deployments.
-- Local development initializes the equivalent tables through SQLAlchemy.

CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(40) NOT NULL,
    canonical_username VARCHAR(40) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE user_preferences (
    user_id VARCHAR(36) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_activity_id VARCHAR(50) NOT NULL DEFAULT 'shopping-value',
    default_difficulty VARCHAR(20) NOT NULL DEFAULT 'Medium'
        CHECK (default_difficulty IN ('Very Easy', 'Easy', 'Medium', 'Hard', 'Extreme Hard')),
    sound_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE task_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_id VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) NOT NULL
        CHECK (difficulty IN ('Very Easy', 'Easy', 'Medium', 'Hard', 'Extreme Hard')),
    prompt VARCHAR(500) NOT NULL,
    hint VARCHAR(300) NOT NULL,
    answer_mode VARCHAR(20) NOT NULL,
    correct_answer NUMERIC(16,2) NOT NULL,
    context JSON NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX ix_tasks_user_created ON task_sessions(user_id, created_at);
CREATE INDEX ix_tasks_expires ON task_sessions(expires_at);

CREATE TABLE attempts (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL UNIQUE REFERENCES task_sessions(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_id VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) NOT NULL
        CHECK (difficulty IN ('Very Easy', 'Easy', 'Medium', 'Hard', 'Extreme Hard')),
    submitted_answer NUMERIC(16,2) NOT NULL,
    result_status VARCHAR(20) NOT NULL
        CHECK (result_status IN ('correct', 'incorrect', 'timeout')),
    points INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER NOT NULL,
    submitted_at TIMESTAMP NOT NULL
);

CREATE INDEX ix_attempts_user_submitted ON attempts(user_id, submitted_at);
CREATE INDEX ix_attempts_activity_difficulty ON attempts(activity_id, difficulty);
