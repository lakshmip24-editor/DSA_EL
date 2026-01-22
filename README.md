# Doctor Scheduler - MediSync Elite

A professional scheduling application for medical practitioners with advanced collision detection and multi-day scheduling capabilities.

## Features

- **Multi-Doctor Support**: Up to 2 doctors can create accounts
- **Smart Scheduling**: 
  - Maximum 7 events per day per doctor
  - Automatic collision detection using interval trees
  - Intelligent alternate time suggestions
  - Undo functionality for last action
- **Event Types**: Patient appointments, Breaks (Breakfast/Lunch/Dinner), Meetings
- **Weekly Overview**: Visual calendar showing availability across the week
- **Real-time Alerts**: Notifications for upcoming events
- **Session Management**: Secure 5-minute sessions with auto-logout

## Technology Stack

### Backend (C)
- **Data Structures**:
  - Hash Map: O(1) event storage and retrieval
  - Interval Tree: O(log n) collision detection
  - Min Heap: O(1) access to next upcoming event
  - Stack: LIFO undo operations

### Frontend (Python/Streamlit)
- Modern dark theme with glassmorphism effects
- Responsive design with real-time updates
- Interactive calendar and scheduling interface

## Installation

### Prerequisites
- GCC compiler (MinGW for Windows)
- Python 3.7+
- Streamlit

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/lakshmip24-editor/DSA_EL.git
   cd DSA_EL
   ```

2. **Install Python dependencies**:
   ```bash
   pip install streamlit
   ```

3. **Compile the C backend**:
   ```bash
   gcc -o backend/scheduler.exe backend/scheduler.c
   ```

## Usage

1. **Run the application**:
   ```bash
   streamlit run frontend/app.py
   ```
   
   Or use the convenience script:
   ```bash
   start.bat
   ```

2. **Create an account**:
   - Navigate to the "Signup" tab
   - Enter username and password
   - Note: Limited to 2 doctor accounts

3. **Login and schedule**:
   - Use your credentials to access the dashboard
   - Select a date from the calendar
   - Add events with time, duration, and type
   - View weekly availability and daily schedule

## Project Structure

```
doctor_scheduler/
├── backend/
│   └── scheduler.c          # C backend with data structures
├── frontend/
│   ├── app.py              # Streamlit frontend
│   └── users.json          # User credentials (auto-generated)
├── README.md
└── start.bat               # Windows startup script
```

## Data Structures Explained

### Hash Map
- Stores events by ID for O(1) lookup
- Uses chaining for collision resolution
- Hash function: `event_id % HASH_SIZE`

### Interval Tree
- Binary search tree for interval overlap detection
- Each node stores max endpoint in its subtree
- Enables O(log n) collision checking

### Min Heap
- Priority queue ordered by event start time
- Root always contains the next upcoming event
- Used for efficient alert generation

### Stack
- LIFO structure for undo operations
- Stores event IDs of recently added events
- Enables single-step undo functionality

## Features in Detail

### Collision Detection
When scheduling an event, the system:
1. Checks the interval tree for overlapping time slots
2. If collision detected, displays conflicting event details in red
3. Suggests the next available slot on the same day
4. Allows user to accept or reject the suggestion

### Weekly View
- Shows 7-day calendar (Monday-Sunday)
- Green indicator: Slots available
- Red indicator: Fully booked (7/7 events)
- Selected day highlighted with neon border

### Event Types
- **Patient**: Medical appointments (Blue gradient)
- **Break**: Meal breaks with type selection (Purple/Pink gradient)
- **Meeting**: Professional meetings (Green/Teal gradient)

## Security

- Password-based authentication
- Session timeout after 5 minutes of inactivity
- User data stored locally in JSON format

## License

This project is created for educational purposes as part of a Data Structures and Algorithms course.

## Contributors

Developed by Lakshmi P
