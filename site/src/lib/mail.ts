import { Resend } from "resend";

let _resend: Resend | null = null;
function resend(): Resend {
  if (_resend) return _resend;
  const key = import.meta.env.RESEND_API_KEY;
  if (!key) throw new Error("RESEND_API_KEY must be set");
  _resend = new Resend(key);
  return _resend;
}
const fromAddress = () =>
  import.meta.env.SCARTI_FROM_EMAIL || "Scarti <newsletter@scarti.example>";

export async function sendConfirmationEmail(
  email: string,
  confirmUrl: string,
  locale: "it" | "en",
): Promise<void> {
  const { subject, text, html } =
    locale === "it"
      ? {
          subject: "Conferma l'iscrizione a Scarti",
          text: `Ciao,\n\nper completare l'iscrizione alla newsletter settimanale di Scarti clicca il link qui sotto.\n\n${confirmUrl}\n\nSe non sei stato tu a iscriverti, ignora questa mail.\n\n— Scarti`,
          html: `<p>Ciao,</p><p>per completare l'iscrizione alla newsletter settimanale di <strong>Scarti</strong> clicca il link qui sotto.</p><p><a href="${confirmUrl}">${confirmUrl}</a></p><p style="color:#888;font-size:13px">Se non sei stato tu a iscriverti, ignora questa mail.</p>`,
        }
      : {
          subject: "Confirm your Scarti subscription",
          text: `Hi,\n\nto complete your subscription to the Scarti weekly newsletter, click the link below.\n\n${confirmUrl}\n\nIf this wasn't you, please ignore this email.\n\n— Scarti`,
          html: `<p>Hi,</p><p>to complete your subscription to the <strong>Scarti</strong> weekly newsletter, click the link below.</p><p><a href="${confirmUrl}">${confirmUrl}</a></p><p style="color:#888;font-size:13px">If this wasn't you, please ignore this email.</p>`,
        };

  await resend().emails.send({ from: fromAddress(), to: email, subject, text, html });
}
