"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { User } from "@/types/auth";

interface AuthContextValue { user: User | null; ready: boolean; login: (token: string, user: User) => void; logout: () => void }
const AuthContext = createContext<AuthContextValue | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null); const [ready, setReady] = useState(false);
  useEffect(() => { const raw = localStorage.getItem("mytasco_user"); if (raw) { try { setUser(JSON.parse(raw) as User); } catch { localStorage.removeItem("mytasco_user"); } } setReady(true); }, []);
  const login = (token: string, nextUser: User) => { localStorage.setItem("mytasco_access_token", token); localStorage.setItem("mytasco_user", JSON.stringify(nextUser)); setUser(nextUser); };
  const logout = () => { localStorage.removeItem("mytasco_access_token"); localStorage.removeItem("mytasco_user"); setUser(null); };
  return <AuthContext.Provider value={{ user, ready, login, logout }}>{children}</AuthContext.Provider>;
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error("useAuth must be used inside AuthProvider"); return value; }
