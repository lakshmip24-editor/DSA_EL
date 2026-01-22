#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_EVENTS_TOTAL 1000
#define MAX_EVENTS_DAILY_LIMIT 7
#define MAX_DOCTORS 100
#define HASH_SIZE 1000

typedef enum { EVENT_PATIENT, EVENT_BREAK, EVENT_MEETING } EventType;
typedef enum { BREAK_BREAKFAST, BREAK_LUNCH, BREAK_DINNER, BREAK_NONE } BreakType;

typedef struct Event {
    int id;
    int doctor_id;
    int start_time; /* Minutes from Global Epoch */
    int duration;   /* Minutes */
    int end_time;
    EventType type;
    BreakType break_type;
    char description[100];
    struct Event* next_in_hash; 
} Event;

/* Global ID counter */
int global_event_id = 1;

/* Hash Map */
Event* event_hash_map[MAX_DOCTORS][HASH_SIZE];

/* Interval Tree Node */
typedef struct ITNode {
    Event* event;
    int max;
    struct ITNode *left, *right;
} ITNode;

ITNode* interval_trees[MAX_DOCTORS] = {NULL};

/* Min Heap */
typedef struct {
    Event* events[MAX_EVENTS_TOTAL];
    int size;
} MinHeap;

MinHeap upcoming_heaps[MAX_DOCTORS];

/* Stack for Undo */
typedef struct StackNode {
    int event_id;
    struct StackNode* next;
} StackNode;

StackNode* undo_stacks[MAX_DOCTORS] = {NULL};

/* --- Helper Utils --- */

int max_val(int a, int b) { return (a > b) ? a : b; }

/* --- Hash Map --- */
void hash_insert(Event* e) {
    int key = e->id % HASH_SIZE;
    e->next_in_hash = event_hash_map[e->doctor_id][key];
    event_hash_map[e->doctor_id][key] = e;
}

void hash_remove(int doctor_id, int event_id) {
    int key = event_id % HASH_SIZE;
    Event* curr = event_hash_map[doctor_id][key];
    Event* prev = NULL;
    while (curr) {
        if (curr->id == event_id) {
            if (prev) prev->next_in_hash = curr->next_in_hash;
            else event_hash_map[doctor_id][key] = curr->next_in_hash;
            return; 
        }
        prev = curr;
        curr = curr->next_in_hash;
    }
}

Event* hash_get(int doctor_id, int event_id) {
    int key = event_id % HASH_SIZE;
    Event* curr = event_hash_map[doctor_id][key];
    while (curr) {
        if (curr->id == event_id) return curr;
        curr = curr->next_in_hash;
    }
    return NULL;
}

/* --- Interval Tree --- */
ITNode* create_it_node(Event* e) {
    ITNode* node = (ITNode*)malloc(sizeof(ITNode));
    node->event = e;
    node->max = e->end_time;
    node->left = node->right = NULL;
    return node;
}

ITNode* it_insert(ITNode* root, Event* e) {
    if (!root) return create_it_node(e);
    int l = root->event->start_time;
    /* Use ID as tie breaker if start times are equal, though logic shouldn't allow overlap */
    if (e->start_time < l) root->left = it_insert(root->left, e);
    else root->right = it_insert(root->right, e);
    
    if (root->max < e->end_time) root->max = e->end_time;
    return root;
}

ITNode* check_collision(ITNode* root, int start, int end) {
    if (!root) return NULL;
    if (root->event->start_time < end && root->event->end_time > start) return root;
    if (root->left && root->left->max > start) return check_collision(root->left, start, end);
    return check_collision(root->right, start, end);
}

void free_it_tree(ITNode* root) {
    if (!root) return;
    free_it_tree(root->left);
    free_it_tree(root->right);
    free(root);
}

/* --- Min Heap --- */
void swap(Event** a, Event** b) { Event* temp = *a; *a = *b; *b = temp; }

void heap_ify(MinHeap* h, int idx) {
    int smallest = idx;
    int left = 2 * idx + 1;
    int right = 2 * idx + 2;

    if (left < h->size && h->events[left]->start_time < h->events[smallest]->start_time)
        smallest = left;
    if (right < h->size && h->events[right]->start_time < h->events[smallest]->start_time)
        smallest = right;
    
    if (smallest != idx) {
        swap(&h->events[smallest], &h->events[idx]);
        heap_ify(h, smallest);
    }
}

void heap_insert(MinHeap* h, Event* e) {
    if (h->size >= MAX_EVENTS_TOTAL) return;
    int i = h->size++;
    h->events[i] = e;
    while (i != 0 && h->events[(i - 1) / 2]->start_time > h->events[i]->start_time) {
        swap(&h->events[i], &h->events[(i - 1) / 2]);
        i = (i - 1) / 2;
    }
}

void heap_remove(MinHeap* h, int event_id) {
    int i;
    for (i = 0; i < h->size; i++) {
        if (h->events[i]->id == event_id) break;
    }
    if (i == h->size) return; 

    h->events[i] = h->events[h->size - 1];
    h->size--;
    heap_ify(h, i);
}

/* --- Stack --- */
void stack_push(int doctor_id, int event_id) {
    StackNode* node = (StackNode*)malloc(sizeof(StackNode));
    node->event_id = event_id;
    node->next = undo_stacks[doctor_id];
    undo_stacks[doctor_id] = node;
}

int stack_pop(int doctor_id) {
    if (!undo_stacks[doctor_id]) return -1;
    StackNode* temp = undo_stacks[doctor_id];
    int id = temp->event_id;
    undo_stacks[doctor_id] = temp->next;
    free(temp);
    return id;
}

/* --- Logic --- */

void init_scheduler() {
    for (int i = 0; i < MAX_DOCTORS; i++) {
        for (int j = 0; j < HASH_SIZE; j++) event_hash_map[i][j] = NULL;
        interval_trees[i] = NULL;
        upcoming_heaps[i].size = 0;
        undo_stacks[i] = NULL;
    }
}

int count_events_on_day(int doctor_id, int day_start, int day_end) {
    /* iterate through heap to count? Heap is array, O(N) */
    int count = 0;
    for(int i = 0; i < upcoming_heaps[doctor_id].size; i++) {
        Event* e = upcoming_heaps[doctor_id].events[i];
        if (e->start_time >= day_start && e->start_time < day_end) {
            count++;
        }
    }
    return count;
}

/* Returns 0 on success, 1 on collision, 2 on max events reached */
int add_event(int doctor_id, int start, int duration, int type, int break_type, const char* desc, int* collision_start, int* collision_end) {
    /* Check Global Limit */
    if (upcoming_heaps[doctor_id].size >= MAX_EVENTS_TOTAL) return 2;
    
    /* Check Daily Limit (7) */
    /* Calculate start of the day for this event */
    int day_start = (start / 1440) * 1440;
    int day_end = day_start + 1440;
    
    if (count_events_on_day(doctor_id, day_start, day_end) >= MAX_EVENTS_DAILY_LIMIT) {
        return 2; /* Using same error code for Limit Reached */
    }
    
    int end = start + duration;
    ITNode* collision = check_collision(interval_trees[doctor_id], start, end);
    if (collision) {
        if (collision_start) *collision_start = collision->event->start_time;
        if (collision_end) *collision_end = collision->event->end_time;
        return 1;
    }

    /* Create Event */
    Event* e = (Event*)malloc(sizeof(Event));
    e->id = global_event_id++;
    e->doctor_id = doctor_id;
    e->start_time = start;
    e->duration = duration;
    e->end_time = end;
    e->type = (EventType)type;
    e->break_type = (BreakType)break_type;
    strncpy(e->description, desc, 99);
    e->description[99] = 0;

    /* Add to Data Structures */
    hash_insert(e);
    interval_trees[doctor_id] = it_insert(interval_trees[doctor_id], e);
    heap_insert(&upcoming_heaps[doctor_id], e);
    stack_push(doctor_id, e->id);

    return 0;
}


/* Suggests simple alternate time: first available slot starting from 8:00 AM (480 mins) on the given day */
int suggest_slot(int doctor_id, int duration, int day_start_mins) {
    /* 8:00 AM to 8:00 PM */
    for (int t = 480; t <= 1200; t += 15) {
        int global_t = day_start_mins + t;
        /* Ensure we don't suggest a start time that collides */
        if (!check_collision(interval_trees[doctor_id], global_t, global_t + duration)) {
            return global_t;
        }
    }
    return -1;
}

void undo_last(int doctor_id) {
    int id = stack_pop(doctor_id);
    if (id == -1) return;

    Event* e = hash_get(doctor_id, id);
    if (!e) return;

    /* Remove from Heap */
    heap_remove(&upcoming_heaps[doctor_id], id);
    
    /* Remove from Hash */
    hash_remove(doctor_id, id);

    /* Rebuild Interval Tree */
    free_it_tree(interval_trees[doctor_id]);
    interval_trees[doctor_id] = NULL;
    
    /* Re-insert all events from heap */
    for (int i = 0; i < upcoming_heaps[doctor_id].size; i++) {
        interval_trees[doctor_id] = it_insert(interval_trees[doctor_id], upcoming_heaps[doctor_id].events[i]);
    }

    free(e);
}

/* Returns JSON string of events. Caller must not free (static buffer), valid until next call */
static char json_buffer[4096];
const char* get_events_json(int doctor_id) {
    strcpy(json_buffer, "[");
    for (int i = 0; i < upcoming_heaps[doctor_id].size; i++) {
        Event* e = upcoming_heaps[doctor_id].events[i];
        char entry[256];
        sprintf(entry, "{\"id\":%d, \"start\":%d, \"duration\":%d, \"type\":%d, \"break\":%d, \"desc\":\"%s\"}", 
            e->id, e->start_time, e->duration, e->type, e->break_type, e->description);
        strcat(json_buffer, entry);
        if (i < upcoming_heaps[doctor_id].size - 1) strcat(json_buffer, ",");
    }
    strcat(json_buffer, "]");
    return json_buffer;
}

/* Returns minutes until nearest event, or -1 if none */
long get_time_to_next_event(int doctor_id, int current_time_mins) {
    if (upcoming_heaps[doctor_id].size == 0) return -1;
    
    int min_diff = 100000;
    int found = 0;
    
    for(int i=0; i<upcoming_heaps[doctor_id].size; i++) {
         int diff = upcoming_heaps[doctor_id].events[i]->start_time - current_time_mins;
         if(diff >= 0 && diff < min_diff) {
             min_diff = diff;
             found = 1;
         }
    }
    
    if (!found) return -1;
    return min_diff; /* Minutes */
}

/* --- Main Loop for Subprocess Communication --- */
int main() {
    init_scheduler();
    /* Disable buffering for stdin/stdout to ensure immediate communication */
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);

    char command[50];
    while (scanf("%s", command) != EOF) {
        if (strcmp(command, "ADD") == 0) {
            int doc_id, start, duration, type, break_type;
            char desc[100];
            scanf("%d %d %d %d %d", &doc_id, &start, &duration, &type, &break_type);
            scanf("%s", desc); 
            
            int col_start = 0, col_end = 0;
            int res = add_event(doc_id, start, duration, type, break_type, desc, &col_start, &col_end);
            if (res == 0) printf("OK\n");
            else if (res == 1) printf("COLLISION %d %d\n", col_start, col_end);
            else if (res == 2) printf("MAX_EVENTS\n");
        }
        else if (strcmp(command, "SUGGEST") == 0) {
            int doc_id, duration, day_start;
            scanf("%d %d %d", &doc_id, &duration, &day_start);
            int slot = suggest_slot(doc_id, duration, day_start);
            printf("SUGGESTION %d\n", slot);
        }
        else if (strcmp(command, "UNDO") == 0) {
            int doc_id;
            scanf("%d", &doc_id);
            undo_last(doc_id);
            printf("OK\n");
        }
        else if (strcmp(command, "GET") == 0) {
            int doc_id;
            scanf("%d", &doc_id);
            printf("%s\n", get_events_json(doc_id));
        }
        else if (strcmp(command, "ALERT") == 0) {
            int doc_id, curr_time;
            scanf("%d %d", &doc_id, &curr_time);
            long diff = get_time_to_next_event(doc_id, curr_time);
            printf("%hd\n", (short)diff); /* Print as short or int */
        }
        else if (strcmp(command, "EXIT") == 0) {
            break;
        }
    }
    return 0;
}
