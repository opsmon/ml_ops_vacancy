export type Lang = 'ru' | 'en';
export type Requirement = 'required' | 'preferred' | 'mentioned' | 'unclear';
export interface Technology {
  name: string;
  category: string;
  matched: string;
  section: string;
  requirement: Requirement;
  evidence: string;
}
export interface Salary {
  lower: number | null;
  upper: number | null;
  currency: string | null;
  gross: boolean | null;
  period: string;
  mode: string;
}
export interface Change {
  at: string;
  kind: string;
  fields: string[];
  before: Record<string, unknown>;
  after: Record<string, unknown>;
}
export interface Vacancy {
  id: string;
  url: string;
  title: string;
  employer_id: string;
  employer: string;
  location: string;
  country: string | null;
  region: string | null;
  arrangement: string[];
  employment: string | null;
  schedule: string | null;
  published_at: string | null;
  created_at: string | null;
  first_seen: string;
  last_seen: string;
  detail_refreshed: string | null;
  experience: string;
  seniority: string;
  seniority_uncertain: boolean;
  years: string[];
  salary: Salary | null;
  category: number;
  score: number;
  reasons: string[];
  negative_signals: string[];
  technologies: Technology[];
  sections: Record<string, string>;
  summary: Record<Lang, string>;
  uncertainties: string[];
  flags: Record<string, boolean | string | null>;
  queries: string[];
  content_hash: string;
  description_hash: string;
  status: string;
  status_evidence: string;
  found_latest: boolean | null;
  possible_reposts: string[];
  events: Change[];
  classifier_version: string;
  extractor_version: string;
}
export interface SnapshotVacancy {
  id: string;
  employer_id: string;
  category: number;
  experience: string;
  location: string;
  arrangement: string[];
  flags: Vacancy['flags'];
  salary: Salary | null;
  technologies: Technology[];
  detail: boolean;
}
export interface Snapshot {
  id: string;
  at: string;
  day: string;
  config_hash: string;
  initial: boolean;
  coverage: string;
  vacancies: SnapshotVacancy[];
  active: number;
}
export interface Daily {
  date: string;
  complete: boolean;
  arrivals: number | null;
  active: number | null;
  published?: number | null;
  updated?: number | null;
  archived?: number | null;
  new_employers?: number | null;
  initial_inventory?: boolean;
  partial_today?: boolean;
  config_hash?: string;
}
export interface Dataset {
  schema_version: 1;
  mode: 'demo' | 'real';
  generated_at: string;
  last_success: string | null;
  coverage: string;
  config_hash: string;
  vacancies: Vacancy[];
  daily: Daily[];
  snapshots: Snapshot[];
  forecast: {
    status: string;
    observations: number;
    minimum: number;
    method: string | null;
    predictions: { date: string; value: number; lower: number; upper: number }[];
    evaluation: Record<string, { mae: number; wape: number | null; n: number }>;
    interval?: { nominal: number; coverage: number | null; validation_n: number };
  };
  runs: {
    id: string;
    finished_at: string;
    status: string;
    initial_inventory: boolean;
    requests: number;
    unique_ids: number;
    truncations: unknown[];
    failures: string[];
  }[];
  taxonomy: { name: string; category: string; aliases: string[] }[];
  dictionaries: Record<string, { id: string; name: string }[]>;
}
export interface Tracking {
  bookmark?: boolean;
  viewed?: boolean;
  dismissed?: boolean;
  status?: string;
  note?: string;
}
export interface Personal {
  version: 1;
  lastVisit?: string | null;
  skills: string[];
  levels: Record<string, string>;
  learn: string[];
  targetRoles: string;
  seniority: string;
  salary: number | null;
  currency: string;
  gross: string;
  period: string;
  salaryMode: string;
  arrangement: string;
  location: string;
  tracking: Record<string, Tracking>;
  presets: { name: string; filters: Filters }[];
}
export interface Filters {
  q: string;
  scope: string;
  exclude: string;
  categories: string;
  minScore: string;
  maxScore: string;
  tech: string;
  techMode: string;
  excludeTech: string;
  techCategory: string;
  requirement: string;
  flag: string;
  experience: string;
  years: string;
  seniority: string;
  salaryOnly: boolean;
  minSalary: string;
  maxSalary: string;
  currency: string;
  tax: string;
  period: string;
  salaryMode: string;
  bound: string;
  salaryChange: string;
  location: string;
  country: string;
  region: string;
  arrangement: string;
  employment: string;
  schedule: string;
  employer: string;
  excludeEmployer: string;
  employerType: string;
  employerActivity: string;
  published: string;
  publishedFrom: string;
  publishedTo: string;
  discoveredFrom: string;
  discoveredTo: string;
  lifecycle: string;
  changed: string;
  workflow: string;
  minFit: string;
  maxMissing: string;
  targetSalary: boolean;
  desiredArrangement: boolean;
}
