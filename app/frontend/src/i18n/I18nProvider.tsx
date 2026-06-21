import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { getTranslation, SupportedLocale } from './translations';

interface I18nContextType {
  locale: SupportedLocale;
  setLocale: (locale: SupportedLocale) => void;
  t: (key: string) => string;
  toggleLanguage: () => void;
}

const I18nContext = createContext<I18nContextType>({
  locale: 'zh',
  setLocale: () => {},
  t: (key: string) => key,
  toggleLanguage: () => {},
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<SupportedLocale>(() => {
    // Check localStorage for saved preference
    const saved = localStorage.getItem('ai-hedge-fund-locale');
    if (saved === 'en' || saved === 'zh') return saved;
    // Default to Chinese for Chinese users
    return 'zh';
  });

  const t = useCallback(
    (key: string) => getTranslation(key, locale),
    [locale]
  );

  const toggleLanguage = useCallback(() => {
    setLocale(prev => {
      const next = prev === 'zh' ? 'en' : 'zh';
      localStorage.setItem('ai-hedge-fund-locale', next);
      return next;
    });
  }, []);

  return (
    <I18nContext.Provider value={{ locale, setLocale, t, toggleLanguage }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useTranslation(): I18nContextType {
  return useContext(I18nContext);
}

export default I18nContext;
