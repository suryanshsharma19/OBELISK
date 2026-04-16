import axios from 'axios';
import './api';
import {
  clearAccessToken,
  ensureAuthenticated,
  getAccessToken,
} from './session';

jest.mock('axios', () => {
  let requestInterceptor = async (config) => config;
  let responseErrorInterceptor = async (error) => Promise.reject(error);

  const instance = {
    interceptors: {
      request: {
        use: (handler) => {
          requestInterceptor = handler;
        },
      },
      response: {
        use: (_success, errorHandler) => {
          responseErrorInterceptor = errorHandler;
        },
      },
    },
  };

  return {
    __esModule: true,
    default: {
      create: () => instance,
      __getInterceptors: () => ({ requestInterceptor, responseErrorInterceptor }),
    },
  };
});

jest.mock('./session', () => ({
  ensureAuthenticated: jest.fn(),
  getAccessToken: jest.fn(),
  clearAccessToken: jest.fn(),
}));

describe('api client interceptors', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    ensureAuthenticated.mockResolvedValue('token-from-login');
    getAccessToken.mockReturnValue('token-from-login');
  });

  it('attaches bearer token to authenticated requests', async () => {
    const { requestInterceptor } = axios.__getInterceptors();

    const config = await requestInterceptor({
      url: '/api/packages/list',
      headers: {},
    });

    expect(ensureAuthenticated).toHaveBeenCalledTimes(1);
    expect(config.headers.Authorization).toBe('Bearer token-from-login');
  });

  it('skips bootstrap auth for login endpoint', async () => {
    const { requestInterceptor } = axios.__getInterceptors();

    getAccessToken.mockReturnValue(null);

    const config = await requestInterceptor({
      url: '/api/auth/login',
      headers: {},
    });

    expect(ensureAuthenticated).not.toHaveBeenCalled();
    expect(config.headers.Authorization).toBeUndefined();
  });

  it('clears local token on 401 session expiry', async () => {
    const { responseErrorInterceptor } = axios.__getInterceptors();

    await expect(
      responseErrorInterceptor({
        response: {
          status: 401,
          data: { message: 'session expired' },
        },
        message: 'Unauthorized',
      }),
    ).rejects.toThrow('session expired');

    expect(clearAccessToken).toHaveBeenCalledTimes(1);
  });
});
