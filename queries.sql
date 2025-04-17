/*
SELECT p.name, p.race, p.class, i.item_name, l.date
FROM items i
	INNER JOIN loot_record l on i.wow_itemid = l.item_id
	INNER JOIN players p on l.winner_id = p.sql_id
--WHERE p.name = 'Artemisl'
WHERE i.item_name LIKE 'Judgement Leg%';
*/
/*
SELECT p.name, i.item_name, lr.date
FROM players p
	inner join loot_record lr on p.sql_id = lr.winner_id
	inner join items i on lr.item_id = i.wow_itemid
where i.item_name like "%Nightslayer%";
*/

/*
SELECT p.name, p.race, p.class, i.item_name, lr.date
FROM loot_record lr
	INNER JOIN players p ON lr.winner_id = p.sql_id
	INNER JOIN items i ON lr.item_id = i.wow_itemid
WHERE lr.date = (SELECT max(date) from loot_record)
AND p.name != '_disenchanted';
*/

/*
SELECT i.item_name, lr.date
FROM loot_record lr
	INNER JOIN players p ON lr.winner_id = p.sql_id
	INNER JOIN items i ON lr.item_id = i.wow_itemid
WHERE lr.date IN ('2025-04-10','2025-04-11')
AND p.name = '_disenchanted';
*/
