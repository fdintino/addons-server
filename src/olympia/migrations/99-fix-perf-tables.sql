-- The old #98.  Unrelated to 99, but still important!
ALTER TABLE file_uploads
    ADD COLUMN `hash` varchar(255) DEFAULT NULL;

-- we need to allow nulls for the baseline numbers
ALTER TABLE `perf_results` CHANGE `addon_id` `addon_id` INT( 11 ) UNSIGNED NULL;
