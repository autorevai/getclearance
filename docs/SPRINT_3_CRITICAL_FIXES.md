# Sprint 3 Critical Fixes - Production Readiness

## Overview
Critical gaps identified in Sprint 3 Polish implementation that must be fixed before production deployment.

**Audit Date:** 2025-12-02
**Completion Date:** 2025-12-02
**Target:** Sumsub-level production quality

---

## Priority 1: Blockers (Must Fix) - ALL COMPLETE

### 1.1 Sorting - FIXED
**Status:** [x] Complete
**Files:** `frontend/src/components/ApplicantsList.jsx`

**Solution Implemented:**
- Added `sort` and `order` to filters state (defaults to `created_at` desc)
- Added `handleSort(field)` handler that toggles sort direction
- Added `getSortIcon(field)` to show ChevronUp/ChevronDown based on sort state
- Updated all 4 sortable column headers with onClick handlers and aria-sort attributes
- Sort state synced to URL params for shareability

---

### 1.2 CSV Export - FIXED
**Status:** [x] Complete
**Files:** `frontend/src/components/ApplicantsList.jsx`, `frontend/src/hooks/useApplicants.js`, `frontend/src/services/applicants.js`, `frontend/src/services/api.js`

**Solution Implemented:**
- Added `useExportApplicants` hook with mutation for CSV download
- Added `exportCSV` method to ApplicantsService
- Added `requestText` method to ApiClient for text responses
- Wired up Export CSV button with loading state and onClick handler
- Supports exporting selected applicants or all with current filters
- Downloads file as `applicants_export_YYYY-MM-DD.csv`

---

### 1.3 Focus Trapping - FIXED
**Status:** [x] Complete
**Files:** `frontend/src/hooks/useFocusTrap.js` (new), `frontend/src/components/shared/ConfirmDialog.jsx`, `frontend/src/components/CreateApplicantModal.jsx`

**Solution Implemented:**
- Created custom `useFocusTrap` hook (no external dependencies)
- Hook traps Tab/Shift+Tab at modal boundaries
- Focuses first element on open (or specified initial focus)
- Returns focus to trigger element on close
- Escape key closes modal (when not loading)
- Applied to both ConfirmDialog and CreateApplicantModal

---

### 1.4 Undo for Approve/Reject - FIXED
**Status:** [x] Complete
**Files:** `frontend/src/components/ApplicantDetail.jsx`, `frontend/src/components/ApplicantsList.jsx`

**Solution Implemented:**
- Success toasts now include "Undo" action button with 10s window
- Stores previous status before mutation
- Undo triggers revert API call to restore previous state
- Works for both single and batch approve/reject operations
- Info toast confirms successful undo

---

## Priority 2: High Impact (Before Production) - ALL COMPLETE

### 2.1 Keyboard Navigation in Dropdowns - FIXED
**Status:** [x] Complete
**Files:** `frontend/src/components/ApplicantsList.jsx`

**Solution Implemented:**
- Added `highlightedIndex` state to track keyboard focus
- Added `handleDropdownKeyDown` handler with arrow keys, Enter, Home, End
- Updated dropdown buttons with `onKeyDown` handlers
- Added `.highlighted` CSS class with visual outline
- Added aria-activedescendant for screen reader support
- Highlighted index syncs with current filter value on open

---

### 2.2 Focus Return on Modal Close - FIXED
**Status:** [x] Complete
**Files:** `frontend/src/hooks/useFocusTrap.js`, `frontend/src/components/shared/ConfirmDialog.jsx`, `frontend/src/components/CreateApplicantModal.jsx`, `frontend/src/components/ApplicantsList.jsx`

**Solution Implemented:**
- `useFocusTrap` stores `previousActiveElement` on activation
- On deactivation, focus returns to stored element
- `triggerRef` prop added to modals for explicit trigger tracking
- `createModalTriggerRef` added to "Create Applicant" button
- Focus restoration happens after small delay to ensure modal is closed

---

### 2.3 Shift+Click Range Selection - FIXED
**Status:** [x] Complete
**Files:** `frontend/src/components/ApplicantsList.jsx`

**Solution Implemented:**
- Added `lastSelectedId` state to track last clicked checkbox
- Added `handleCheckboxClick` that detects shiftKey
- When Shift+Click: calculates range between last and current, selects all in range
- Updated checkbox click handlers to use new function
- Added aria-label hint about Shift to select range

---

### 2.4 Error Recovery with Retry - FIXED
**Status:** [x] Complete
**Files:** `frontend/src/components/ApplicantsList.jsx`, `frontend/src/components/ApplicantDetail.jsx`

**Solution Implemented:**
- Error toasts now include "Retry" action button
- Failed export: Retry button re-executes `handleExport`
- Failed approve/reject: Retry button restores selection and re-opens confirm dialog
- Failed single review: Retry button re-opens confirm dialog with same action

---

## Progress Tracking

| Task | Priority | Status | Completed |
|------|----------|--------|-----------|
| 1.1 Sorting | P1 | Complete | [x] |
| 1.2 CSV Export | P1 | Complete | [x] |
| 1.3 Focus Trapping | P1 | Complete | [x] |
| 1.4 Undo Actions | P1 | Complete | [x] |
| 2.1 Keyboard Nav Dropdowns | P2 | Complete | [x] |
| 2.2 Focus Return | P2 | Complete | [x] |
| 2.3 Shift+Click Selection | P2 | Complete | [x] |
| 2.4 Error Retry | P2 | Complete | [x] |

---

## Completion Criteria

**P1 Complete When:**
- [x] All 4 sortable columns respond to clicks and show direction
- [x] CSV export downloads file with current filters applied
- [x] Cannot Tab out of any modal
- [x] Approve/Reject shows "Undo" toast that works

**P2 Complete When:**
- [x] Can navigate dropdowns with arrow keys
- [x] Focus returns to trigger after modal close
- [x] Shift+Click selects range of checkboxes
- [x] Error toasts have "Retry" button that works

---

## Files Created/Modified

### New Files
- `frontend/src/hooks/useFocusTrap.js` - Custom focus trap hook

### Modified Files
- `frontend/src/components/ApplicantsList.jsx` - Sorting, export, keyboard nav, shift+click, undo/retry
- `frontend/src/components/ApplicantDetail.jsx` - Undo/retry for review actions
- `frontend/src/components/shared/ConfirmDialog.jsx` - Focus trapping, trigger ref
- `frontend/src/components/CreateApplicantModal.jsx` - Focus trapping, trigger ref
- `frontend/src/hooks/useApplicants.js` - Added useExportApplicants hook
- `frontend/src/hooks/index.js` - Export useExportApplicants
- `frontend/src/services/applicants.js` - Added exportCSV method
- `frontend/src/services/api.js` - Added requestText method

---

## Notes

- Backend `/applicants/export` endpoint created at `backend/app/api/v1/applicants.py:144`
- Focus trap implemented without external dependencies for smaller bundle
- Undo relies on being able to re-apply previous status via review API
- All keyboard shortcuts work with screen readers (proper ARIA attributes)

---

## Backend Endpoint Added

### GET /api/v1/applicants/export

**File:** `backend/app/api/v1/applicants.py`

**Features:**
- Returns CSV with all applicant fields
- Supports same filters as list endpoint (status, risk_level, search)
- Supports `ids` query param for exporting selected applicants
- Supports sorting (sort, order params)
- Returns streaming response for large exports
- Includes X-Total-Count header

**CSV Columns:**
- ID, External ID, Email, First Name, Last Name
- Status, Risk Score, Risk Level
- Nationality, Country of Residence, Date of Birth
- Flags, Created At, Updated At, Reviewed At, Source
