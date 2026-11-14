// The session cookie is HttpOnly and lives on the API host, so the web app cannot see it.
// This flag only says that this browser made a family before: a hint, never proof. It saves
// an anonymous visitor the API call, and the API still decides.
const KEY = "jumbaq.has_family";

export function hasFamilyHint(): boolean {
  try {
    return window.localStorage.getItem(KEY) === "1";
  } catch {
    return false;
  }
}

export function setFamilyHint(present: boolean): void {
  try {
    if (present) window.localStorage.setItem(KEY, "1");
    else window.localStorage.removeItem(KEY);
  } catch {
    // Private mode or blocked storage: the hint is only a convenience.
  }
}
