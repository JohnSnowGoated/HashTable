#pragma once


typedef struct {
	char* key;
	char* value;
}ht_item;

typedef struct {
	ht_item** items;
	int size;
	int count;
}ht_hash_table;

ht_hash_table* ht_new(void);
void ht_del_hash_table(ht_hash_table* ht);
void ht_insert(ht_hash_table* ht, const char* key, const char* value);
char* ht_search(ht_hash_table* ht, const char* key);
void ht_delete(ht_hash_table* h, const char* key);