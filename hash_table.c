#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define HT_PRIME_1 151
#define HT_PRIME_2 163
#define MAX_STR_LEN 256

// Hash Table Data Structures
typedef struct {
    char* key;
    char* value;
} ht_item;

typedef struct {
    int size;
    int count;
    ht_item** items;
} ht_hash_table;

// Global Sentinel Tombstone Pointer
static ht_item HT_DELETED_ITEM = {NULL, NULL};

// --- Helper Functions ---

static ht_item* ht_new_item(const char* k, const char* v) {
    ht_item* i = malloc(sizeof(ht_item));
    i->key = strdup(k);
    i->value = strdup(v);
    return i;
}

static void ht_del_item(ht_item* i) {
    free(i->key);
    free(i->value);
    free(i);
}

ht_hash_table* ht_new(void) {
    ht_hash_table* ht = malloc(sizeof(ht_hash_table));
    ht->size = 53; // Base prime size
    ht->count = 0;
    ht->items = calloc((size_t)ht->size, sizeof(ht_item*));
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
    long hash = 0;
    int len_s = strlen(s);
    for (int i = 0; i < len_s; i++) {
        hash += (long)pow(a, len_s - (i + 1)) * (int)s[i];
        hash = hash % m;
    }
    return (int)hash;
}

// Double Hashing Probe Calculation
static int ht_get_hash(const char* s, const int num_buckets, const int attempt) {
    const int hash_a = ht_hash(s, HT_PRIME_1, num_buckets);
    const int hash_b = ht_hash(s, HT_PRIME_2, num_buckets);
    return (hash_a + (attempt * (hash_b + 1))) % num_buckets;
}

// --- Hash Table Operations ---

void ht_insert(ht_hash_table* ht, const char* key, const char* value) {
    ht_item* item = ht_new_item(key, value);
    int index = ht_get_hash(item->key, ht->size, 0);
    ht_item* cur_item = ht->items[index];
    int i = 1;

    while (cur_item != NULL && cur_item != &HT_DELETED_ITEM) {
        if (strcmp(cur_item->key, key) == 0) {
            ht_del_item(cur_item);
            ht->items[index] = item;
            printf(" Updated existing key '%s'.\n", key);
            return;
        }
        index = ht_get_hash(item->key, ht->size, i);
        cur_item = ht->items[index];
        i++;
    }

    ht->items[index] = item;
    ht->count++;
    printf(" Inserted ('%s': '%s') at index %d.\n", key, value, index);
}

char* ht_search(ht_hash_table* ht, const char* key) {
    int index = ht_get_hash(key, ht->size, 0);
    ht_item* item = ht->items[index];
    int i = 1;

    while (item != NULL) {
        if (item != &HT_DELETED_ITEM) {
            if (strcmp(item->key, key) == 0) {
                return item->value;
            }
        }
        index = ht_get_hash(key, ht->size, i);
        item = ht->items[index];
        i++;
    }
    return NULL;
}

void ht_delete(ht_hash_table* ht, const char* key) {
    int index = ht_get_hash(key, ht->size, 0);
    ht_item* item = ht->items[index];
    int i = 1;

    while (item != NULL) {
        if (item != &HT_DELETED_ITEM) {
            if (strcmp(item->key, key) == 0) {
                ht_del_item(item);
                ht->items[index] = &HT_DELETED_ITEM;
                ht->count--;
                printf(" Key '%s' deleted successfully from index %d.\n", key, index);
                return;
            }
        }
        index = ht_get_hash(key, ht->size, i);
        item = ht->items[index];
        i++;
    }
    printf(" Key '%s' not found.\n", key);
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

// --- Menu Interface ---

int main(void) {
    ht_hash_table* ht = ht_new();
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