--SELECT p.name, i.item_name, l.date
--FROM items i
--	INNER JOIN loot_record l on i.wow_itemid = l.item_id
--	INNER JOIN players p on l.winner_id = p.sql_id
--WHERE p.name = 'Artemisl'

SELECT p.name, lr.date
FROM players p
	inner join loot_record lr on p.sql_id = lr.winner_id
	inner join items i on lr.item_id = i.wow_itemid
where i.item_name like "%Nightslayer%";