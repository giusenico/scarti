import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.SUPABASE_URL;
const key = import.meta.env.SUPABASE_SERVICE_ROLE_KEY;

if (!url || !key) {
  throw new Error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set");
}

export const supabase = createClient(url, key, {
  auth: { persistSession: false },
});

export interface Subscriber {
  email: string;
  locale: "it" | "en";
  confirm_token: string;
  confirmed_at: string | null;
  unsub_token: string;
  created_at: string;
  last_sent_at: string | null;
}
