import streamlit as st
import subprocess
import time
import json
import sys
import os

# --- Constants ---
SESSION_DURATION = 300 # 5 minutes
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

# --- Backend Interface ---
class SchedulerBackend:
    def __init__(self):
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
        exe_path = os.path.join(backend_dir, "scheduler.exe")
        py_path = os.path.join(backend_dir, "scheduler.py")

        cmd = []
        if os.path.exists(exe_path):
            cmd = [exe_path]
        elif os.path.exists(py_path):
            # Fallback to Python implementation
            cmd = [sys.executable, py_path]
            print("Using Python Fallback Backend")
        else:
            st.error(f"Backend not found! Looked for {exe_path} or {py_path}")
            self.process = None
            return

        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0 # Unbuffered
            )
        except Exception as e:
            st.error(f"Failed to start backend: {e}")
            self.process = None

    def send_command(self, cmd):
        if not self.process: return None
        if self.process.poll() is not None:
            st.error("Backend process has crashed or stopped.")
            # Restart?
            return None
        
        try:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
            return self.process.stdout.readline().strip()
        except Exception as e:
            st.error(f"Communication Error: {e}")
            return None

    def add_event(self, doc_id, start, duration, type_id, break_type, desc):
        desc = "".join(c for c in desc if c.isalnum() or c in " -_")
        desc = desc.replace(" ", "_").replace("-", "_")
        if not desc: desc = "Event"
        if len(desc) > 95: desc = desc[:95]
        
        resp = self.send_command(f"ADD {doc_id} {start} {duration} {type_id} {break_type} {desc}")
        if resp == "OK":
            st.session_state['edu_msg'] = "✅ Added: Inserted into Hash Map (O(1)), Interval Tree (O(log n)) & Min Heap. Stack updated for Undo."
        elif resp and resp.startswith("COLLISION"):
            st.session_state['edu_msg'] = "⚠️ Collision: Interval Tree detection found overlapping interval [Start, End)."
        return resp

    def suggest(self, doc_id, duration, day_start):
        st.session_state['edu_msg'] = "🔎 Suggestion Algo: Linear scan checked against Interval Tree verification for free slots."
        resp = self.send_command(f"SUGGEST {doc_id} {duration} {day_start}")
        if resp and resp.startswith("SUGGESTION"):
            return int(resp.split()[1])
        return -1

    def undo(self, doc_id):
        st.session_state['edu_msg'] = "↩️ Undo Operation: Stack LIFO Pop. Event ID retrieved. Hash Map Entry & Interval Tree Node removed & rebalanced."
        self.send_command(f"UNDO {doc_id}")

    def get_events(self, doc_id):
        resp = self.send_command(f"GET {doc_id}")
        try:
            return json.loads(resp)
        except:
            return []

    def check_alert(self, doc_id):
        now = time.localtime()
        curr_mins = now.tm_hour * 60 + now.tm_min
        resp = self.send_command(f"ALERT {doc_id} {curr_mins}")
        try:
            return int(resp)
        except:
            return -1

    def delete_event(self, doc_id, event_id):
        st.session_state['edu_msg'] = "❌ Deletion: Removed from Hash Map O(1) & Heap O(log n). Interval Tree Rebuilt."
        self.send_command(f"DELETE {doc_id} {event_id}")

    def set_limit(self, doc_id, limit):
        self.send_command(f"SET_LIMIT {doc_id} {limit}")


@st.cache_resource
def get_backend():
    return SchedulerBackend()

backend = get_backend()


# --- Auth System ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def register_user(username, password):
    users = load_users()
    if username in users:
        return "Exists"
    
    # STRICT LIMIT: Max 2 Doctors
    if len(users) >= 2: 
        return "Full"
    
    new_id = len(users)
    users[username] = {"password": password, "id": new_id}
    save_users(users)
    return True

def authenticate(username, password):
    users = load_users()
    if username in users and users[username]["password"] == password:
        return users[username]["id"]
    return None

# --- Page Config & Styling ---
st.set_page_config(page_title="MediSync Elite", layout="wide", page_icon="🩺")

# Premium Dark Theme
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #050510;
        background-image: radial-gradient(circle at 50% 0%, #1a1a40 0%, #050510 70%);
        color: #e0e0e0;
    }
    
    /* Typography */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        color: #ffffff;
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3.5rem;
        text-align: center;
        padding-bottom: 20px;
    }
    
    .sub-gradient-text {
        color: #8892b0;
        text-align: center;
        margin-bottom: 40px;
        font-size: 1.2rem;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 1.5rem;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        border-radius: 8px;
    }
    .stSelectbox > div > div > div {
       background-color: rgba(255, 255, 255, 0.05);
       color: white;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
        color: white;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 30px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 114, 255, 0.5);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 20px;
        color: #aaa;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0072ff;
        color: white;
    }
    
    /* Events */
    .event-item {
        margin-bottom: 12px;
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid;
        transition: transform 0.2s;
    }
    .event-item:hover {
        transform: scale(1.01);
    }
    
    /* Alerts */
    .collision-box {
        background: rgba(255, 59, 48, 0.1);
        border: 1px solid rgba(255, 59, 48, 0.3);
        color: #ff453a;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Session Management ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.doctor_id = -1
    st.session_state.login_time = 0

def login_user_session(username, doc_id):
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.doctor_id = doc_id
    st.session_state.login_time = time.time()

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.doctor_id = -1
    st.rerun()

# --- Application Logic ---
if not st.session_state.logged_in:
    st.markdown("<h1 class='gradient-text'>MediSync Elite</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-gradient-text'>Next-Generation Scheduling for Specialists</p>", unsafe_allow_html=True)

    col_shim1, col_center, col_shim2 = st.columns([1, 1.5, 1])
    with col_center:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔐 Login", "✨ Signup"])
        
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            l_user = st.text_input("Username", key="l_user", placeholder="Enter username")
            l_pass = st.text_input("Password", type="password", key="l_pass", placeholder="••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Access Dashboard"):
                uid = authenticate(l_user, l_pass)
                if uid is not None:
                    login_user_session(l_user, uid)
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("Limited to 2 Practitioners only.")
            r_user = st.text_input("Choose Username", key="r_user", placeholder="Dr. Name")
            r_pass = st.text_input("Choose Password", type="password", key="r_pass", placeholder="••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account"):
                if r_user and r_pass:
                    res = register_user(r_user, r_pass)
                    if res == True:
                        st.balloons()
                        st.success("Account created successfully! Please login.")
                    elif res == "Full":
                        st.error("Registration Closed: Max 2 doctors reached.")
                    elif res == "Exists":
                        st.error("Username already taken.")
                else:
                    st.warning("Please fill all fields.")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # Session Timeout
    if time.time() - st.session_state.login_time > SESSION_DURATION:
        st.warning("Session Expired")
        time.sleep(1)
        logout()

    doc_idx = st.session_state.doctor_id
    

    # Navbar
    c1, c2 = st.columns([8, 2])
    with c1:
        st.markdown(f"<h2 style='margin:0; padding-top:10px;'>Welcome, <span style='color:#0072ff'>Dr. {st.session_state.username}</span></h2>", unsafe_allow_html=True)
    with c2:
        if st.button("Log Out"):
            logout()

    # Spacer
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # --- Educational Message Pop-up ---
    if 'edu_msg' in st.session_state:
        e_msg = st.session_state.pop('edu_msg')
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px rgba(118, 75, 162, 0.4);
            border-left: 6px solid #fbbf24;
            animation: fadeIn 0.5s;
        ">
            <div style="font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9; margin-bottom: 5px;">
                🧠 Data Structure Operation
            </div>
            <div style="font-size: 1.1em; font-weight: 500;">
                {e_msg}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- Date Selection ---
    from datetime import datetime, date, timedelta
    
    # Store base date as today
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = date.today()


    col_date, col_view = st.columns([1, 3])
    with col_date:
        st.markdown("<div class='glass-card' style='height: 100%; display: flex; flex-direction: column; justify-content: center;'>", unsafe_allow_html=True)
        st.markdown("<span style='color: #8892b0; font-size: 0.9em;'>Jump to Date</span>", unsafe_allow_html=True)
        sel_d = st.date_input("Select Date", value=st.session_state.selected_date, label_visibility="collapsed")
        st.session_state.selected_date = sel_d
        st.markdown("</div>", unsafe_allow_html=True)

        # Settings
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("⚙️ Settings"):
             st.markdown("### Daily Limit")
             limit_hours = st.slider("Max Work Hours/Day", 1, 12, 8)
             if st.button("Update Limit"):
                 backend.set_limit(doc_idx, limit_hours * 60)
                 st.success(f"Limit set to {limit_hours} hours!")

        
    with col_view:
        # Calculate Stats for the Selected Date
        current_ord = sel_d.toordinal()
        all_events = backend.get_events(doc_idx)
        day_events = [e for e in all_events if (e['start'] // 1440) == current_ord]
        
        count = len(day_events)
        slots_left = 7 - count
        
        # Next Opening (Mock logic or use suggest)
        # We can just show counts for now as "Next Opening" requires complex query
        
        st.markdown(f"""
        <div class='glass-card' style='display: flex; justify-content: space-around; align-items: center; padding: 1.2rem;'>
            <div style="text-align: center;">
                <div style="color: #8892b0; font-size: 0.9em; margin-bottom: 5px;">📅 SCHEDULED</div>
                <div style="font-size: 1.8em; font-weight: bold; color: #00c6ff;">{count} <span style="font-size: 0.5em; opacity: 0.5;">Event(s)</span></div>
            </div>
            <div style="width: 1px; height: 40px; background: rgba(255,255,255,0.1);"></div>
            <div style="text-align: center;">
                <div style="color: #8892b0; font-size: 0.9em; margin-bottom: 5px;">🔓 AVAILABLE</div>
                <div style="font-size: 1.8em; font-weight: bold; color: #00ff9b;">{slots_left} <span style="font-size: 0.5em; opacity: 0.5;">Slot(s)</span></div>
            </div>
             <div style="width: 1px; height: 40px; background: rgba(255,255,255,0.1);"></div>
            <div style="text-align: center;">
                <div style="color: #8892b0; font-size: 0.9em; margin-bottom: 5px;">📊 STATUS</div>
                <div style="font-size: 1.2em; font-weight: bold; color: {'#ff3b30' if slots_left == 0 else '#fff'};">
                    {"FULLY BOOKED" if slots_left == 0 else "ACCEPTING"}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    current_day_ordinal = sel_d.toordinal()

    # Alert System
    minutes_to_next = backend.check_alert(doc_idx)
    # Filter alert? The backend returns global diff time. 
    # If the closest event is today, it works. If it's tomorrow, it might show huge minutes.
    # User only cares if < 15 mins.
    if minutes_to_next >= 0 and minutes_to_next <= 30:
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #ff3b30, #ff9500); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px; font-weight: bold; box-shadow: 0 5px 15px rgba(255, 59, 48, 0.3);">
             Starting in {minutes_to_next} mins!
        </div>
        """, unsafe_allow_html=True)

    # Main Layout
    col_schedule, col_form = st.columns([1.8, 1])
    
    with col_form:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"### ➕ Book for {sel_d.strftime('%b %d')}")
        
        with st.form("add_event", border=False):
            desc = st.text_input("Patient Name / Details", placeholder="e.g. John Doe - Checkup")
            
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                hour = st.number_input("Hour (0-23)", 0, 23, 9)
            with t_col2:
                minute = st.number_input("Minute", 0, 59, 0, step=15)
            
            # Global Start Time
            # We map ordinal to offset 0 for "today"? No, just use ordinal * 1440
            # Wait, ordinal is huge. Integers in C are 32-bit (2 billion).
            # Ordinal is ~700,000. 700,000 * 1440 = 1 billion. Safe for signed 32-bit int.
            
            global_start_mins = (current_day_ordinal * 1440) + (hour * 60) + minute
            duration = st.number_input("Duration (mins)", 15, 120, 30, step=15)
            
            e_type = st.selectbox("Type", ["Patient", "Break", "Meeting"])
            type_map = {"Patient": 0, "Break": 1, "Meeting": 2}
            
            break_type = 3 # None
            if e_type == "Break":
                b_map = {"Breakfast": 0, "Lunch": 1, "Dinner": 2}
                b_sel = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner"])
                break_type = b_map[b_sel]
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Add to Schedule")
            
            if submit:
                st.session_state.pop('suggestion', None)
                
                res = backend.add_event(doc_idx, global_start_mins, duration, type_map[e_type], break_type, desc)
                if res == "OK":
                    st.success("Scheduled Successfully!")
                    st.rerun()
                elif res == "MAX_EVENTS":
                    st.error("Limit Reached: Max 7 events per day.")
                elif res == "TIME_LIMIT":
                     st.error("Time Limit Exceeded: You have reached your daily workload limit.")
                elif res and res.startswith("COLLISION"):

                    parts = res.split()
                    c_start, c_end = int(parts[1]), int(parts[2])
                    
                    # Convert Global Collision Time back to Local for display
                    c_h = (c_start % 1440) // 60
                    c_m = (c_start % 1440) % 60
                    c_end_h = (c_end % 1440) // 60
                    c_end_m = (c_end % 1440) % 60
                    
                    st.session_state.collision_display = f"{c_h:02d}:{c_m:02d} - {c_end_h:02d}:{c_end_m:02d}"
                    
                    day_start_mins = current_day_ordinal * 1440
                    sug_time = backend.suggest(doc_idx, duration, day_start_mins)
                    st.session_state.suggestion = {
                        'new_time': sug_time,
                        'duration': duration,
                        'type': type_map[e_type],
                        'break': break_type,
                        'desc': desc
                    }
                    st.rerun()

        # Suggestion / Collision Handling
        if 'suggestion' in st.session_state:
            sug = st.session_state.suggestion
            c_disp = st.session_state.get('collision_display', 'Unknown')
            
            st.markdown(f"""
            <div class='collision-box'>
                <strong>⛔ Collision Detected</strong><br>
                Conflict at {c_disp}
            </div>
            """, unsafe_allow_html=True)
            
            if sug['new_time'] != -1:
                # Suggestion is Global Time. Need to show Date + Time
                s_ordinal = sug['new_time'] // 1440
                
                # Safety check for valid ordinal
                if s_ordinal < 1:
                    st.warning("Invalid suggestion time received from backend.")
                else:
                    s_date = date.fromordinal(s_ordinal)
                    s_h = (sug['new_time'] % 1440) // 60
                    s_m = (sug['new_time'] % 1440) % 60
                    
                    day_str = "TODAY" if s_ordinal == current_day_ordinal else s_date.strftime("%b %d")
                    
                    st.info(f"💡 Suggestion: {day_str} at {s_h:02d}:{s_m:02d}")
                    
                    c_yes, c_no = st.columns(2)
                    with c_yes:
                        if st.button("Accept"):
                            res = backend.add_event(doc_idx, sug['new_time'], sug['duration'], sug['type'], sug['break'], sug['desc'])
                            if res == "OK":
                                st.success("Rescheduled!")
                                del st.session_state.suggestion
                                st.rerun()
                    with c_no:
                        if st.button("Reject"):
                            del st.session_state.suggestion
                            st.rerun()
            else:
                st.warning("No alternative slots found.")
                if st.button("Cancel"):
                     del st.session_state.suggestion
                     st.rerun()

        st.markdown("---")
        if st.button("↩️ Undo Last Action"):
            backend.undo(doc_idx)
            # st.toast("Last action undone") - Removed in favor of edu_msg
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with col_schedule:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        
        # --- Weekly View ---
        # Get start/end of the selected week (Mon-Sun)
        start_of_week = sel_d - timedelta(days=sel_d.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Fetch ALL events
        all_events = backend.get_events(doc_idx)
        
        # --- Day Slot Matrix ---
        st.markdown("### 🗓️ Weekly Overview")
        
        # Create 7 columns
        days_cols = st.columns(7)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for i, col in enumerate(days_cols):
            curr_d = start_of_week + timedelta(days=i)
            curr_ord = curr_d.toordinal()
            is_selected = (curr_d == sel_d)
            
            # Count events for this day
            ev_count = sum(1 for e in all_events if (e['start'] // 1440) == curr_ord)
            status_color = "#4Caf50" if ev_count < 7 else "#f44336" # Green if open, Red if full
            
            border_style = "2px solid #00c6ff" if is_selected else "1px solid rgba(255,255,255,0.1)"
            bg_style = "rgba(0,198,255,0.1)" if is_selected else "rgba(255,255,255,0.02)"
            
            with col:
                st.markdown(f"""
                <div style="text-align: center; border: {border_style}; background: {bg_style}; border-radius: 8px; padding: 10px 5px; cursor: pointer;">
                    <div style="font-size: 0.8em; color: #888;">{days[i]}</div>
                    <div style="font-weight: bold;">{curr_d.day}</div>
                    <div style="margin-top: 5px; height: 6px; width: 6px; background-color: {status_color}; border-radius: 50%; display: inline-block;"></div>
                    <div style="font-size: 0.7em; color: #aaa;">{ev_count}/7</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"### 📋 Schedule for {sel_d.strftime('%A, %b %d')}")
        
        # Filter for Selected Day
        day_events = [e for e in all_events if (e['start'] // 1440) == current_day_ordinal]
        day_events.sort(key=lambda x: x['start'])
        
        if not day_events:
            st.markdown("<div style='text-align:center; padding: 40px; color: #666;'>No events scheduled.<br>Select a slot to add one.</div>", unsafe_allow_html=True)
        
        for e in day_events:
            # Local Time
            local_start = e['start'] % 1440
            start_h = local_start // 60
            start_m = local_start % 60
            
            local_end = (e['start'] + e['duration']) % 1440
            end_h = local_end // 60
            end_m = local_end % 60
            
            styles = {
                0: "linear-gradient(90deg, rgba(0, 198, 255, 0.1) 0%, rgba(0, 114, 255, 0.05) 100%)",
                1: "linear-gradient(90deg, rgba(255, 0, 204, 0.1) 0%, rgba(51, 51, 153, 0.05) 100%)",
                2: "linear-gradient(90deg, rgba(0, 255, 155, 0.1) 0%, rgba(0, 200, 83, 0.05) 100%)"
            }
            border_colors = { 0: "#00c6ff", 1: "#ff00cc", 2: "#00ff9b" }
            icons = {0: "😷", 1: "☕", 2: "📊"}
            
            bg = styles.get(e['type'], styles[0])
            bor = border_colors.get(e['type'], border_colors[0])
            icon = icons.get(e['type'], "📅")
            
            title = e['desc'].replace("_", " ")
            if e['type'] == 1:
                title += f" ({['Breakfast','Lunch','Dinner'][e['break']]})"
            
            st.markdown(f"""
            <div class="event-item" style="background: {bg}; border-color: {bor};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <span style="font-family: monospace; font-size: 1.1em; color: {bor}; filter: brightness(1.2);">
                        {start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}
                    </span>
                    <span style="font-size: 1.5em; opacity: 0.8;">{icon}</span>
                </div>
                <div style="font-weight: 500; font-size: 1.1em; color: #e0e0e0;">
                    {title}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Delete Button (using columns to align right below the card or inside it? Inside is hard with HTML injection)
            # Alternative: Render a small st.button below each card
            d_col1, d_col2 = st.columns([0.85, 0.15])
            with d_col2:
                 if st.button("🗑️", key=f"del_{e['id']}", help="Delete this event"):
                     backend.delete_event(doc_idx, e['id'])
                     st.rerun()

            
        st.markdown("</div>", unsafe_allow_html=True)
