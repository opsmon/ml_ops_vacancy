import { describe, expect, test } from 'vitest';
import demo from '../../public/data/demo.json';
import {
  csvCell,
  defaults,
  emptyPersonal,
  filterVacancies,
  fit,
  fromURL,
  isDefault,
  learning,
  radarHistory,
  salarySamples,
  technologyStats,
  toURL,
  validateDataset,
} from './market';
import { date, dictionaries, moscowDay, translate } from './i18n';
import { loadPersonal, parsePersonal, savePersonal, STORAGE_KEY } from './storage';
import type { Dataset, Filters, Personal, Vacancy } from './types';
const data = validateDataset(demo, 'demo');
const profile = (): Personal => structuredClone(emptyPersonal);
const filter = (patch: Partial<Filters> = {}) =>
  filterVacancies(data.vacancies, { ...defaults, ...patch }, profile(), data.generated_at);

describe('Filters and filtered statistics', () => {
  test('default categories exclude generic company AI DevOps and archive', () => {
    expect(filter().some((v) => v.id === 'demo-8')).toBe(false);
    expect(filter().some((v) => v.status === 'archived')).toBe(false);
    expect(filter().some((v) => v.id === 'demo-9')).toBe(true);
  });
  test('ANY and ALL use unique vacancy IDs', () => {
    const any = filter({ tech: 'MLflow,Kubeflow', techMode: 'ANY' }),
      all = filter({ tech: 'MLflow,Kubeflow', techMode: 'ALL' });
    expect(any.length).toBeGreaterThan(all.length);
    expect(
      all.every(
        (v) =>
          v.technologies.some((t) => t.name === 'MLflow') &&
          v.technologies.some((t) => t.name === 'Kubeflow'),
      ),
    ).toBe(true);
  });
  test('excluded technologies and required/preferred distinguish evidence', () => {
    expect(
      filter({ excludeTech: 'MLflow' }).every(
        (v) => !v.technologies.some((t) => t.name === 'MLflow'),
      ),
    ).toBe(true);
    expect(filter({ tech: 'ClearML', requirement: 'preferred' }).length).toBeGreaterThan(0);
    expect(filter({ tech: 'ClearML', requirement: 'required' }).map((v) => v.id)).not.toEqual(
      filter({ tech: 'ClearML', requirement: 'preferred' }).map((v) => v.id),
    );
  });
  test('right dashboard denominator and per-vacancy counts match filtered subset', () => {
    const vs = filter({ tech: 'Kubernetes' }),
      stats = technologyStats(vs);
    const kubernetes = stats.find((t) => t.name === 'Kubernetes')!;
    expect(kubernetes.count).toBe(vs.length);
    expect(kubernetes.percent).toBe(100);
    expect(stats.every((t) => t.count <= vs.length)).toBe(true);
  });
  test('salary numeric filters require explicit comparable units', () => {
    expect(filter({ minSalary: '100000' })).toHaveLength(0);
    expect(
      filter({ minSalary: '100000', currency: 'RUR', period: 'MONTHLY', salaryMode: 'MONTH' })
        .length,
    ).toBeGreaterThan(0);
    expect(salarySamples(filter()).every((g) => g.n >= 5 || g.median === null)).toBe(true);
  });
  test('unknown conditions are neither false nor true evidence', () => {
    const vs = filter({ flag: 'oncall' });
    expect(vs.every((v) => v.flags.oncall === true)).toBe(true);
    expect(filter({ employerType: 'direct' })).toHaveLength(0);
  });
  test('title versus full text and date windows', () => {
    expect(filter({ q: 'ClearML', scope: 'title' })).toHaveLength(0);
    expect(filter({ q: 'ClearML' }).length).toBeGreaterThan(0);
    expect(filter({ publishedFrom: '2026-10-23' })).toHaveLength(0);
  });
});
describe('Profiles, privacy and safety', () => {
  test('required skill weights dominate preferred skills', () => {
    const v = data.vacancies[0],
      p = profile();
    p.skills = ['Linux', 'Python', 'Kubernetes', 'MLflow'];
    const score = fit(v, p);
    expect(score.missingRequired).toHaveLength(0);
    expect(score.score).toBeGreaterThan(50);
    p.skills = ['ClearML', 'Terraform'];
    expect(fit(v, p).score).toBeLessThan(score.score!);
    expect(fit({ ...v, technologies: [] } as Vacancy, p).score).toBeNull();
  });
  test('learning priorities count additional covered required sets', () => {
    const v = data.vacancies[0],
      p = profile();
    p.skills = fit(v, p).required.filter((x) => x !== 'MLflow');
    expect(learning([v], p).find((x) => x.name === 'MLflow')?.unlock).toBe(1);
  });
  test('personal data survives separate browser loads', () => {
    const map = new Map<string, string>(),
      storage = {
        getItem: (k: string) => map.get(k) || null,
        setItem: (k: string, v: string) => {
          map.set(k, v);
        },
      };
    const p = profile();
    p.skills = ['Linux'];
    p.tracking['demo-1'] = { bookmark: true, note: 'private note', status: 'interview' };
    savePersonal(storage, p);
    expect(loadPersonal(storage)).toEqual(p);
    expect(map.has(STORAGE_KEY)).toBe(true);
  });
  test('backup imports validate shape and reject corrupted fields', () => {
    expect(parsePersonal(JSON.stringify(profile())).skills).toEqual([]);
    expect(() => parsePersonal('{"version":2}')).toThrow();
    expect(() => parsePersonal(JSON.stringify({ ...profile(), skills: [{}] }))).toThrow();
    expect(() => parsePersonal(JSON.stringify({ ...profile(), salary: 'bad' }))).toThrow();
  });
  test('share URLs round trip filters and language without notes or profile', () => {
    const f = { ...defaults, q: 'GPU + ML', tech: 'Kubernetes,MLflow', salaryOnly: true };
    const url = toURL(
      new URL('https://owner.github.io/repo/?note=private&token=secret'),
      f,
      'en',
      'radar',
    );
    expect(url.pathname).toBe('/repo/');
    expect(fromURL(url).filters).toEqual(f);
    expect(fromURL(url).lang).toBe('en');
    expect(url.href).not.toMatch(/private|secret|note|skills/);
    expect(isDefault(fromURL(new URL('https://x/')).filters)).toBe(true);
  });
  test.each(['=HYPERLINK("x")', '+cmd', '-1+2', '@SUM(A1)', '  =bad', '\t=bad'])(
    'CSV escapes formula %s',
    (value) => expect(csvCell(value).startsWith('"\'')).toBe(true),
  );
  test('mode mismatch cannot silently load demo as real', () =>
    expect(() => validateDataset(demo, 'real')).toThrow());
});
describe('Localization and historical evidence', () => {
  test('translation key parity and fallback', () => {
    expect(Object.keys(dictionaries.en).sort()).toEqual(Object.keys(dictionaries.ru).sort());
    expect(translate('ru', 'missing_key')).toBe('missing_key');
    expect(translate('en', 'techHeading')).toBe('Technologies in vacancies');
    expect(translate('ru', 'techHeading')).toBe('Технологии в вакансиях');
  });
  test('Moscow dates respect UTC midnight offset and localized output', () => {
    expect(moscowDay('2026-10-21T21:00:00Z')).toBe('2026-10-22');
    expect(date('2026-10-22T12:00:00Z', 'ru')).not.toEqual(date('2026-10-22T12:00:00Z', 'en'));
  });
  test('stack assessment is unavailable without complete comparable history', () => {
    expect(radarHistory(data, defaults, 7, data.generated_at)).toBeNull();
  });
  test('radar uses historical cohort attributes, not current attributes', () => {
    const p = structuredClone(data) as Dataset;
    p.daily = [];
    p.snapshots = [];
    for (let i = 0; i < 14; i++) {
      const date = new Date('2026-10-08T12:00:00Z');
      date.setUTCDate(date.getUTCDate() + i);
      const day = date.toISOString().slice(0, 10);
      p.daily.push({
        date: day,
        complete: true,
        arrivals: 2,
        active: 30,
        config_hash: p.config_hash,
      });
      const vacancies = Array.from({ length: 30 }, (_, id) => ({
        id: String(id),
        employer_id: String(id % 5),
        category: 1,
        experience: 'between3And6',
        location: 'Москва',
        arrangement: ['REMOTE'],
        flags: {},
        salary: null,
        detail: true,
        technologies:
          id < (i < 7 ? 10 : 20)
            ? [p.vacancies[0].technologies.find((t) => t.name === 'Kubernetes')!]
            : [],
      }));
      p.snapshots.push({
        id: day,
        at: date.toISOString(),
        day,
        config_hash: p.config_hash,
        initial: false,
        coverage: 'complete',
        vacancies,
        active: 30,
      });
    }
    const row = radarHistory(p, defaults, 7, p.generated_at)?.find((r) => r.name === 'Kubernetes');
    expect(row?.before).toBe(10);
    expect(row?.after).toBe(20);
    expect(row?.assessment).toBe('growing');
    expect(radarHistory(p, { ...defaults, q: 'new current text' }, 7, p.generated_at)).toBeNull();
    p.daily[0].complete = false;
    expect(radarHistory(p, defaults, 7, p.generated_at)).toBeNull();
  });
});
