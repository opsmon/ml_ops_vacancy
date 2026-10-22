<script lang="ts">
  import type { Dataset, Filters, Lang, Personal, Vacancy } from '../lib/types';
  import { date, number, translate as tr } from '../lib/i18n';
  import { radarHistory, technologyStats } from '../lib/market';
  let {
    data,
    vacancies,
    filters,
    personal,
    lang,
    applyTechnology,
  }: {
    data: Dataset;
    vacancies: Vacancy[];
    filters: Filters;
    personal: Personal;
    lang: Lang;
    applyTechnology: (name: string) => void;
  } = $props();
  const t = (key: string) => tr(lang, key);
  let windowDays = $state(7);
  let history = $derived(radarHistory(data, filters, windowDays, data.generated_at));
  let stats = $derived(
    technologyStats(
      vacancies.map((v) => ({
        ...v,
        technologies: v.technologies.filter(
          (t) => !filters.requirement || t.requirement === filters.requirement,
        ),
      })),
    ),
  );
  function points(values: { count: number; n: number }[]) {
    return values
      .map(
        (x, i) =>
          `${(i * 100) / Math.max(1, values.length - 1)},${30 - (x.n ? (30 * x.count) / x.n : 0)}`,
      )
      .join(' ');
  }
</script>

<div class="section-heading">
  <div>
    <h2>{t('radar')}</h2>
    <p class="small">
      {t('scopeFiltered')} · n={vacancies.length} · {date(data.last_success, lang, true)}
    </p>
  </div>
  <label class="field"
    >{t('window')}<select bind:value={windowDays}
      >{#each [7, 30, 90] as days (days)}<option value={days}>{t('days' + days)}</option
        >{/each}</select
    ></label
  >
</div>
<p>{t('radarExplain')}</p>
{#if !history}<p class="notice">{t('noHistory')}</p>{/if}
<div class="table-scroll">
  <table class="radar-table">
    <thead
      ><tr
        ><th>{t('technology')}</th><th>{t('prevalence')}</th><th>{t('requiredPreferred')}</th><th
          >{t('employersCount')}</th
        ><th>{t('coreAdjacent')}</th><th>{t('change')}</th><th>{t('assessment')}</th><th
          >{t('history')}</th
        ></tr
      ></thead
    ><tbody>
      {#each stats as row (row.name)}
        {@const trend = history?.find((x) => x.name === row.name)}
        <tr
          ><td
            ><button class="text-button" onclick={() => applyTechnology(row.name)}
              >{row.name}</button
            >{#if personal.skills.includes(row.name)}<span title={t('mine')}> ✓</span>{/if}</td
          ><td
            ><span class="inline-bar"><span style:width={`${row.percent}%`}></span></span
            >{row.count}/{vacancies.length} · {number(row.percent, lang, 1)}%</td
          ><td>{row.required} / {row.preferred}</td><td>{row.employers.size}</td><td
            >{row.core} / {row.adjacent}</td
          ><td
            >{#if trend}{trend.delta > 0 ? '+' : ''}{number(trend.delta, lang, 1)}<small
                class="block"
                >{trend.before}/{trend.previousN} → {trend.after}/{trend.currentN}</small
              >{:else}—{/if}</td
          ><td>{t(trend?.assessment || 'insufficient')}</td><td
            >{#if trend}<svg
                width="100"
                height="30"
                viewBox="0 0 100 30"
                role="img"
                aria-label={`${row.name}: ${trend.history.map((p) => p.day + ': ' + p.count + '/' + p.n).join('; ')}`}
                ><polyline
                  points={points(trend.history)}
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                /></svg
              >{:else}—{/if}</td
          ></tr
        >
      {/each}
    </tbody>
  </table>
</div>
{#if history?.some((x) => x.assessment !== 'insufficient')}
  <h3>{t('demandGrowth')}</h3>
  <svg class="scatter" viewBox="0 0 600 260" role="img" aria-label={t('demandGrowth')}>
    <line x1="45" y1="210" x2="570" y2="210" stroke="currentColor" /><line
      x1="45"
      y1="30"
      x2="45"
      y2="210"
      stroke="currentColor"
    />
    <text x="240" y="250">{t('prevalence')} %</text><text x="50" y="20">{t('growth')}</text>
    {#each stats.filter((r) => history?.find((h) => h.name === r.name)?.assessment !== 'insufficient') as row (row.name)}{@const h =
        history!.find((x) => x.name === row.name)!}<circle
        cx={45 + row.percent * 5.2}
        cy={120 - Math.max(-80, Math.min(80, h.delta)) * 1.1}
        r="4"
        fill="currentColor"
        ><title>{row.name}: {number(row.percent, lang, 1)}%; {number(h.delta, lang, 1)}</title
        ></circle
      ><text
        x={52 + row.percent * 5.2}
        y={120 - Math.max(-80, Math.min(80, h.delta)) * 1.1}
        font-size="10">{row.name}</text
      >{/each}
  </svg>
{/if}
<p class="small">{t('policyText')}</p>
