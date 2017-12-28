"""
This module contains the sql pragmas to generate the sqlite database.
"""


# Pragmas relating to samples

PRAGMA_SAMPLES = """
            DROP TABLE IF EXISTS "samples";

            CREATE TABLE "samples" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `name`          TEXT        NOT NULL,
                `batch`         TEXT        NOT NULL,

                `contact`       TEXT        NOT NULL,
                `source`        TEXT        NOT NULL,
                `type`          TEXT        NOT NULL,

                `project`       TEXT,
                `struct`        TEXT,
                `form`          TEXT,
                `comment`       TEXT,

                UNIQUE(name,batch)
                FOREIGN KEY(`contact`)      REFERENCES `contacts`(`nick`),
                FOREIGN KEY(`source`)       REFERENCES `sources`(`nick`),
                FOREIGN KEY(`type`)         REFERENCES `sample_type`(`type`)
                );
"""

PRAGMA_SAMPLE_TYPE = """
            DROP TABLE IF EXISTS "sample_type";

            CREATE TABLE "sample_type" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT        NOT NULL UNIQUE,
                `name`          TEXT
                );
"""

PRAGMA_SAMPLE_PROPERTIES = """

            DROP TABLE IF EXISTS "sample_properties";

            CREATE TABLE "sample_properties" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `sample_id`     INTEGER     NOT NULL,
                `type`          TEXT        NOT NULL,
                `value`         TEXT,

                FOREIGN KEY(`sample_id`)    REFERENCES `samples`(`id`),
                FOREIGN KEY(`type`)         REFERENCES 'sample_properties_type'('type')
                );
"""

PRAGMA_SAMPLE_PROPERTY_TYPE = """

            DROP TABLE IF EXISTS "sample_properties_type";

            CREATE TABLE "sample_properties_type" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT        NOT NULL UNIQUE,
                `unit`          TEXT
                );
"""


# Pragmas relating to experiments

PRAGMA_EXPERIMENTS = """
            DROP TABLE IF EXISTS "experiments";

            CREATE TABLE "experiments" (
                `id`            TEXT        NOT NULL PRIMARY KEY UNIQUE,
                `sample_name`   TEXT        NOT NULL,
                `sample_batch`  TEXT        NOT NULL,
                `t_exp`         REAL        NOT NULL,
                `adsorbate`     TEXT        NOT NULL,

                `exp_type`      TEXT        NOT NULL,
                `machine`       TEXT        NOT NULL,
                `user`          TEXT        NOT NULL,

                `date`          TEXT,
                `is_real`       INTEGER,
                `t_act`         REAL,
                `lab`           TEXT,
                `project`       TEXT,
                `comment`       TEXT,

                FOREIGN KEY(`sample_name`,`sample_batch`)   REFERENCES `samples`(`name`,`batch`),
                FOREIGN KEY(`exp_type`)         REFERENCES `experiment_type`(`type`),
                FOREIGN KEY(`machine`)          REFERENCES `machines`(`nick`),
                FOREIGN KEY(`user`)             REFERENCES `contacts`(`nick`),
                FOREIGN KEY(`adsorbate`)        REFERENCES `adsorbates`(`nick`)
                );
"""

PRAGMA_EXPERIMENT_TYPE = """

            DROP TABLE IF EXISTS "experiment_type";

            CREATE TABLE "experiment_type" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT        NOT NULL UNIQUE,
                `name`          TEXT
                );
"""
PRAGMA_EXPERIMENT_PROPERTIES = """

            DROP TABLE IF EXISTS "experiment_properties";

            CREATE TABLE "experiment_properties" (
                `id`            INTEGER         NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `exp_id` INTEGER         NOT NULL,
                `type`          TEXT            NOT NULL,
                `value`         TEXT            NOT NULL,

                FOREIGN KEY(`exp_id`)    REFERENCES `experiments`(`id`),
                FOREIGN KEY(`type`)             REFERENCES 'experiment_properties_type'('type')
                );
"""

PRAGMA_EXPERIMENT_PROPERTY_TYPE = """

            DROP TABLE IF EXISTS "experiment_properties_type";

            CREATE TABLE "experiment_properties_type" (
                `id`            INTEGER         NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT            NOT NULL UNIQUE,
                `unit`          TEXT
                );
"""


PRAGMA_EXPERIMENT_DATA = """
            DROP TABLE IF EXISTS "experiment_data";

            CREATE TABLE "experiment_data" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `exp_id`        INTEGER     NOT NULL,
                `type`          TEXT        NOT NULL,
                `data`          BLOB        NOT NULL,

                FOREIGN KEY(`exp_id`) REFERENCES `experiments`(`id`),
                FOREIGN KEY(`type`) REFERENCES `experiment_data_type`(`type`)
                );
"""

PRAGMA_EXPERIMENT_DATA_TYPE = """
            DROP TABLE IF EXISTS "experiment_data_type";

            CREATE TABLE "experiment_data_type" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT        NOT NULL UNIQUE,
                `unit`          TEXT
                );
"""

# Pragmas relating to gasses
PRAGMA_ADSORBATES = """
            DROP TABLE IF EXISTS "adsorbates";

            CREATE TABLE "adsorbates" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          TEXT        NOT NULL UNIQUE,
                `formula`       TEXT
                );
"""

PRAGMA_ADSORBATE_PROPERTIES = """
            DROP TABLE IF EXISTS "adsorbate_properties";

            CREATE TABLE `adsorbate_properties` (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `ads_id`        INTEGER     NOT NULL,
                `type`          TEXT        NOT NULL,
                `value`         REAL        NOT NULL,

                FOREIGN KEY(`ads_id`) REFERENCES `adsorbates`(`id`),
                FOREIGN KEY(`type`) REFERENCES `adsorbate_properties_type`(`type`)
                );
"""

PRAGMA_ADSORBATE_PROPERTIES_TYPE = """
            DROP TABLE IF EXISTS "adsorbate_properties_type";

            CREATE TABLE `adsorbate_properties_type` (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT        NOT NULL UNIQUE,
                `unit`          TEXT
                );
"""

# Pragmas relating to contacts
PRAGMA_CONTACTS = """
            DROP TABLE IF EXISTS "contacts";

            CREATE TABLE "contacts" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          TEXT        NOT NULL UNIQUE,
                `name`          TEXT        NOT NULL,
                `email`         TEXT,
                `phone`         TEXT
                );
"""

# Pragmas relating to machines

PRAGMA_MACHINES = """
            DROP TABLE IF EXISTS "machines";

            CREATE TABLE "machines" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          TEXT        NOT NULL UNIQUE,
                `name`          TEXT,
                `type`          TEXT
                );
"""

# Pragmas relating to sources

PRAGMA_SOURCES = """
            DROP TABLE IF EXISTS "sources";

            CREATE TABLE "sources" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          TEXT        NOT NULL UNIQUE,
                `name`          TEXT
                );
"""

# List of pragmas

PRAGMAS = [
    PRAGMA_SAMPLES,
    PRAGMA_SAMPLE_PROPERTIES,
    PRAGMA_SAMPLE_TYPE,
    PRAGMA_SAMPLE_PROPERTY_TYPE,

    PRAGMA_EXPERIMENT_TYPE,
    PRAGMA_EXPERIMENTS,
    PRAGMA_EXPERIMENT_PROPERTY_TYPE,
    PRAGMA_EXPERIMENT_PROPERTIES,
    PRAGMA_EXPERIMENT_DATA_TYPE,
    PRAGMA_EXPERIMENT_DATA,

    PRAGMA_ADSORBATES,
    PRAGMA_ADSORBATE_PROPERTIES_TYPE,
    PRAGMA_ADSORBATE_PROPERTIES,

    PRAGMA_CONTACTS,
    PRAGMA_MACHINES,
    PRAGMA_SOURCES,
]
