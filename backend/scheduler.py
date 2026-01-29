import sys
import json

# Constants
MAX_EVENTS_TOTAL = 1000
MAX_EVENTS_DAILY_LIMIT = 7
MAX_DOCTORS = 100
HASH_SIZE = 1000

# Enums
EVENT_PATIENT = 0
EVENT_BREAK = 1
EVENT_MEETING = 2

BREAK_BREAKFAST = 0
BREAK_LUNCH = 1
BREAK_DINNER = 2
BREAK_NONE = 3

# Data Structures
class Event:
    def __init__(self, id, doctor_id, start_time, duration, type, break_type, description):
        self.id = id
        self.doctor_id = doctor_id
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.type = type
        self.break_type = break_type
        self.description = description
        self.next_in_hash = None

# Global State
global_event_id = 1
# vector<Event> heaps[MAX_DOCTORS]
upcoming_heaps = {i: [] for i in range(MAX_DOCTORS)}
# undo_stack[MAX_DOCTORS] = list of event_ids
undo_stacks = {i: [] for i in range(MAX_DOCTORS)}
# map[doctor_id][key] = list of Events
event_hash_map = {i: {} for i in range(MAX_DOCTORS)}
# ITNode
class ITNode:
    def __init__(self, event):
        self.event = event
        self.max = event.end_time
        self.left = None
        self.right = None

interval_trees = {i: None for i in range(MAX_DOCTORS)}

# --- Helpers ---

def get_events_on_day(doctor_id, day_start, day_end):
    count = 0
    for e in upcoming_heaps[doctor_id]:
        if e.start_time >= day_start and e.start_time < day_end:
            count += 1
    return count

# --- Interval Tree ---

def it_insert(root, event):
    if root is None:
        return ITNode(event)
    
    # Tie breaker: simple < logic as per C
    if event.start_time < root.event.start_time:
        root.left = it_insert(root.left, event)
    else:
        root.right = it_insert(root.right, event)
        
    if root.max < event.end_time:
        root.max = event.end_time
    return root

def check_collision(root, start, end):
    if root is None:
        return None
    # Overlap condition: start < node.end && end > node.start
    # Node interval: [root.event.start_time, root.event.end_time)
    if root.event.start_time < end and root.event.end_time > start:
        return root
    
    if root.left and root.left.max > start:
        return check_collision(root.left, start, end)
    
    return check_collision(root.right, start, end)

# --- Logic ---

def add_event(doctor_id, start, duration, type_id, break_type, desc):
    global global_event_id
    
    # Global Limit
    if len(upcoming_heaps[doctor_id]) >= MAX_EVENTS_TOTAL:
        print("MAX_EVENTS")
        return

    # Daily Limit
    day_start = (start // 1440) * 1440
    day_end = day_start + 1440
    if get_events_on_day(doctor_id, day_start, day_end) >= MAX_EVENTS_DAILY_LIMIT:
        print("MAX_EVENTS")
        return

    end = start + duration
    
    # Collision
    col_node = check_collision(interval_trees[doctor_id], start, end)
    if col_node:
        print(f"COLLISION {col_node.event.start_time} {col_node.event.end_time}")
        return

    # Insert
    eid = global_event_id
    global_event_id += 1
    
    new_event = Event(eid, doctor_id, start, duration, type_id, break_type, desc)
    
    # 1. Heap (Just a list sorted later or maintained? C used explicit heap logic. 
    # Python list + sort is easiest, or just append since we iterate mostly)
    upcoming_heaps[doctor_id].append(new_event)
    # Maintain heap property? C implementation sorts by start_time.
    upcoming_heaps[doctor_id].sort(key=lambda x: x.start_time)
    
    # 2. Hash
    key = eid % HASH_SIZE
    if key not in event_hash_map[doctor_id]:
        event_hash_map[doctor_id][key] = []
    event_hash_map[doctor_id][key].append(new_event)
    
    # 3. Interval Tree
    interval_trees[doctor_id] = it_insert(interval_trees[doctor_id], new_event)
    
    # 4. Stack
    undo_stacks[doctor_id].append(eid)
    
    print("OK")

def suggest(doctor_id, duration, day_start):
    # 8:00 AM (480) to 8:00 PM (1200)
    for t in range(480, 1201, 15):
        global_t = day_start + t
        if not check_collision(interval_trees[doctor_id], global_t, global_t + duration):
            print(f"SUGGESTION {global_t}")
            return
    print("SUGGESTION -1")

def undo(doctor_id):
    if not undo_stacks[doctor_id]:
        print("OK") # Empty stack, do nothing
        return
        
    eid = undo_stacks[doctor_id].pop()
    
    # Remove from Hash
    key = eid % HASH_SIZE
    # Find and remove
    bucket = event_hash_map[doctor_id].get(key, [])
    tgt = None
    for e in bucket:
        if e.id == eid:
            tgt = e
            break
    if tgt:
        bucket.remove(tgt)
        
    # Remove from Heap
    upcoming_heaps[doctor_id] = [e for e in upcoming_heaps[doctor_id] if e.id != eid]
    
    # Rebuild Interval Tree
    interval_trees[doctor_id] = None
    for e in upcoming_heaps[doctor_id]:
        interval_trees[doctor_id] = it_insert(interval_trees[doctor_id], e)
        
    print("OK")

def get_all(doctor_id):
    events = []
    # Heap is already sorted by start time
    for e in upcoming_heaps[doctor_id]:
        events.append({
            "id": e.id,
            "start": e.start_time,
            "duration": e.duration,
            "type": e.type,
            "break": e.break_type,
            "desc": e.description
        })
    print(json.dumps(events))

def check_alert(doctor_id, curr_time):
    if not upcoming_heaps[doctor_id]:
        print("-1")
        return
        
    min_diff = 100000
    found = False
    
    for e in upcoming_heaps[doctor_id]:
        diff = e.start_time - curr_time
        if diff >= 0 and diff < min_diff:
            min_diff = diff
            found = True
            
    if found:
        print(f"{min_diff}")
    else:
        print("-1")

def main():
    # Unbuffered IO
    sys.stdin = open(sys.stdin.fileno(), 'r', encoding='utf-8')
    sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            parts = line.strip().split()
            if not parts: continue
            
            cmd = parts[0]
            
            if cmd == "ADD":
                # ADD doc_id start duration type break desc
                doc_id = int(parts[1])
                start = int(parts[2])
                dur = int(parts[3])
                tid = int(parts[4])
                bid = int(parts[5])
                desc = parts[6]
                add_event(doc_id, start, dur, tid, bid, desc)
                
            elif cmd == "SUGGEST":
                doc_id = int(parts[1])
                dur = int(parts[2])
                day_start = int(parts[3])
                suggest(doc_id, dur, day_start)
                
            elif cmd == "UNDO":
                doc_id = int(parts[1])
                undo(doc_id)
                
            elif cmd == "GET":
                doc_id = int(parts[1])
                get_all(doc_id)
                
            elif cmd == "ALERT":
                doc_id = int(parts[1])
                curr = int(parts[2])
                check_alert(doc_id, curr)
                
            elif cmd == "EXIT":
                break
                
        except Exception as e:
            # sys.stderr.write(str(e))
            continue

if __name__ == "__main__":
    main()
