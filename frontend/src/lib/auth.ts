const SESSION_KEY = "marketsense.session.v1";

export type MarketSenseSession = {
  accessToken: string;
  role: string;
  expiresAt: number;
};

export function saveSession(accessToken: string, role: string, expiresIn: number) {
  if (typeof window === "undefined") return;
  const session: MarketSenseSession = {
    accessToken,
    role,
    expiresAt: Date.now() + expiresIn * 1000,
  };
  window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function getSession(): MarketSenseSession | null {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    const session = JSON.parse(raw) as MarketSenseSession;
    if (!session.accessToken || session.expiresAt <= Date.now()) {
      clearSession();
      return null;
    }
    return session;
  } catch {
    clearSession();
    return null;
  }
}

export function getAccessToken() {
  return getSession()?.accessToken ?? null;
}

export function clearSession() {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(SESSION_KEY);
}
