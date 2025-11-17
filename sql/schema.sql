CREATE DATABASE IF NOT EXISTS lost_found_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE lost_found_portal;

CREATE TABLE users (
  id             BIGINT AUTO_INCREMENT PRIMARY KEY,
  name           VARCHAR(100) NOT NULL,
  email          VARCHAR(255) NOT NULL UNIQUE,
  password_hash  VARCHAR(255) NOT NULL,
  role           ENUM('user', 'admin') NOT NULL DEFAULT 'user',
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE items (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id       BIGINT NOT NULL,
  type          ENUM('lost', 'found') NOT NULL,
  title         VARCHAR(255) NOT NULL,
  description   TEXT,
  category      VARCHAR(100),
  location      VARCHAR(255),
  date_reported DATE,
  status        ENUM('open', 'matched', 'closed') DEFAULT 'open',
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE item_images (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  item_id     BIGINT NOT NULL,
  image_url   VARCHAR(512) NOT NULL,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE TABLE image_features (
  id           BIGINT AUTO_INCREMENT PRIMARY KEY,
  image_id     BIGINT NOT NULL,
  model_name   VARCHAR(100) NOT NULL,
  feature_dim  INT NOT NULL,
  feature_vec  BLOB NOT NULL,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (image_id) REFERENCES item_images(id) ON DELETE CASCADE
);
