/**
 * React Query hooks for Settings
 *
 * Production-grade hooks for:
 * - Tenant settings (general, notifications, security, branding)
 * - Team member management
 * - Team invitations
 */

import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth';
import { SettingsService } from '../services';

// Query key factory for consistent key management
export const settingsKeys = {
  all: ['settings'],
  settings: () => [...settingsKeys.all, 'tenant'],
  notifications: () => [...settingsKeys.all, 'notifications'],
  security: () => [...settingsKeys.all, 'security'],
  branding: () => [...settingsKeys.all, 'branding'],
  team: () => [...settingsKeys.all, 'team'],
  teamMembers: () => [...settingsKeys.team(), 'members'],
  invitations: () => [...settingsKeys.team(), 'invitations'],
};

/**
 * Hook to get a memoized SettingsService instance
 */
function useSettingsService() {
  const { getToken } = useAuth();
  return useMemo(() => new SettingsService(getToken), [getToken]);
}

// ===========================================
// SETTINGS HOOKS
// ===========================================

/**
 * Hook to fetch all tenant settings
 */
export function useSettings(options = {}) {
  const service = useSettingsService();

  return useQuery({
    queryKey: settingsKeys.settings(),
    queryFn: ({ signal }) => service.getSettings({ signal }),
    staleTime: 60000, // Settings don't change often
    ...options,
  });
}

/**
 * Hook to update general settings
 */
export function useUpdateGeneralSettings() {
  const service = useSettingsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.updateGeneralSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.settings() });
    },
  });
}

// ===========================================
// NOTIFICATION HOOKS
// ===========================================

/**
 * Hook to fetch notification preferences
 */
export function useNotificationPreferences(options = {}) {
  const service = useSettingsService();

  return useQuery({
    queryKey: settingsKeys.notifications(),
    queryFn: ({ signal }) => service.getNotificationPreferences({ signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to update notification preferences
 */
export function useUpdateNotificationPreferences() {
  const service = useSettingsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (preferences) => service.updateNotificationPreferences(preferences),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.notifications() });
      queryClient.invalidateQueries({ queryKey: settingsKeys.settings() });
    },
  });
}

// ===========================================
// SECURITY HOOKS
// ===========================================

/**
 * Hook to fetch security settings
 */
export function useSecuritySettings(options = {}) {
  const service = useSettingsService();

  return useQuery({
    queryKey: settingsKeys.security(),
    queryFn: ({ signal }) => service.getSecuritySettings({ signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to update security settings
 */
export function useUpdateSecuritySettings() {
  const service = useSettingsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.updateSecuritySettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.security() });
      queryClient.invalidateQueries({ queryKey: settingsKeys.settings() });
    },
  });
}

// ===========================================
// BRANDING HOOKS
// ===========================================

/**
 * Hook to fetch branding settings
 */
export function useBrandingSettings(options = {}) {
  const service = useSettingsService();

  return useQuery({
    queryKey: settingsKeys.branding(),
    queryFn: ({ signal }) => service.getBrandingSettings({ signal }),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to update branding settings
 */
export function useUpdateBrandingSettings() {
  const service = useSettingsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => service.updateBrandingSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.branding() });
      queryClient.invalidateQueries({ queryKey: settingsKeys.settings() });
    },
  });
}

// ===========================================
// TEAM MEMBER HOOKS
// ===========================================

/**
 * Hook to fetch team members
 */
export function useTeamMembers(options = {}) {
  const service = useSettingsService();

  return useQuery({
    queryKey: settingsKeys.teamMembers(),
    queryFn: ({ signal }) => service.getTeamMembers({ signal }),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to update team member role
 */
export function useUpdateTeamMemberRole() {
  const service = useSettingsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ memberId, role }) => service.updateTeamMemberRole(memberId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.teamMembers() });
    },
  });
}

/**
 * Hook to remove team member
 */
export function useRemoveTeamMember() {
  const service = useSettingsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (memberId) => service.removeTeamMember(memberId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.teamMembers() });
    },
  });
}

// ===========================================
// INVITATION HOOKS
// ===========================================

/**
 * Hook to fetch pending invitations
 */
export function useInvitations(options = {}) {
  const service = useSettingsService();

  return useQuery({
    queryKey: settingsKeys.invitations(),
    queryFn: ({ signal }) => service.getInvitations({ signal }),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to invite a team member
 */
export function useInviteTeamMember() {
  const service = useSettingsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ email, role, message }) => service.inviteTeamMember(email, role, message),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.invitations() });
    },
  });
}

/**
 * Hook to cancel an invitation
 */
export function useCancelInvitation() {
  const service = useSettingsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invitationId) => service.cancelInvitation(invitationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.invitations() });
    },
  });
}

/**
 * Hook to resend an invitation
 */
export function useResendInvitation() {
  const service = useSettingsService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invitationId) => service.resendInvitation(invitationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.invitations() });
    },
  });
}
