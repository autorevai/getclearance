import { useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for trapping focus within a container
 *
 * @param {boolean} isActive - Whether the focus trap is active
 * @param {Object} options - Configuration options
 * @param {HTMLElement} options.initialFocus - Element to focus initially (defaults to first focusable)
 * @param {Function} options.onEscape - Callback when Escape is pressed
 * @param {HTMLElement} options.returnFocus - Element to return focus to when trap deactivates
 * @returns {Object} ref to attach to container
 */
export function useFocusTrap(isActive, options = {}) {
  const containerRef = useRef(null);
  const previousActiveElement = useRef(null);

  const getFocusableElements = useCallback(() => {
    if (!containerRef.current) return [];

    const focusableSelectors = [
      'button:not([disabled]):not([tabindex="-1"])',
      'a[href]:not([tabindex="-1"])',
      'input:not([disabled]):not([tabindex="-1"])',
      'select:not([disabled]):not([tabindex="-1"])',
      'textarea:not([disabled]):not([tabindex="-1"])',
      '[tabindex]:not([tabindex="-1"]):not([disabled])',
    ].join(', ');

    return Array.from(containerRef.current.querySelectorAll(focusableSelectors))
      .filter(el => el.offsetParent !== null); // Visible elements only
  }, []);

  useEffect(() => {
    if (!isActive) return;

    // Store the previously focused element for returning focus
    previousActiveElement.current = options.returnFocus || document.activeElement;

    // Focus initial element or first focusable
    const focusInitial = () => {
      if (options.initialFocus) {
        options.initialFocus.focus();
      } else {
        const focusableElements = getFocusableElements();
        if (focusableElements.length > 0) {
          focusableElements[0].focus();
        }
      }
    };

    // Small delay to ensure the modal is rendered
    const timeoutId = setTimeout(focusInitial, 10);

    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && options.onEscape) {
        e.preventDefault();
        options.onEscape();
        return;
      }

      if (e.key !== 'Tab') return;

      const focusableElements = getFocusableElements();
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      // Shift + Tab on first element -> go to last
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
        return;
      }

      // Tab on last element -> go to first
      if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
        return;
      }

      // If focus is outside the container, move it to the first element
      if (!containerRef.current?.contains(document.activeElement)) {
        e.preventDefault();
        firstElement.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('keydown', handleKeyDown);

      // Return focus to the previous element
      if (previousActiveElement.current && previousActiveElement.current.focus) {
        // Small delay to ensure the modal is fully closed
        setTimeout(() => {
          previousActiveElement.current?.focus();
        }, 10);
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive, options.initialFocus, options.onEscape, options.returnFocus, getFocusableElements]);

  return containerRef;
}

/**
 * FocusTrap component wrapper
 */
export function FocusTrap({ isActive, onEscape, returnFocus, initialFocus, children }) {
  const containerRef = useFocusTrap(isActive, { onEscape, returnFocus, initialFocus });

  return (
    <div ref={containerRef}>
      {children}
    </div>
  );
}

export default useFocusTrap;
