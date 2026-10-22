<script lang="ts">
  import type { Dataset, Lang } from '../lib/types';
  import { date, number, translate as tr } from '../lib/i18n';
  import { pairs, salarySamples } from '../lib/market';
  let { data, lang, supported }: { data: Dataset; lang: Lang; supported: boolean } = $props();
  const t = (key: string) => tr(lang, key);
  let selected = $state('Kubernetes');
  let historical = $derived(
    data.snapshots.map((s) => ({
      day: s.day,
      coverage: s.coverage,
      n: s.vacancies.length,
      count: s.vacancies.filter((v) =>
        v.technologies.some((t) => t.name === selected && t.section !== 'company'),
      ).length,
      remote: s.vacancies.filter((v) => v.arrangement.includes('REMOTE')).length,
      salaried: s.vacancies.filter((v) => v.salary).length,
    })),
  );
  const value = (n: number | null | undefined) => (n == null ? '—' : number(n, lang));
</script>

<h2>{t('trends')}</h2>
<p class="small">{t('scopeGlobal')} · {t('metricText')}</p>
{#if !data.daily.length}<p class="notice">{t('noHistory')}</p>{:else}
  <div class="table-scroll">
    <table>
      <thead
        ><tr
          >{#each ['date', 'arrivals', 'activeInventory', 'publishedToday', 'updated', 'archived', 'coverage'] as key (key)}<th
              >{t(key)}</th
            >{/each}</tr
        ></thead
      ><tbody>
        {#each data.daily as row (row.date)}<tr
            ><td>{date(row.date + 'T12:00:00Z', lang)}</td><td>{value(row.arrivals)}</td><td
              >{value(row.active)}</td
            ><td>{value(row.published)}</td><td>{value(row.updated)}</td><td
              >{value(row.archived)}</td
            ><td
              >{t(
                row.initial_inventory
                  ? 'inventory'
                  : row.partial_today
                    ? 'incomplete'
                    : row.complete
                      ? 'complete'
                      : 'missingDay',
              )}</td
            ></tr
          >{/each}
      </tbody>
    </table>
  </div>{/if}
<section class="content-section">
  <h2>{t('forecast')}</h2>
  <p class="small">{t('filteredForecast')}</p>
  {#if !supported}<p class="notice">{t('unsupportedForecast')}</p>
  {:else if data.mode === 'demo' || data.forecast.status !== 'available'}<p class="notice">
      {t('coldStart')}
    </p>
    <p>{t('observations')}: {data.forecast.observations} / {data.forecast.minimum}</p>
  {:else}<p>{t('forecastMethod')}: {t(data.forecast.method!)} · {t('interval')}</p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>{t('date')}</th><th>{t('arrivals')}</th><th>{t('interval')}</th></tr></thead
        ><tbody
          >{#each data.forecast.predictions as row (row.date)}<tr
              ><td>{date(row.date + 'T12:00:00Z', lang)}</td><td>{row.value}</td><td
                >{row.lower}–{row.upper}</td
              ></tr
            >{/each}</tbody
        >
      </table>
    </div>
    {#each Object.entries(data.forecast.evaluation) as [method, evaluation] (method)}<p>
        {t(method)} · {t('mae')}: {evaluation.mae} · {t('wape')}: {evaluation.wape == null
          ? '—'
          : number(evaluation.wape * 100, lang, 1) + '%'} · n={evaluation.n}
      </p>{/each}
    <p>
      {t('coverage')}: {data.forecast.interval?.coverage == null
        ? '—'
        : number(data.forecast.interval.coverage * 100, lang, 1) + '%'} · n={data.forecast.interval
        ?.validation_n || 0}
    </p>
    <p class="small">{t('intervalCaveat')}</p>{/if}
</section>
<section class="content-section">
  <h2>{t('history')}</h2>
  <label class="field narrow"
    >{t('technology')}<select bind:value={selected}
      >{#each data.taxonomy as tech (tech.name)}<option value={tech.name}>{tech.name}</option
        >{/each}</select
    ></label
  >
  {#if !historical.length}<p>{t('noHistory')}</p>{:else}<div class="table-scroll">
      <table>
        <thead
          ><tr
            ><th>{t('date')}</th><th>{t('prevalence')}</th><th>{t('remote')}</th><th
              >{t('salaryDisclosure')}</th
            ><th>{t('sample')}</th></tr
          ></thead
        ><tbody
          >{#each historical as row, index (index)}<tr
              ><td>{row.day}</td><td
                >{row.count}/{row.n} · {row.n
                  ? number((row.count * 100) / row.n, lang, 1)
                  : '—'}%</td
              ><td>{row.remote}/{row.n}</td><td>{row.salaried}/{row.n}</td><td>{row.n}</td></tr
            >{/each}</tbody
        >
      </table>
    </div>{/if}
</section>
<section class="content-section">
  <h2>{t('cohortHistory')}</h2>
  {#if data.snapshots.length}
    <div class="table-scroll">
      <table>
        <thead
          ><tr
            ><th>{t('date')}</th><th>{t('sample')}</th><th>{t('coreAdjacent')}</th><th
              >{t('experienceDistribution')}</th
            ><th>{t('arrangementDistribution')}</th><th>{t('employersCount')}</th></tr
          ></thead
        ><tbody>
          {#each data.snapshots as s (s.id)}<tr
              ><td>{date(s.at, lang, true)}</td><td>{s.vacancies.length}</td><td
                >{s.vacancies.filter((v) => v.category === 1).length} / {s.vacancies.filter(
                  (v) => v.category === 3,
                ).length}</td
              ><td
                >{[...new Set(s.vacancies.map((v) => v.experience))]
                  .map((e) => `${t(e)}: ${s.vacancies.filter((v) => v.experience === e).length}`)
                  .join('; ')}</td
              ><td
                >{['REMOTE', 'HYBRID', 'ON_SITE', 'unknown']
                  .map(
                    (a) =>
                      `${t(({ REMOTE: 'remote', HYBRID: 'hybrid', ON_SITE: 'onsite' } as Record<string, string>)[a] || a)}: ${s.vacancies.filter((v) => v.arrangement.includes(a)).length}`,
                  )
                  .join('; ')}</td
              ><td>{new Set(s.vacancies.map((v) => v.employer_id)).size}</td></tr
            >{/each}
        </tbody>
      </table>
    </div>
    <h3>{t('historicalEmployer')}</h3>
    <div class="table-scroll">
      <table>
        <thead><tr><th>{t('date')}</th><th>{t('employer')}</th><th>{t('counts')}</th></tr></thead
        ><tbody>
          {#each data.snapshots as s (s.id)}{#each [...new Set(s.vacancies.map((v) => v.employer_id))] as id (id)}<tr
                ><td>{date(s.at, lang, true)}</td><td
                  >{data.vacancies.find((v) => v.employer_id === id)?.employer || id}</td
                ><td>{s.vacancies.filter((v) => v.employer_id === id).length}</td></tr
              >{/each}{/each}
        </tbody>
      </table>
    </div>
    <h3>{t('salarySamples')}</h3>
    {#each data.snapshots as s (s.id)}<p class="small">
        {date(s.at, lang, true)} · n={s.vacancies.length}
      </p>
      {#each salarySamples(s.vacancies) as row (row.key)}<p>
          {row.key} · n={row.n} · {row.median == null
            ? t('noSalarySummary')
            : number(row.median, lang)}
        </p>{/each}{/each}
    <h3>{t('historicalPairs')}</h3>
    <div class="table-scroll">
      <table>
        <thead><tr><th>{t('date')}</th><th>{t('pairs')}</th><th>{t('counts')}</th></tr></thead
        ><tbody>
          {#each data.snapshots as s (s.id)}{#each pairs(s.vacancies) as [pair, count] (pair)}<tr
                ><td>{date(s.at, lang, true)}</td><td>{pair}</td><td
                  >{count}/{s.vacancies.length}</td
                ></tr
              >{/each}{/each}
        </tbody>
      </table>
    </div>
  {:else}<p>{t('noHistory')}</p>{/if}
</section>
