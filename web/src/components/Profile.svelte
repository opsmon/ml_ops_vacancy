<script lang="ts">
  import type { Lang, Personal } from '../lib/types';
  import { translate as tr } from '../lib/i18n';
  import { tokens } from '../lib/market';
  import { download, parsePersonal } from '../lib/storage';
  let {
    personal = $bindable(),
    lang,
    onclose,
  }: { personal: Personal; lang: Lang; onclose: () => void } = $props();
  const t = (key: string) => tr(lang, key);
  let skills = $state(personal.skills.join(', ')),
    learn = $state(personal.learn.join(', '));
  let levels = $state(
    Object.entries(personal.levels)
      .map(([k, v]) => k + ':' + v)
      .join('\n'),
  );
  let error = $state('');
  function save() {
    personal = {
      ...personal,
      skills: tokens(skills),
      learn: tokens(learn),
      levels: Object.fromEntries(
        levels
          .split('\n')
          .map((x) => x.split(':').map((s) => s.trim()))
          .filter((x) => x.length === 2),
      ),
    };
    onclose();
  }
  async function importFile(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    try {
      personal = parsePersonal(await file.text());
      skills = personal.skills.join(', ');
      learn = personal.learn.join(', ');
      levels = Object.entries(personal.levels)
        .map(([k, v]) => k + ':' + v)
        .join('\n');
      error = '';
    } catch {
      error = t('importError');
    }
  }
</script>

<div class="modal-heading">
  <h2>{t('personal')}</h2>
  <button onclick={onclose}>{t('close')}</button>
</div>
<p class="notice">{t('localOnly')}</p>
<form
  onsubmit={(e) => {
    e.preventDefault();
    save();
  }}
  class="profile-form"
>
  <label class="field">{t('mySkills')}<textarea rows="3" bind:value={skills}></textarea></label>
  <label class="field">{t('skillLevels')}<textarea rows="3" bind:value={levels}></textarea></label>
  <label class="field">{t('learning')}<input bind:value={learn} /></label>
  <div class="form-grid">
    <label class="field">{t('targetRoles')}<input bind:value={personal.targetRoles} /></label>
    <label class="field">{t('targetSeniority')}<input bind:value={personal.seniority} /></label>
    <label class="field"
      >{t('targetPay')}<input type="number" min="0" bind:value={personal.salary} /></label
    >
    <label class="field">{t('targetCurrency')}<input bind:value={personal.currency} /></label>
    <label class="field"
      >{t('targetTax')}<select bind:value={personal.gross}
        >{#each ['gross', 'net', 'unknown'] as value (value)}<option {value}>{t(value)}</option
          >{/each}</select
      ></label
    >
    <label class="field">{t('targetPeriod')}<input bind:value={personal.period} /></label>
    <label class="field"
      >{t('salaryMode')}<select bind:value={personal.salaryMode}
        >{#each ['MONTH', 'HOUR', 'SHIFT', 'SERVICE', 'FLY_IN_FLY_OUT', 'unknown'] as value (value)}<option
            {value}>{t(value)}</option
          >{/each}</select
      ></label
    >
    <label class="field"
      >{t('desiredWork')}<select bind:value={personal.arrangement}
        >{#each ['', 'REMOTE', 'HYBRID', 'ON_SITE', 'unknown'] as value (value)}<option {value}
            >{t(
              ({ REMOTE: 'remote', HYBRID: 'hybrid', ON_SITE: 'onsite' } as Record<string, string>)[
                value
              ] ||
                value ||
                'notSet',
            )}</option
          >{/each}</select
      ></label
    >
    <label class="field">{t('desiredLocation')}<input bind:value={personal.location} /></label>
  </div>
  <button class="primary">{t('save')}</button>
</form>
<hr />
<div class="toolbar">
  <button onclick={() => download('mlpops-personal.json', JSON.stringify(personal, null, 2))}
    >{t('backup')}</button
  ><label class="file-button"
    >{t('import')}<input type="file" accept="application/json,.json" onchange={importFile} /></label
  >
</div>
{#if error}<p role="alert">{error}</p>{/if}
