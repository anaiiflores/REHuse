-- ReHuse Unified Backend — Database Schema
-- Single database serving both physio web and patient mobile app

SET NAMES utf8mb4;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;

CREATE DATABASE IF NOT EXISTS rehuse_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rehuse_db;

-- ─────────────────────────────────────────────
-- USERS  (physios, patients, admins)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                    VARCHAR(36)   NOT NULL DEFAULT (UUID()),
    email                 VARCHAR(255)  NOT NULL,
    password_hash         VARCHAR(255)  NOT NULL,
    role                  VARCHAR(20)   NOT NULL DEFAULT 'patient',  -- physio / patient / admin
    name                  VARCHAR(100)  NOT NULL,
    phone                 VARCHAR(20)   NULL,
    profile_image_url     TEXT          NULL,
    push_token            TEXT          NULL,
    notifications_enabled BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- PATIENT PROFILES  (extra info for patients)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patient_profiles (
    id            VARCHAR(36)   NOT NULL DEFAULT (UUID()),
    user_id       VARCHAR(36)   NOT NULL,
    physio_id     VARCHAR(36)   NULL,            -- which physio manages this patient
    dni           VARCHAR(20)   NULL,
    birth_date    DATE          NULL,
    weight        DECIMAL(5,2)  NULL,            -- kg
    height        DECIMAL(5,2)  NULL,            -- cm
    notes         TEXT          NULL,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_pp_user (user_id),
    CONSTRAINT fk_pp_user   FOREIGN KEY (user_id)   REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_pp_physio FOREIGN KEY (physio_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- EXERCISES  (global catalog)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS exercises (
    id                     VARCHAR(36)   NOT NULL DEFAULT (UUID()),
    name                   VARCHAR(200)  NOT NULL,
    description            TEXT          NULL,
    series                 INT           NULL,
    reps                   INT           NULL,
    minutes                INT           NULL,
    image_url              TEXT          NULL,
    video_url              TEXT          NULL,
    angle                  VARCHAR(20)   NULL,   -- FRONTAL, LATERAL, SUPERIOR
    total_duration_seconds INT           NULL,
    rhythm                 VARCHAR(20)   NULL,   -- LENTO, NORMAL, INTENSO
    rest_after_seconds     INT           NULL,
    created_by             VARCHAR(36)   NULL,   -- physio user id
    created_at             DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_ex_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- EXERCISE IMAGES  (multiple images per exercise)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS exercise_images (
    id          VARCHAR(36)  NOT NULL DEFAULT (UUID()),
    exercise_id VARCHAR(36)  NOT NULL,
    url         TEXT         NOT NULL,
    order_index INT          NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    CONSTRAINT fk_ei_exercise FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- ASSIGNED SESSIONS  (physio assigns to patient)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS assigned_sessions (
    id             VARCHAR(36)   NOT NULL DEFAULT (UUID()),
    physio_id      VARCHAR(36)   NOT NULL,
    patient_id     VARCHAR(36)   NOT NULL,   -- references users.id (patient)
    title          VARCHAR(200)  NOT NULL,
    scheduled_date DATE          NULL,
    scheduled_time TIME          NULL,
    notes          TEXT          NULL,
    difficulty     VARCHAR(10)   NOT NULL DEFAULT 'MEDIA',  -- BAJA, MEDIA, ALTA
    status         VARCHAR(20)   NOT NULL DEFAULT 'PENDING', -- PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    seen_by_patient BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_as_physio  FOREIGN KEY (physio_id)  REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_as_patient FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- ASSIGNED SESSION EXERCISES  (exercises within an assigned session)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS assigned_session_exercises (
    id                  VARCHAR(36)  NOT NULL DEFAULT (UUID()),
    assigned_session_id VARCHAR(36)  NOT NULL,
    exercise_id         VARCHAR(36)  NOT NULL,
    order_index         INT          NOT NULL DEFAULT 0,
    series              INT          NULL,
    reps                INT          NULL,
    rest_seconds        INT          NULL,
    duration_seconds    INT          NULL,
    notes               TEXT         NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_ase_order (assigned_session_id, order_index),
    CONSTRAINT fk_ase_session  FOREIGN KEY (assigned_session_id) REFERENCES assigned_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_ase_exercise FOREIGN KEY (exercise_id)         REFERENCES exercises(id)         ON DELETE CASCADE
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- WORKOUT LOGS  (patient executes a session)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS workout_logs (
    id                  VARCHAR(36)  NOT NULL DEFAULT (UUID()),
    assigned_session_id VARCHAR(36)  NOT NULL,
    patient_id          VARCHAR(36)  NOT NULL,
    started_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at        DATETIME     NULL,
    status              VARCHAR(20)  NOT NULL DEFAULT 'in_progress',  -- in_progress, completed, abandoned
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_wl_session FOREIGN KEY (assigned_session_id) REFERENCES assigned_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_wl_patient FOREIGN KEY (patient_id)          REFERENCES users(id)             ON DELETE CASCADE
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- EXERCISE LOGS  (per-exercise progress within a workout)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS exercise_logs (
    id             VARCHAR(36)  NOT NULL DEFAULT (UUID()),
    workout_log_id VARCHAR(36)  NOT NULL,
    exercise_id    VARCHAR(36)  NOT NULL,
    started_at     DATETIME     NULL,
    completed_at   DATETIME     NULL,
    skipped        BOOLEAN      NOT NULL DEFAULT FALSE,
    skip_reason    VARCHAR(100) NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_el_workout  FOREIGN KEY (workout_log_id) REFERENCES workout_logs(id) ON DELETE CASCADE,
    CONSTRAINT fk_el_exercise FOREIGN KEY (exercise_id)    REFERENCES exercises(id)    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- NOTIFICATIONS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id           VARCHAR(36)   NOT NULL DEFAULT (UUID()),
    user_id      VARCHAR(36)   NOT NULL,
    type         VARCHAR(30)   NOT NULL,  -- message, reminder, sessionComplete, newAssignment
    title        VARCHAR(200)  NOT NULL,
    body         TEXT          NOT NULL,
    is_read      BOOLEAN       NOT NULL DEFAULT FALSE,
    has_action   BOOLEAN       NOT NULL DEFAULT FALSE,
    action_label VARCHAR(100)  NULL,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

SET foreign_key_checks = 1;

-- ═════════════════════════════════════════════
-- SEED DATA
-- ═════════════════════════════════════════════

-- Physio: fisio@rehuse.com / password: 1234
-- bcrypt hash for "1234" (rounds=12)
INSERT INTO users (id, email, password_hash, role, name, phone)
VALUES (
    'u-fisio-000-0000-0000-000000000001',
    'fisio@rehuse.com',
    '$2b$12$hQuPrXp7Akw0.tEYmobg3eWPycSJ/QRs2jEmB5UGfpwlg22qGWREu',
    'physio',
    'Dr. García López',
    '+34 600 123 456'
);

-- Admin/Physio: admin@rehuse.com / password: 1234 (cuenta del superadmin de ReHuse)
INSERT INTO users (id, email, password_hash, role, name, phone)
VALUES (
    'u-admin-000-0000-0000-000000000099',
    'admin@rehuse.com',
    '$2b$12$hQuPrXp7Akw0.tEYmobg3eWPycSJ/QRs2jEmB5UGfpwlg22qGWREu',
    'physio',
    'Anai',
    '600000000'
);

-- Patient 1: ana@rehuse.com / password: 1234
INSERT INTO users (id, email, password_hash, role, name)
VALUES (
    'u-ana-0000-0000-0000-000000000001',
    'ana@rehuse.com',
    '$2b$12$hQuPrXp7Akw0.tEYmobg3eWPycSJ/QRs2jEmB5UGfpwlg22qGWREu',
    'patient',
    'Ana Martínez'
);

-- Patient 2: carlos@rehuse.com / password: 1234
INSERT INTO users (id, email, password_hash, role, name)
VALUES (
    'u-carlos-00-0000-0000-000000000002',
    'carlos@rehuse.com',
    '$2b$12$hQuPrXp7Akw0.tEYmobg3eWPycSJ/QRs2jEmB5UGfpwlg22qGWREu',
    'patient',
    'Carlos Ruiz'
);

-- Patient profiles
INSERT INTO patient_profiles (id, user_id, physio_id, birth_date, weight, height)
VALUES
    (UUID(), 'u-ana-0000-0000-0000-000000000001', 'u-fisio-000-0000-0000-000000000001', '1992-12-01', 62.5, 164.0),
    (UUID(), 'u-carlos-00-0000-0000-000000000002', 'u-fisio-000-0000-0000-000000000001', '1988-05-15', 78.0, 178.0);

-- Exercises catalog
INSERT INTO exercises (id, name, description, series, reps, minutes, angle, rhythm, rest_after_seconds)
VALUES
    ('e-knee-0000-0000-0000-000000000001', 'Extensión de Rodilla', 'Extiende la rodilla completamente desde posición sentada. Mantén 2 segundos arriba.', 3, 12, NULL, 'LATERAL', 'NORMAL', 15),
    ('e-hamst-0000-0000-0000-000000000002', 'Estiramiento de Isquiotibiales', 'Mantén la posición 30 segundos por serie. Respira profundo.', 3, NULL, NULL, 'LATERAL', 'LENTO', 20),
    ('e-squat-0000-0000-0000-000000000003', 'Sentadillas', 'Baja lentamente hasta 90° y sube controlado. Pies al ancho de hombros.', 3, 10, NULL, 'FRONTAL', 'NORMAL', 15),
    ('e-rotat-0000-0000-0000-000000000004', 'Rotación de Hombros', 'Círculos completos hacia adelante y atrás. Mantén espalda recta.', 3, 10, NULL, 'FRONTAL', 'NORMAL', 10),
    ('e-pecto-0000-0000-0000-000000000005', 'Estiramiento Pectoral', 'Apoya el brazo en la pared a 90° y rota el cuerpo. Mantén 2 minutos.', NULL, NULL, 2, 'LATERAL', 'LENTO', 15);

-- Assigned session: physio assigns to Ana (today)
INSERT INTO assigned_sessions (id, physio_id, patient_id, title, scheduled_date, notes, difficulty, status, seen_by_patient)
VALUES (
    'as-ana-0001-0000-0000-000000000001',
    'u-fisio-000-0000-0000-000000000001',
    'u-ana-0000-0000-0000-000000000001',
    'Rehabilitación Hombro — Semana 1',
    CURDATE(),
    'Empezar suave. Avisar si hay dolor agudo.',
    'BAJA',
    'PENDING',
    FALSE
);

-- Exercises in that assigned session
INSERT INTO assigned_session_exercises (id, assigned_session_id, exercise_id, order_index, series, reps, rest_seconds)
VALUES
    (UUID(), 'as-ana-0001-0000-0000-000000000001', 'e-rotat-0000-0000-0000-000000000004', 1, 3, 10, 15),
    (UUID(), 'as-ana-0001-0000-0000-000000000001', 'e-pecto-0000-0000-0000-000000000005', 2, NULL, NULL, 20),
    (UUID(), 'as-ana-0001-0000-0000-000000000001', 'e-hamst-0000-0000-0000-000000000002', 3, 3, NULL, 20);

-- Notification for Ana: new session assigned
INSERT INTO notifications (id, user_id, type, title, body, is_read, has_action, action_label)
VALUES (
    UUID(),
    'u-ana-0000-0000-0000-000000000001',
    'newAssignment',
    'Nueva sesión asignada',
    'El Dr. García López te ha asignado una sesión de rehabilitación para hoy.',
    FALSE,
    TRUE,
    'Ver sesión'
);
