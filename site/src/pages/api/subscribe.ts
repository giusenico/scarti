import type { APIRoute } from "astro";
import { supabase } from "~/lib/supabase";
import { sendConfirmationEmail } from "~/lib/mail";

export const prerender = false;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const POST: APIRoute = async ({ request, url }) => {
  let body: { email?: string; locale?: string };
  try {
    const ct = request.headers.get("content-type") ?? "";
    if (ct.includes("application/json")) {
      body = await request.json();
    } else {
      const form = await request.formData();
      body = {
        email: form.get("email")?.toString(),
        locale: form.get("locale")?.toString(),
      };
    }
  } catch {
    return new Response(JSON.stringify({ error: "invalid body" }), {
      status: 400,
      headers: { "content-type": "application/json" },
    });
  }

  const email = (body.email ?? "").trim().toLowerCase();
  const locale = body.locale === "en" ? "en" : "it";

  if (!EMAIL_RE.test(email)) {
    return new Response(JSON.stringify({ error: "invalid email" }), {
      status: 400,
      headers: { "content-type": "application/json" },
    });
  }

  // Upsert: if the email already exists we refresh the token and re-send,
  // instead of leaking that the address is already known.
  const { data, error } = await supabase()
    .from("subscribers")
    .upsert({ email, locale }, { onConflict: "email" })
    .select("confirm_token")
    .single();

  if (error || !data) {
    return new Response(JSON.stringify({ error: "database error" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }

  const confirmUrl = new URL(
    `/api/confirm?token=${data.confirm_token}`,
    url.origin,
  ).toString();

  try {
    await sendConfirmationEmail(email, confirmUrl, locale);
  } catch {
    return new Response(JSON.stringify({ error: "mail error" }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
};
