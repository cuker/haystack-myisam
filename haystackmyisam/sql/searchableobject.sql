DROP TABLE `haystackmyisam_searchableobject`;

CREATE TABLE `haystackmyisam_searchableobject` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  `search_text` longtext NOT NULL,
  `document` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`object_id`),
  KEY `haystackmyisam_searchableobject_e4470c6e` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_ba30d5f5` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=MyIsam;

DROP TABLE `haystackmyisam_searchableindex`;

CREATE TABLE `haystackmyisam_searchableindex` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `searchable_object_id` int(11) NOT NULL,
  `key` varchar(32) NOT NULL,
  `value` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `haystackmyisam_searchableindex_8b86f9bd` (`searchable_object_id`),
  KEY `haystackmyisam_searchableindex_45544485` (`key`),
  KEY `haystackmyisam_searchableindex_40858fbd` (`value`),
  CONSTRAINT `searchable_object_id_refs_id_9de87b3d` FOREIGN KEY (`searchable_object_id`) REFERENCES `haystackmyisam_searchableobject` (`id`)
) ENGINE=MyIsam;

ALTER TABLE `haystackmyisam_searchableobject` ADD FULLTEXT(search_text); 
