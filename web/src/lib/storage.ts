import type { Personal } from './types';
import { defaults, emptyPersonal } from './market';
export const STORAGE_KEY = 'mlpops.personal.v1';
export function parsePersonal(value: string): Personal {
  if (value.length > 2_000_000) throw new Error('oversized');
  const p = JSON.parse(value);
  if (
    p.version !== 1 ||
    !Array.isArray(p.skills) ||
    !p.skills.every((v: unknown) => typeof v === 'string') ||
    !Array.isArray(p.learn) ||
    !p.learn.every((v: unknown) => typeof v === 'string') ||
    typeof p.tracking !== 'object' ||
    !p.tracking ||
    Array.isArray(p.tracking) ||
    !Array.isArray(p.presets)
  )
    throw new Error('invalid_backup');
  const result: Personal = { ...structuredClone(emptyPersonal), ...p };
  for (const t of Object.values(result.tracking))
    if (!t || typeof t !== 'object' || (t.note !== undefined && typeof t.note !== 'string'))
      throw new Error('invalid_tracking');
  for (const preset of result.presets) {
    if (typeof preset.name !== 'string' || !preset.filters) throw new Error('invalid_preset');
    preset.filters = {
      ...defaults,
      ...Object.fromEntries(
        Object.entries(preset.filters).filter(
          ([k, v]) => k in defaults && typeof v === typeof defaults[k as keyof typeof defaults],
        ),
      ),
    };
  }
  if (
    !result.levels ||
    typeof result.levels !== 'object' ||
    (result.salary !== null &&
      (typeof result.salary !== 'number' || !Number.isFinite(result.salary)))
  )
    throw new Error('invalid_profile');
  for (const key of [
    'targetRoles',
    'seniority',
    'currency',
    'gross',
    'period',
    'salaryMode',
    'arrangement',
    'location',
  ] as const)
    if (typeof result[key] !== 'string') throw new Error('invalid_profile');
  return result;
}
export function loadPersonal(storage: Pick<Storage, 'getItem'>): Personal {
  const raw = storage.getItem(STORAGE_KEY);
  return raw ? parsePersonal(raw) : structuredClone(emptyPersonal);
}
export function savePersonal(storage: Pick<Storage, 'setItem'>, profile: Personal) {
  storage.setItem(STORAGE_KEY, JSON.stringify(profile));
}
export function download(name: string, content: string, type = 'application/json') {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
