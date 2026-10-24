#include "hash_table.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define HT_PRIME_1 151
#define HT_PRIME_2 163
#define MAX_STR_LEN HT_KEY_MAX

// Global Sentinel Tombstone Pointer
static ht_item HT_DELETED_ITEM = {NULL, NULL};

// --- Helper Functions ---

static ht_item* ht_new_item(const char* k, const char* v) {
    ht_item* i = malloc(sizeof(ht_item));
    if (i == NULL) return NULL;
    size_t key_size = strlen(k) + 1;
    size_t value_size = strlen(v) + 1;
    i->key = malloc(key_size);
    i->value = malloc(value_size);
    if (i->key == NULL || i->value == NULL) {
        free(i->key);
        free(i->value);
        free(i);
        return NULL;
    }
    memcpy(i->key, k, key_size);
    memcpy(i->value, v, value_size);
    return i;
}

static void ht_del_item(ht_item* i) {
    free(i->key);
    free(i->value);
    free(i);
}

ht_hash_table* ht_new(void) {
    ht_hash_table* ht = malloc(sizeof(ht_hash_table));
    if (ht == NULL) return NULL;
    ht->size = 53; // Base prime size
    ht->count = 0;
    ht->items = calloc((size_t)ht->size, sizeof(ht_item*));
    if (ht->items == NULL) {
        free(ht);
        return NULL;
    }
    return ht;
}

void ht_del_hash_table(ht_hash_table* ht) {
    for (int i = 0; i < ht->size; i++) {
        ht_item* item = ht->items[i];
        if (item != NULL && item != &HT_DELETED_ITEM) {
            ht_del_item(item);
        }
    }
    free(ht->items);
    free(ht);
}

// Polynomial Rolling Hash Calculation
static int ht_hash(const char* s, int a, int m) {
    unsigned int hash = 0;
    for (const unsigned char* byte = (const unsigned char*)s; *byte != '\0'; byte++) {
        hash = (hash * (unsigned int)a + *byte) % (unsigned int)m;
    }
    return (int)hash;
}

static void ht_trace_init(const ht_hash_table* ht, const char* key, ht_trace* trace) {
    memset(trace, 0, sizeof(*trace));
    trace->hash_a = ht_hash(key, HT_PRIME_1, ht->size);
    trace->hash_b = ht_hash(key, HT_PRIME_2, ht->size);
    trace->start_index = trace->hash_a;
    trace->stride = (trace->hash_b + 1) % ht->size;
    if (trace->stride == 0) trace->stride = 1;
    trace->result_index = -1;
}

static int ht_probe_index(const ht_trace* trace, int attempt, int size) {
    return (trace->start_index + attempt * trace->stride) % size;
}

static void ht_trace_step_add(ht_trace* trace, int index, ht_item* item, int action) {
    ht_trace_step* step = &trace->steps[trace->step_count++];
    step->index = index;
    step->action = action;
    if (item == NULL) {
        step->state = HT_SLOT_EMPTY;
    } else if (item == &HT_DELETED_ITEM) {
        step->state = HT_SLOT_DELETED;
    } else {
        step->state = HT_SLOT_OCCUPIED;
        snprintf(step->key, sizeof(step->key), "%s", item->key);
        snprintf(step->value, sizeof(step->value), "%s", item->value);
    }
}

int ht_insert_trace(ht_hash_table* ht, const char* key, const char* value, ht_trace* trace) {
    if (ht == NULL || key == NULL || value == NULL || trace == NULL ||
        strlen(key) >= HT_KEY_MAX || strlen(value) >= HT_KEY_MAX) return HT_RESULT_FULL;
    ht_trace_init(ht, key, trace);
    ht_item* replacement = ht_new_item(key, value);
    if (replacement == NULL) return HT_RESULT_FULL;
    int first_deleted = -1;

    for (int attempt = 0; attempt < ht->size; attempt++) {
        int index = ht_probe_index(trace, attempt, ht->size);
        ht_item* item = ht->items[index];
        if (item == NULL) {
            ht_trace_step_add(trace, index, item, HT_TRACE_EMPTY);
            int target = first_deleted >= 0 ? first_deleted : index;
            ht->items[target] = replacement;
            ht->count++;
            trace->result_index = target;
            trace->result = HT_RESULT_INSERTED;
            return trace->result;
        }
        if (item == &HT_DELETED_ITEM) {
            ht_trace_step_add(trace, index, item, HT_TRACE_TOMBSTONE);
            if (first_deleted < 0) first_deleted = index;
            continue;
        }
        if (strcmp(item->key, key) == 0) {
            ht_trace_step_add(trace, index, item, HT_TRACE_UPDATED);
            ht_del_item(item);
            ht->items[index] = replacement;
            trace->result_index = index;
            trace->result = HT_RESULT_UPDATED;
            return trace->result;
        }
        ht_trace_step_add(trace, index, item, HT_TRACE_COLLISION);
    }

    if (first_deleted >= 0) {
        ht->items[first_deleted] = replacement;
        ht->count++;
        trace->result_index = first_deleted;
        trace->result = HT_RESULT_INSERTED;
        return trace->result;
    }
    ht_del_item(replacement);
    trace->result = HT_RESULT_FULL;
    return trace->result;
}

int ht_search_trace(ht_hash_table* ht, const char* key, ht_trace* trace) {
    if (ht == NULL || key == NULL || trace == NULL) return HT_RESULT_NOT_FOUND;
    ht_trace_init(ht, key, trace);
    for (int attempt = 0; attempt < ht->size; attempt++) {
        int index = ht_probe_index(trace, attempt, ht->size);
        ht_item* item = ht->items[index];
        if (item == NULL) {
            ht_trace_step_add(trace, index, item, HT_TRACE_MISS);
            return HT_RESULT_NOT_FOUND;
        }
        if (item == &HT_DELETED_ITEM) {
            ht_trace_step_add(trace, index, item, HT_TRACE_TOMBSTONE);
        } else if (strcmp(item->key, key) == 0) {
            ht_trace_step_add(trace, index, item, HT_TRACE_FOUND);
            trace->result_index = index;
            trace->result = HT_RESULT_UPDATED;
            return trace->result;
        } else {
            ht_trace_step_add(trace, index, item, HT_TRACE_COLLISION);
        }
    }
    trace->result = HT_RESULT_NOT_FOUND;
    return trace->result;
}

int ht_delete_trace(ht_hash_table* ht, const char* key, ht_trace* trace) {
    if (ht == NULL || key == NULL || trace == NULL) return HT_RESULT_NOT_FOUND;
    ht_trace_init(ht, key, trace);
    for (int attempt = 0; attempt < ht->size; attempt++) {
        int index = ht_probe_index(trace, attempt, ht->size);
        ht_item* item = ht->items[index];
        if (item == NULL) {
            ht_trace_step_add(trace, index, item, HT_TRACE_MISS);
            return HT_RESULT_NOT_FOUND;
        }
        if (item == &HT_DELETED_ITEM) {
            ht_trace_step_add(trace, index, item, HT_TRACE_TOMBSTONE);
        } else if (strcmp(item->key, key) == 0) {
            ht_trace_step_add(trace, index, item, HT_TRACE_DELETED);
            ht_del_item(item);
            ht->items[index] = &HT_DELETED_ITEM;
            ht->count--;
            trace->result_index = index;
            trace->result = HT_RESULT_UPDATED;
            return trace->result;
        } else {
            ht_trace_step_add(trace, index, item, HT_TRACE_COLLISION);
        }
    }
    trace->result = HT_RESULT_NOT_FOUND;
    return trace->result;
}

void ht_insert(ht_hash_table* ht, const char* key, const char* value) {
    ht_trace trace;
    int result = ht_insert_trace(ht, key, value, &trace);
    if (result == HT_RESULT_UPDATED) printf(" Updated existing key '%s'.\n", key);
    else if (result == HT_RESULT_INSERTED) printf(" Inserted ('%s': '%s') at index %d.\n", key, value, trace.result_index);
    else printf(" Hash table is full or input is too long.\n");
}

char* ht_search(ht_hash_table* ht, const char* key) {
    ht_trace trace;
    if (ht_search_trace(ht, key, &trace) == HT_RESULT_NOT_FOUND) return NULL;
    return ht->items[trace.result_index]->value;
}

void ht_delete(ht_hash_table* ht, const char* key) {
    ht_trace trace;
    if (ht_delete_trace(ht, key, &trace) == HT_RESULT_NOT_FOUND) printf(" Key '%s' not found.\n", key);
    else printf(" Key '%s' deleted successfully from index %d.\n", key, trace.result_index);
}

int ht_slot_state(const ht_hash_table* ht, int index) {
    if (ht == NULL || index < 0 || index >= ht->size) return HT_SLOT_EMPTY;
    if (ht->items[index] == NULL) return HT_SLOT_EMPTY;
    return ht->items[index] == &HT_DELETED_ITEM ? HT_SLOT_DELETED : HT_SLOT_OCCUPIED;
}

int ht_table_size(const ht_hash_table* ht) {
    return ht == NULL ? 0 : ht->size;
}

int ht_table_count(const ht_hash_table* ht) {
    return ht == NULL ? 0 : ht->count;
}

const char* ht_slot_key(const ht_hash_table* ht, int index) {
    if (ht_slot_state(ht, index) != HT_SLOT_OCCUPIED) return NULL;
    return ht->items[index]->key;
}

const char* ht_slot_value(const ht_hash_table* ht, int index) {
    if (ht_slot_state(ht, index) != HT_SLOT_OCCUPIED) return NULL;
    return ht->items[index]->value;
}

void ht_display(ht_hash_table* ht) {
    printf("\n=== Hash Table Status (Count: %d / Size: %d) ===\n", ht->count, ht->size);
    if (ht->count == 0) {
        printf(" [Table is currently empty]\n");
        return;
    }
    for (int i = 0; i < ht->size; i++) {
        if (ht->items[i] != NULL && ht->items[i] != &HT_DELETED_ITEM) {
            printf(" Index [%02d]: Key = '%s', Value = '%s'\n", i, ht->items[i]->key, ht->items[i]->value);
        }
    }
    printf("===============================================\n");
}

#ifndef HT_LIBRARY_ONLY
// --- Menu Interface ---

int main(void) {
    ht_hash_table* ht = ht_new();
    if (ht == NULL) {
        fprintf(stderr, "Unable to allocate hash table.\n");
        return 1;
    }
    int choice = 0;
    char key[MAX_STR_LEN];
    char value[MAX_STR_LEN];

    while (1) {
        printf("\n-----------------------------------\n");
        printf("     HASH TABLE MENU OPERATIONS    \n");
        printf("-----------------------------------\n");
        printf(" 1. Insert / Update Pair\n");
        printf(" 2. Search Value by Key\n");
        printf(" 3. Delete Key\n");
        printf(" 4. Display Active Items\n");
        printf(" 5. Exit\n");
        printf("-----------------------------------\n");
        printf(" Enter your choice (1-5): ");

        if (scanf("%d", &choice) != 1) {
            printf(" Invalid input. Please enter a number.\n");
            while (getchar() != '\n'); // Clear buffer
            continue;
        }

        switch (choice) {
            case 1:
                printf("Enter Key: ");
                scanf("%255s", key);
                printf("Enter Value: ");
                scanf("%255s", value);
                ht_insert(ht, key, value);
                break;

            case 2:
                printf("Enter Key to Search: ");
                scanf("%255s", key);
                {
                    char* res = ht_search(ht, key);
                    if (res != NULL) {
                        printf(" Found! Value: '%s'\n", res);
                    } else {
                        printf(" Key '%s' does not exist.\n", key);
                    }
                }
                break;

            case 3:
                printf("Enter Key to Delete: ");
                scanf("%255s", key);
                ht_delete(ht, key);
                break;

            case 4:
                ht_display(ht);
                break;

            case 5:
                printf(" Freeing memory and exiting...\n");
                ht_del_hash_table(ht);
                return 0;

            default:
                printf(" Invalid choice. Please choose between 1 and 5.\n");
                break;
        }
    }

    return 0;
}
#endif