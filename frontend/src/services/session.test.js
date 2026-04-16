import axios from 'axios';

import {
  clearAccessToken,
  ensureAuthenticated,
  getAccessToken,
  setAccessToken,
} from './session';

jest.mock('axios', () => ({
  post: jest.fn(),
}));

describe('session service', () => {
  const originalUsername = process.env.REACT_APP_AUTH_USERNAME;
  const originalPassword = process.env.REACT_APP_AUTH_PASSWORD;

  beforeEach(() => {
    jest.clearAllMocks();
    clearAccessToken();
    process.env.REACT_APP_AUTH_USERNAME = 'admin';
    process.env.REACT_APP_AUTH_PASSWORD = 'strong-password';
  });

  afterAll(() => {
    process.env.REACT_APP_AUTH_USERNAME = originalUsername;
    process.env.REACT_APP_AUTH_PASSWORD = originalPassword;
  });

  it('reuses one login request for concurrent ensureAuthenticated calls', async () => {
    let resolveLogin;
    axios.post.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveLogin = resolve;
        }),
    );

    const first = ensureAuthenticated();
    const second = ensureAuthenticated();

    expect(axios.post).toHaveBeenCalledTimes(1);

    resolveLogin({ data: { access_token: 'token-123' } });

    await expect(first).resolves.toBe('token-123');
    await expect(second).resolves.toBe('token-123');
    expect(getAccessToken()).toBe('token-123');
  });

  it('returns existing access token without triggering login', async () => {
    setAccessToken('already-present');

    await expect(ensureAuthenticated()).resolves.toBe('already-present');
    expect(axios.post).not.toHaveBeenCalled();
  });

  it('fails fast when credential env vars are missing', async () => {
    process.env.REACT_APP_AUTH_USERNAME = '';
    process.env.REACT_APP_AUTH_PASSWORD = '';

    await expect(ensureAuthenticated()).rejects.toThrow(
      /missing react_app_auth_username\/react_app_auth_password/i,
    );
    expect(axios.post).not.toHaveBeenCalled();
  });
});
