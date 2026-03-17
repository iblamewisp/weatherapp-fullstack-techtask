"use client";
import { Toaster, toast } from "react-hot-toast";

export function Notification() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        success: {
          style: { background: "#22c55e", color: "#fff" },
        },
        error: {
          style: { background: "#ef4444", color: "#fff" },
        },
      }}
    />
  );
}

export const notify = {
  success: (msg: string) => toast.success(msg),
  error: (msg: string) => toast.error(msg),
};
