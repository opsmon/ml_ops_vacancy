import type {
  Dataset,
  Filters,
  Lang,
  Personal,
  Salary,
  Snapshot,
  SnapshotVacancy,
  Technology,
  Vacancy,
} from './types';
import { moscowDay, number, translate } from './i18n';
import policy from '../../../config/scoring.json';

export const defaults: Filters = {
  q: '',
  scope: 'full',
  exclude: '',
  categories: '1,2,3',
  minScore: '',
  maxScore: '',
  tech: '',
  techMode: 'ANY',
  excludeTech: '',
  techCategory: '',
  requirement: '',
  flag: '',
  experience: '',
  years: '',
  seniority: '',
  salaryOnly: false,
  minSalary: '',
  maxSalary: '',
  currency: '',
  tax: '',
  period: '',
  salaryMode: '',
  bound: '',
  salaryChange: '',
  location: '',
  country: '',
  region: '',
  arrangement: '',
  employment: '',
  schedule: '',
  employer: '',
  excludeEmployer: '',
  employerType: '',
  employerActivity: '',
  published: '',
  publishedFrom: '',
  publishedTo: '',
  discoveredFrom: '',
  discoveredTo: '',
  lifecycle: 'active',
  changed: '',
  workflow: 'hideDismissed',
  minFit: '',
  maxMissing: '',
  targetSalary: false,
  desiredArrangement: false,
};
export const emptyPersonal: Personal = {
  version: 1,
  lastVisit: null,
  skills: [],
  levels: {},
  learn: [],
  targetRoles: '',
  seniority: '',
  salary: null,
  currency: 'RUR',
  gross: 'net',
  period: 'MONTHLY',
  salaryMode: 'MONTH',
  arrangement: '',
  location: '',
  tracking: {},
  presets: [],
};
export const tokens = (text: string) =>
  text
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean);
const includes = (text: string, value: string) =>
  text.toLocaleLowerCase().includes(value.toLocaleLowerCase());
export function techNames(v: { technologies: Technology[] }, requirement = '') {
  return [
    ...new Set(
      v.technologies
        .filter((t) => t.section !== 'company' && (!requirement || t.requirement === requirement))
        .map((t) => t.name),
    ),
  ];
}
export function fit(v: Vacancy, profile: Personal) {
  const required = techNames(v, 'required');
  const preferred = techNames(v, 'preferred').filter((x) => !required.includes(x));
  const knows = new Set(profile.skills.map((x) => x.toLowerCase()));
  const missingRequired = required.filter((x) => !knows.has(x.toLowerCase()));
  const missingPreferred = preferred.filter((x) => !knows.has(x.toLowerCase()));
  const total = required.length * 3 + preferred.length;
  return {
    score: total
      ? Math.round((100 * (total - missingRequired.length * 3 - missingPreferred.length)) / total)
      : null,
    required,
    preferred,
    missingRequired,
    missingPreferred,
    matched: [...required, ...preferred].filter((x) => knows.has(x.toLowerCase())),
  };
}
export function comparable(s: Salary | null, profile: Personal) {
  return (
    !!s &&
    s.currency === profile.currency &&
    s.period === profile.period &&
    s.mode === profile.salaryMode &&
    (s.gross === null ? 'unknown' : s.gross ? 'gross' : 'net') === profile.gross
  );
}
export function filterVacancies(
  vacancies: Vacancy[],
  f: Filters,
  profile: Personal,
  now: string,
): Vacancy[] {
  const employerCounts = new Map<string, number>();
  const employerFirst = new Map<string, string>();
  for (const v of vacancies) {
    if (v.category <= 3 && v.status === 'active')
      employerCounts.set(v.employer_id, (employerCounts.get(v.employer_id) || 0) + 1);
    employerFirst.set(
      v.employer_id,
      [employerFirst.get(v.employer_id) || v.first_seen, v.first_seen].sort()[0],
    );
  }
  return vacancies.filter((v) => {
    const text =
      f.scope === 'title'
        ? v.title
        : [v.title, ...Object.values(v.sections), ...v.technologies.map((t) => t.evidence)].join(
            ' ',
          );
    if (
      f.q &&
      !f.q
        .toLowerCase()
        .split(/\s+/)
        .every((word) => includes(text, word))
    )
      return false;
    if (tokens(f.exclude).some((word) => includes(text, word))) return false;
    if (f.categories && !tokens(f.categories).includes(String(v.category))) return false;
    if (
      (f.minScore && v.score < Number(f.minScore)) ||
      (f.maxScore && v.score > Number(f.maxScore))
    )
      return false;
    const names = techNames(v, f.requirement);
    const wanted = tokens(f.tech);
    if (
      wanted.length &&
      !(f.techMode === 'ALL'
        ? wanted.every((x) =>
            names.some((n) => includes(n, x) && n.toLowerCase() === x.toLowerCase()),
          )
        : wanted.some((x) => names.some((n) => n.toLowerCase() === x.toLowerCase())))
    )
      return false;
    if (
      tokens(f.excludeTech).some((x) =>
        techNames(v).some((n) => n.toLowerCase() === x.toLowerCase()),
      )
    )
      return false;
    if (
      f.techCategory &&
      !v.technologies.some(
        (t) =>
          t.category === f.techCategory &&
          t.section !== 'company' &&
          (!f.requirement || t.requirement === f.requirement),
      )
    )
      return false;
    if (
      tokens(f.flag).some((flag) =>
        flag === 'junior'
          ? !(v.seniority === 'junior' || v.experience === 'noExperience')
          : !v.flags[flag],
      )
    )
      return false;
    if (
      (f.experience && v.experience !== f.experience) ||
      (f.seniority && v.seniority !== f.seniority) ||
      (f.years && !v.years.some((x) => includes(x, f.years)))
    )
      return false;
    const salary = v.salary;
    if (f.salaryOnly && !salary) return false;
    if (
      (f.currency && salary?.currency !== f.currency) ||
      (f.period && salary?.period !== f.period)
    )
      return false;
    if (
      f.tax &&
      (!salary || (salary.gross === null ? 'unknown' : salary.gross ? 'gross' : 'net') !== f.tax)
    )
      return false;
    // Numeric salary filters require an explicit currency and payment period to avoid mixing units.
    if (f.salaryMode && salary?.mode !== f.salaryMode) return false;
    if ((f.minSalary || f.maxSalary) && (!f.currency || !f.period || !f.salaryMode || !salary))
      return false;
    if (f.minSalary && (salary?.lower == null || salary.lower < Number(f.minSalary))) return false;
    if (f.maxSalary && (salary?.upper == null || salary.upper > Number(f.maxSalary))) return false;
    if (
      (f.bound === 'lowerOnly' && !(salary?.lower != null && salary.upper == null)) ||
      (f.bound === 'upperOnly' && !(salary?.upper != null && salary.lower == null)) ||
      (f.bound === 'closedRange' && !(salary?.lower != null && salary.upper != null))
    )
      return false;
    if (
      f.salaryChange &&
      !v.events.some((e) => {
        const before = e.before.salary as Salary | undefined,
          after = e.after.salary as Salary | undefined;
        return (
          before?.lower != null &&
          after?.lower != null &&
          before.currency === after.currency &&
          before.gross === after.gross &&
          before.period === after.period &&
          before.mode === after.mode &&
          (f.salaryChange === 'increase' ? after.lower > before.lower : after.lower < before.lower)
        );
      })
    )
      return false;
    if (
      (f.location && !includes(v.location, f.location)) ||
      (f.country && !includes(v.country || '', f.country)) ||
      (f.region && !includes(v.region || '', f.region))
    )
      return false;
    if (
      (f.arrangement && !v.arrangement.includes(f.arrangement)) ||
      (f.employment && (v.employment || 'unknown') !== f.employment) ||
      (f.schedule && (v.schedule || 'unknown') !== f.schedule)
    )
      return false;
    if (
      (f.employer && !tokens(f.employer).some((x) => includes(v.employer, x))) ||
      tokens(f.excludeEmployer).some((x) => includes(v.employer, x))
    )
      return false;
    if (f.employerType && v.flags.agency !== (f.employerType === 'agency')) return false;
    if (f.employerActivity === 'multiple' && (employerCounts.get(v.employer_id) || 0) < 2)
      return false;
    if (
      f.employerActivity === 'newEmployer' &&
      (moscowDay(employerFirst.get(v.employer_id)!) !== moscowDay(now) ||
        !v.events.some((e) => e.kind === 'discovered'))
    )
      return false;
    if (
      f.published &&
      (!v.published_at ||
        Date.parse(now) - Date.parse(v.published_at) > Number(f.published) * 86400000 ||
        Date.parse(v.published_at) > Date.parse(now))
    )
      return false;
    if (
      (f.publishedFrom && (!v.published_at || moscowDay(v.published_at) < f.publishedFrom)) ||
      (f.publishedTo && (!v.published_at || moscowDay(v.published_at) > f.publishedTo))
    )
      return false;
    if (
      (f.discoveredFrom && moscowDay(v.first_seen) < f.discoveredFrom) ||
      (f.discoveredTo && moscowDay(v.first_seen) > f.discoveredTo)
    )
      return false;
    if (
      f.lifecycle === 'notFoundLatest'
        ? v.found_latest !== false
        : f.lifecycle && v.status !== f.lifecycle
    )
      return false;
    if (
      f.changed === 'sinceVisit' &&
      (!profile.lastVisit ||
        !v.events.some((e) => e.kind === 'updated' && e.at > (profile.lastVisit || '')))
    )
      return false;
    if (
      f.changed &&
      f.changed !== 'sinceVisit' &&
      (f.changed === 'repost'
        ? !v.possible_reposts.length
        : f.changed === 'updated'
          ? !v.events.some((e) => e.kind === 'updated')
          : !v.events.some((e) => e.fields.includes(f.changed)))
    )
      return false;
    const track = profile.tracking[v.id] || {};
    if (
      (f.workflow === 'hideViewed' && track.viewed) ||
      (f.workflow === 'hideDismissed' && track.dismissed) ||
      (f.workflow === 'bookmarked' && !track.bookmark)
    )
      return false;
    if (
      ['interested', 'applied', 'interview', 'offer', 'rejected'].includes(f.workflow) &&
      track.status !== f.workflow
    )
      return false;
    const match = fit(v, profile);
    if (
      (f.minFit && (match.score === null || match.score < Number(f.minFit))) ||
      (f.maxMissing &&
        (match.required.length === 0 || match.missingRequired.length > Number(f.maxMissing)))
    )
      return false;
    if (
      f.targetSalary &&
      (!comparable(salary, profile) ||
        profile.salary == null ||
        salary?.lower == null ||
        salary.lower < profile.salary)
    )
      return false;
    if (
      f.desiredArrangement &&
      (!profile.arrangement || !v.arrangement.includes(profile.arrangement))
    )
      return false;
    return true;
  });
}
export function fromURL(url: URL): { filters: Filters; lang: Lang | null; tab: string } {
  const f = { ...defaults };
  for (const key of Object.keys(defaults) as (keyof Filters)[]) {
    const value = url.searchParams.get(key);
    if (value !== null && value.length <= 1000)
      (f as unknown as Record<string, string | boolean>)[key] =
        typeof defaults[key] === 'boolean' ? value === '1' : value;
  }
  return {
    filters: f,
    lang:
      url.searchParams.get('lang') === 'en'
        ? 'en'
        : url.searchParams.get('lang') === 'ru'
          ? 'ru'
          : null,
    tab: url.searchParams.get('tab') || 'vacancies',
  };
}
export function toURL(url: URL, filters: Filters, lang: Lang, tab: string) {
  // Whitelist only public filters, tab and language. Never serialize the profile.
  const out = new URL(url.pathname, url.origin);
  for (const key of Object.keys(defaults) as (keyof Filters)[])
    if (filters[key] !== defaults[key])
      out.searchParams.set(
        key,
        typeof filters[key] === 'boolean' ? (filters[key] ? '1' : '0') : String(filters[key]),
      );
  out.searchParams.set('lang', lang);
  out.searchParams.set('tab', tab);
  return out;
}
export function isDefault(f: Filters) {
  return JSON.stringify(f) === JSON.stringify(defaults);
}
export function salaryText(s: Salary | null, lang: Lang) {
  if (!s) return translate(lang, 'unknown');
  return `${s.lower == null ? '…' : number(s.lower, lang)} – ${s.upper == null ? '…' : number(s.upper, lang)} ${s.currency || ''} · ${translate(lang, s.gross === null ? 'unknown' : s.gross ? 'gross' : 'net')} · ${translate(lang, s.mode)} · ${translate(lang, s.period)}`;
}
export function technologyStats(
  vacancies: { technologies: Technology[]; employer_id: string; category: number }[],
) {
  const result = new Map<
    string,
    {
      name: string;
      category: string;
      count: number;
      percent: number;
      required: number;
      preferred: number;
      employers: Set<string>;
      core: number;
      adjacent: number;
    }
  >();
  for (const v of vacancies)
    for (const name of techNames(v)) {
      const mentions = v.technologies.filter((t) => t.name === name && t.section !== 'company');
      const row = result.get(name) || {
        name,
        category: mentions[0].category,
        count: 0,
        percent: 0,
        required: 0,
        preferred: 0,
        employers: new Set<string>(),
        core: 0,
        adjacent: 0,
      };
      row.count++;
      row.percent = (100 * row.count) / vacancies.length;
      row.required += Number(mentions.some((t) => t.requirement === 'required'));
      row.preferred += Number(mentions.some((t) => t.requirement === 'preferred'));
      row.employers.add(v.employer_id);
      row.core += Number(v.category === 1);
      row.adjacent += Number(v.category === 3);
      result.set(name, row);
    }
  return [...result.values()].sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}
export function pairs(vacancies: { technologies: Technology[] }[]) {
  const counts = new Map<string, number>();
  for (const v of vacancies) {
    const names = techNames(v).sort();
    for (let i = 0; i < names.length; i++)
      for (let j = i + 1; j < names.length; j++) {
        const key = names[i] + ' + ' + names[j];
        counts.set(key, (counts.get(key) || 0) + 1);
      }
  }
  return [...counts]
    .filter(([, n]) => n >= 2)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);
}
export function learning(vacancies: Vacancy[], p: Personal) {
  const result = new Map<string, { name: string; overlap: number; unlock: number }>();
  for (const v of vacancies) {
    const match = fit(v, p);
    for (const name of match.missingRequired) {
      const row = result.get(name) || { name, overlap: 0, unlock: 0 };
      row.overlap++;
      row.unlock += Number(match.missingRequired.length === 1);
      result.set(name, row);
    }
  }
  return [...result.values()].sort((a, b) => b.unlock - a.unlock || b.overlap - a.overlap);
}
export function salarySamples(vacancies: { salary: Salary | null }[]) {
  const groups = new Map<string, number[]>();
  for (const v of vacancies) {
    const s = v.salary;
    if (s?.lower != null && s.upper != null) {
      const key = [
        s.currency,
        s.gross === null ? 'unknown' : s.gross ? 'gross' : 'net',
        s.period,
        s.mode,
      ].join(' · ');
      groups.set(key, [...(groups.get(key) || []), (s.lower + s.upper) / 2]);
    }
  }
  return [...groups].map(([key, values]) => {
    const a = values.sort((x, y) => x - y),
      n = a.length;
    return {
      key,
      n,
      median:
        n >= 5 && !key.includes('unknown')
          ? (a[Math.floor((n - 1) / 2)] + a[Math.floor(n / 2)]) / 2
          : null,
    };
  });
}
function dateShift(day: string, days: number) {
  const date = new Date(day + 'T00:00:00Z');
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}
export function radarHistory(data: Dataset, f: Filters, days: number, now: string) {
  const today = moscowDay(now),
    start = dateShift(today, -days),
    previousStart = dateShift(today, -days * 2);
  const eligibleDays = data.daily.filter(
    (r) =>
      r.complete && r.date >= previousStart && r.date < today && r.config_hash === data.config_hash,
  );
  // Only supported historical cohort fields; free-text/current-lifecycle/personal filters cannot reconstruct history.
  const supported = new Set([
    'categories',
    'experience',
    'location',
    'arrangement',
    'flag',
    'requirement',
  ]);
  const unsupported = Object.keys(defaults).some(
    (k) => !supported.has(k) && f[k as keyof Filters] !== defaults[k as keyof Filters],
  );
  if (unsupported || eligibleDays.length !== days * 2) return null;
  const validDays = new Set(eligibleDays.map((d) => d.date));
  const dailyLast = new Map<string, Snapshot>();
  for (const s of [...data.snapshots].sort((a, b) => a.at.localeCompare(b.at)))
    if (
      validDays.has(s.day) &&
      s.coverage === 'complete' &&
      !s.initial &&
      s.config_hash === data.config_hash
    )
      dailyLast.set(s.day, s);
  if (dailyLast.size !== days * 2) return null;
  function cohort(v: SnapshotVacancy) {
    return (
      (!f.categories || tokens(f.categories).includes(String(v.category))) &&
      (!f.experience || v.experience === f.experience) &&
      (!f.location || includes(v.location, f.location)) &&
      (!f.arrangement || v.arrangement.includes(f.arrangement)) &&
      tokens(f.flag).every((flag) => v.flags[flag])
    );
  }
  function aggregate(snapshots: Snapshot[]) {
    const byId = new Map<string, SnapshotVacancy>();
    for (const s of snapshots)
      for (const v of s.vacancies)
        if (cohort(v))
          byId.set(v.id, {
            ...v,
            technologies: v.technologies.filter(
              (t) => !f.requirement || t.requirement === f.requirement,
            ),
          });
    return [...byId.values()];
  }
  const previous = aggregate([...dailyLast.values()].filter((s) => s.day < start));
  const current = aggregate([...dailyLast.values()].filter((s) => s.day >= start));
  const prevStats = technologyStats(previous),
    currStats = technologyStats(current);
  const names = [...new Set([...prevStats, ...currStats].map((t) => t.name))];
  const p = policy.radar;
  return names.map((name) => {
    const before = prevStats.find((t) => t.name === name),
      after = currStats.find((t) => t.name === name);
    const delta = (after?.percent || 0) - (before?.percent || 0);
    const enough =
      previous.length >= p.minimum_sample &&
      current.length >= p.minimum_sample &&
      Math.max(before?.count || 0, after?.count || 0) >= p.minimum_mentions &&
      Math.max(before?.employers.size || 0, after?.employers.size || 0) >= p.minimum_employers;
    const firstObserved = data.snapshots
      .filter((s) => s.vacancies.some((v) => techNames(v).includes(name)))
      .map((s) => s.day)
      .sort()[0];
    const assessment = !enough
      ? 'insufficient'
      : !before && firstObserved >= start && delta >= p.growth_pp
        ? 'emerging'
        : !before ||
            !after ||
            before.count < p.minimum_mentions ||
            after.count < p.minimum_mentions ||
            before.employers.size < p.minimum_employers ||
            after.employers.size < p.minimum_employers
          ? 'insufficient'
          : delta >= p.growth_pp
            ? 'growing'
            : delta <= -p.growth_pp
              ? 'declining'
              : before.percent >= p.common_prevalence && after.percent >= p.common_prevalence
                ? 'common'
                : Math.abs(delta) <= p.stable_pp
                  ? 'stable'
                  : 'insufficient';
    const history = [...dailyLast.values()]
      .sort((a, b) => a.day.localeCompare(b.day))
      .map((s) => {
        const vs = s.vacancies.filter(cohort);
        return {
          day: s.day,
          count: vs.filter((v) => techNames(v, f.requirement).includes(name)).length,
          n: vs.length,
        };
      });
    return {
      name,
      delta,
      before: before?.count || 0,
      after: after?.count || 0,
      previousN: previous.length,
      currentN: current.length,
      assessment,
      history,
    };
  });
}
export function csvCell(value: unknown) {
  const text = String(value ?? '');
  return '"' + (/^[\s]*[=+\-@\t\r\n]/.test(text) ? "'" : '') + text.replaceAll('"', '""') + '"';
}
export function csv(vacancies: Vacancy[]) {
  return (
    '\uFEFF' +
    [
      [
        'id',
        'title',
        'employer',
        'location',
        'salary_from',
        'salary_to',
        'currency',
        'gross',
        'period',
        'url',
      ],
      ...vacancies.map((v) => [
        v.id,
        v.title,
        v.employer,
        v.location,
        v.salary?.lower,
        v.salary?.upper,
        v.salary?.currency,
        v.salary?.gross,
        v.salary?.period,
        v.url,
      ]),
    ]
      .map((row) => row.map(csvCell).join(','))
      .join('\r\n')
  );
}
export function validateDataset(value: unknown, mode: string): Dataset {
  const data = value as Dataset;
  if (
    !data ||
    data.schema_version !== 1 ||
    data.mode !== mode ||
    !Array.isArray(data.vacancies) ||
    !Array.isArray(data.daily) ||
    !data.forecast ||
    !Array.isArray(data.snapshots) ||
    !data.taxonomy
  )
    throw new Error('invalid_dataset');
  if (new Set(data.vacancies.map((v) => v.id)).size !== data.vacancies.length)
    throw new Error('duplicate_id');
  for (const v of data.vacancies)
    if (
      !v.summary?.ru ||
      !v.summary?.en ||
      !Array.isArray(v.technologies) ||
      !v.events ||
      v.score < 0 ||
      v.score > 100
    )
      throw new Error('invalid_vacancy');
  return data;
}
