import { createContext, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "./api.js";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If we already have a token, confirm it still works.
    if (!getToken()) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const finishAuth = (data) => {
    setToken(data.token);
    setUser(data.user);
  };

  const value = {
    user,
    loading,
    login: async (email, password) => finishAuth(await api.login(email, password)),
    signup: async (email, password) => finishAuth(await api.signup(email, password)),
    logout: () => {
      setToken(null);
      setUser(null);
    },
  };
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth() {
  return useContext(AuthCtx);
}
