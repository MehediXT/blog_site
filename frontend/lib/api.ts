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

type FatwaResponse = { results: Fatwa[]; count: number };

const apiOrigin =
  process.env.API_ORIGIN ||
  process.env.NEXT_PUBLIC_API_ORIGIN ||
  'http://127.0.0.1:8000';

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${apiOrigin}/api/v1${path}`, {
      cache: 'no-store',
    });

    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export function isLocale(value: string): value is Locale {
  return value === 'bn' || value === 'en';
}

export async function getFatwas(query = '', category = '') {
  const params = new URLSearchParams({ page_size: '6' });
  if (query) params.set('q', query);
  if (category) params.set('category', category);
  return getJson<FatwaResponse>(`/fatwas/?${params.toString()}`);
}

export async function getFatwa(id: string) {
  return getJson<{ fatwa: Fatwa }>(`/fatwas/${id}/`);
}

export async function getCategories() {
  return getJson<{ results: Category[] }>('/categories/');
}
