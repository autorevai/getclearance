/**
 * useToast hook - Convenient wrapper for toast notifications
 *
 * Re-exports the useToast hook from ToastContext with additional
 * convenience methods for common notification patterns.
 */

import { useCallback } from 'react';
import { useToast as useToastContext } from '../contexts/ToastContext';

/**
 * Hook to trigger toast notifications
 *
 * @example
 * const toast = useToast();
 *
 * // Basic usage
 * toast.success('Operation completed');
 * toast.error('Something went wrong');
 * toast.warning('Please check your input');
 * toast.info('New update available');
 *
 * // With custom duration
 * toast.success('Saved!', { duration: 2000 });
 *
 * // With action button
 * toast.error('Failed to save', {
 *   action: { label: 'Retry', onClick: handleRetry }
 * });
 *
 * // Promise-based (show loading, then success/error)
 * toast.promise(saveData(), {
 *   loading: 'Saving...',
 *   success: 'Saved successfully',
 *   error: 'Failed to save'
 * });
 */
export function useToast() {
  const context = useToastContext();

  /**
   * Promise-based toast that shows loading state, then success/error
   */
  const promise = useCallback(
    async (promiseOrFn, messages = {}) => {
      const {
        loading = 'Loading...',
        success = 'Success!',
        error = 'Something went wrong',
      } = messages;

      // Show loading toast (doesn't auto-dismiss)
      const loadingId = context.info(loading, { duration: 0 });

      try {
        const result = typeof promiseOrFn === 'function'
          ? await promiseOrFn()
          : await promiseOrFn;

        // Remove loading toast and show success
        context.remove(loadingId);
        const successMessage = typeof success === 'function' ? success(result) : success;
        context.success(successMessage);

        return result;
      } catch (err) {
        // Remove loading toast and show error
        context.remove(loadingId);
        const errorMessage = typeof error === 'function' ? error(err) : error;
        context.error(errorMessage);

        throw err;
      }
    },
    [context]
  );

  /**
   * Show a dismissible error toast with retry action
   */
  const errorWithRetry = useCallback(
    (message, onRetry) => {
      return context.error(message, {
        duration: 0,
        action: {
          label: 'Retry',
          onClick: onRetry,
        },
      });
    },
    [context]
  );

  /**
   * Show success toast for CRUD operations
   */
  const crud = useCallback(
    (action, resourceName) => {
      const messages = {
        create: `${resourceName} created successfully`,
        update: `${resourceName} updated successfully`,
        delete: `${resourceName} deleted successfully`,
        save: `${resourceName} saved successfully`,
      };
      context.success(messages[action] || `${resourceName} ${action} successfully`);
    },
    [context]
  );

  return {
    ...context,
    promise,
    errorWithRetry,
    crud,
  };
}

export default useToast;
