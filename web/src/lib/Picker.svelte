<script>
  import { untrack } from 'svelte'
  import Tile from './Tile.svelte'
  import { index, search } from './search.js'

  let { companies, placed, onadd, onclose } = $props()
  let query = $state('')
  let active = $state(0)
  let dialog
  let input
  let grid

  const entries = $derived(index(companies))
  const results = $derived(search(entries, query))

  $effect(() => {
    dialog.showModal()
    input.focus()
  })

  $effect(() => {
    results
    untrack(() => (active = firstFree(0, 1)))
  })

  $effect(() => {
    grid?.children[active]?.scrollIntoView({ block: 'nearest' })
  })

  function firstFree(from, step) {
    for (let i = from; i >= 0 && i < results.length; i += step) if (!placed.has(results[i].id)) return i
    return Math.max(0, Math.min(from, results.length - 1))
  }

  function columns() {
    return getComputedStyle(grid).gridTemplateColumns.split(' ').length
  }

  function pick(i) {
    const c = results[i]
    if (!c || placed.has(c.id)) return
    onadd(c)
    active = firstFree(i + 1, 1)
  }

  function onkeydown(e) {
    const n = results.length
    if (!n) return
    const moves = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: columns(), ArrowUp: -columns() }
    if (e.key === 'Enter') {
      e.preventDefault()
      pick(active)
    } else if (e.key in moves) {
      if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && query && input.selectionStart !== input.value.length) return
      e.preventDefault()
      const next = active + moves[e.key]
      if (next >= 0 && next < n) active = next
    }
  }
</script>

<dialog bind:this={dialog} onclose={onclose} onclick={(e) => e.target === dialog && dialog.close()}>
  <div class="box">
    <div class="hint">
      Enter to add ·
      <span class="arrows">
        {#each [180, 270, 90, 0] as deg (deg)}
          <svg viewBox="2 2 12 12" style:transform="rotate({deg}deg)"><path d="M3 8h10M9 4l4 4-4 4" /></svg>
        {/each}
      </span>
      to select
    </div>
    <div class="top">
      <input bind:this={input} type="search" placeholder="Search…" bind:value={query} {onkeydown} />
      <button class="close" aria-label="Close" onclick={() => dialog.close()}>×</button>
    </div>
    <div class="grid" bind:this={grid}>
      {#each results as c, i (c.id)}
        {@const added = placed.has(c.id)}
        <button
          class="co"
          class:added
          class:active={i === active}
          disabled={added}
          tabindex="-1"
          onmousemove={() => (active = i)}
          onclick={() => pick(i)}
        >
          <Tile company={c} size="56px" />
          <span>{c.name}</span>
        </button>
      {:else}
        <p class="none">No matches</p>
      {/each}
    </div>
  </div>
</dialog>

<style>
  dialog {
    width: min(760px, calc(100vw - 32px));
    height: min(640px, calc(100dvh - 64px));
    padding: 0;
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--panel);
    color: var(--text);
  }
  dialog::backdrop {
    background: rgba(0, 0, 0, 0.55);
  }
  .box {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 14px;
    height: 100%;
  }
  .hint {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-style: italic;
    color: var(--muted);
  }
  .arrows {
    display: inline-flex;
    gap: 0;
  }
  .arrows svg {
    width: 13px;
    height: 13px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.7;
    stroke-linecap: round;
    stroke-linejoin: round;
  }
  .top {
    display: flex;
    gap: 8px;
  }
  input {
    flex: 1;
    min-width: 0;
    background: var(--bg);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 9px 12px;
  }
  input:focus {
    outline: 2px solid var(--accent);
    outline-offset: -1px;
  }
  button {
    border: 0;
    background: none;
    cursor: pointer;
  }
  .close {
    width: 38px;
    font-size: 22px;
    border-radius: 8px;
  }
  .close:hover {
    background: var(--panel-2);
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
    gap: 0;
    align-content: start;
    flex: 1;
    overflow-y: auto;
    min-height: 0;
  }
  .co {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 8px 4px;
    border-radius: 0;
    font-size: 12px;
    text-align: center;
  }
  .co span {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .co.active {
    background: var(--panel-2);
    box-shadow: inset 0 0 0 2px var(--text);
  }
  .co.added {
    opacity: 0.3;
    cursor: default;
  }
  .none {
    grid-column: 1 / -1;
    color: var(--muted);
    text-align: center;
  }
</style>
