#pragma once

#define HT_TRACE_MAX_STEPS 53
#define HT_KEY_MAX 256

enum {
	HT_SLOT_EMPTY = 0,
	HT_SLOT_OCCUPIED = 1,
	HT_SLOT_DELETED = 2
};

enum {
	HT_TRACE_EMPTY = 0,
	HT_TRACE_COLLISION = 1,
	HT_TRACE_TOMBSTONE = 2,
	HT_TRACE_FOUND = 3,
	HT_TRACE_UPDATED = 4,
	HT_TRACE_DELETED = 5,
	HT_TRACE_MISS = 6
};

enum {
	HT_RESULT_NOT_FOUND = 0,
	HT_RESULT_INSERTED = 1,
	HT_RESULT_UPDATED = 2,
	HT_RESULT_FULL = 3
};

typedef struct {
	char* key;
	char* value;
}ht_item;

typedef struct {
	ht_item** items;
	int size;
	int count;
}ht_hash_table;

typedef struct {
	int index;
	int state;
	int action;
	char key[HT_KEY_MAX];
	char value[HT_KEY_MAX];
} ht_trace_step;

typedef struct {
	int hash_a;
	int hash_b;
	int start_index;
	int stride;
	int step_count;
	int result_index;
	int result;
	ht_trace_step steps[HT_TRACE_MAX_STEPS];
} ht_trace;

ht_hash_table* ht_new(void);
void ht_del_hash_table(ht_hash_table* ht);
void ht_insert(ht_hash_table* ht, const char* key, const char* value);
char* ht_search(ht_hash_table* ht, const char* key);
void ht_delete(ht_hash_table* h, const char* key);
int ht_insert_trace(ht_hash_table* ht, const char* key, const char* value, ht_trace* trace);
int ht_search_trace(ht_hash_table* ht, const char* key, ht_trace* trace);
int ht_delete_trace(ht_hash_table* ht, const char* key, ht_trace* trace);
int ht_table_size(const ht_hash_table* ht);
int ht_table_count(const ht_hash_table* ht);
int ht_slot_state(const ht_hash_table* ht, int index);
const char* ht_slot_key(const ht_hash_table* ht, int index);
const char* ht_slot_value(const ht_hash_table* ht, int index);