import type { APIRoute } from "astro";
import { supabase } from "~/lib/supabase";

export const prerender = false;

export const GET: APIRoute = async ({ url }) => {
  const token = url.searchParams.get("token");
  if (!token) {
    return new Response("Missing token", { status: 400 });
  }

  const { error } = await supabase
    .from("subscribers")
    .delete()
    .eq("unsub_token", token);

  if (error) {
    return new Response("Errore / Error", { status: 500 });
  }

  return new Response(
    "Iscrizione annullata. / You have been unsubscribed.",
    { status: 200, headers: { "content-type": "text/plain; charset=utf-8" } },
  );
};
