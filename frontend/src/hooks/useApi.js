/**
 * Custom hook for API calls with loading / error state.
 *
 * Usage:
 *   const { data, loading, error, execute } = useApi(getPackages);
 *   useEffect(() => { execute({ limit: 20 }); }, [execute]);
 */

import { useState, useCallback } from 'react';

export default function useApi(apiFunc) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(
    async (...args) => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiFunc(...args);
        setData(result);
        return result;
      } catch (err) {
        setError(err.message || 'Request failed');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiFunc],
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}
