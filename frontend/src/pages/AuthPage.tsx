import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { fetchMe, login, register, type LoginInput, type RegisterInput } from "../features/auth/authApi";
import { useAuthStore } from "../features/auth/authStore";
import { extractApiError } from "../utils/errors";

type Mode = "login" | "register";

const emptyRegister: RegisterInput = {
  username: "",
  email: "",
  phone: "",
  national_id: "",
  first_name: "",
  last_name: "",
  password: "",
};

export function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("login");
  const [loginForm, setLoginForm] = useState<LoginInput>({ identifier: "", password: "" });
  const [registerForm, setRegisterForm] = useState<RegisterInput>(emptyRegister);
  const [message, setMessage] = useState("");
  const setAuth = useAuthStore((state) => state.setAuth);
  const setRoles = useAuthStore((state) => state.setRoles);

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: async (data) => {
      setAuth({ user: data.user, tokens: data.tokens });
      const me = await fetchMe();
      setRoles(me.roles || []);
      navigate("/dashboard");
    },
    onError: (error) => setMessage(extractApiError(error, "Login failed")),
  });

  const registerMutation = useMutation({
    mutationFn: register,
    onSuccess: () => {
      setMessage("Registration successful. Please login.");
      setMode("login");
    },
    onError: (error) => setMessage(extractApiError(error, "Registration failed")),
  });

  function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    loginMutation.mutate(loginForm);
  }

  function submitRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    registerMutation.mutate(registerForm);
  }

  return (
    <section className="page auth-page">
      <div className="auth-card">
        <div className="auth-switcher">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
            Login
          </button>
          <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
            Register
          </button>
        </div>

        {mode === "login" ? (
          <form onSubmit={submitLogin} className="form-grid">
            <label>
              Identifier
              <input
                value={loginForm.identifier}
                onChange={(event) => setLoginForm((prev) => ({ ...prev, identifier: event.target.value }))}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm((prev) => ({ ...prev, password: event.target.value }))}
                required
              />
            </label>
            <button type="submit" className="primary-button" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? "Signing in..." : "Sign In"}
            </button>
          </form>
        ) : (
          <form onSubmit={submitRegister} className="form-grid register-grid">
            <label>
              Username
              <input
                value={registerForm.username}
                onChange={(event) => setRegisterForm((prev) => ({ ...prev, username: event.target.value }))}
                required
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={registerForm.email}
                onChange={(event) => setRegisterForm((prev) => ({ ...prev, email: event.target.value }))}
                required
              />
            </label>
            <label>
              Phone
              <input
                value={registerForm.phone}
                onChange={(event) => setRegisterForm((prev) => ({ ...prev, phone: event.target.value }))}
                required
              />
            </label>
            <label>
              National ID
              <input
                value={registerForm.national_id}
                onChange={(event) => setRegisterForm((prev) => ({ ...prev, national_id: event.target.value }))}
                required
              />
            </label>
            <label>
              First Name
              <input
                value={registerForm.first_name}
                onChange={(event) => setRegisterForm((prev) => ({ ...prev, first_name: event.target.value }))}
                required
              />
            </label>
            <label>
              Last Name
              <input
                value={registerForm.last_name}
                onChange={(event) => setRegisterForm((prev) => ({ ...prev, last_name: event.target.value }))}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={registerForm.password}
                onChange={(event) => setRegisterForm((prev) => ({ ...prev, password: event.target.value }))}
                required
              />
            </label>
            <button type="submit" className="primary-button" disabled={registerMutation.isPending}>
              {registerMutation.isPending ? "Submitting..." : "Create Account"}
            </button>
          </form>
        )}

        {message && <p className="form-message">{message}</p>}
      </div>
    </section>
  );
}
