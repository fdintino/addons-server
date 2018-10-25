-- adding primary keys like nobody's business:

ALTER TABLE addon_recommendations
    ADD UNIQUE(addon_id, other_addon_id),
    ADD COLUMN id INTEGER UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY FIRST;


ALTER TABLE addons_collections
    ADD UNIQUE(addon_id, collection_id),
    DROP PRIMARY KEY,
    ADD COLUMN id INTEGER UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY FIRST;


ALTER TABLE addons_collections
    ADD COLUMN `created` datetime NOT NULL DEFAULT '0000-00-00 00:00:00';

ALTER TABLE collection_addon_recommendations
    ADD COLUMN id INTEGER UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY FIRST;

ALTER TABLE versions_summary
    ADD COLUMN id INTEGER UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY FIRST;

-- users_tags_addons removed, that's already in migration 15. --fwenzel
