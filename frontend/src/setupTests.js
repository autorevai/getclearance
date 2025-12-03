/**
 * Test Setup Configuration
 *
 * This file runs before each test and sets up:
 * - Jest DOM matchers
 * - Global mocks for browser APIs
 * - Toast context mock
 */

import '@testing-library/jest-dom';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock URL.createObjectURL
global.URL.createObjectURL = jest.fn(() => 'mock-url');
global.URL.revokeObjectURL = jest.fn();

// Mock XMLHttpRequest for upload tests
global.XMLHttpRequest = class MockXMLHttpRequest {
  constructor() {
    this.readyState = 0;
    this.status = 0;
    this.statusText = '';
    this.response = null;
    this.responseText = '';
    this.responseType = '';
    this.timeout = 0;
    this.upload = {
      onprogress: null,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    };
    this.onload = null;
    this.onerror = null;
    this.ontimeout = null;
    this.onabort = null;
    this.onreadystatechange = null;
  }

  open() {}
  send() {
    // Simulate successful upload
    this.status = 200;
    if (this.upload.onprogress) {
      this.upload.onprogress({ lengthComputable: true, loaded: 100, total: 100 });
    }
    if (this.onload) {
      setTimeout(() => this.onload(), 0);
    }
  }
  setRequestHeader() {}
  abort() {
    if (this.onabort) this.onabort();
  }
  getAllResponseHeaders() {
    return '';
  }
  getResponseHeader() {
    return null;
  }
};

// Mock console methods to reduce noise in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    // Filter out known React warnings in tests
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
       args[0].includes('Warning: An update to') ||
       args[0].includes('Warning: validateDOMNesting'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
