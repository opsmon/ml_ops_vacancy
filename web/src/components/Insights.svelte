<script lang="ts">
  import type { Vacancy, Personal, Lang, Dataset, Filters } from '../lib/types';
  import { number, translate as tr } from '../lib/i18n';
  import { learning, pairs, radarHistory, technologyStats } from '../lib/market';
  let {
    vacancies,
    profile,
    lang,
    filtered,
    applyTechnology,
    openRadar,
    data,
    filters,
  }: {
    data: Dataset;
    filters: Filters;
    vacancies: Vacancy[];
    profile: Personal;
    lang: Lang;
    filtered: boolean;
    applyTechnology: (name: string) => void;
    openRadar: () => void;
  } = $props();
  const t = (key: string) => tr(lang, key);
  let history = $derived(radarHistory(data, filters, 7, data.generated_at));
  let stats = $derived(technologyStats(vacancies));
  let skillGaps = $derived(learning(vacancies, profile));
  let employers = $derived(
    [...new Set(vacancies.map((v) => v.employer))]
      .map((name) => ({ name, count: vacancies.filter((v) => v.employer === name).length }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5),
  );
  function distribution(field: 'experience' | 'arrangement') {
    const count = new Map<string, number>();
    for (const v of vacancies)
      for (const value of field === 'arrangement' ? v.arrangement : [v.experience])
        count.set(value, (count.get(value) || 0) + 1);
    return [...count].sort((a, b) => b[1] - a[1]);
  }
  function label(value: string) {
    return t(
      ({ REMOTE: 'remote', HYBRID: 'hybrid', ON_SITE: 'onsite' } as Record<string, string>)[
        value
      ] || value,
    );
  }
</script>

<div class="panel-heading"><h2>{t('techHeading')}</h2></div>
<p class="context">{t(filtered ? 'scopeFiltered' : 'scopeGlobal')}</p>
<p class="small">
  {t('denominator')}: <strong data-testid="insights-denominator">{vacancies.length}</strong> · {t(
    'detailsCoverage',
  )}: {vacancies.filter((v) => !v.uncertainties.includes('details_missing'))
    .length}/{vacancies.length}
</p>
<div class="bars">
  {#each stats.slice(0, 12) as row (row.name)}
    <button
      class="bar-row"
      onclick={() => applyTechnology(row.name)}
      title={`${t('requiredPreferred')}: ${row.required} / ${row.preferred}`}
    >
      <span class="bar-label"
        >{row.name}{#if profile.skills.includes(row.name)}
          <span class="muted" aria-label={t('mine')}>✓</span>{/if}</span
      >
      <span class="bar-value"
        >{row.count} <span class="muted">{number(row.percent, lang)}%</span></span
      >
      <span class="small"
        >{t(history?.find((x) => x.name === row.name)?.assessment || 'insufficient')}</span
      >
      <span class="bar-track"><span style:width={`${row.percent}%`}></span></span>
    </button>
  {/each}
</div>
<button class="wide" onclick={openRadar}>{t('radar')} →</button>
<p class="small">{t('days7')} · {t('assessment')}</p>
<section class="aside-section">
  <h3>{t('requiredPreferred')}</h3>
  {#each stats.slice(0, 5) as row (row.name)}<div class="stat-line">
      <span>{row.name}</span><span>{row.required} / {row.preferred}</span>
    </div>{/each}
</section>
<section class="aside-section">
  <h3>{t('categoryDistribution')}</h3>
  {#each [...new Set(stats.map((r) => r.category))] as cat (cat)}<div class="stat-line">
      <span>{t(cat === 'lifecycle' ? 'mlLifecycle' : cat)}</span><span
        >{vacancies.filter((v) =>
          v.technologies.some((x) => x.category === cat && x.section !== 'company'),
        ).length}</span
      >
    </div>{/each}
</section>
{#each ['experience', 'arrangement'] as field (field)}<section class="aside-section">
    <h3>{t(field === 'experience' ? 'experienceDistribution' : 'arrangementDistribution')}</h3>
    {#each distribution(field as 'experience' | 'arrangement') as [value, count] (value)}<div
        class="stat-line"
      >
        <span>{label(value)}</span><span>{count}</span>
      </div>{/each}
  </section>{/each}
<section class="aside-section">
  <h3>{t('salaryDisclosure')}</h3>
  <p>
    {vacancies.filter((v) => v.salary).length}/{vacancies.length} · {number(
      vacancies.length ? (100 * vacancies.filter((v) => v.salary).length) / vacancies.length : 0,
      lang,
    )}%
  </p>
</section>
<section class="aside-section">
  <h3>{t('topEmployers')}</h3>
  {#each employers as employer (employer.name)}<div class="stat-line">
      <span>{employer.name}</span><span>{employer.count}</span>
    </div>{/each}
</section>
<section class="aside-section">
  <h3>{t('pairs')}</h3>
  {#each pairs(vacancies) as [name, count] (name)}<div class="stat-line">
      <span>{name}</span><span>{count}</span>
    </div>{/each}
</section>
<section class="aside-section">
  <h3>{t('missingSkills')}</h3>
  {#each skillGaps.slice(0, 5) as row (row.name)}<div class="stat-line">
      <button class="text-button" onclick={() => applyTechnology(row.name)}>{row.name}</button><span
        >{row.overlap}</span
      >
    </div>{/each}
</section>
