<script>
  import TierRow from './lib/TierRow.svelte'
  import Zone from './lib/Zone.svelte'
  import Picker from './lib/Picker.svelte'

  const tiers = [
    { key: 'SS', color: '#ff5fa2' },
    { key: 'S', color: '#ff7f7f' },
    { key: 'A', color: '#ffbf7f' },
    { key: 'B', color: '#ffdf7f' },
    { key: 'C', color: '#ffff7f' },
    { key: 'D', color: '#bfff7f' },
    { key: 'F', color: '#7fffff' },
    { key: 'Z', color: '#bfbfbf' },
  ]
  const zones = [...tiers.map((t) => t.key), 'unranked']
  const empty = () => Object.fromEntries(zones.map((k) => [k, []]))

  let companies = $state.raw([])
  let error = $state('')
  let board = $state.raw(empty())
  let trash = $state.raw([])
  let picking = $state(false)
  let dark = $state(false)

  const placed = $derived(new Set(zones.flatMap((k) => board[k].map((c) => c.id))))

  $effect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
  })

  fetch(new URL('companies.json', new URL(import.meta.env.BASE_URL, location.href)))
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
    .then((data) => (companies = data))
    .catch(() => (error = 'Could not load companies.json'))

  const setZone = (key) => (items) => (board = { ...board, [key]: items })

  function add(company) {
    if (placed.has(company.id)) return
    board = { ...board, unranked: [...board.unranked, company] }
  }

  function remove(id) {
    board = Object.fromEntries(zones.map((k) => [k, board[k].filter((c) => c.id !== id)]))
  }

  function onTrash(items, type) {
    trash = type === 'finalize' ? [] : items
  }

  function reset() {
    board = empty()
  }

  function openPicker(e) {
    if (!e.target.closest('.item')) picking = true
  }
</script>

<main>
  <header>
    <h1>tiers.fredyang.com</h1>
    <div class="actions">
      <button class="btn" aria-label="Toggle theme" onclick={() => (dark = !dark)}>{dark ? '☀' : '☾'}</button>
      <button class="btn reset" onclick={reset}>Reset</button>
    </div>
  </header>
  {#if error}<p class="error">{error}</p>{/if}

  <section class="board">
    {#each tiers as t (t.key)}
      <TierRow label={t.key} color={t.color} items={board[t.key]} onchange={setZone(t.key)} onremove={remove} />
    {/each}
  </section>

  <div class="bottom">
    <section class="tray" onclick={openPicker} role="presentation">
      <div class="add">+ Add companies</div>
      <Zone items={board.unranked} onchange={setZone('unranked')} onremove={remove} />
    </section>

    <section class="trash" aria-label="Drop here to remove">
      <Zone items={trash} onchange={onTrash} ghost={false} class="trashzone">
        {#snippet empty()}
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6" />
          </svg>
        {/snippet}
      </Zone>
    </section>
  </div>

  <footer>This is basically all AI</footer>
</main>

{#if picking}
  <Picker {companies} {placed} onadd={add} onclose={() => (picking = false)} />
{/if}

<style>
  main {
    max-width: 1100px;
    margin: 0 auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  h1 {
    margin: 0;
    font-size: 22px;
  }
  .actions {
    display: flex;
    gap: 8px;
  }
  .btn {
    background: var(--panel-2);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 8px 14px;
    cursor: pointer;
  }
  .reset:hover {
    border-color: var(--danger);
    color: var(--danger);
  }
  footer {
    padding: 8px 0 4px;
    text-align: center;
    font-size: 13px;
    font-style: italic;
    color: var(--muted);
  }
  .error {
    margin: 0;
    color: var(--danger);
  }
  .board,
  .tray {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    overflow: hidden;
  }
  .bottom {
    display: flex;
    gap: 14px;
    align-items: stretch;
  }
  .tray {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    cursor: pointer;
  }
  .tray:hover {
    border-color: var(--accent);
  }
  .add {
    padding: 20px 14px 12px;
    font-size: 14px;
    color: var(--muted);
  }
  .tray:hover .add {
    color: var(--text);
  }
  .trash {
    flex: none;
    width: calc(var(--tile) + 24px);
    display: flex;
    border: 2px dashed var(--line);
    border-radius: 10px;
    color: var(--muted);
  }
  .trash:hover,
  .trash:has(:global(.item)) {
    border-color: var(--danger);
    color: var(--danger);
  }
  .trash :global(.trashzone .item) {
    display: none;
  }
</style>
