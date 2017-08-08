# %%
"""
This module contains the sql pragmas to generate the sqlite database
"""

__author__ = 'Paul A. Iacomi'

# Pragmas relating to samples
PRAGMA_SAMPLE_TYPE = """
            DROP TABLE IF EXISTS "sample_type";

            CREATE TABLE "sample_type" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          TEXT        NOT NULL UNIQUE,
                `name`          TEXT        NOT NULL
                );
"""

PRAGMA_SAMPLE_FORMS = """
            DROP TABLE IF EXISTS "sample_forms";

            CREATE TABLE "sample_forms" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          INTEGER     NOT NULL UNIQUE,
                `name`          INTEGER     NOT NULL,
                `desc`          INTEGER
                );
"""

PRAGMA_SAMPLES = """
            DROP TABLE IF EXISTS "samples";

            CREATE TABLE "samples" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `name`          TEXT        NOT NULL,
                `batch`         TEXT        NOT NULL,
                `owner`         TEXT        NOT NULL,
                `contact`       TEXT        NOT NULL,
                `source_lab`    TEXT        NOT NULL,
                `project`       TEXT,
                `struct`        TEXT,
                `type`          TEXT        NOT NULL,
                `form`          TEXT        NOT NULL,
                `modifier`      TEXT,
                `comment`       TEXT,

                FOREIGN KEY(`owner`)        REFERENCES `contacts`(`nick`),
                FOREIGN KEY(`contact`)      REFERENCES `contacts`(`nick`),
                FOREIGN KEY(`source_lab`)   REFERENCES `labs`(`nick`),
                FOREIGN KEY(`type`)         REFERENCES `sample_type`(`nick`),
                FOREIGN KEY(`form`)         REFERENCES `sample_forms`(`nick`)
                UNIQUE(name,batch)
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

PRAGMA_SAMPLE_PROPERTIES = """

            DROP TABLE IF EXISTS "sample_properties";

            CREATE TABLE "sample_properties" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `sample_id`     INTEGER     NOT NULL,
                `type`          TEXT        NOT NULL,
                `value`         REAL        NOT NULL,

                FOREIGN KEY(`sample_id`)    REFERENCES `samples`(`id`),
                FOREIGN KEY(`type`)         REFERENCES 'sample_properties_type'('type')
                );
"""

# Pragmas relating to experiments
PRAGMA_EXPERIMENT_TYPE = """

            DROP TABLE IF EXISTS "experiment_type";

            CREATE TABLE "experiment_type" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          TEXT        NOT NULL UNIQUE,
                `name`          INTEGER
                );
"""

PRAGMA_EXPERIMENTS = """
            DROP TABLE IF EXISTS "experiments";

            CREATE TABLE "experiments" (
                `id`            TEXT        NOT NULL PRIMARY KEY UNIQUE,
                `date`          TEXT,
                `is_real`       INTEGER     NOT NULL,
                `exp_type`      TEXT        NOT NULL,
                `sample_name`   TEXT        NOT NULL,
                `sample_batch`  TEXT        NOT NULL,
                `t_act`         REAL        NOT NULL,
                `t_exp`         REAL        NOT NULL,
                `machine`       TEXT        NOT NULL,
                `gas`           TEXT        NOT NULL,
                `user`          TEXT        NOT NULL,
                `lab`           TEXT        NOT NULL,
                `project`       TEXT,
                `comment`       TEXT,

                FOREIGN KEY(`sample_name`,`sample_batch`)   REFERENCES `samples`(`name`,`batch`),
                FOREIGN KEY(`exp_type`)         REFERENCES `experiment_type`(`nick`),
                FOREIGN KEY(`machine`)          REFERENCES `machines`(`nick`),
                FOREIGN KEY(`user`)             REFERENCES `contacts`(`nick`),
                FOREIGN KEY(`gas`)              REFERENCES `gasses`(`nick`),
                FOREIGN KEY(`lab`)              REFERENCES `labs`(`nick`)
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

PRAGMA_EXPERIMENT_DATA = """
            DROP TABLE IF EXISTS "experiment_data";

            CREATE TABLE "experiment_data" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `exp_id`        INTEGER     NOT NULL,
                `dtype`         TEXT        NOT NULL,
                `data`          BLOB        NOT NULL,

                FOREIGN KEY(`exp_id`) REFERENCES `experiments`(`id`),
                FOREIGN KEY(`dtype`) REFERENCES `experiment_data_type`(`type`)
                );
"""

# Pragmas relating to gasses
PRAGMA_GASSES = """
            DROP TABLE IF EXISTS "gasses";

            CREATE TABLE "gasses" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          TEXT        NOT NULL UNIQUE,
                `formula`       TEXT
                );
"""

PRAGMA_GAS_PROPERTIES_TYPE = """
            DROP TABLE IF EXISTS "gas_properties_type";

            CREATE TABLE `gas_properties_type` (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT        NOT NULL UNIQUE,
                `unit`          TEXT
                );
"""

PRAGMA_GAS_PROPERTIES = """
            DROP TABLE IF EXISTS "gas_properties";

            CREATE TABLE `gas_properties` (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `gas_id`        INTEGER     NOT NULL,
                `type`          TEXT        NOT NULL,
                `value`         REAL        NOT NULL,

                FOREIGN KEY(`gas_id`) REFERENCES `gasses`(`id`),
                FOREIGN KEY(`type`) REFERENCES `gas_properties_type`(`type`)
                );
"""

# Pragmas relating to users and locations
PRAGMA_CONTACTS = """
            DROP TABLE IF EXISTS "contacts";

            CREATE TABLE "contacts" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `name`          TEXT        NOT NULL,
                `nick`          TEXT        NOT NULL UNIQUE,
                `email`         TEXT,
                `phone`         TEXT,
                `labID`         INTEGER     NOT NULL,
                `type`          TEXT,
                `permanent`     INTEGER,

                FOREIGN KEY(`labID`) REFERENCES `labs`(`nick`)
                );
"""

PRAGMA_LABS = """
            DROP TABLE IF EXISTS "labs";

            CREATE TABLE "labs" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          TEXT        NOT NULL UNIQUE,
                `name`          TEXT        NOT NULL UNIQUE,
                `address`       INTEGER
                );
"""

PRAGMA_PROJECTS = """
            DROP TABLE IF EXISTS "projects";

            CREATE TABLE "projects" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          TEXT        NOT NULL UNIQUE,
                `id_number`     TEXT        UNIQUE,
                `contact`       TEXT        NOT NULL,
                `name`          TEXT        NOT NULL,
                `type`          TEXT,
                `startdate`     TEXT,
                `enddate`       TEXT,

                FOREIGN KEY(`contact`) REFERENCES `contacts`(`nick`)
                );
"""

# Pragmas relating to machines used
PRAGMA_MACHINE_TYPE = """
            DROP TABLE IF EXISTS "machine_type";

            CREATE TABLE "machine_type" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT        NOT NULL UNIQUE
                );
"""

PRAGMA_MACHINES = """
            DROP TABLE IF EXISTS "machines";

            CREATE TABLE "machines" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `nick`          TEXT        NOT NULL UNIQUE,
                `name`          TEXT        NOT NULL,
                `type`          INTEGER     NOT NULL,

                FOREIGN KEY(`type`) REFERENCES machine_type(`type`)
                );
"""

PRAGMAS = [
    PRAGMA_SAMPLE_TYPE,
    PRAGMA_SAMPLE_FORMS,
    PRAGMA_SAMPLES,
    PRAGMA_SAMPLE_PROPERTY_TYPE,
    PRAGMA_SAMPLE_PROPERTIES,

    PRAGMA_EXPERIMENT_TYPE,
    PRAGMA_EXPERIMENTS,
    PRAGMA_EXPERIMENT_DATA_TYPE,
    PRAGMA_EXPERIMENT_DATA,

    PRAGMA_GASSES,
    PRAGMA_GAS_PROPERTIES_TYPE,
    PRAGMA_GAS_PROPERTIES,

    PRAGMA_CONTACTS,
    PRAGMA_PROJECTS,
    PRAGMA_LABS,

    PRAGMA_MACHINE_TYPE,
    PRAGMA_MACHINES,
]
