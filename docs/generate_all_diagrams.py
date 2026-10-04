import urllib.request
import base64
import zlib
import os
import sys

output_dir = r"d:\K9Match\docs"
os.makedirs(output_dir, exist_ok=True)

def render_plantuml_to_png(plantuml_code, output_filepath):
    print(f"Rendering PlantUML -> {os.path.basename(output_filepath)}...")
    compressed = zlib.compress(plantuml_code.strip().encode('utf-8'))
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
    url = f"https://kroki.io/plantuml/png/{encoded}"
    req = urllib.request.Request(url, headers={'User-Agent': 'K9Match-Doc-Generator/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = resp.read()
            with open(output_filepath, 'wb') as f:
                f.write(data)
            print(f"  [OK] Saved {len(data)} bytes to {output_filepath}")
            return True
    except Exception as e:
        print(f"  [ERROR] PlantUML failed: {e}")
        return False

def render_mermaid_to_png(mermaid_code, output_filepath):
    print(f"Rendering Mermaid -> {os.path.basename(output_filepath)}...")
    compressed = zlib.compress(mermaid_code.strip().encode('utf-8'))
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
    url = f"https://kroki.io/mermaid/png/{encoded}"
    req = urllib.request.Request(url, headers={'User-Agent': 'K9Match-Doc-Generator/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = resp.read()
            with open(output_filepath, 'wb') as f:
                f.write(data)
            print(f"  [OK] Saved {len(data)} bytes to {output_filepath}")
            return True
    except Exception as e:
        print(f"  [ERROR] Mermaid failed: {e}")
        return False

# ==============================================================================
# 1. Figure 4.1: System Architecture Diagram (PlantUML)
# ==============================================================================
puml_arch = """
@startuml
skinparam handwritten false
skinparam packageStyle rectangle
skinparam defaultFontName "Segoe UI"
skinparam defaultFontSize 12
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180

actor "Pet Owner / Breeder / Admin" as User

package "Client Presentation Layer" {
    [Responsive Web Interface] as UI
    note right of UI
        - HTML5 & Modern Semantic Elements
        - Custom Glassmorphism CSS & Tailwind
        - Dynamic Vanilla JavaScript & Fetch API
    end note
}

package "Application & Processing Layer (Django WSGI)" {
    [Web Server & Reverse Proxy\\n(Nginx / HTTPS)] as Nginx
    [WSGI Application Server\\n(Gunicorn Process Pool)] as Gunicorn
    
    package "Django Core Subsystems" {
        [Authentication & RBAC Controller\\n(Email OTP & Google OAuth 2.0)] as AuthCtrl
        [Canine Profile & Media Manager\\n(Upload & Size Validation)] as DogCtrl
        [Spatial Matchmaking Engine\\n(Haversine Distance Algorithm)] as MatchEngine
        [Real-Time Messaging Controller\\n(Chat & Permission Guard)] as ChatCtrl
        [Admin Vetting & Moderation Panel\\n(Document Approval)] as AdminCtrl
        [Dynamic PDF Synthesis Engine\\n(ReportLab Canvas Graphics)] as PDFEngine
    }
}

package "External Services & APIs" {
    [OpenStreetMap Nominatim API\\n(Reverse Geocoding)] as OSM
    [SMTP Email Gateway\\n(Transaction OTP & Alerts)] as SMTP
}

package "Data & Persistence Layer" {
    database "PostgreSQL Relational DB" as DB {
        [User & Auth Tables]
        [DogProfile & DogImage Tables]
        [MatchRequest & ChatMessage]
        [VeterinaryClinic & Reports]
    }
    folder "Static & Media Storage\\n(WhiteNoise / Local Storage)" as Storage
}

User --> UI: HTTPS Requests (Port 443)
UI --> Nginx: Secure HTTPS Traffic
Nginx --> Gunicorn: Forward WSGI Request (Port 8000)
Gunicorn --> AuthCtrl
Gunicorn --> DogCtrl
Gunicorn --> MatchEngine
Gunicorn --> ChatCtrl
Gunicorn --> AdminCtrl
Gunicorn --> PDFEngine

DogCtrl --> Storage: Persist Canine Photos (Max 5MB)
PDFEngine --> Storage: Generate Breeding Contracts & Passports
MatchEngine ..> OSM: Coordinate Resolution (Lat, Lon)
AuthCtrl ..> SMTP: Dispatch 6-Digit Verification OTP

AuthCtrl --> DB: Verify PBKDF2 Credentials
DogCtrl --> DB: Read/Write Dog Profiles & Status
MatchEngine --> DB: Filter Opposite Gender & Active Listings
ChatCtrl --> DB: Store Direct Messages & Read Flags
AdminCtrl --> DB: Update Approval States
@enduml
"""

# ==============================================================================
# 2. Figure 4.2: Use Case Diagram (PlantUML)
# ==============================================================================
puml_use_case = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180

left to right direction

actor "Pet Owner" as Owner
actor "Verified Breeder" as Breeder
actor "System Administrator" as Admin
actor "Veterinarian" as Vet

rectangle "K9MATCH: Ethical Canine Matching Platform" {
    usecase "UC-1: Register & Authenticate\\n(Email OTP / OAuth 2.0)" as UC1
    usecase "UC-2: Create & Manage Dog Profile" as UC2
    usecase "UC-3: Upload Photos & KCI / Vaccine Docs" as UC3
    usecase "UC-4: Search Matches with Distance Radius" as UC4
    usecase "UC-5: Enforce Opposite-Gender & Self-Match Guard" as UC5
    usecase "UC-6: Transmit Match Request with Terms" as UC6
    usecase "UC-7: Accept / Decline Mating Request" as UC7
    usecase "UC-8: Engage in Direct Chatroom" as UC8
    usecase "UC-9: Download Breeding Contract & Passport PDF" as UC9
    usecase "UC-10: Access Veterinary Directory & Heat Calculator" as UC10
    usecase "UC-11: Review & Approve / Reject Dog Listings" as UC11
    usecase "UC-12: Resolve Community Scam Reports" as UC12
    usecase "UC-13: Manage Clinic Directory Listings" as UC13
}

Owner --> UC1
Owner --> UC2
Owner --> UC4
Owner --> UC6
Owner --> UC7
Owner --> UC8
Owner --> UC9
Owner --> UC10

Breeder --|> Owner
Breeder --> UC2

UC2 ..> UC3 : <<include>>
UC4 ..> UC5 : <<include>>
UC6 ..> UC7 : <<triggers>>
UC7 ..> UC8 : <<unlocks>>
UC7 ..> UC9 : <<enables>>

Admin --> UC11
Admin --> UC12
Admin --> UC13

Vet --> UC10
Vet --> UC13
@enduml
"""

# ==============================================================================
# 3. Figure 4.3: Sequence Diagram 1: Registration & Admin Approval (PlantUML)
# ==============================================================================
puml_seq_reg = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180
autonumber

actor "Pet Owner / Breeder" as User
boundary "Registration UI" as UI
control "DogProfile Controller\\n(views.add_dog)" as Ctrl
entity "Validation Engine" as Val
database "PostgreSQL Database" as DB
actor "System Administrator" as Admin
boundary "Admin Dashboard" as AdminUI

User -> UI: Enter dog details, KCI reg number & upload photos
UI -> Ctrl: POST /add-dog/ (multipart form payload)
Ctrl -> Val: Validate image sizes (<= 5MB), MIME (.jpg/.png), age (0-25 yrs)

alt Validation Error
    Val --> Ctrl: Validation Failure (e.g., File > 5MB)
    Ctrl --> UI: Render form error message
    UI --> User: Prompt corrections
else Validation Successful
    Val --> Ctrl: Validation Passed
    Ctrl -> DB: INSERT DogProfile (status='pending', is_available=True)
    Ctrl -> DB: INSERT DogImage records (primary & gallery)
    DB --> Ctrl: Record created successfully
    Ctrl --> UI: Redirect to /my-dogs/ with "Pending Approval" notice
    UI --> User: Display Profile with "Status: Pending Verification"
end

== Administrative Verification Lifecycle ==

Admin -> AdminUI: GET /admin-dashboard/
AdminUI -> DB: SELECT * FROM DogProfile WHERE status='pending'
DB --> AdminUI: Return pending canine listings queue
AdminUI --> Admin: Render documents & pedigree certificates

alt Approve Listing
    Admin -> AdminUI: Click "Approve Dog"
    AdminUI -> DB: UPDATE DogProfile SET status='approved' WHERE id=dog_id
    DB --> AdminUI: Status Updated
    AdminUI --> Admin: Display "Listing Approved" success toast
    note over DB: Profile now appears in public "Find Matches" pool
else Reject Listing
    Admin -> AdminUI: Click "Reject Dog"
    AdminUI -> DB: UPDATE DogProfile SET status='rejected' WHERE id=dog_id
    DB --> AdminUI: Status Updated
    AdminUI --> Admin: Listing rejected & archived
end
@enduml
"""

# ==============================================================================
# 4. Figure 4.4: Sequence Diagram 2: Spatial Match & Chat Unlock (PlantUML)
# ==============================================================================
puml_seq_match = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180
autonumber

actor "User A (Sender Dog Owner)" as UserA
boundary "Find Matches UI" as UI
control "Explore View\\n(views.explore_dogs)" as ExpCtrl
control "Spatial Utility\\n(utils.haversine_distance)" as MathUtil
database "PostgreSQL Database" as DB
actor "User B (Target Dog Owner)" as UserB
boundary "Chatroom UI" as ChatUI
control "Chat API\\n(views.send_message_api)" as ChatAPI

UserA -> UI: Select Breed, City & Distance Radius (e.g. 20 km)
UI -> ExpCtrl: GET /explore/?breed=Golden+Retriever&radius=20
ExpCtrl -> DB: Query approved dogs (status='approved', is_available=True)
note over ExpCtrl: Filter out User A's dogs (Self-match prevention)\\nFilter for opposite gender (Male to Female only)
DB --> ExpCtrl: Return candidate canine records with coordinates

loop For Each Candidate Dog
    ExpCtrl -> MathUtil: haversine_distance(UserLat, UserLon, DogLat, DogLon)
    MathUtil --> ExpCtrl: Return distance in kilometers
end

ExpCtrl --> UI: Render dogs within 20 km sorted by proximity
UI --> UserA: Display verified partner cards

UserA -> UI: Click "Send Match Request" (Select Terms: Pick of Litter)
UI -> DB: INSERT MatchRequest (sender_dog, target_dog, status='pending')
DB --> UI: Request Queued
UI --> UserB: Notification: "New Match Request for your dog"

UserB -> UI: Review User A's dog pedigree & Click "Accept"
UI -> DB: UPDATE MatchRequest SET status='accepted'
DB --> UI: Request Accepted & Chatroom Enabled

== Permission-Isolated Chatting Lifecycle ==

UserA -> ChatUI: Open /chat/<match_id>/
ChatUI -> DB: Verify UserA is participant in accepted MatchRequest
DB --> ChatUI: Verification Confirmed (Access Granted)

UserA -> ChatUI: Type message: "Hello! Let's discuss breeding terms."
ChatUI -> ChatAPI: POST /api/chat/<match_id>/send/
ChatAPI -> DB: INSERT ChatMessage (match_id, sender, message, is_read=False)
DB --> ChatAPI: Message Saved
ChatAPI --> ChatUI: Append message to chat thread
ChatAPI --> UserB: Live Notification & In-line Message Stream
@enduml
"""

# ==============================================================================
# 5. Figure 4.5: Entity-Relationship (ER) Diagram (PlantUML)
# ==============================================================================
puml_erd = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180
skinparam linetype ortho

entity "User" as user {
    * id : INTEGER <<PK>>
    --
    * username : VARCHAR(150) <<UNIQUE>>
    * email : VARCHAR(254) <<UNIQUE>>
    password : VARCHAR(128)
    role : VARCHAR(20) [owner, breeder]
    phone_number : VARCHAR(10)
    is_verified : BOOLEAN
    kennel_name : VARCHAR(150)
    city : VARCHAR(100)
    state : VARCHAR(100)
}

entity "DogProfile" as dog {
    * id : INTEGER <<PK>>
    --
    * owner_id : INTEGER <<FK>>
    * name : VARCHAR(100)
    * breed : VARCHAR(100)
    breed_type : VARCHAR(20) [purebred, crossbreed]
    secondary_breed : VARCHAR(100)
    * age_years : INTEGER
    * age_months : INTEGER
    * gender : VARCHAR(10) [male, female]
    weight : DECIMAL(5,2)
    weight_unit : VARCHAR(5) [kg, lbs]
    kci_registered : BOOLEAN
    kci_number : VARCHAR(50)
    microchip_number : VARCHAR(50)
    vaccinated : BOOLEAN
    dewormed : BOOLEAN
    mating_terms : VARCHAR(20) [stud_fee, want_puppy, negotiable]
    stud_fee : DECIMAL(10,2)
    city : VARCHAR(100)
    state : VARCHAR(100)
    latitude : DECIMAL(9,6)
    longitude : DECIMAL(9,6)
    is_available_for_mating : BOOLEAN
    status : VARCHAR(20) [pending, approved, rejected, hidden]
}

entity "DogImage" as image {
    * id : INTEGER <<PK>>
    --
    * dog_id : INTEGER <<FK>>
    * image : VARCHAR(255)
    is_primary : BOOLEAN
    created_at : DATETIME
}

entity "MatchRequest" as match {
    * id : INTEGER <<PK>>
    --
    * sender_id : INTEGER <<FK>>
    * receiver_id : INTEGER <<FK>>
    * sender_dog_id : INTEGER <<FK>>
    * target_dog_id : INTEGER <<FK>>
    status : VARCHAR(20) [pending, accepted, rejected, cancelled]
    mating_terms : VARCHAR(30)
    message : TEXT
    created_at : DATETIME
    updated_at : DATETIME
}

entity "ChatMessage" as chat {
    * id : INTEGER <<PK>>
    --
    * match_request_id : INTEGER <<FK>>
    * sender_id : INTEGER <<FK>>
    * receiver_id : INTEGER <<FK>>
    message : TEXT
    is_read : BOOLEAN
    is_edited : BOOLEAN
    is_deleted : BOOLEAN
    created_at : DATETIME
}

entity "VeterinaryClinic" as vet {
    * id : INTEGER <<PK>>
    --
    * name : VARCHAR(200)
    address : TEXT
    city : VARCHAR(100)
    state : VARCHAR(100)
    phone : VARCHAR(20)
    emergency_services : BOOLEAN
    latitude : DECIMAL(9,6)
    longitude : DECIMAL(9,6)
}

entity "EmailOTP" as otp {
    * id : INTEGER <<PK>>
    --
    user_id : INTEGER <<FK>>
    email : VARCHAR(254)
    otp_code : VARCHAR(6)
    purpose : VARCHAR(30)
    expires_at : DATETIME
    is_used : BOOLEAN
}

entity "ReportListing" as report {
    * id : INTEGER <<PK>>
    --
    * reporter_id : INTEGER <<FK>>
    * reported_dog_id : INTEGER <<FK>>
    reason : VARCHAR(100)
    details : TEXT
    status : VARCHAR(20) [pending, resolved, dismissed]
    created_at : DATETIME
}

user ||--o{ dog : "owns"
user ||--o{ match : "sends / receives"
user ||--o{ chat : "writes"
user ||--o{ otp : "requests"
user ||--o{ report : "submits"

dog ||--o{ image : "has photos"
dog ||--o{ match : "participates in"
dog ||--o{ report : "is reported in"

match ||--o{ chat : "unlocks messaging"
@enduml
"""

# ==============================================================================
# 6. Figure 4.6: Data Flow Diagram (DFD Level 0) (PlantUML)
# ==============================================================================
puml_dfd0 = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180

actor "Pet Owner / Breeder" as User
rectangle "0.0\\nK9MATCH: Ethical Canine Matching\\nCentral System" as System
actor "System Administrator" as Admin
actor "Veterinarian" as Vet
cloud "OpenStreetMap\\nNominatim Service" as OSM

User --> System : Registration Credentials, Canine Details,\\nKCI Documents, Match Requests, Chat Messages
System --> User : Verified Match Feed, Distance Calculations,\\nChat Notifications, Breeding Contract & Passport PDF

Admin --> System : Document Review, Listing Approvals,\\nUser Bans & Fraud Resolutions
System --> Admin : Pending Listings Queue, Scam Reports & Analytics

Vet --> System : Clinic Profiles, Emergency Schedules
System --> Vet : Patient Leads & Breeding Health Inquiries

System --> OSM : Request Reverse Geocoding (Lat, Lon)
OSM --> System : Return Standardized City & State Names
@enduml
"""

# ==============================================================================
# 7. Figure 4.7: Data Flow Diagram (DFD Level 1) (PlantUML)
# ==============================================================================
puml_dfd1 = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180

actor "User" as User
actor "Administrator" as Admin

rectangle "1.0 User Auth & Verification" as P1
rectangle "2.0 Canine Profile & Gallery" as P2
rectangle "3.0 Spatial Matching Engine" as P3
rectangle "4.0 Match Negotiation & Chat" as P4
rectangle "5.0 Document Synthesis Engine" as P5
rectangle "6.0 Admin Moderation Subsystem" as P6

database "D1: Users" as D1
database "D2: DogProfiles & Images" as D2
database "D3: MatchRequests" as D3
database "D4: ChatMessages" as D4

User --> P1 : Login / OTP Credentials
P1 --> D1 : Verify & Authenticate
P1 --> User : Auth Session

User --> P2 : Dog Bio, KCI Docs, Photos
P2 --> D2 : Save Profile (Pending)

Admin --> P6 : Approve / Reject Listing
P6 --> D2 : Update Status (Approved)

User --> P3 : Search Query (Breed, Radius)
P3 --> D2 : Fetch Opposite Gender & Approved Dogs
D2 --> P3 : Candidate Canine Records
P3 --> User : Ranked Proximity Match List

User --> P4 : Transmit / Accept Match Request
P4 --> D3 : Store Request State
P4 --> D4 : Store Chat Messages
D3 --> P4 : Access Control Verification
D4 --> User : Live Message Feed

User --> P5 : Request PDF Contract / Passport
D2 --> P5 : Retrieve Dog & Pedigree Specs
D3 --> P5 : Retrieve Accepted Mating Terms
P5 --> User : Formatted PDF Documents
@enduml
"""

# ==============================================================================
# 8. Figure 4.8: Data Flow Diagram (DFD Level 2) (PlantUML)
# ==============================================================================
puml_dfd2 = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180

actor "Pet Owner" as Owner
database "D2: DogProfiles" as D2
database "D3: MatchRequests" as D3
database "D4: ChatMessages" as D4

package "3.0 Spatial Matching Sub-Processes" {
    rectangle "3.1 Retrieve User Location & Radius" as P31
    rectangle "3.2 Query Approved Opposite-Gender Dogs" as P32
    rectangle "3.3 Compute Haversine Great-Circle Distance" as P33
    rectangle "3.4 Filter by Radius & Sort Ascending" as P34
}

package "4.0 Match & Messaging Sub-Processes" {
    rectangle "4.1 Formulate Match Request with Terms" as P41
    rectangle "4.2 Process Owner Acceptance / Rejection" as P42
    rectangle "4.3 Authenticate & Broadcast Chat Stream" as P43
}

Owner --> P31 : Search Form (City, 20 km)
P31 --> P32 : Coordinates & Filter Specs
P32 --> D2 : Query (gender != UserDog.gender, status='approved')
D2 --> P32 : Candidate Records
P32 --> P33 : Raw Dog Coordinates
P33 --> P34 : Computed Distances (km)
P34 --> Owner : Ranked Proximity Feed

Owner --> P41 : Send Request (Terms: Stud Fee)
P41 --> D3 : Save Pending Request
D3 --> P42 : Fetch Request Details
Owner --> P42 : Target Owner Clicks "Accept"
P42 --> D3 : Update status='accepted'
D3 --> P43 : Verify Mutual Acceptance
Owner --> P43 : Send Chat Message
P43 --> D4 : Persist Message
D4 --> Owner : Render Message in Thread
@enduml
"""

# ==============================================================================
# 9. Figure 4.9: Activity Diagram: Spatial Matchmaking (PlantUML)
# ==============================================================================
puml_activity = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180

start
:User navigates to "Find Matches" Page;
:Enter Search Criteria (Breed, City/State, Radius);

:Fetch User's Selected Canine Profile;
:Query database for active profiles (status='approved');

while (More candidate dogs in database?) is (yes)
    :Retrieve candidate dog profile;
    if (Is candidate owned by current user?) then (yes)
        :Exclude (Self-match prevention);
    else (no)
        if (Are genders opposite? (Male + Female)) then (yes)
            :Retrieve coordinates (Lat, Lon) for user and candidate;
            :Compute distance using Haversine Formula:
            d = 2 * R * asin(sqrt(h));
            if (Distance <= Selected Radius?) then (yes)
                :Attach computed distance to profile;
                :Add candidate to Eligible Match List;
            else (no)
                :Exclude (Out of radius);
            endif
        else (no)
            :Exclude (Incompatible genders);
        endif
    endif
endwhile (no)

:Sort Eligible Match List ascending by distance;
:Render verified dog profile cards with pedigree badges;

if (User clicks "Send Match Request"?) then (yes)
    :Select Mating Terms (Stud Fee / Puppy Pick);
    :Submit Match Request (status='pending');
    :Notify Target Dog Owner;
else (no)
    :Continue browsing;
endif

stop
@enduml
"""

# ==============================================================================
# 10. Figure 4.10: Collaboration Diagram (PlantUML)
# ==============================================================================
puml_collab = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180

rectangle "1: User (Browser Client)" as User
rectangle "2: ExploreView (Controller)" as Ctrl
rectangle "3: SpatialService (Haversine Math)" as Math
rectangle "4: MatchRequestManager" as MatchMgr
rectangle "5: ChatService" as Chat
rectangle "6: Database (ORM Engine)" as DB

User -right-> Ctrl : 1. Submit Search (Breed, Radius)
Ctrl -down-> DB : 2. SELECT * FROM DogProfile WHERE status='approved'
DB -up-> Ctrl : 3. Return Candidate Records
Ctrl -right-> Math : 4. Calculate Distance (Lat1, Lon1, Lat2, Lon2)
Math -left-> Ctrl : 5. Return Proximity in km
Ctrl -left-> User : 6. Render Filtered Match Grid

User -down-> MatchMgr : 7. POST /send-request/ (Terms)
MatchMgr -down-> DB : 8. INSERT MatchRequest (pending)
DB -up-> MatchMgr : 9. Request Stored
MatchMgr -up-> User : 10. Target Owner Notified & Accepts

User -right-> Chat : 11. POST /chat/<match_id>/send/
Chat -down-> DB : 12. Verify Accepted Status & INSERT Message
DB -up-> Chat : 13. Confirm Write
Chat -left-> User : 14. Broadcast Real-Time Message
@enduml
"""

# ==============================================================================
# 11. Figure 4.11: Component Diagram (PlantUML)
# ==============================================================================
puml_component = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180

package "Presentation Components" {
    [Templates & Static UI Engine] as UIComp
    [Forms & Client-Side Validators] as FormComp
}

package "Core Application Business Logic" {
    [Authentication Component\\n(EmailOTP & Google OAuth)] as AuthComp
    [Canine Registry Component\\n(DogProfile & Gallery)] as ProfileComp
    [Spatial Matchmaking Subsystem\\n(Haversine Distance)] as SpatialComp
    [Negotiation & Messaging Subsystem\\n(MatchRequest & Chat)] as MsgComp
    [Admin Moderation Subsystem\\n(Dashboard & Document Verification)] as AdminComp
    [PDF Synthesis Engine\\n(ReportLab Graphics)] as PDFComp
}

package "Data Persistence & Storage" {
    [Django ORM Data Access Object] as ORM
    database "PostgreSQL Relational DB" as DB
    folder "Media Uploads Directory" as MediaStore
}

cloud "External Web Services" {
    [OpenStreetMap Nominatim] as OSMService
    [SMTP Email Host] as MailService
}

UIComp --> FormComp
FormComp --> AuthComp : Submit Credentials
FormComp --> ProfileComp : Submit Dog Data
FormComp --> SpatialComp : Search Query
FormComp --> MsgComp : Send Chat / Request

AuthComp ..> MailService : Send OTP
SpatialComp ..> OSMService : Reverse Geocoding
ProfileComp --> MediaStore : Store Dog Photos

AuthComp --> ORM
ProfileComp --> ORM
SpatialComp --> ORM
MsgComp --> ORM
AdminComp --> ORM
PDFComp --> ORM

ORM --> DB : SQL Transactions
@enduml
"""

# ==============================================================================
# 12. Figure 4.12: State Machine Diagram (PlantUML)
# ==============================================================================
puml_state = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180

state "Canine Profile Lifecycle" as DogLifecycle {
    [*] --> Draft : Owner starts registration
    Draft --> PendingApproval : Submit KCI & Vaccination Docs
    
    state PendingApproval {
        PendingApproval : Locked from public matchmaking feed
        PendingApproval : Awaiting administrative review
    }
    
    PendingApproval --> Approved : Admin clicks "Approve"
    PendingApproval --> Rejected : Admin flags fraudulent docs
    
    state Approved {
        Approved : Discoverable in "Find Matches"
        Approved : Eligible for distance calculation
    }
    
    Approved --> Hidden : Owner toggles "Not Available for Mating"
    Hidden --> Approved : Owner toggles "Available for Mating"
    
    Rejected --> [*] : Archived / Deleted
    Approved --> [*] : Deleted by Owner
}

--

state "Match Request Lifecycle" as MatchLifecycle {
    [*] --> RequestInitiated : Sender selects partner & terms
    RequestInitiated --> Pending : Request transmitted
    
    state Pending {
        Pending : Target owner receives alert
        Pending : Chatroom remains locked
    }
    
    Pending --> Accepted : Target owner clicks "Accept"
    Pending --> Declined : Target owner clicks "Decline"
    Pending --> Cancelled : Sender revokes request
    
    state Accepted {
        Accepted : Direct chatroom unlocked
        Accepted : Breeding contract PDF available
    }
    
    Accepted --> [*] : Mating Completed / Closed
    Declined --> [*]
    Cancelled --> [*]
}
@enduml
"""

# ==============================================================================
# 13. Figure 4.13: Deployment Diagram (PlantUML)
# ==============================================================================
puml_deploy = """
@startuml
skinparam defaultFontName "Segoe UI"
skinparam roundCorner 8
skinparam shadowing false
skinparam dpi 180

node "Client Tier (Desktop / Mobile Devices)" {
    artifact "Modern Web Browser\\n(Chrome, Firefox, Safari, Edge)" as Browser
}

node "Cloud Infrastructure Host (Linux Virtual Server)" {
    node "Web Server Container (Port 80 / 443)" {
        component "Nginx Reverse Proxy\\n& SSL Termination (Let's Encrypt)" as Nginx
    }
    
    node "Application Server Container" {
        component "Gunicorn WSGI Server\\n(4 Parallel Sync Workers)" as Gunicorn
        component "Django 5.x / 6.0 Web Application\\n(Python 3.12 Runtime)" as DjangoApp
        component "WhiteNoise Static File Server\\n(Gzip / Brotli Caching)" as WhiteNoise
    }
    
    node "Database Container" {
        database "PostgreSQL 15+ Relational Database\\n(Port 5432)" as Postgres
    }
    
    folder "Persistent Media Storage Volume\\n(/var/www/k9match/media)" as MediaVol
}

cloud "Third-Party External Services" {
    node "OpenStreetMap Foundation" {
        component "Nominatim Reverse Geocoding API" as OSM
    }
    node "Google Cloud Platform" {
        component "Google OAuth 2.0 Identity Service" as GoogleAuth
    }
    node "SMTP Relay Server" {
        component "Email OTP & Alert Service" as SMTP
    }
}

Browser -- Nginx : HTTPS / TLS 1.3
Nginx -- Gunicorn : Proxy Pass (Port 8000)
Gunicorn -- DjangoApp : WSGI Interface
DjangoApp -- WhiteNoise : Serve Static CSS/JS
DjangoApp -- Postgres : TCP / IP Connection Pool
DjangoApp -- MediaVol : Read / Write Dog Photos

DjangoApp ..> OSM : HTTPS REST API
DjangoApp ..> GoogleAuth : OAuth 2.0 Callbacks
DjangoApp ..> SMTP : TLS SMTP Protocol
@enduml
"""

diagrams = [
    (puml_arch, os.path.join(output_dir, "figure4_1_architecture.png")),
    (puml_use_case, os.path.join(output_dir, "figure4_2_use_case.png")),
    (puml_seq_reg, os.path.join(output_dir, "figure4_3_sequence_registration.png")),
    (puml_seq_match, os.path.join(output_dir, "figure4_4_sequence_matching.png")),
    (puml_erd, os.path.join(output_dir, "figure4_5_er_diagram.png")),
    (puml_dfd0, os.path.join(output_dir, "figure4_6_dfd_level_0.png")),
    (puml_dfd1, os.path.join(output_dir, "figure4_7_dfd_level_1.png")),
    (puml_dfd2, os.path.join(output_dir, "figure4_8_dfd_level_2.png")),
    (puml_activity, os.path.join(output_dir, "figure4_9_activity_diagram.png")),
    (puml_collab, os.path.join(output_dir, "figure4_10_collaboration_diagram.png")),
    (puml_component, os.path.join(output_dir, "figure4_11_component_diagram.png")),
    (puml_state, os.path.join(output_dir, "figure4_12_state_machine.png")),
    (puml_deploy, os.path.join(output_dir, "figure4_13_deployment_diagram.png")),
]

success_count = 0
for code, path in diagrams:
    if render_plantuml_to_png(code, path):
        success_count += 1

print(f"\nCompleted: {success_count}/{len(diagrams)} diagrams successfully rendered to PNG.")
