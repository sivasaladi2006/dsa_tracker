CREATE TABLE IF NOT EXISTS topics (
    topic_id  INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS topic_prerequisites (
    topic_id   INT NOT NULL,
    prereq_id  INT NOT NULL,
    PRIMARY KEY (topic_id, prereq_id),
    FOREIGN KEY (topic_id)  REFERENCES topics(topic_id),
    FOREIGN KEY (prereq_id) REFERENCES topics(topic_id),
    CHECK (topic_id <> prereq_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS problems (
    problem_id  INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    platform    VARCHAR(50) NOT NULL DEFAULT 'LeetCode',
    difficulty  ENUM('Easy','Medium','Hard') NOT NULL,
    url         VARCHAR(300),
    UNIQUE (platform, title)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS problem_topics (
    problem_id  INT NOT NULL,
    topic_id    INT NOT NULL,
    PRIMARY KEY (problem_id, topic_id),
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id),
    FOREIGN KEY (topic_id)   REFERENCES topics(topic_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS submissions (
    submission_id   INT AUTO_INCREMENT PRIMARY KEY,
    problem_id      INT NOT NULL,
    status          ENUM('Solved','Attempted','Needs Revision') NOT NULL,
    attempts        INT NOT NULL DEFAULT 1,
    time_taken_min  INT,
    submitted_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id),
    CHECK (attempts >= 1),
    CHECK (time_taken_min IS NULL OR time_taken_min >= 0),
    INDEX idx_submissions_problem (problem_id),
    INDEX idx_submissions_date (submitted_at)
) ENGINE=InnoDB;
