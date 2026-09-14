import { Dispatch, SetStateAction, useEffect, useState } from 'react';

type PersistedState<T> = [T, Dispatch<SetStateAction<T>>];

function usePersistedState<T>(defaultValue: T, key: string): PersistedState<T> {
  const [value, setValue] = useState<T>(() => {
    const value = window.localStorage.getItem(key);

    if (!value) {
      return defaultValue;
    }
    const parsed = JSON.parse(value) as T;
    // Merge over the defaults so settings stored by older app versions pick
    // up newly added fields instead of leaving them undefined.
    if (
      typeof defaultValue === "object" &&
      defaultValue !== null &&
      typeof parsed === "object" &&
      parsed !== null
    ) {
      return { ...defaultValue, ...parsed };
    }
    return parsed;
  });

  useEffect(() => {
    window.localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);

  return [value, setValue];
}

export { usePersistedState };
