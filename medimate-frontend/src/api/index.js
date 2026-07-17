import { realApi } from './client.js';
import { mockApi } from './mock.js';

const useMocks = String(import.meta.env.VITE_USE_MOCKS).toLowerCase() === 'true';

export const api = useMocks ? mockApi : realApi;
export { ApiError } from './client.js';
