<script lang="ts">
  import type { Dataset, Filters, Lang, Personal } from '../lib/types';
  import { translate as tr } from '../lib/i18n';
  import { defaults } from '../lib/market';
  let {
    filters = $bindable(),
    lang,
    data,
    personal = $bindable(),
    openProfile,
  }: {
    filters: Filters;
    lang: Lang;
    data: Dataset;
    personal: Personal;
    openProfile: () => void;
  } = $props();
  let presetName = $state('');
  const t = (key: string) => tr(lang, key);
  type Field = { key: keyof Filters; label: string; type?: string; options?: string[] };
  const groups: { name: string; fields: Field[] }[] = [
    {
      name: 'roles',
      fields: [
        { key: 'categories', label: 'category' },
        { key: 'minScore', label: 'minScore', type: 'number' },
        { key: 'maxScore', label: 'maxScore', type: 'number' },
        { key: 'scope', label: 'scope', options: ['full', 'title'] },
        { key: 'exclude', label: 'exclude' },
      ],
    },
    {
      name: 'stack',
      fields: [
        { key: 'tech', label: 'tech' },
        { key: 'techMode', label: 'techMode', options: ['ANY', 'ALL'] },
        { key: 'excludeTech', label: 'excludeTech' },
        {
          key: 'techCategory',
          label: 'techCategory',
          options: [
            '',
            'infrastructure',
            'observability',
            'lifecycle',
            'inference',
            'gpu',
            'data',
            'cloud',
          ],
        },
        {
          key: 'requirement',
          label: 'requirement',
          options: ['', 'required', 'preferred', 'mentioned', 'unclear'],
        },
        {
          key: 'flag',
          label: 'flag',
          options: [
            '',
            'gpu',
            'inference',
            'training',
            'llm',
            'kubernetes_ml',
            'transition',
            'junior',
            'research',
            'degree',
            'relocation',
            'travel',
            'oncall',
            'english',
          ],
        },
      ],
    },
    {
      name: 'experience',
      fields: [
        {
          key: 'experience',
          label: 'experience',
          options: ['', 'noExperience', 'between1And3', 'between3And6', 'moreThan6'],
        },
        { key: 'years', label: 'years' },
        {
          key: 'seniority',
          label: 'seniority',
          options: ['', 'junior', 'middle', 'senior', 'lead', 'unknown'],
        },
      ],
    },
    {
      name: 'compensation',
      fields: [
        { key: 'salaryOnly', label: 'salaryOnly', type: 'checkbox' },
        { key: 'minSalary', label: 'minSalary', type: 'number' },
        { key: 'maxSalary', label: 'maxSalary', type: 'number' },
        { key: 'currency', label: 'currency' },
        { key: 'tax', label: 'tax', options: ['', 'gross', 'net', 'unknown'] },
        {
          key: 'period',
          label: 'period',
          options: ['', 'DAILY', 'WEEKLY', 'TWICE_PER_MONTH', 'MONTHLY', 'PER_PROJECT', 'unknown'],
        },
        {
          key: 'salaryMode',
          label: 'salaryMode',
          options: ['', 'MONTH', 'HOUR', 'SHIFT', 'SERVICE', 'FLY_IN_FLY_OUT', 'unknown'],
        },
        { key: 'bound', label: 'bound', options: ['', 'lowerOnly', 'upperOnly', 'closedRange'] },
        { key: 'salaryChange', label: 'salaryChange', options: ['', 'increase', 'decrease'] },
      ],
    },
    {
      name: 'conditions',
      fields: [
        { key: 'location', label: 'location' },
        { key: 'country', label: 'country' },
        { key: 'region', label: 'region' },
        {
          key: 'arrangement',
          label: 'arrangement',
          options: ['', 'REMOTE', 'HYBRID', 'ON_SITE', 'unknown'],
        },
        { key: 'employment', label: 'employment', options: ['', 'FULL', 'unknown'] },
        { key: 'schedule', label: 'schedule', options: ['', 'unknown'] },
      ],
    },
    {
      name: 'employer',
      fields: [
        { key: 'employer', label: 'employer' },
        { key: 'excludeEmployer', label: 'excludeEmployer' },
        { key: 'employerType', label: 'employerType', options: ['', 'direct', 'agency'] },
        {
          key: 'employerActivity',
          label: 'employerActivity',
          options: ['', 'multiple', 'newEmployer'],
        },
      ],
    },
    {
      name: 'freshness',
      fields: [
        { key: 'published', label: 'published', options: ['', '1', '3', '7', '30'] },
        { key: 'publishedFrom', label: 'publishedFrom', type: 'date' },
        { key: 'publishedTo', label: 'publishedTo', type: 'date' },
        { key: 'discoveredFrom', label: 'discoveredFrom', type: 'date' },
        { key: 'discoveredTo', label: 'discoveredTo', type: 'date' },
        {
          key: 'lifecycle',
          label: 'lifecycle',
          options: ['', 'active', 'archived', 'inaccessible', 'unknown', 'notFoundLatest'],
        },
        {
          key: 'changed',
          label: 'changed',
          options: ['', 'updated', 'sinceVisit', 'salary', 'technologies', 'repost'],
        },
      ],
    },
    {
      name: 'personal',
      fields: [
        {
          key: 'workflow',
          label: 'workflow',
          options: [
            '',
            'hideViewed',
            'hideDismissed',
            'bookmarked',
            'interested',
            'applied',
            'interview',
            'offer',
            'rejected',
          ],
        },
        { key: 'minFit', label: 'minFit', type: 'number' },
        { key: 'maxMissing', label: 'maxMissing', type: 'number' },
        { key: 'targetSalary', label: 'targetSalary', type: 'checkbox' },
        { key: 'desiredArrangement', label: 'desiredArrangement', type: 'checkbox' },
      ],
    },
  ];
  function update(key: keyof Filters, value: string | boolean) {
    filters = { ...filters, [key]: value };
  }
  function option(value: string) {
    return value === ''
      ? t('allValues')
      : t(
          (
            {
              title: 'titleOnly',
              ANY: 'any',
              ALL: 'all',
              REMOTE: 'remote',
              HYBRID: 'hybrid',
              ON_SITE: 'onsite',
            } as Record<string, string>
          )[value] || (value === 'lifecycle' ? 'mlLifecycle' : value),
        );
  }
  function options(field: Field) {
    const name = (
      {
        experience: 'experience',
        arrangement: 'work_format',
        period: 'salary_range_frequency',
        salaryMode: 'salary_range_mode',
        employment: 'employment_form',
        schedule: 'schedule',
      } as Record<string, string>
    )[field.key];
    const source = data.dictionaries[name];
    return source?.length ? ['', ...source.map((x) => x.id), 'unknown'] : field.options || [];
  }
  function savePreset() {
    if (presetName.trim()) {
      personal = {
        ...personal,
        presets: [...personal.presets, { name: presetName.trim(), filters: { ...filters } }],
      };
      presetName = '';
    }
  }
</script>

<div class="panel-heading">
  <h2>{t('filters')}</h2>
  <button class="text-button" onclick={() => (filters = { ...defaults })}>{t('reset')}</button>
</div>
<label class="field"
  >{t('search')}<input
    type="search"
    value={filters.q}
    oninput={(e) => update('q', e.currentTarget.value)}
    placeholder={t('searchPlaceholder')}
  /></label
>
<button class="wide" onclick={openProfile}>{t('personal')} · {personal.skills.length}</button>
<div class="quick-presets">
  <button onclick={() => (filters = { ...defaults, categories: '1' })}>{t('category1')}</button>
  <button onclick={() => (filters = { ...defaults, flag: 'transition' })}>{t('transition')}</button>
  <button onclick={() => (filters = { ...defaults, tech: 'MLflow,ClearML,Kubeflow' })}
    >MLflow / ClearML / Kubeflow</button
  >
</div>
{#each groups as group (group.name)}
  <details open={group.name === 'stack'}>
    <summary>{t(group.name)}</summary>
    {#each group.fields as field (field.key)}
      <label class:check={field.type === 'checkbox'} class="field">
        {#if field.type === 'checkbox'}<input
            type="checkbox"
            checked={Boolean(filters[field.key])}
            onchange={(e) => update(field.key, e.currentTarget.checked)}
          />{t(field.label)}
        {:else}
          <span>{t(field.label)}</span>
          {#if field.options}
            <select
              aria-label={t(field.label)}
              value={String(filters[field.key])}
              onchange={(e) => update(field.key, e.currentTarget.value)}
            >
              {#each options(field) as value (value)}<option {value}>{option(value)}</option>{/each}
            </select>
          {:else}<input
              type={field.type || 'text'}
              value={String(filters[field.key])}
              min={field.type === 'number' ? 0 : undefined}
              oninput={(e) => update(field.key, e.currentTarget.value)}
              list={field.key === 'tech'
                ? 'taxonomy'
                : field.key === 'period'
                  ? 'periods'
                  : undefined}
            />{/if}
        {/if}
      </label>
    {/each}
    {#if group.name === 'roles'}<small>{t('categoriesHelp')}</small>{/if}
    {#if group.name === 'stack'}<small>{t('techHelp')}</small>{/if}
    {#if group.name === 'compensation'}<small>{t('salaryText')}</small>{/if}
  </details>
{/each}
<details>
  <summary>{t('presets')}</summary>
  {#each personal.presets as preset, index (index)}
    <div class="inline">
      <button onclick={() => (filters = { ...preset.filters })}>{preset.name}</button><button
        class="text-button"
        aria-label={t('delete') + ' ' + preset.name}
        onclick={() =>
          (personal = { ...personal, presets: personal.presets.filter((_, i) => i !== index) })}
        >×</button
      >
    </div>
  {/each}
  <form
    onsubmit={(e) => {
      e.preventDefault();
      savePreset();
    }}
  >
    <label class="field"
      >{t('presetName')}<input bind:value={presetName} maxlength="60" required /></label
    ><button>{t('savePreset')}</button>
  </form>
</details>
<datalist id="taxonomy"
  >{#each data.taxonomy as item (item.name)}<option value={item.name}></option>{/each}</datalist
>
<datalist id="periods"
  >{#each data.dictionaries.salary_range_frequency || [{ id: 'MONTHLY', name: 'MONTHLY' }] as item (item.id)}<option
      value={item.id}>{item.name}</option
    >{/each}</datalist
>
