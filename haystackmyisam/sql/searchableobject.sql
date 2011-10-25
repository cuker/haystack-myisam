ALTER TABLE `haystackmyisam_searchableobject` ENGINE=MyIsam;
ALTER TABLE `haystackmyisam_searchableindex` ENGINE=MyIsam;

ALTER TABLE `haystackmyisam_searchableobject` ADD FULLTEXT(search_text); 
