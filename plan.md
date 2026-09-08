# 📋 K9Match Web Platform: Feature Requirements & Fixes

## Epic 1: Dog Registration Form Updates

*(Note: Items 1-5 [Breed Typeahead, State/City Cascading, KCI/Vaccination Logic, Stud Fee, Pure/Crossbreed Logic] are marked as **Completed**. The following are pending tasks.)*

**Task 1.1: Implement Mandatory Field Validation**

* **Description:** Enforce strict form validation before submission.
* **Action:** Add asterisks `*` to all required fields. Prevent form submission if any mandatory field is left blank, and display clear, inline error messages prompting the user to fill them out.

**Task 2.2: Add "Available for Mating" Toggle**

* **Description:** Give users control over their dog's public visibility.
* **Action:** Add a mandatory Yes/No question: *"Is your dog currently available for mating?"*
* **Logic:** If "Yes", the profile enters the public search pool (subject to admin approval). If "No", the profile is created but remains private/hidden from other users' search results. This also explains the "Status: Hidden" badge on the profile (it should display when the dog is either pending admin approval or marked unavailable by the owner).

---

## Epic 2: Matchmaking & Discovery (Find Matches Page)

**Task 2.1: Create Dedicated "Find Matches" Interface**

* **Description:** Build the core discovery page where users can browse potential mates for their dog.
* **Action:** Create a grid or list layout displaying available dog profiles. Each profile card must show essential info (Breed, Distance, KCI status) and include a Call-to-Action (CTA) to view the full profile.

**Task 2.2: Exclude User's Own Dog from Search Results**

* **Description:** Prevent users from seeing their own registered dogs in the matchmaking feed.
* **Action:** Update the database query for the "Find Matches" page to automatically filter out any dog IDs associated with the currently logged-in user's account ID.

**Task 2.3: Implement "Like / Express Interest" System**

* **Description:** Allow users to signal interest in a dog before chatting.
* **Action:** Add a "Like" or "Send Request" button on dog profiles. When clicked, the receiving dog owner gets a notification/request.

**Task 2.4: Overhaul Search UI & Animations**

* **Description:** Move away from a basic/static layout to a modern, engaging user interface.
* **Action:** Implement CSS transitions, hover effects on dog profile cards, and smooth loading animations to make the browsing experience feel premium and dynamic.

---

## Epic 3: Advanced Search Filters (Location & Breed)

**Task 3.1: Synchronize Search Dropdowns with Registration Form**

* **Description:** Ensure search filters have the exact same options as the registration form to prevent search mismatches.
* **Action:** Populate the *Breed*, *State*, and *City* dropdowns on the search page using the exact same dynamic database lists (including the Pure/Crossbreed logic) used in the Dog Registration form.

**Task 3.2: Implement Geolocation Radius Filter**

* **Description:** Allow users to find mates based on physical distance.
* **Action:** Add a range slider or dropdown (e.g., 0-5km, 5-10km, 10-20km). Use geolocation coordinates (based on the user's city/pincode) to calculate the distance between dogs and filter the results accordingly.

**Task 3.3: Remove Keyword Search Filter**

* **Description:** Clean up the search UI by removing redundant elements.
* **Action:** Delete the generic text/keyword search bar from the "Filter Matches" form to force users to use the structured dropdowns (Breed, City, Radius).

---

## Epic 4: Messaging & Communication (Chat System)

**Task 4.1: Update Navigation Bar for Chats**

* **Description:** Make communication easily accessible from anywhere on the platform.
* **Action:** Remove the "Add Dog" button from the main navbar (move it to a user dashboard/profile menu). Add a "Chats" or "Messages" icon to the navbar.
* **Sub-feature:** Tapping "Chats" should open a list of active conversations showing the other user's name and a preview of the last sent message.

**Task 4.2: Edit and Delete Chat Messages**

* **Description:** Give users control over their sent messages in the live chat.
* **Action:** Add an "Edit" and "Delete" option to messages sent by the logged-in user. If a message is deleted or edited, the change must reflect instantly in the chatbox for both the sender and the receiver via the live messaging database.

**Task 4.3: Match-to-Chat Pipeline**

* **Description:** Define how a conversation starts.
* **Action:** Chatting should ideally be unlocked only after two users mutually "Like" each other's dogs, OR a user should be able to hit "Send Message" directly from a dog's profile. *(Note: Decide which flow you prefer and implement the respective button on the dog profile).*

---

## Epic 5: Admin Workflow & Security (Major Priority)

**Task 5.1: Admin Approval System for New Registrations**

* **Description:** Ensure only authentic, verified dogs appear on the platform.
* **Action:** When a user registers a dog, set its database status to `Pending Approval`. Create an Admin Dashboard where the admin can view the submission, verify the uploaded KCI documents/vaccination records, and click "Approve" or "Reject". Only dogs with `Approved` status will render on the "Find Matches" page.

---

## Epic 6: New Feature Addition

**Task 6.1: Location-Based Veterinary Directory**

* **Description:** Add a value-add service for dog owners to find local vets.
* **Action:** Create a new "Find Vets" page or section. It should list veterinary clinics, doctor contacts, and addresses, filterable by the user's selected City/State or distance radius.