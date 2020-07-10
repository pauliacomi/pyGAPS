"""All sql pragmas to generate the sqlite database."""

# Pragmas relating to adsorbates

PRAGMA_ADSORBATES = """
    DROP TABLE IF EXISTS "adsorbates";

    CREATE TABLE "adsorbates" (
        `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        `name`          TEXT        NOT NULL UNIQUE
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

# Pragmas relating to materials

PRAGMA_MATERIALS = """
    DROP TABLE IF EXISTS "materials";

    CREATE TABLE "materials" (
        `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        `name`          TEXT        NOT NULL UNIQUE
    );
"""

PRAGMA_MATERIAL_PROPERTIES = """
    DROP TABLE IF EXISTS "material_properties";

    CREATE TABLE "material_properties" (
        `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        `mat_id`        INTEGER     NOT NULL,
        `type`          TEXT        NOT NULL,
        `value`         REAL        NOT NULL,

        FOREIGN KEY(`mat_id`)       REFERENCES `materials`(`id`),
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
        `id`              TEXT      NOT NULL PRIMARY KEY UNIQUE,
        `iso_type`        TEXT      NOT NULL,
        `material`        TEXT      NOT NULL,
        `adsorbate`       TEXT      NOT NULL,
        `temperature`     REAL      NOT NULL,

        FOREIGN KEY(`iso_type`)     REFERENCES `isotherm_type`(`type`),
        FOREIGN KEY(`material`)     REFERENCES `materials`(`name`),
        FOREIGN KEY(`adsorbate`)    REFERENCES `adsorbates`(`name`)
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
        `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        `iso_id`        INTEGER     NOT NULL,
        `type`          TEXT        NOT NULL,
        `value`         REAL        NOT NULL,

        FOREIGN KEY(`iso_id`)       REFERENCES `isotherms`(`id`)
    );
"""

PRAGMA_ISOTHERM_DATA = """
    DROP TABLE IF EXISTS "isotherm_data";

    CREATE TABLE "isotherm_data" (
        `id`            INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        `iso_id`        INTEGER     NOT NULL,
        `type`          TEXT        NOT NULL,
        `data`          BLOB        NOT NULL,

        FOREIGN KEY(`iso_id`)       REFERENCES `isotherms`(`id`)
    );
"""

# List of pragmas

PRAGMAS = [
    PRAGMA_ADSORBATES,
    PRAGMA_ADSORBATE_PROPERTIES_TYPE,
    PRAGMA_ADSORBATE_PROPERTIES,
    PRAGMA_MATERIALS,
    PRAGMA_MATERIAL_PROPERTY_TYPE,
    PRAGMA_MATERIAL_PROPERTIES,
    PRAGMA_ISOTHERM_TYPE,
    PRAGMA_ISOTHERMS,
    PRAGMA_ISOTHERM_PROPERTIES,
    PRAGMA_ISOTHERM_DATA,
]
