import { useEffect, useCallback } from 'react';

/**
 * Hook to detect clicks outside of a referenced element
 * @param {React.RefObject} ref - Ref to the element to detect outside clicks for
 * @param {Function} handler - Callback to run when clicking outside
 * @param {boolean} enabled - Whether the hook is active (default: true)
 */
export function useClickOutside(ref, handler, enabled = true) {
  const handleClickOutside = useCallback(
    (event) => {
      if (!enabled) return;
      if (!ref.current) return;
      if (ref.current.contains(event.target)) return;

      handler(event);
    },
    [ref, handler, enabled]
  );

  useEffect(() => {
    if (!enabled) return;

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [handleClickOutside, enabled]);
}

/**
 * Hook to detect clicks outside of multiple referenced elements
 * @param {React.RefObject[]} refs - Array of refs to elements
 * @param {Function} handler - Callback to run when clicking outside all refs
 * @param {boolean} enabled - Whether the hook is active (default: true)
 */
export function useClickOutsideMultiple(refs, handler, enabled = true) {
  const handleClickOutside = useCallback(
    (event) => {
      if (!enabled) return;

      const clickedInsideAny = refs.some(
        (ref) => ref.current && ref.current.contains(event.target)
      );

      if (!clickedInsideAny) {
        handler(event);
      }
    },
    [refs, handler, enabled]
  );

  useEffect(() => {
    if (!enabled) return;

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [handleClickOutside, enabled]);
}

export default useClickOutside;
