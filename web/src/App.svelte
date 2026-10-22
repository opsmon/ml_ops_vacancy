<script lang="ts">
  import { onMount } from 'svelte';
  import type {
    Dataset,
    Filters as FilterState,
    Lang,
    Personal,
    Tracking,
    Vacancy,
  } from './lib/types';
  import { date, moscowDay, number, translate as tr } from './lib/i18n';
  import {
    csv,
    defaults,
    emptyPersonal,
    filterVacancies,
    fit,
    fromURL,
    isDefault,
    learning,
    salarySamples,
    salaryText,
    techNames,
    toURL,
    tokens,
    validateDataset,
  } from './lib/market';
  import { download, loadPersonal, savePersonal } from './lib/storage';
  import Filters from './components/Filters.svelte';
  import Insights from './components/Insights.svelte';
  import Profile from './components/Profile.svelte';
  import Details from './components/Details.svelte';
  import Radar from './components/Radar.svelte';
  import History from './components/History.svelte';
  const initial = fromURL(new URL(location.href));
  const tabs = ['vacancies', 'radar', 'trends', 'skills', 'employers', 'methodology'];
  let lang = $state<Lang>(initial.lang || 'ru');
  let filters = $state<FilterState>(initial.filters);
  let tab = $state(tabs.includes(initial.tab) ? initial.tab : 'vacancies');
  let personal = $state<Personal>(structuredClone(emptyPersonal));
  let data = $state<Dataset | null>(null),
    loading = $state(true),
    error = $state(false),
    storageError = $state(false),
    initialized = $state(false);
  let sort = $state('relevance'),
    view = $state('list'),
    mobile = $state('vacancies'),
    theme = $state('light');
  let selected = $state<Vacancy | null>(null),
    profileOpen = $state(false),
    compare = $state<string[]>([]),
    compareOpen = $state(false),
    copied = $state(false);
  let modal: HTMLDialogElement;
  let previousFocus: HTMLElement | null = null;
  let previousVisit = $state<string | null>(null);
  const mode = import.meta.env.VITE_DATA_MODE || 'demo';
  const t = (key: string) => tr(lang, key);
  let filtered = $derived(
    data
      ? filterVacancies(
          data.vacancies,
          filters,
          { ...personal, lastVisit: previousVisit },
          data.mode === 'demo' ? data.generated_at : new Date().toISOString(),
        )
      : [],
  );
  let results = $derived(
    [...filtered].sort((a, b) => {
      if (sort === 'publication') return (b.published_at || '').localeCompare(a.published_at || '');
      if (sort === 'discovery') return b.first_seen.localeCompare(a.first_seen);
      if (sort === 'fit') return (fit(b, personal).score ?? -1) - (fit(a, personal).score ?? -1);
      if (sort === 'missing')
        return (
          (fit(a, personal).required.length ? fit(a, personal).missingRequired.length : Infinity) -
          (fit(b, personal).required.length ? fit(b, personal).missingRequired.length : Infinity)
        );
      if (sort === 'salary') {
        const comparable = (v: Vacancy) =>
          v.salary?.currency === filters.currency &&
          v.salary?.period === filters.period &&
          v.salary?.mode === filters.salaryMode &&
          (v.salary.gross === null ? 'unknown' : v.salary.gross ? 'gross' : 'net') === filters.tax;
        return (
          (comparable(b) ? (b.salary?.lower ?? -1) : -1) -
          (comparable(a) ? (a.salary?.lower ?? -1) : -1)
        );
      }
      return b.score - a.score;
    }),
  );
  let chips = $derived(
    (Object.keys(defaults) as (keyof FilterState)[]).filter(
      (key) => filters[key] !== defaults[key],
    ),
  );
  let today = $derived(
    data ? moscowDay(data.mode === 'demo' ? data.generated_at : new Date().toISOString()) : '',
  );
  let discovered = $derived(
    filtered.filter((v) =>
      v.events.some((e) => e.kind === 'discovered' && moscowDay(e.at) === today),
    ).length,
  );
  let published = $derived(
    filtered.filter((v) => v.published_at && moscowDay(v.published_at) === today).length,
  );
  let stats = $derived(salarySamples(filtered));
  async function load() {
    loading = true;
    error = false;
    try {
      const response = await fetch(
        import.meta.env.BASE_URL + `data/${mode === 'real' ? 'market' : 'demo'}.json`,
        { cache: 'no-cache' },
      );
      if (!response.ok) throw new Error('fetch');
      data = validateDataset(await response.json(), mode);
    } catch {
      error = true;
    } finally {
      loading = false;
    }
  }
  onMount(() => {
    try {
      personal = loadPersonal(localStorage);
      if (!initial.lang) lang = localStorage.getItem('mlpops.lang') === 'en' ? 'en' : 'ru';
      theme = localStorage.getItem('mlpops.theme') || 'light';
    } catch {
      storageError = true;
    }
    previousVisit = personal.lastVisit || null;
    personal = { ...personal, lastVisit: new Date().toISOString() };
    initialized = true;
    load();
  });
  $effect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dataset.theme = theme;
    if (initialized) {
      history.replaceState(null, '', toURL(new URL(location.href), filters, lang, tab));
      try {
        savePersonal(localStorage, personal);
        localStorage.setItem('mlpops.lang', lang);
        localStorage.setItem('mlpops.theme', theme);
      } catch {
        storageError = true;
      }
    }
  });
  $effect(() => {
    if (!modal) return;
    if (selected || profileOpen || compareOpen) {
      previousFocus = document.activeElement as HTMLElement;
      if (!modal.open) modal.showModal();
    } else if (modal.open) {
      modal.close();
      previousFocus?.focus();
    }
  });
  function closeModal() {
    selected = null;
    profileOpen = false;
    compareOpen = false;
  }
  function track(v: Vacancy, patch: Tracking) {
    personal = {
      ...personal,
      tracking: { ...personal.tracking, [v.id]: { ...personal.tracking[v.id], ...patch } },
    };
  }
  function open(v: Vacancy) {
    track(v, { viewed: true });
    selected = v;
  }
  function applyTechnology(name: string) {
    const list = tokens(filters.tech);
    filters = { ...filters, tech: [...new Set([...list, name])].join(',') };
    tab = 'vacancies';
    mobile = 'vacancies';
  }
  async function share() {
    try {
      await navigator.clipboard.writeText(toURL(new URL(location.href), filters, lang, tab).href);
      copied = true;
      setTimeout(() => (copied = false), 1800);
    } catch {
      copied = false;
    }
  }
  function addCompare(id: string) {
    compare = compare.includes(id)
      ? compare.filter((x) => x !== id)
      : compare.length < 3
        ? [...compare, id]
        : compare;
  }
  function pop() {
    const state = fromURL(new URL(location.href));
    filters = state.filters;
    lang = state.lang || lang;
    tab = tabs.includes(state.tab) ? state.tab : 'vacancies';
  }
</script>

<svelte:window onpopstate={pop} />
<svelte:head><title>MlPops · {t(tab)}</title></svelte:head>
<a class="skip-link" href="#main">{t('skipContent')}</a>
<header class="app-header">
  <div class="brand">
    <span class="brand-mark">m/</span><strong>MlPops</strong><span class="brand-caption"
      >MLOps · ML Infrastructure</span
    >
  </div>
  <div class="header-controls">
    <button
      class="text-button"
      onclick={() => (theme = theme === 'dark' ? 'light' : 'dark')}
      aria-label={t('theme')}>{t(theme === 'dark' ? 'light' : 'dark')}</button
    >
    <div class="language" aria-label={t('language')}>
      {#each ['ru', 'en'] as value (value)}<button
          aria-pressed={lang === value}
          class:active={lang === value}
          onclick={() => (lang = value as Lang)}>{value.toUpperCase()}</button
        >{/each}
    </div>
    <button onclick={() => (profileOpen = true)}>{t('personal')}</button>
  </div>
</header>
{#if storageError}<p class="status-banner" role="alert">{t('storageError')}</p>{/if}
{#if loading}<main class="loading" aria-live="polite">{t('loading')}</main>
{:else if error || !data}<main class="loading">
    <p role="alert">{t('error')}</p>
    <button onclick={load}>{t('retry')}</button>
  </main>
{:else}
  <div class="status-banner" class:demo={data.mode === 'demo'}>
    <strong>{t(data.mode === 'demo' ? 'demo' : 'real')}</strong><span
      >{t('refresh')}: {date(data.last_success, lang, true)} · {t(data.coverage)}</span
    >{#if data.mode === 'real' && data.last_success && Date.now() - Date.parse(data.last_success) > 86400000}<strong
        >{t('stale')}</strong
      >{/if}
  </div>
  <div class="mobile-tabs">
    {#each ['filters', 'vacancies', 'insights'] as value (value)}<button
        class:active={mobile === value}
        onclick={() => (mobile = value)}>{t(value)}</button
      >{/each}
  </div>
  <div class="workspace">
    <aside class="filter-panel" class:mobile-visible={mobile === 'filters'}>
      <Filters bind:filters {lang} {data} bind:personal openProfile={() => (profileOpen = true)} />
    </aside>
    <main id="main" class:mobile-visible={mobile === 'vacancies'}>
      <nav class="tabs" aria-label={t('navigation')}>
        {#each tabs as value (value)}<button
            class:active={tab === value}
            aria-current={tab === value ? 'page' : undefined}
            onclick={() => (tab = value)}>{t(value)}</button
          >{/each}
      </nav>
      <div class="main-body">
        {#if data.mode === 'demo'}<p class="demo-description">{t('demoExplain')}</p>{/if}
        {#if tab === 'vacancies'}
          <div class="metrics" aria-label={t('scopeFiltered')}>
            <div>
              <span>{t('observedActive')}</span><strong
                >{number(filtered.filter((v) => v.status === 'active').length, lang)}</strong
              >
            </div>
            <div>
              <span>{t('discoveredToday')}</span><strong>{number(discovered, lang)}</strong>
            </div>
            <div><span>{t('publishedToday')}</span><strong>{number(published, lang)}</strong></div>
          </div>
          <p class="small context">
            {t('scopeFiltered')} · {t('incomplete')} · {t('asOf')}
            {date(data.generated_at, lang, true)}
          </p>
          {#if data.runs.some((r) => r.initial_inventory) && !data.daily.some((r) => r.complete)}<p
              class="small"
            >
              {t('inventory')}
            </p>{/if}
          {#if chips.length}<div class="filter-chips">
              {#each chips as key (key)}<button
                  onclick={() => (filters = { ...filters, [key]: defaults[key] })}
                  >{t(key === 'q' ? 'search' : key === 'categories' ? 'category' : key)}: {typeof filters[
                    key
                  ] === 'boolean'
                    ? t('enabled')
                    : String(filters[key])} ×</button
                >{/each}
            </div>{/if}
          <div class="results-toolbar">
            <strong data-testid="results-count">{t('resultCount')}: {results.length}</strong><label
              >{t('sort')}
              <select bind:value={sort}
                ><option value="relevance">{t('relevance')}</option><option value="publication"
                  >{t('publication')}</option
                ><option value="discovery">{t('discovery')}</option><option value="fit"
                  >{t('fit')}</option
                ><option value="missing">{t('missing')}</option><option
                  value="salary"
                  disabled={!filters.currency ||
                    !filters.period ||
                    !filters.tax ||
                    !filters.salaryMode}>{t('salary')}</option
                ></select
              ></label
            >
            <div class="view-toggle">
              <button class:active={view === 'list'} onclick={() => (view = 'list')}
                >{t('list')}</button
              ><button class:active={view === 'table'} onclick={() => (view = 'table')}
                >{t('table')}</button
              >
            </div>
          </div>
          <div class="toolbar secondary">
            <button
              onclick={() =>
                download('mlpops-vacancies.csv', csv(filtered), 'text/csv;charset=utf-8')}
              >{t('exportCsv')}</button
            ><button onclick={share}>{t(copied ? 'copied' : 'share')}</button
            >{#if compare.length}<button class="primary" onclick={() => (compareOpen = true)}
                >{t('compare')} ({compare.length}/3)</button
              >{/if}
          </div>
          {#if !results.length}<div class="empty">
              <h2>{t('noResults')}</h2>
              <button onclick={() => (filters = { ...defaults })}>{t('reset')}</button>
            </div>
          {:else if view === 'table'}<div class="table-scroll">
              <table>
                <thead
                  ><tr
                    >{#each ['title', 'employer', 'salary', 'experience', 'fit', 'compare'] as key (key)}<th
                        >{t(key)}</th
                      >{/each}</tr
                  ></thead
                ><tbody
                  >{#each results as v (v.id)}<tr
                      ><td
                        ><button class="text-button" onclick={() => open(v)}>{v.title}</button></td
                      ><td>{v.employer}</td><td>{salaryText(v.salary, lang)}</td><td
                        >{t(v.experience)}</td
                      ><td>{fit(v, personal).score ?? '—'}%</td><td
                        ><input
                          type="checkbox"
                          aria-label={t('compare') + ' ' + v.title}
                          checked={compare.includes(v.id)}
                          disabled={compare.length >= 3 && !compare.includes(v.id)}
                          onchange={() => addCompare(v.id)}
                        /></td
                      ></tr
                    >{/each}</tbody
                >
              </table>
            </div>
          {:else}<div class="vacancy-list">
              {#each results as v (v.id)}
                {@const match = fit(v, personal)}{@const tracking = personal.tracking[v.id] || {}}
                <article class="vacancy-row" class:viewed={tracking.viewed} data-testid="vacancy">
                  <div class="vacancy-heading">
                    <button class="vacancy-title" onclick={() => open(v)}>{v.title}</button><button
                      class:active={tracking.bookmark}
                      aria-label={t(tracking.bookmark ? 'unbookmark' : 'bookmark') + ' ' + v.title}
                      aria-pressed={!!tracking.bookmark}
                      onclick={() => track(v, { bookmark: !tracking.bookmark })}
                      >{tracking.bookmark ? '★' : '☆'}</button
                    >
                  </div>
                  <p class="employer-line">
                    {v.employer} · {v.location} · {v.arrangement
                      .map((x) =>
                        t(
                          (
                            { REMOTE: 'remote', HYBRID: 'hybrid', ON_SITE: 'onsite' } as Record<
                              string,
                              string
                            >
                          )[x] || x,
                        ),
                      )
                      .join(', ')}
                  </p>
                  <p class="salary-line">{salaryText(v.salary, lang)}</p>
                  <div class="metadata">
                    <span>{t('category' + v.category)} · {v.score}/100</span><span
                      >{t(v.experience)}</span
                    ><span>{t('fit')}: {match.score === null ? '—' : match.score + '%'}</span
                    >{#if v.events.some((e) => e.kind === 'updated')}<span class="change-label"
                        >{t('updated')}</span
                      >{/if}{#if v.possible_reposts.length}<span>{t('repost')}</span
                      >{/if}{#if v.events.some((e) => e.kind === 'discovered' && moscowDay(e.at) === today)}<span
                        >{t('new')}</span
                      >{/if}
                  </div>
                  <div class="tech-tags">
                    {#each techNames(v).slice(0, 8) as name (name)}<button
                        class:selected={tokens(filters.tech).includes(name)}
                        onclick={() => applyTechnology(name)}>{name}</button
                      >{/each}
                  </div>
                  <p class="vacancy-summary">{v.summary[lang]}</p>
                  <div class="vacancy-footer">
                    <span
                      >{t('publishedAt')}: {date(v.published_at, lang)} · {t('discovered')}: {date(
                        v.first_seen,
                        lang,
                      )}</span
                    >
                    <div class="row-actions">
                      <button
                        class="text-button"
                        onclick={() => track(v, { dismissed: !tracking.dismissed })}
                        >{t(tracking.dismissed ? 'restore' : 'dismiss')}</button
                      ><label class="inline"
                        ><input
                          type="checkbox"
                          checked={compare.includes(v.id)}
                          disabled={compare.length >= 3 && !compare.includes(v.id)}
                          onchange={() => addCompare(v.id)}
                        />{t('compare')}</label
                      ><button onclick={() => open(v)}>{t('details')}</button>
                    </div>
                  </div>
                </article>
              {/each}
            </div>{/if}
        {:else if tab === 'radar'}<Radar
            {data}
            vacancies={filtered}
            {filters}
            {personal}
            {lang}
            {applyTechnology}
          />
        {:else if tab === 'trends'}<History {data} {lang} supported={isDefault(filters)} />
        {:else if tab === 'skills'}<h2>{t('skills')}</h2>
          <p>{t('overlapHelp')}</p>
          <button onclick={() => (profileOpen = true)}>{t('personal')}</button>
          <p>
            {t('fitCoverage')}: {filtered.filter(
              (v) =>
                fit(v, personal).required.length && fit(v, personal).missingRequired.length === 0,
            ).length}/{filtered.filter((v) => fit(v, personal).required.length).length}
          </p>
          <h3>{t('learningPriority')}</h3>
          <div class="table-scroll">
            <table>
              <thead
                ><tr><th>{t('technology')}</th><th>{t('overlap')}</th><th>{t('unlock')}</th></tr
                ></thead
              ><tbody
                >{#each learning(filtered, personal) as row (row.name)}<tr
                    ><td
                      ><button class="text-button" onclick={() => applyTechnology(row.name)}
                        >{row.name}</button
                      ></td
                    ><td>{row.overlap}</td><td>{row.unlock}</td></tr
                  >{/each}</tbody
              >
            </table>
          </div>
          <p class="small">{t('learningExplain')}</p>
        {:else if tab === 'employers'}<h2>{t('employers')}</h2>
          <p class="small">{t('scopeFiltered')} · n={filtered.length}</p>
          <table>
            <thead
              ><tr><th>{t('employer')}</th><th>{t('counts')}</th><th>{t('discovery')}</th></tr
              ></thead
            ><tbody
              >{#each [...new Set(filtered.map((v) => v.employer_id))].sort((a, b) => filtered.filter((v) => v.employer_id === b).length - filtered.filter((v) => v.employer_id === a).length) as id (id)}<tr
                  ><td
                    ><button
                      class="text-button"
                      onclick={() => {
                        filters = {
                          ...filters,
                          employer: filtered.find((v) => v.employer_id === id)!.employer,
                        };
                        tab = 'vacancies';
                      }}>{filtered.find((v) => v.employer_id === id)!.employer}</button
                    ></td
                  ><td>{filtered.filter((v) => v.employer_id === id).length}</td><td
                    >{date(
                      filtered
                        .filter((v) => v.employer_id === id)
                        .map((v) => v.first_seen)
                        .sort()[0],
                      lang,
                    )}</td
                  ></tr
                >{/each}</tbody
            >
          </table>
          <h3>{t('salarySamples')}</h3>
          {#each stats as row (row.key)}<p>
              {row.key} · n={row.n} · {row.median == null
                ? t('noSalarySummary')
                : number(row.median, lang)}
            </p>{/each}
        {:else}<h2>{t('methodology')}</h2>
          {#each ['methodologyText', 'metricText', 'salaryText', 'policyText', 'privacyText', 'publicGate', 'localOnly'] as key (key)}<p
            >
              {t(key)}
            </p>{/each}
          <p>
            <a href="https://dev.hh.ru/admin/developer_agreement" target="_blank" rel="noreferrer"
              >{t('sourceTerms')}</a
            >
            ·
            <a
              href="https://github.com/opsmon/ml_ops_vacancy/tree/main/docs"
              target="_blank"
              rel="noreferrer">{t('documentation')}</a
            >
          </p>
          <h3>{t('collectionRuns')}</h3>
          <div class="table-scroll">
            <table>
              <thead
                ><tr
                  >{#each ['date', 'coverage', 'apiRequests', 'counts'] as key (key)}<th
                      >{t(key)}</th
                    >{/each}</tr
                ></thead
              ><tbody
                >{#each data.runs.slice(-10).reverse() as run (run.id)}<tr
                    ><td>{date(run.finished_at, lang, true)}</td><td>{t(run.status)}</td><td
                      >{run.requests}</td
                    ><td>{run.unique_ids}</td></tr
                  >{/each}</tbody
              >
            </table>
          </div>{/if}
      </div>
    </main>
    <aside class="insights-panel" class:mobile-visible={mobile === 'insights'}>
      <Insights
        {data}
        {filters}
        vacancies={filtered}
        profile={personal}
        {lang}
        filtered={!isDefault(filters)}
        {applyTechnology}
        openRadar={() => {
          tab = 'radar';
          mobile = 'vacancies';
        }}
      />
    </aside>
  </div>
{/if}
<dialog
  bind:this={modal}
  oncancel={(e) => {
    e.preventDefault();
    closeModal();
  }}
  onclose={closeModal}
>
  {#if profileOpen}<Profile bind:personal {lang} onclose={closeModal} />{:else if selected}<Details
      vacancy={selected}
      bind:personal
      {lang}
      demo={data?.mode === 'demo'}
      onclose={closeModal}
    />{:else if compareOpen}<div class="modal-heading">
      <h2>{t('comparison')}</h2>
      <button onclick={closeModal}>{t('close')}</button>
    </div>
    <div class="compare-grid">
      {#each compare as id (id)}{@const v = data!.vacancies.find((v) => v.id === id)!}
        <section>
          <h3>{v.title}</h3>
          <p>{v.employer}</p>
          <p>{salaryText(v.salary, lang)}</p>
          <p>{t(v.experience)}</p>
          <p>{t('fit')}: {fit(v, personal).score ?? '—'}%</p>
          <p>{t('missingRequired')}: {fit(v, personal).missingRequired.join(', ') || '—'}</p>
          <p>{v.summary[lang]}</p>
          <button onclick={() => open(v)}>{t('details')}</button>
        </section>{/each}
    </div>{/if}
</dialog>
