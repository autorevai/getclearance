# Sprint 3 Polish Plan: Production-Ready Applicants Module

## Overview
This plan addresses the gaps identified in the Sprint 3 implementation to bring the Applicants module to Sumsub-level production quality.

---

## Task 1: Debounced Search Input
**Priority: High | Complexity: Low**

### Problem
Search fires API calls on every keystroke, causing unnecessary load and poor UX.

### Solution
Create a `useDebounce` hook and apply to search input.

### Files to Create/Modify
- `frontend/src/hooks/useDebounce.js` (new)
- `frontend/src/components/ApplicantsList.jsx` (modify)

### Implementation
```javascript
// useDebounce.js
export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

---

## Task 2: Toast Notification System
**Priority: High | Complexity: Medium**

### Problem
No feedback after actions (approve, reject, create, download).

### Solution
Create a toast context and hook for app-wide notifications.

### Files to Create/Modify
- `frontend/src/contexts/ToastContext.jsx` (new)
- `frontend/src/components/shared/Toast.jsx` (new)
- `frontend/src/components/shared/index.js` (modify)
- `frontend/src/index.js` (wrap with ToastProvider)
- `frontend/src/components/ApplicantDetail.jsx` (add toast calls)
- `frontend/src/components/ApplicantsList.jsx` (add toast calls)
- `frontend/src/components/CreateApplicantModal.jsx` (add toast calls)

### Toast Types
- `success` - Green, checkmark icon
- `error` - Red, alert icon
- `warning` - Yellow, warning icon
- `info` - Blue, info icon

### API
```javascript
const { toast } = useToast();
toast.success('Applicant approved successfully');
toast.error('Failed to reject applicant');
```

---

## Task 3: Confirmation Dialogs
**Priority: High | Complexity: Medium**

### Problem
Destructive actions (reject) happen with one click, no confirmation.

### Solution
Create a reusable ConfirmDialog component.

### Files to Create/Modify
- `frontend/src/components/shared/ConfirmDialog.jsx` (new)
- `frontend/src/components/shared/index.js` (modify)
- `frontend/src/components/ApplicantDetail.jsx` (add confirm before reject)

### Props
```javascript
<ConfirmDialog
  isOpen={showConfirm}
  title="Reject Applicant"
  message="Are you sure you want to reject this applicant? This action cannot be undone."
  confirmLabel="Reject"
  confirmVariant="danger"
  onConfirm={handleReject}
  onCancel={() => setShowConfirm(false)}
/>
```

---

## Task 4: Click Outside Hook for Dropdowns
**Priority: High | Complexity: Low**

### Problem
Filter dropdowns don't close when clicking outside.

### Solution
Create `useClickOutside` hook.

### Files to Create/Modify
- `frontend/src/hooks/useClickOutside.js` (new)
- `frontend/src/components/ApplicantsList.jsx` (apply to dropdowns)

### Implementation
```javascript
export function useClickOutside(ref, handler) {
  useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) return;
      handler(event);
    };
    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);
    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
}
```

---

## Task 5: Keyboard Shortcuts
**Priority: Medium | Complexity: Medium**

### Problem
No keyboard navigation for power users.

### Solution
Create keyboard shortcut system with visual hints.

### Files to Create/Modify
- `frontend/src/hooks/useKeyboardShortcut.js` (new)
- `frontend/src/components/shared/KeyboardShortcutHint.jsx` (new)
- `frontend/src/components/ApplicantsList.jsx` (add Cmd+K for search focus)
- `frontend/src/components/ApplicantDetail.jsx` (add A/R for approve/reject)
- `frontend/src/components/CreateApplicantModal.jsx` (Esc to close)

### Shortcuts
| Key | Context | Action |
|-----|---------|--------|
| `Cmd/Ctrl + K` | Anywhere | Focus search |
| `A` | Applicant Detail | Approve (opens confirm) |
| `R` | Applicant Detail | Reject (opens confirm) |
| `Esc` | Modal open | Close modal |
| `Enter` | Confirm dialog | Confirm action |

---

## Task 6: URL State for Detail Page Tabs
**Priority: Medium | Complexity: Low**

### Problem
Active tab lost on page refresh.

### Solution
Store active tab in URL search params.

### Files to Modify
- `frontend/src/components/ApplicantDetail.jsx`

### Implementation
```javascript
const [searchParams, setSearchParams] = useSearchParams();
const activeTab = searchParams.get('tab') || 'overview';

const setActiveTab = (tab) => {
  setSearchParams({ tab }, { replace: true });
};
```

---

## Task 7: Optimistic Updates for Review Actions
**Priority: Medium | Complexity: Medium**

### Problem
UI waits for API response before showing status change.

### Solution
Use React Query's optimistic update pattern.

### Files to Modify
- `frontend/src/hooks/useApplicants.js`

### Implementation
```javascript
export function useReviewApplicant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, decision, notes }) => { ... },
    onMutate: async ({ id, decision }) => {
      await queryClient.cancelQueries({ queryKey: applicantKeys.detail(id) });
      const previous = queryClient.getQueryData(applicantKeys.detail(id));

      queryClient.setQueryData(applicantKeys.detail(id), (old) => ({
        ...old,
        review_status: decision === 'approve' ? 'approved' : 'rejected',
      }));

      return { previous };
    },
    onError: (err, { id }, context) => {
      queryClient.setQueryData(applicantKeys.detail(id), context.previous);
    },
    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: applicantKeys.detail(id) });
    },
  });
}
```

---

## Task 8: Wire Up Batch Actions
**Priority: Medium | Complexity: Medium**

### Problem
Batch approve/reject buttons in list view are non-functional.

### Solution
Create batch mutation hooks and wire up buttons.

### Files to Modify
- `frontend/src/hooks/useApplicants.js` (add useBatchReview)
- `frontend/src/components/ApplicantsList.jsx` (wire up batch buttons)

---

## Task 9: Error Boundary
**Priority: Medium | Complexity: Low**

### Problem
Component errors crash the entire app.

### Solution
Add error boundaries around major sections.

### Files to Create/Modify
- `frontend/src/components/shared/ErrorBoundary.jsx` (new - may already exist, check first)
- `frontend/src/App.jsx` (wrap routes)

---

## Task 10: Accessibility Improvements
**Priority: Medium | Complexity: Medium**

### Problem
Missing ARIA labels, keyboard navigation, focus management.

### Solution
Systematic accessibility pass on all components.

### Changes
1. Add `aria-label` to icon-only buttons
2. Add `role="menu"` and `role="menuitem"` to dropdowns
3. Add keyboard navigation (arrow keys) to dropdowns
4. Trap focus in modals
5. Return focus to trigger element when modal closes
6. Add `aria-live="polite"` to toast container

### Files to Modify
- `frontend/src/components/ApplicantsList.jsx`
- `frontend/src/components/ApplicantDetail.jsx`
- `frontend/src/components/CreateApplicantModal.jsx`
- `frontend/src/components/shared/Toast.jsx`
- `frontend/src/components/shared/ConfirmDialog.jsx`

---

## Execution Order

### Phase 1: Foundation (Tasks 1, 2, 3, 4)
These are dependencies for other tasks and highest impact.

1. **useDebounce hook** - 5 min
2. **useClickOutside hook** - 5 min
3. **Toast system** - 20 min
4. **ConfirmDialog** - 15 min

### Phase 2: UX Enhancement (Tasks 5, 6, 7)
Improve user experience for power users.

5. **Keyboard shortcuts** - 20 min
6. **URL state for tabs** - 5 min
7. **Optimistic updates** - 15 min

### Phase 3: Completeness (Tasks 8, 9, 10)
Fill in remaining gaps.

8. **Batch actions** - 15 min
9. **Error boundary** - 10 min
10. **Accessibility** - 20 min

---

## Success Criteria

After implementation:
- [ ] Search waits 300ms before firing API
- [ ] Toast appears after every action (approve, reject, create, download)
- [ ] Reject shows confirmation dialog first
- [ ] Clicking outside dropdown closes it
- [ ] Cmd+K focuses search from anywhere
- [ ] A/R keys work on detail page
- [ ] Tab state persists on refresh
- [ ] Status updates instantly, rolls back on error
- [ ] Batch approve/reject works on selected items
- [ ] Component errors show fallback UI, not crash
- [ ] Screen reader can navigate the interface

---

## Files Summary

### New Files
- `frontend/src/hooks/useDebounce.js`
- `frontend/src/hooks/useClickOutside.js`
- `frontend/src/hooks/useKeyboardShortcut.js`
- `frontend/src/contexts/ToastContext.jsx`
- `frontend/src/components/shared/Toast.jsx`
- `frontend/src/components/shared/ConfirmDialog.jsx`
- `frontend/src/components/shared/KeyboardShortcutHint.jsx`

### Modified Files
- `frontend/src/hooks/useApplicants.js`
- `frontend/src/components/ApplicantsList.jsx`
- `frontend/src/components/ApplicantDetail.jsx`
- `frontend/src/components/CreateApplicantModal.jsx`
- `frontend/src/components/shared/index.js`
- `frontend/src/components/shared/ErrorBoundary.jsx`
- `frontend/src/index.js`
- `frontend/src/App.jsx`
