import type { APIRoute } from "astro";
import { supabase } from "~/lib/supabase";

export const prerender = false;

export const GET: APIRoute = async ({ url }) => {
  const token = url.searchParams.get("token");
  if (!token) {
    return new Response("Missing token", { status: 400 });
  }

  const { data, error } = await supabase
    .from("subscribers")
    .update({ confirmed_at: new Date().toISOString() })
    .eq("confirm_token", token)
    .select("locale")
    .single();

  if (error || !data) {
    return new Response("Token non valido o già usato / Invalid or already used token.", {
      status: 400,
    });
  }

  const dest = data.locale === "en" ? "/en/iscriviti?confirmed=1" : "/iscriviti?confirmed=1";
  return Response.redirect(new URL(dest, url.origin).toString(), 302);
};
