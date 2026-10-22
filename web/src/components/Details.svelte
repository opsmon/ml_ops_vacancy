<script lang="ts">
  import type { Lang, Personal, Vacancy } from '../lib/types';
  import { date, translate as tr } from '../lib/i18n';
  import { fit, salaryText } from '../lib/market';
  let {
    vacancy: v,
    personal = $bindable(),
    lang,
    demo,
    onclose,
  }: {
    vacancy: Vacancy;
    personal: Personal;
    lang: Lang;
    demo: boolean;
    onclose: () => void;
  } = $props();
  const t = (key: string) => tr(lang, key);
  let match = $derived(fit(v, personal));
  let tracking = $derived(personal.tracking[v.id] || {});
  function update(field: string, value: string) {
    personal = {
      ...personal,
      tracking: { ...personal.tracking, [v.id]: { ...tracking, [field]: value } },
    };
  }
  const reason = (value: string) =>
    value.startsWith('technology:')
      ? value.slice(11)
      : t(
          (
            {
              core_title: 'category1',
              platform_title: 'category2',
              operational_ml: 'responsibility',
              no_explicit_ml_responsibilities: 'noExplicitML',
              company_ai_only: 'companyOnlyAI',
              section_extraction_heuristic: 'sectionUncertain',
              salary_unknown: 'salaryUnknown',
              arrangement_unknown: 'arrangementUnknown',
              details_missing: 'detailsMissing',
              source_detail: 'sourceDetail',
              source_404_or_410_not_archival: 'sourceInaccessible',
              detail_unavailable: 'sourceInaccessible',
            } as Record<string, string>
          )[value] || value,
        );
</script>

<div class="modal-heading">
  <div>
    <p class="eyebrow">{t('details')}</p>
    <h2>{v.title}</h2>
  </div>
  <button onclick={onclose}>{t('close')}</button>
</div>
<p>
  {v.employer} · {v.location} · {v.arrangement
    .map((x) =>
      t(
        ({ REMOTE: 'remote', HYBRID: 'hybrid', ON_SITE: 'onsite' } as Record<string, string>)[x] ||
          x,
      ),
    )
    .join(', ')}
</p>
<p><strong>{salaryText(v.salary, lang)}</strong></p>
<div class="tagline">
  <span>{t('category' + v.category)} · {v.score}/100</span><span>{t(v.experience)}</span><span
    >{t('seniority')}: {v.seniority} {v.seniority_uncertain ? '· ' + t('uncertain') : ''}</span
  >
</div>
<h3>{t('practicalSummary')}</h3>
<p class="small">{t('summaryLanguage')}</p>
<p>{v.summary[lang]}</p>
<h3>{t('fit')}</h3>
<p>{match.score === null ? t('sparseFit') : match.score + '%'}</p>
<p class="small">{t('overlapHelp')}</p>
{#each ['matched', 'missingRequired', 'missingPreferred'] as key (key)}<p>
    <strong>{t(key)}:</strong>
    {match[key as 'matched' | 'missingRequired' | 'missingPreferred'].join(', ') || '—'}
  </p>{/each}
{#if v.flags.transition}<p>{t('transition')} · {t('transitionExplain')}</p>{/if}
<h3>{t('reasons')} · {v.classifier_version}</h3>
<ul>
  {#each v.reasons as value (value)}<li>{reason(value)}</li>{/each}
</ul>
{#if v.negative_signals.length}<h3>{t('negative')}</h3>
  <ul>
    {#each v.negative_signals as value (value)}<li>{reason(value)}</li>{/each}
  </ul>{/if}
<h3>{t('original')} · {v.extractor_version}</h3>
<div class="table-scroll">
  <table>
    <thead
      ><tr
        ><th>{t('technology')}</th><th>{t('requirementType')}</th><th>{t('section')}</th><th
          >{t('evidence')}</th
        ></tr
      ></thead
    ><tbody>
      {#each v.technologies as tech, index (index)}<tr
          ><td>{tech.name}</td><td>{t(tech.requirement)}</td><td
            >{t(tech.section === 'responsibilities' ? 'responsibility' : tech.section)}</td
          ><td>{tech.evidence}</td></tr
        >{/each}
    </tbody>
  </table>
</div>
<h3>{t('uncertainties')}</h3>
<ul>
  {#each v.uncertainties as value (value)}<li>{reason(value)}</li>{/each}
</ul>
<h3>{t('changes')}</h3>
{#if !v.events.length}<p>{t('noChanges')}</p>{/if}
{#each v.events as event, index (index)}<details>
    <summary
      >{date(event.at, lang, true)} · {t(
        event.kind === 'updated'
          ? 'updatedEvent'
          : event.kind === 'discovered'
            ? 'discoveredEvent'
            : event.kind,
      )} · {event.fields.map((x) => t(x)).join(', ')}</summary
    >
    <pre>{JSON.stringify({ before: event.before, after: event.after }, null, 2)}</pre>
  </details>{/each}
<dl class="facts">
  <dt>{t('publishedAt')}</dt>
  <dd>{date(v.published_at, lang, true)}</dd>
  <dt>{t('discovered')}</dt>
  <dd>{date(v.first_seen, lang, true)}</dd>
  <dt>{t('statusEvidence')}</dt>
  <dd>{t(v.status)} · {reason(v.status_evidence)}</dd>
  <dt>{t('queries')}</dt>
  <dd>{v.queries.join(', ')}</dd>
</dl>
<h3>{t('jobTracking')}</h3>
<label class="field"
  >{t('application')}<select
    aria-label={t('application')}
    value={tracking.status || ''}
    onchange={(e) => update('status', e.currentTarget.value)}
    >{#each ['', 'interested', 'applied', 'interview', 'offer', 'rejected'] as value (value)}<option
        {value}>{t(value || 'notSet')}</option
      >{/each}</select
  ></label
>
<label class="field"
  >{t('notes')}<textarea
    rows="4"
    value={tracking.note || ''}
    oninput={(e) => update('note', e.currentTarget.value)}></textarea></label
>
<p class="small">{t('localOnly')}</p>
{#if demo}<p class="muted">{t('sourceDemo')}</p>{:else}<a
    class="button primary"
    href={`https://hh.ru/vacancy/${encodeURIComponent(v.id)}`}
    target="_blank"
    rel="noopener noreferrer">{t('source')} ↗</a
  >{/if}
