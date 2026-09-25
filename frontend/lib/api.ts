export type Locale = 'bn' | 'en';

export type Fatwa = {
  id: number;
  public_id: string | null;
  slug: string;
  title: string;
  question: string;
  answer: string;
  language: string;
  references: string[] | string;
  methodology: string | null;
  scholar: { id: number; name: string };
  published_at: string | null;
};

export type Category = {
  slug: string;
  name_en: string;
  name_bn: string;
};

export type Methodology = {
  id?: number;
  slug: string;
  name_en: string;
  name_bn: string;
  description: string;
};

export type User = {
  id: number;
  username: string;
  email: string;
  email_verified?: boolean;
  preferred_language?: Locale;
  display_name?: string;
  scholar?: boolean;
  moderator?: boolean;
};

export type Scholar = {
  id: number;
  name: string;
  institution: string;
  specialties: string[] | string;
  languages: string[] | string;
  biography?: string;
  qualifications?: string[] | string;
};

export type ScholarApplication = {
  institution: string;
  biography: string;
  public_bio: string;
  qualifications: string;
  specialties: string[];
  languages: Locale[];
  verification_status: 'pending' | 'approved' | 'rejected';
  is_suspended: boolean;
  can_author: boolean;
  created_at: string;
  updated_at: string;
};

export type ModerationScholar = {
  user_id: number;
  username: string;
  email: string;
  display_name: string;
  institution: string;
  qualifications: string;
  specialties: string[];
  languages: Locale[];
  biography: string;
  public_bio: string;
  verification_status: 'pending' | 'approved' | 'rejected';
  verification_note: string;
  verified_at: string | null;
  is_suspended: boolean;
  created_at: string;
  updated_at: string;
};

export type ModerationQuestion = {
  id: number;
  status: string;
  language: string;
  original_title: string;
  original_body: string;
  category_name: string;
  madhhab_preference: string;
  created_at: string;
  submitted_at: string | null;
  asker_name: string;
  assigned_scholar_id: number | null;
  assigned_reviewer_id: number | null;
};

export type Notification = {
  id: number;
  kind: string;
  title: string;
  body: string;
  target_url: string;
  read: boolean;
  created_at: string;
};

export type Question = {
  id: number;
  status: string;
  language: string;
  category: string | null;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  title?: string;
  body?: string;
  original_title: string;
  original_body: string;
  public_title: string;
  public_body: string;
  madhhab_preference: string;
  assigned_scholar_id: number | null;
  assigned_reviewer_id: number | null;
  clarifications: Array<{ id: number; author_id: number; body: string; created_at: string }>;
};

export type ReviewItem = {
  id: number;
  question: Question;
  body: string;
  author_id: number;
  revision_number: number;
  submitted_at: string;
};

type AuthResponse = {
  access: string;
  refresh: string;
  user: User;
  email_verified?: boolean;
};

export type ApiFailure = Error & { code?: string; fields?: Record<string, unknown> };

type FatwaResponse = { results: Fatwa[]; count: number };

const apiOrigin = (
  process.env.API_ORIGIN ||
  process.env.NEXT_PUBLIC_API_ORIGIN ||
  'http://127.0.0.1:8000'
).replace(/\/$/, '');

function apiUrl(path: string) {
  // Browser requests stay same-origin and are routed by Caddy/Next.js.
  // Server components use the Docker-internal Django service URL.
  return typeof window === 'undefined'
    ? `${apiOrigin}/api/v1${path}`
    : `/api/v1${path}`;
}

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(apiUrl(path), {
      cache: 'no-store',
    });

    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function authHeaders(token: string | null, headers?: HeadersInit) {
  const nextHeaders = new Headers(headers);
  nextHeaders.set('Content-Type', 'application/json');
  if (token) nextHeaders.set('Authorization', `Bearer ${token}`);
  return nextHeaders;
}

function storedAccessToken() {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem('universe_access');
}

function storedRefreshToken() {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem('universe_refresh');
}

export function saveAuth(response: AuthResponse) {
  window.localStorage.setItem('universe_access', response.access);
  window.localStorage.setItem('universe_refresh', response.refresh);
  window.localStorage.setItem('universe_user', JSON.stringify(response.user));
  return response;
}

export function clearAuth() {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem('universe_access');
  window.localStorage.removeItem('universe_refresh');
  window.localStorage.removeItem('universe_user');
}

export function savedUser(): User | null {
  if (typeof window === 'undefined') return null;
  const value = window.localStorage.getItem('universe_user');
  if (!value) return null;
  try {
    return JSON.parse(value) as User;
  } catch {
    return null;
  }
}

async function refreshAccessToken() {
  const refresh = storedRefreshToken();
  if (!refresh) return null;
  const response = await fetch(apiUrl('/auth/token/refresh/'), {
    method: 'POST',
    headers: authHeaders(null),
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) {
    clearAuth();
    return null;
  }
  const data = (await response.json()) as { access: string; refresh?: string };
  window.localStorage.setItem('universe_access', data.access);
  if (data.refresh) window.localStorage.setItem('universe_refresh', data.refresh);
  return data.access;
}

async function clientRequest<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const token = storedAccessToken();
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: authHeaders(token, init.headers),
  });

  if (response.status === 401 && retry && storedRefreshToken()) {
    const access = await refreshAccessToken();
    if (access) return clientRequest<T>(path, init, false);
  }

  const rawBody = await response.text();
  let body: Record<string, unknown> = {};
  try {
    body = rawBody ? JSON.parse(rawBody) as Record<string, unknown> : {};
  } catch {
    // Django or a proxy may return an HTML error page. Keep the UI readable.
  }
  if (!response.ok) {
    const firstFieldError = Object.values(body).find((value) => Array.isArray(value) && value.length);
    const firstFieldMessage = Array.isArray(firstFieldError) && typeof firstFieldError[0] === 'string'
      ? firstFieldError[0]
      : null;
    const failure = new Error(
      typeof body.detail === 'string'
        ? body.detail
        : firstFieldMessage
          ? firstFieldMessage
          : `Request failed (${response.status}). Please try again.`,
    ) as ApiFailure;
    failure.code = typeof body.code === 'string' ? body.code : undefined;
    failure.fields = body;
    throw failure;
  }
  return body as T;
}

export async function login(identifier: string, password: string) {
  const response = await clientRequest<AuthResponse>('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ username: identifier, password }),
  });
  return saveAuth(response);
}

export async function register(username: string, email: string, password: string) {
  const response = await clientRequest<AuthResponse>('/auth/register/', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  });
  return saveAuth(response);
}

export async function getCurrentUser() {
  const response = await clientRequest<User>('/me/');
  window.localStorage.setItem('universe_user', JSON.stringify(response));
  return response;
}

export async function getScholarApplication() {
  return clientRequest<{ scholar_profile: ScholarApplication | null }>('/me/scholar-profile/');
}

export async function submitScholarApplication(payload: {
  institution: string;
  biography: string;
  public_bio: string;
  qualifications: string;
  specialties: string[];
  languages: Locale[];
}) {
  return clientRequest<{ scholar_profile: ScholarApplication }>('/me/scholar-profile/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateCurrentUser(payload: { display_name?: string; preferred_language?: Locale }) {
  const response = await clientRequest<User>('/me/', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  window.localStorage.setItem('universe_user', JSON.stringify(response));
  return response;
}

export async function getMyQuestions() {
  const response = await clientRequest<Question[] | { results: Question[] }>('/me/questions/');
  return Array.isArray(response) ? response : response.results;
}

export async function createQuestion(payload: {
  title: string;
  body: string;
  language: string;
  category: string | null;
  is_public: boolean;
}) {
  const response = await clientRequest<{ question: Question }>('/me/questions/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return response.question;
}

export async function getScholarAssignments() {
  return clientRequest<{ results: Question[] }>('/scholar/assignments/');
}

export async function getMethodologies() {
  const response = await getJson<{ results: Methodology[] } | Methodology[]>('/methodologies/');
  return response ? (Array.isArray(response) ? response : response.results) : [];
}

export async function getReviewQueue() {
  return clientRequest<{ results: ReviewItem[] }>('/reviews/');
}

export async function getScholars() {
  return getJson<{ results: Scholar[] }>('/scholars/');
}

export async function getModerationScholars() {
  return clientRequest<{ results: ModerationScholar[] }>('/moderation/scholars/');
}

export async function moderateScholar(userId: number, action: 'approve' | 'reject' | 'suspend' | 'unsuspend', note = '') {
  return clientRequest<{ scholar: ModerationScholar }>(`/moderation/scholars/${userId}/`, {
    method: 'PATCH',
    body: JSON.stringify({ action, note }),
  });
}

export async function getModerationQuestions() {
  return clientRequest<{ results: ModerationQuestion[] }>('/moderation/questions/');
}

export async function assignModerationQuestion(questionId: number, scholarId: number, reviewerId: number) {
  return clientRequest<{ question: Question }>(`/moderation/questions/${questionId}/assign/`, {
    method: 'POST',
    body: JSON.stringify({ scholar_id: scholarId, reviewer_id: reviewerId }),
  });
}

export async function getJsonScholar(id: string) {
  return getJson<{ scholar: Scholar }>(`/scholars/${id}/`);
}

export async function getBookmarks() {
  return clientRequest<{ results: Array<{ id: number; fatwa: Fatwa; created_at: string }> }>('/me/bookmarks/');
}

export async function getNotifications() {
  return clientRequest<{ results: Notification[] }>('/me/notifications/');
}

export async function addBookmark(publicationId: number) {
  return clientRequest<{ bookmarked: boolean; created: boolean }>('/me/bookmarks/', {
    method: 'POST',
    body: JSON.stringify({ publication_id: publicationId }),
  });
}

export async function removeBookmark(publicationId: number) {
  return clientRequest<void>('/me/bookmarks/', {
    method: 'DELETE',
    body: JSON.stringify({ publication_id: publicationId }),
  });
}

export async function reportFatwa(publicationId: number, reason: string) {
  return clientRequest<{ report_id: number }>(`/fatwas/${publicationId}/report/`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function saveAnswer(questionId: number, payload: {
  body: string;
  language: string;
  references: string[];
  methodology_id?: number | null;
  action: 'save' | 'submit_for_review';
}) {
  return clientRequest<{ revision_id: number; status: string }>(`/scholar/questions/${questionId}/answer/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function reviewRevision(revisionId: number, action: 'approve' | 'request-changes' | 'reject', feedback = '') {
  return clientRequest<{ decision: string; revision_id: number }>(`/reviews/${revisionId}/${action}/`, {
    method: 'POST',
    body: JSON.stringify({ feedback }),
  });
}

export async function submitQuestion(id: number, payload: {
  is_public: boolean;
  public_title?: string;
  public_body?: string;
}) {
  const response = await clientRequest<{ question: Question }>(`/me/questions/${id}/`, {
    method: 'POST',
    body: JSON.stringify({ action: 'submit', ...payload }),
  });
  return response.question;
}

export async function clarifyQuestion(id: number, body: string) {
  const response = await clientRequest<{ question: Question }>(`/me/questions/${id}/`, {
    method: 'POST',
    body: JSON.stringify({ action: 'clarify', body }),
  });
  return response.question;
}

export async function withdrawQuestion(id: number) {
  const response = await clientRequest<{ question: Question }>(`/me/questions/${id}/`, {
    method: 'POST',
    body: JSON.stringify({ action: 'withdraw' }),
  });
  return response.question;
}

export async function logout() {
  const refresh = storedRefreshToken();
  if (refresh) {
    await fetch(apiUrl('/auth/logout/'), {
      method: 'POST',
      headers: authHeaders(storedAccessToken()),
      body: JSON.stringify({ refresh }),
    }).catch(() => undefined);
  }
  clearAuth();
}

export function isLocale(value: string): value is Locale {
  return value === 'bn' || value === 'en';
}

export async function getFatwas(
  locale: Locale,
  query = '',
  category = '',
  methodology = '',
  scholar = '',
  pageSize = 6,
  page = 1,
) {
  const params = new URLSearchParams({ page_size: String(pageSize), page: String(page), language: locale });
  if (query) params.set('q', query);
  if (category) params.set('category', category);
  if (methodology) params.set('methodology', methodology);
  if (scholar) params.set('scholar', scholar);
  return getJson<FatwaResponse>(`/fatwas/?${params.toString()}`);
}

export async function getFatwa(locale: Locale, id: string) {
  return getJson<{ fatwa: Fatwa }>(`/fatwas/${id}/?language=${locale}`);
}

export async function getCategories() {
  return getJson<{ results: Category[] }>('/categories/');
}
