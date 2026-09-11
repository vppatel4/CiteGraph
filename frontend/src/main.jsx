import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "./styles.css";
import { AuthProvider, useAuth } from "./auth.jsx";
import App from "./App.jsx";
import Login from "./pages/Login.jsx";

function Backdrop() {
  return (
    <div className="backdrop" aria-hidden="true">
      <div className="blob a" />
      <div className="blob b" />
      <div className="blob c" />
    </div>
  );
}

function Protected() {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="login-shell">
        <span className="spinner" />
      </div>
    );
  }
  return user ? <App /> : <Navigate to="/login" replace />;
}

function Root() {
  const { user } = useAuth();
  return (
    <>
      <Backdrop />
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
        <Route path="/*" element={<Protected />} />
      </Routes>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Root />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
