/**
 * usePermissions hook - Permission-based UI controls
 *
 * Reads permissions from the Auth0 user token and provides
 * convenient methods for checking access rights.
 *
 * Available permissions (from backend RBAC):
 * - read:applicants, write:applicants, review:applicants
 * - read:screening, review:screening
 * - read:cases, write:cases, review:cases
 * - read:documents, write:documents
 * - admin (full access)
 */

import { useMemo, useCallback } from 'react';
import { useAuth } from '../auth';

/**
 * Permission definitions by role for reference:
 *
 * viewer:
 *   - read:applicants
 *   - read:screening
 *   - read:cases
 *   - read:documents
 *
 * analyst:
 *   - read:applicants, write:applicants
 *   - read:screening, review:screening
 *   - read:cases, write:cases
 *   - read:documents, write:documents
 *
 * reviewer:
 *   - read:applicants, write:applicants, review:applicants
 *   - read:screening, review:screening
 *   - read:cases, write:cases, review:cases
 *   - read:documents, write:documents
 *
 * admin:
 *   - all permissions + admin
 */

// Permission constants for type safety
export const PERMISSIONS = {
  // Applicants
  READ_APPLICANTS: 'read:applicants',
  WRITE_APPLICANTS: 'write:applicants',
  REVIEW_APPLICANTS: 'review:applicants',

  // Screening
  READ_SCREENING: 'read:screening',
  REVIEW_SCREENING: 'review:screening',

  // Cases
  READ_CASES: 'read:cases',
  WRITE_CASES: 'write:cases',
  REVIEW_CASES: 'review:cases',

  // Documents
  READ_DOCUMENTS: 'read:documents',
  WRITE_DOCUMENTS: 'write:documents',

  // Admin
  ADMIN: 'admin',
};

/**
 * Hook to check user permissions
 *
 * @returns {Object} Permission checking utilities
 *
 * @example
 * const { can, canAny, canAll, isAdmin } = usePermissions();
 *
 * // Check single permission
 * if (can('review:applicants')) { ... }
 *
 * // Check if user can do any of these
 * if (canAny(['write:applicants', 'review:applicants'])) { ... }
 *
 * // Check if user can do all of these
 * if (canAll(['read:applicants', 'write:applicants'])) { ... }
 *
 * // Component usage
 * {can('review:applicants') && <ApproveButton />}
 */
export function usePermissions() {
  const { user, isAuthenticated } = useAuth();

  // Extract permissions from user object
  // Auth0 typically stores permissions in a custom namespace claim
  const permissions = useMemo(() => {
    if (!isAuthenticated || !user) {
      return [];
    }

    // Check various places where Auth0 might store permissions
    // The exact location depends on your Auth0 API configuration
    const perms =
      user.permissions || // Direct permissions array
      user['https://api.getclearance.com/permissions'] || // Custom namespace
      user['https://getclearance.dev/permissions'] || // Alt namespace
      [];

    return Array.isArray(perms) ? perms : [];
  }, [user, isAuthenticated]);

  // Check for admin role
  const isAdmin = useMemo(() => {
    return permissions.includes(PERMISSIONS.ADMIN);
  }, [permissions]);

  /**
   * Check if user has a specific permission
   * Admins always have all permissions
   */
  const can = useCallback(
    (permission) => {
      if (!isAuthenticated) return false;
      if (isAdmin) return true;
      return permissions.includes(permission);
    },
    [isAuthenticated, isAdmin, permissions]
  );

  /**
   * Check if user has ANY of the specified permissions
   */
  const canAny = useCallback(
    (permissionList) => {
      if (!isAuthenticated) return false;
      if (isAdmin) return true;
      return permissionList.some((p) => permissions.includes(p));
    },
    [isAuthenticated, isAdmin, permissions]
  );

  /**
   * Check if user has ALL of the specified permissions
   */
  const canAll = useCallback(
    (permissionList) => {
      if (!isAuthenticated) return false;
      if (isAdmin) return true;
      return permissionList.every((p) => permissions.includes(p));
    },
    [isAuthenticated, isAdmin, permissions]
  );

  // Convenience methods for common permission checks
  const canViewApplicants = useMemo(
    () => can(PERMISSIONS.READ_APPLICANTS),
    [can]
  );

  const canEditApplicants = useMemo(
    () => can(PERMISSIONS.WRITE_APPLICANTS),
    [can]
  );

  const canReviewApplicants = useMemo(
    () => can(PERMISSIONS.REVIEW_APPLICANTS),
    [can]
  );

  const canViewScreening = useMemo(
    () => can(PERMISSIONS.READ_SCREENING),
    [can]
  );

  const canReviewScreening = useMemo(
    () => can(PERMISSIONS.REVIEW_SCREENING),
    [can]
  );

  const canViewCases = useMemo(
    () => can(PERMISSIONS.READ_CASES),
    [can]
  );

  const canEditCases = useMemo(
    () => can(PERMISSIONS.WRITE_CASES),
    [can]
  );

  const canResolveCases = useMemo(
    () => can(PERMISSIONS.REVIEW_CASES),
    [can]
  );

  return {
    // Raw permissions array
    permissions,

    // Check functions
    can,
    canAny,
    canAll,
    isAdmin,

    // Convenience flags
    canViewApplicants,
    canEditApplicants,
    canReviewApplicants,
    canViewScreening,
    canReviewScreening,
    canViewCases,
    canEditCases,
    canResolveCases,
  };
}

/**
 * Component wrapper for permission-based rendering
 *
 * @example
 * <PermissionGate permission="review:applicants">
 *   <ApproveButton />
 * </PermissionGate>
 *
 * <PermissionGate permissions={['write:cases', 'review:cases']} requireAll>
 *   <AdminPanel />
 * </PermissionGate>
 */
export function PermissionGate({
  permission,
  permissions: permissionList,
  requireAll = false,
  fallback = null,
  children,
}) {
  const { can, canAny, canAll } = usePermissions();

  let hasPermission = false;

  if (permission) {
    hasPermission = can(permission);
  } else if (permissionList) {
    hasPermission = requireAll ? canAll(permissionList) : canAny(permissionList);
  }

  return hasPermission ? children : fallback;
}

/**
 * Hook for showing disabled state with reason
 *
 * @example
 * const { disabled, disabledReason } = useDisabledForPermission('review:applicants');
 *
 * <button disabled={disabled} title={disabledReason}>
 *   Approve
 * </button>
 */
export function useDisabledForPermission(permission, customMessage) {
  const { can } = usePermissions();
  const hasPermission = can(permission);

  return {
    disabled: !hasPermission,
    disabledReason: hasPermission
      ? null
      : customMessage || "You don't have permission for this action",
  };
}

export default usePermissions;
