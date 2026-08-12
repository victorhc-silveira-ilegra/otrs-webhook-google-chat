CREATE DATABASE IF NOT EXISTS otrs;
USE otrs;

CREATE TABLE IF NOT EXISTS queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    UNIQUE KEY queue_name (name)
);

CREATE TABLE IF NOT EXISTS ticket (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tn VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    queue_id INT NOT NULL,
    ticket_state_id INT NOT NULL,
    create_time DATETIME NOT NULL,
    KEY ticket_title (title),
    KEY ticket_create_time (create_time),
    CONSTRAINT fk_ticket_queue FOREIGN KEY (queue_id) REFERENCES queue (id)
);

CREATE TABLE IF NOT EXISTS gchat_alert_dispatch (
    ticket_id BIGINT NOT NULL,
    dedup_hash CHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    queue_name VARCHAR(200) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (ticket_id),
    UNIQUE KEY uq_gchat_alert_dedup_hash (dedup_hash),
    KEY idx_gchat_alert_created_at (created_at)
);

INSERT INTO queue (id, name)
VALUES (1, 'Raw'), (2, 'CloudTeam')
ON DUPLICATE KEY UPDATE name = VALUES(name);
