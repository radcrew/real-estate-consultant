import { NextResponse } from "next/server";

const BUTTONDOWN_API = "https://api.buttondown.email/v1/subscribers";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Subscribe an email to the Buttondown newsletter list. Runs server-side so the
 * Buttondown API key (BUTTONDOWN_API_KEY) is never exposed to the browser.
 */
export async function POST(request: Request) {
  const apiKey = process.env.BUTTONDOWN_API_KEY?.trim();
  if (!apiKey) {
    return NextResponse.json(
      { error: "Newsletter is not configured." },
      { status: 503 },
    );
  }

  let email: unknown;
  try {
    ({ email } = await request.json());
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  if (typeof email !== "string" || !EMAIL_RE.test(email.trim())) {
    return NextResponse.json(
      { error: "Please enter a valid email address." },
      { status: 400 },
    );
  }

  let res: Response;
  try {
    res = await fetch(BUTTONDOWN_API, {
      method: "POST",
      headers: {
        Authorization: `Token ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email_address: email.trim() }),
    });
  } catch {
    return NextResponse.json(
      { error: "Could not reach the newsletter service. Please try again." },
      { status: 502 },
    );
  }

  if (res.status === 201 || res.status === 200) {
    return NextResponse.json({ ok: true });
  }

  // Buttondown returns 400 with a code when the email already exists.
  const detail = (await res.json().catch(() => null)) as
    | { code?: string; detail?: string }
    | null;

  const code = detail?.code ?? "";
  if (res.status === 400 && /exist|already|duplicate/i.test(`${code} ${detail?.detail ?? ""}`)) {
    return NextResponse.json({ ok: true, alreadySubscribed: true });
  }

  console.error("[newsletter] Buttondown error:", res.status, detail);
  return NextResponse.json(
    { error: detail?.detail || "Could not subscribe. Please try again later." },
    { status: 502 },
  );
}
