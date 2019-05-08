"""All sql pragmas to generate the sqlite database."""


# Pragmas relating to materials

PRAGMA_MATERIALS = """
            DROP TABLE IF EXISTS "materials";

            CREATE TABLE "materials" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `name`          TEXT        NOT NULL,
                `batch`         TEXT        NOT NULL,

                UNIQUE(name,batch)
                );
"""

PRAGMA_MATERIAL_PROPERTIES = """

            DROP TABLE IF EXISTS "material_properties";

            CREATE TABLE "material_properties" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `material_id`   INTEGER     NOT NULL,
                `type`          TEXT        NOT NULL,
                `value`         REAL,

                FOREIGN KEY(`material_id`)    REFERENCES `materials`(`id`),
                FOREIGN KEY(`type`)         REFERENCES 'material_properties_type'('type')
                );
"""

PRAGMA_MATERIAL_PROPERTY_TYPE = """

            DROP TABLE IF EXISTS "material_properties_type";

            CREATE TABLE "material_properties_type" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT        NOT NULL UNIQUE,
                `unit`          TEXT,
                `description`   TEXT
);
"""


# Pragmas relating to isotherms

PRAGMA_ISOTHERMS = """
            DROP TABLE IF EXISTS "isotherms";

            CREATE TABLE "isotherms" (
                `id`            TEXT        NOT NULL PRIMARY KEY UNIQUE,
                `material_name`   TEXT      NOT NULL,
                `material_batch`  TEXT      NOT NULL,
                `t_iso`         REAL        NOT NULL,
                `adsorbate`     TEXT        NOT NULL,
                `iso_type`      TEXT        NOT NULL,

                FOREIGN KEY(`material_name`,`material_batch`)   REFERENCES `materials`(`name`,`batch`),
                FOREIGN KEY(`iso_type`)         REFERENCES `isotherm_type`(`type`),
                FOREIGN KEY(`adsorbate`)        REFERENCES `adsorbates`(`name`)
                );
"""

PRAGMA_ISOTHERM_TYPE = """

            DROP TABLE IF EXISTS "isotherm_type";

            CREATE TABLE "isotherm_type" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT        NOT NULL UNIQUE,
                `description`   TEXT
                );
"""
PRAGMA_ISOTHERM_PROPERTIES = """

            DROP TABLE IF EXISTS "isotherm_properties";

            CREATE TABLE "isotherm_properties" (
                `id`            INTEGER         NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `iso_id`        INTEGER         NOT NULL,
                `type`          TEXT            NOT NULL,
                `value`         REAL            NOT NULL,

                FOREIGN KEY(`iso_id`)    REFERENCES `isotherms`(`id`),
                FOREIGN KEY(`type`)      REFERENCES 'isotherm_properties_type'('type')
                );
"""

PRAGMA_ISOTHERM_PROPERTY_TYPE = """

            DROP TABLE IF EXISTS "isotherm_properties_type";

            CREATE TABLE "isotherm_properties_type" (
                `id`            INTEGER         NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT            NOT NULL UNIQUE,
                `unit`          TEXT,
                `description`   TEXT
                );
"""


PRAGMA_ISOTHERM_DATA = """
            DROP TABLE IF EXISTS "isotherm_data";

            CREATE TABLE "isotherm_data" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `iso_id`        INTEGER     NOT NULL,
                `type`          TEXT        NOT NULL,
                `data`          BLOB        NOT NULL,

                FOREIGN KEY(`iso_id`) REFERENCES `isotherms`(`id`),
                FOREIGN KEY(`type`) REFERENCES `isotherm_data_type`(`type`)
                );
"""

PRAGMA_ISOTHERM_DATA_TYPE = """
            DROP TABLE IF EXISTS "isotherm_data_type";

            CREATE TABLE "isotherm_data_type" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `type`          TEXT        NOT NULL UNIQUE,
                `unit`          TEXT,
                `description`   TEXT
                );
"""


# Pragmas relating to gasses
PRAGMA_ADSORBATES = """
            DROP TABLE IF EXISTS "adsorbates";

            CREATE TABLE "adsorbates" (
                `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                `name`          TEXT        NOT NULL UNIQUE
                );
"""

PRAGMA_ADSORBATE_NAMES = """
            DROP TABLE IF EXISTS "adsorbate_names";

            CREATE TABLE `adsorbate_names` (
            `id`                INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            `ads_id`            INTEGER     NOT NULL,
            `name`              TEXT        NOT NULL UNIQUE,

            FOREIGN KEY(`ads_id`) REFERENCES `adsorbates`(`id`)
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
                `unit`          TEXT,
                `description`   TEXT
                );
"""


# List of pragmas

PRAGMAS = [
    PRAGMA_MATERIALS,
    PRAGMA_MATERIAL_PROPERTIES,
    PRAGMA_MATERIAL_PROPERTY_TYPE,

    PRAGMA_ISOTHERM_TYPE,
    PRAGMA_ISOTHERMS,
    PRAGMA_ISOTHERM_PROPERTY_TYPE,
    PRAGMA_ISOTHERM_PROPERTIES,
    PRAGMA_ISOTHERM_DATA_TYPE,
    PRAGMA_ISOTHERM_DATA,

    PRAGMA_ADSORBATES,
    PRAGMA_ADSORBATE_NAMES,
    PRAGMA_ADSORBATE_PROPERTIES_TYPE,
    PRAGMA_ADSORBATE_PROPERTIES,
]
