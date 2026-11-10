<script>
  import Zone from './Zone.svelte'

  let { label, color, items, onchange, onremove } = $props()
</script>

<div class="row">
  <div class="label" style:background={color}>{label}</div>
  <Zone {items} {onchange} {onremove} />
</div>

<style>
  .row {
    display: flex;
    min-height: calc(var(--tile) + 12px);
    border-bottom: 1px solid var(--line);
  }
  .row:last-child {
    border-bottom: 0;
  }
  .label {
    flex: none;
    width: calc(var(--tile) + 12px);
    display: grid;
    place-items: center;
    color: #111;
    font-size: 28px;
    font-weight: 700;
  }
  @media (max-width: 600px) {
    .label {
      width: 48px;
      font-size: 22px;
    }
  }
</style>
