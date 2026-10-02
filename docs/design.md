# Design - Mediate Healthcare MR App

## 1. Design principles
| Principle | What it means |
|---|---|
| Field first | Used outdoors, walking, often one-handed and with weak network. Big buttons, high contrast, few taps |
| Speed to record | A visit report should take under 60 seconds |
| Always show status | Online / offline, Pending sync, Verified / Not verified, Approved / Rejected are always visible |
| Trust | Show GPS accuracy, distance and time clearly; never hide failures |
| Consistency | Same component, colour and pattern for the same meaning on every screen |
| Calm and clean | Healthcare look: lots of white space, few colours, no clutter |

## 2. Design tokens
Replace brand colours when the company logo and palette are final (Open Question Q10).
### Colours
| Token | Hex | Use |
|---|---|---|
| primary | #0E8C7F | Main buttons, active tab, links |
| primaryDark | #0A6B61 | Pressed state |
| navy | #12355B | Headers, titles |
| background | #F5F8FB | Screen background |
| surface | #FFFFFF | Cards, sheets |
| border | #C9D3DC | Dividers, input borders |
| textPrimary | #1F2933 | Main text |
| textSecondary | #5B6770 | Hints, captions |
| success | #2E7D32 | Approved, verified, done |
| warning | #F2A900 | Pending, submitted, low accuracy |
| danger | #B3261E | Rejected, error, overdue |
| info | #1E6FD9 | Information, planned |

### Typography
System font (Roboto on Android, SF on iOS). Sizes: title 22, heading 18, subheading 16, body 14, caption 12. Weights: regular 400, medium 500, bold 700. Minimum body text 14.

### Spacing, shape, elevation
Spacing scale 4, 8, 12, 16, 24, 32. Screen padding 16. Radius: small 8, medium 12, large 16. Card elevation low (one soft shadow). Touch target minimum 44 x 44.

### Status chip colours
| Status | Colour |
|---|---|
| Draft | grey |
| Planned / Submitted / Pending | warning (amber) |
| Approved / Completed / Verified / Done | success (green) |
| Rejected / Missed / Overdue / Not verified | danger (red) |
| Cancelled | grey |
| Pending sync | info (blue) with small cloud icon |

## 3. Shared components
| Component | Notes |
|---|---|
| Button | primary, secondary, danger, text; loading state; full width on forms |
| Input, Select, DateField, TimeField | Label above, helper text, inline error |
| EntityPicker | Search and pick doctor, hospital, chemist or stockist; shows territory |
| Card, ListItem | Title, subtitle, right-side status chip |
| StatusChip | Uses the status colour table |
| Badge | Unread counts, pending sync counts |
| Loader, Skeleton | Skeleton for lists and cards |
| EmptyState | Icon, message, one action |
| ErrorState | Friendly message and Retry |
| Toast | Success and error messages at the bottom |
| ScreenContainer, Header | Safe area, title, back, actions |
| BottomSheet | Filters and pickers |
| MapView wrapper | Permission handling and fallback |
| LocationCard | Shows lat/lng, accuracy, address, map preview, refresh |
| OfflineBanner | Thin bar when offline with pending count |
| ConfirmDialog | For destructive or final actions |

## 4. Navigation per role
Bottom tabs, maximum 5 per role. Extra items live under a More or Profile screen.
| Role | Tab 1 | Tab 2 | Tab 3 | Tab 4 | Tab 5 |
|---|---|---|---|---|---|
| MR | Home | Plan | Customers | Tasks | More |
| MANAGER | Home | Team | Approvals | Tasks | More |
| ADMIN | Home | Users | Masters | Reports | More |
More contains: Profile, Notifications, Attendance history, Tour, Expense, Leave, Orders, Stock, Meetings, Reports, Maps, Sync status, Settings, Logout (items depend on role).
Notifications bell with unread badge sits in the Home header for every role.
A tab or More item for an unbuilt feature shows a named ComingSoon screen. Tabs never crash or stay blank.

## 5. Screen inventory
### Common
Splash, Login, Change Password, Profile, Notifications, Sync Status, Conflict Review, Needs Attention list, Settings.
### MR
Home (today), Check-in/out, Attendance history, Plan today, Plan visit, Customers list/detail (doctor, hospital, chemist, stockist), Nearby customers, DCR list, DCR form (steps), Post-call analysis, Follow-ups, Tour list/create, Expense list/create, Leave list/apply/balance, My Requests, Tasks list/detail/chat, Meetings, My Stock, Products, E-detailing viewer, Orders list/create/detail, Dashboard, Reports, My route map.
### Manager
Home (team dashboard), Team list, Team attendance, Team map, MR detail (visits, plan, stock), Approvals inbox/detail, Tasks assign/list/chat, Joint Working form, Meetings, Targets, Reports.
### Admin
Home (admin dashboard), Users list/create/edit, Assign manager, Masters (all dropdowns), Territories and assignments, Customers admin, Approval matrix, Geofence settings, Products, Promo items, Stock allocation, Presentations, System alerts broadcast, Reports and export.

## 6. Key screen specifications
### 6.1 MR Home
- Header: greeting, date, notification bell, sync status dot.
- Check-in card (top): status (Not checked in / Checked in at time), big Check-in or Check-out button, work type.
- Today summary: planned visits count, done, pending; progress bar.
- Next up: first pending planned visit with Start visit button.
- Quick actions grid: Plan visit, New DCR, Add expense, Apply leave, Orders (only when enabled).
- Alerts strip: overdue follow-ups, pending tasks, rejected requests.

### 6.2 Check-in
1. Tap Check-in. Ask location permission with a reason if needed.
2. Show LocationCard: map preview, accuracy in metres, address text, time.
3. If accuracy is poor, show warning and a Retry location button.
4. Choose work type, confirm. Result shows success or a Pending sync badge when offline.

### 6.3 DCR form (steps with progress bar)
1. Customer and visit type (EntityPicker, link to plan if started from plan).
2. Location: capture GPS, show distance to customer and Verified / Not verified preview (final result comes from the server).
3. Products, samples, gifts: add rows with quantity; show remaining stock live (enabled in Phase 8; greyed "Available later" before).
4. Remarks and next visit date.
5. Review and Submit. Save draft at any step.
After submit: Post-call analysis screen (outcome, response, follow-up).

### 6.4 Approvals inbox (Manager)
Tabs: Pending, History. Group by type (Tour, Expense, Leave). Card shows requester, dates or amount, status. Detail screen shows full request, receipts, timeline. Actions: Approve and Reject (reject opens a required comment box).

### 6.5 Dashboards
KPI cards at top (2 per row), date range chip, one or two charts below. Tapping a card opens the related list or report. Use skeleton loading and pull-to-refresh. Colour only for meaning (green good, red problem).

### 6.6 Maps
Full-screen map with filter chips (type, date). Bottom sheet lists items; tapping a marker highlights the list item. Verified visits green pin, not verified red pin. Route view shows numbered markers and a polyline with a timeline list.

### 6.7 E-Detailing viewer
Full screen, swipe between slides, pinch to zoom, tap to show a slim control bar, exit button always reachable. Time per slide tracked silently. Works from downloaded package.

### 6.8 Admin Home: Live Field Activity (owner requirement)
The first thing an Admin sees is the live state of all MRs in the field. Style: like the MR Buddy admin panel, with the current app tokens.
Layout (top to bottom):
1. Header: greeting, date chip (Today), notification bell with badge.
2. Summary strip (horizontal scroll): MRs in field (for example 38/52), Total calls, Doctors visited, Chemists visited, Attendance %, Not checked in.
3. Section "Live Field Activity" with a List | Map toggle, search, filter chips: All, Visiting, Checked in, Idle, Not checked in, On leave.
4. MR cards: round profile photo with a status ring (green active, amber idle 2+ hours, grey not checked in), name, employee code, territory, check-in time, stat pills (Calls, Doctors, Chemists, Samples), thin progress bar (calls vs target), line "Last activity: Visited <customer>, <time> (<n> min ago)" with a Verified or Not verified chip, map-pin button to open the MR location.
5. Pending approvals card with a small donut by type (Tour, Expense, Leave) and View all.
6. Quick links row: Users, Masters, Territories, Approval Matrix, Geofence Settings, Stock Allocation.
Rules:
- "Live" means last activity from check-in and visit events. No continuous background tracking (D-12, S-05). If the owner later wants moving dots, that is a new decision with MR consent.
- Data needs a backend endpoint (suggested: GET /dashboard/admin/live-activity with per-MR check-in time, today counts, last activity, target, status). Record it in memory.md Dependencies and in the backend P7 task list. Until it exists, build the UI with a mock adapter under src/mocks (section 5.4) and flag it clearly.
- Paginate or virtualize the list (FlatList). Pull-to-refresh; auto refresh every 60 seconds only while the screen is focused.
- Tapping a card opens MrDetail (S44). Scope: Admin sees all MRs.

## 7. Feedback and state patterns
| State | Pattern |
|---|---|
| Loading | Skeleton (lists, cards); small loader for buttons |
| Empty | EmptyState with icon, one line, one action |
| Error | ErrorState with friendly text and Retry; never raw server text |
| Offline | OfflineBanner; actions still work and show Pending sync |
| Pending sync | Blue cloud chip on the item; count in Sync Status |
| Needs attention | Red chip; opens the reason and a Fix action |
| Success | Toast, and navigate to the next logical screen |
| Destructive | ConfirmDialog with clear button text |

## 8. Forms
- Label above field, required marked with a star, helper text below.
- Inline error under the field after first blur or submit.
- Submit disabled while saving; keyboard-safe scrolling; next-field focus.
- Long forms split into steps; drafts saved locally.
- Date and time use native pickers. Numbers use numeric keypad.

## 9. Accessibility and usability
- Text contrast at least 4.5:1; status never relies on colour alone (chip also has text or icon).
- Accessibility labels on icon buttons; touch targets at least 44 pt.
- Supports system font scaling up to large without breaking layouts.
- Works on small phones (360 dp wide) and large phones.

## 10. Content and tone
Short, simple English. Verbs on buttons: Check in, Submit visit, Approve, Reject. Error messages say what happened and what to do: "No network. Your visit is saved and will sync when you are online." All strings in one strings file for later Hindi and Gujarati.

## 11. Icons and images
One icon family (Feather or Material icons). Simple line illustrations for empty states. Photos compressed. Product images use a fixed aspect ratio with placeholder.

## 12. Performance UX
Show cached data immediately, refresh in the background. Paginate lists (20 per page). Avoid heavy animations. Charts limited to one or two per screen.