/*
SELECT p.name, p.race, p.class, i.item_name, l.date
FROM items i
	INNER JOIN loot_record l on i.wow_itemid = l.item_id
	INNER JOIN players p on l.winner_id = p.sql_id
--WHERE p.name = 'Artemisl'
WHERE i.item_name LIKE 'Judgement Leg%';
*/
/*
SELECT p.name, i.item_name, lr.date, lr.sql_id
FROM players p
	inner join loot_record lr on p.sql_id = lr.winner_id
	inner join items i on lr.item_id = i.wow_itemid
where i.item_name like "%Nightslayer%";
*/
/*
update loot_record
set winner_id = 125
where sql_id = 923;
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
SELECT distinct i.item_name, lr.date, p.name
FROM loot_record lr
	INNER JOIN players p ON lr.winner_id = p.sql_id
	INNER JOIN items i ON lr.item_id = i.wow_itemid
AND p.name = 'Vallerya';
*/

/*
SELECT i.item_name, lr.date, p.name
FROM loot_record lr
	INNER JOIN players p ON lr.winner_id = p.sql_id
	INNER JOIN items i ON lr.item_id = i.wow_itemid
--AND p.name = 'Vallerya';
WHERE i.item_name like '%Idol';
*/


SELECT p.name, p.race, p.class, i.item_name, lr.date
FROM loot_record lr
    INNER JOIN players p ON lr.winner_id = p.sql_id
    INNER JOIN items i ON lr.item_id = i.wow_itemid
WHERE lr.date IN ('2025-04-27', '2025-05-02')
    AND p.name != '_disenchanted'
    AND guild_rank IS NOT NULL;

/*
SELECT p.name, p.race, p.class, i.item_name, lr.date
FROM loot_record lr
INNER JOIN players p ON lr.winner_id = p.sql_id
INNER JOIN items i ON lr.item_id = i.wow_itemid
WHERE lr.date = (SELECT max(date) from loot_record)
AND p.name != '_disenchanted'
AND p.guild_rank IS NOT NULL;
*/


 /*
SELECT
case p.name
    WHEN '_disenchanted' THEN 'DISENCHANTED'
    ELSE p.name
END AS name,
p.race, p.class, i.item_name, lr.date
FROM loot_record lr
INNER JOIN players p ON lr.winner_id = p.sql_id
INNER JOIN items i ON lr.item_id = i.wow_itemid
WHERE lr.date = (SELECT max(date) from loot_record);
--AND p.name != '_disenchanted'
--AND p.guild_rank IS NOT NULL;
*/
/*
SELECT p.name, i.item_name, lr.date
FROM loot_record lr
        INNER JOIN players p ON lr.winner_id = p.sql_id
        INNER JOIN items i ON lr.item_id = i.wow_itemid
WHERE i.item_name like "Schematic: %" or i.item_name like "Pattern: %" or i.item_name like "Formula: %" or i.item_name like "Plans: %"
AND p.guild_rank IS NOT NULL
AND p.guild_rank != ''
ORDER BY lr.date
;

*/

