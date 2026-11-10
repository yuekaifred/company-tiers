<script>
  let { company, size = 'var(--tile)', onremove = null } = $props()
  let failed = $state(false)
  const src = $derived(import.meta.env.BASE_URL + company.logo)
</script>

<div
  class="tile"
  class:dark={company.bg === 'dark'}
  style:--size={size}
  title={company.name}
  ondblclick={() => onremove?.(company.id)}
  role="img"
  aria-label={company.name}
>
  {#if failed}
    <span class="name">{company.name}</span>
  {:else}
    <img {src} alt={company.name} draggable="false" onerror={() => (failed = true)} />
  {/if}
  {#if onremove}
    <button
      class="x"
      aria-label="Remove {company.name}"
      onclick={() => onremove(company.id)}
    >
      <svg viewBox="0 0 10 10" width="10" height="10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2 2l6 6M8 2l-6 6" /></svg>
    </button>
  {/if}
</div>

<style>
  .tile {
    position: relative;
    width: var(--size);
    height: var(--size);
    flex: none;
    border-radius: 10px;
    background: #fff;
    color: #111;
    padding: 8%;
    display: grid;
    place-items: center;
    overflow: hidden;
    user-select: none;
    -webkit-user-select: none;
    -webkit-touch-callout: none;
  }
  .tile.dark {
    background: #1a1a1a;
    color: #eee;
  }
  img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    pointer-events: none;
  }
  .name {
    font-size: 11px;
    font-weight: 600;
    line-height: 1.15;
    text-align: center;
    word-break: break-word;
  }
  .x {
    position: absolute;
    top: 2px;
    right: 2px;
    width: 20px;
    height: 20px;
    padding: 0;
    border: 0;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.65);
    color: #fff;
    display: grid;
    place-items: center;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.12s;
  }
  .tile:hover .x,
  .x:focus-visible {
    opacity: 1;
  }
  @media (hover: none) {
    .x {
      opacity: 0.8;
    }
  }
</style>
