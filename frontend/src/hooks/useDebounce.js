/**
 * Debounce hook — delays a value update until `delay` ms have passed
 * without another change.  Perfect for search inputs.
 *
 * Usage:
 *   const debouncedQuery = useDebounce(query, 300);
 */

import { useState, useEffect } from 'react';

export default function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
