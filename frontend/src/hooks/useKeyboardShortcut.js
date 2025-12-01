import { useEffect, useCallback } from 'react';

/**
 * Hook to register a keyboard shortcut
 * @param {string|string[]} keys - Key or array of keys (e.g., 'k', ['meta', 'k'], ['ctrl', 'shift', 'p'])
 * @param {Function} callback - Function to call when shortcut is triggered
 * @param {Object} options - Configuration options
 * @param {boolean} options.enabled - Whether the shortcut is active (default: true)
 * @param {boolean} options.preventDefault - Whether to prevent default behavior (default: true)
 * @param {boolean} options.enableOnFormElements - Allow in inputs/textareas (default: false)
 */
export function useKeyboardShortcut(keys, callback, options = {}) {
  const {
    enabled = true,
    preventDefault = true,
    enableOnFormElements = false,
  } = options;

  const handleKeyDown = useCallback(
    (event) => {
      if (!enabled) return;

      // Check if we're in a form element
      const target = event.target;
      const isFormElement =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable;

      if (isFormElement && !enableOnFormElements) {
        // Allow Escape in form elements
        if (event.key !== 'Escape') return;
      }

      // Normalize keys to array
      const keyArray = Array.isArray(keys) ? keys : [keys];

      // Check modifier keys
      const modifiers = {
        meta: event.metaKey,
        ctrl: event.ctrlKey,
        alt: event.altKey,
        shift: event.shiftKey,
      };

      // Separate modifier keys from regular keys
      const requiredModifiers = keyArray.filter((k) =>
        ['meta', 'ctrl', 'alt', 'shift'].includes(k.toLowerCase())
      );
      const requiredKeys = keyArray.filter(
        (k) => !['meta', 'ctrl', 'alt', 'shift'].includes(k.toLowerCase())
      );

      // Check if all required modifiers are pressed
      const modifiersMatch = requiredModifiers.every(
        (mod) => modifiers[mod.toLowerCase()]
      );

      // Check if the main key matches
      const keyMatches = requiredKeys.some(
        (k) => event.key.toLowerCase() === k.toLowerCase()
      );

      // For single key shortcuts without modifiers, make sure no modifiers are pressed
      const noUnwantedModifiers =
        requiredModifiers.length > 0 ||
        (!event.metaKey && !event.ctrlKey && !event.altKey);

      if (modifiersMatch && keyMatches && noUnwantedModifiers) {
        if (preventDefault) {
          event.preventDefault();
        }
        callback(event);
      }
    },
    [keys, callback, enabled, preventDefault, enableOnFormElements]
  );

  useEffect(() => {
    if (!enabled) return;

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown, enabled]);
}

/**
 * Hook to register multiple keyboard shortcuts
 * @param {Array<{keys: string|string[], callback: Function, options?: Object}>} shortcuts
 */
export function useKeyboardShortcuts(shortcuts) {
  useEffect(() => {
    const handlers = shortcuts.map(({ keys, callback, options = {} }) => {
      const {
        enabled = true,
        preventDefault = true,
        enableOnFormElements = false,
      } = options;

      const handler = (event) => {
        if (!enabled) return;

        const target = event.target;
        const isFormElement =
          target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.tagName === 'SELECT' ||
          target.isContentEditable;

        if (isFormElement && !enableOnFormElements) {
          if (event.key !== 'Escape') return;
        }

        const keyArray = Array.isArray(keys) ? keys : [keys];

        const modifiers = {
          meta: event.metaKey,
          ctrl: event.ctrlKey,
          alt: event.altKey,
          shift: event.shiftKey,
        };

        const requiredModifiers = keyArray.filter((k) =>
          ['meta', 'ctrl', 'alt', 'shift'].includes(k.toLowerCase())
        );
        const requiredKeys = keyArray.filter(
          (k) => !['meta', 'ctrl', 'alt', 'shift'].includes(k.toLowerCase())
        );

        const modifiersMatch = requiredModifiers.every(
          (mod) => modifiers[mod.toLowerCase()]
        );

        const keyMatches = requiredKeys.some(
          (k) => event.key.toLowerCase() === k.toLowerCase()
        );

        const noUnwantedModifiers =
          requiredModifiers.length > 0 ||
          (!event.metaKey && !event.ctrlKey && !event.altKey);

        if (modifiersMatch && keyMatches && noUnwantedModifiers) {
          if (preventDefault) {
            event.preventDefault();
          }
          callback(event);
        }
      };

      document.addEventListener('keydown', handler);
      return handler;
    });

    return () => {
      handlers.forEach((handler) => {
        document.removeEventListener('keydown', handler);
      });
    };
  }, [shortcuts]);
}

/**
 * Get the display string for a keyboard shortcut
 * @param {string|string[]} keys - Key or array of keys
 * @returns {string} Display string (e.g., "⌘K" or "Ctrl+K")
 */
export function getShortcutDisplay(keys) {
  const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform);

  const keyArray = Array.isArray(keys) ? keys : [keys];

  const symbols = {
    meta: isMac ? '⌘' : 'Ctrl',
    ctrl: isMac ? '⌃' : 'Ctrl',
    alt: isMac ? '⌥' : 'Alt',
    shift: isMac ? '⇧' : 'Shift',
    enter: '↵',
    escape: 'Esc',
    esc: 'Esc',
  };

  return keyArray
    .map((k) => symbols[k.toLowerCase()] || k.toUpperCase())
    .join(isMac ? '' : '+');
}

export default useKeyboardShortcut;
