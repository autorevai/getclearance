/**
 * GetClearance SDK Components
 * ===========================
 * Export all SDK-related components for easy importing.
 */

export { default as VerificationSDK } from './VerificationSDK';
export { default as SDKVerifyPage } from './SDKVerifyPage';
export { default as SDKDemoPage } from './SDKDemoPage';

// Individual step components (for custom implementations)
export {
  ConsentStep,
  DocumentStep,
  SelfieStep,
  ReviewStep,
  CompleteStep,
} from './VerificationSDK';
