<script>
  import { dndzone, SHADOW_ITEM_MARKER_PROPERTY_NAME } from 'svelte-dnd-action'
  import Tile from './Tile.svelte'

  let { items, onchange, onremove, empty, ghost = true, class: cls = '' } = $props()

  const handle = (e) => onchange(e.detail.items, e.type)
</script>

<div class="wrap {cls}">
  <div
    class="zone"
    use:dndzone={{ items, flipDurationMs: 0, useCursorForDetection: true, type: 'tile', dropTargetStyle: {}, delayTouchStartMs: 200 }}
    onconsider={handle}
    onfinalize={handle}
  >
    {#each items as item (item.id)}
      <div class="item" class:shadow={ghost && item[SHADOW_ITEM_MARKER_PROPERTY_NAME]}>
        <Tile company={item} {onremove} />
      </div>
    {/each}
  </div>
  {#if empty && !items.some((i) => !i[SHADOW_ITEM_MARKER_PROPERTY_NAME])}
    <div class="empty">{@render empty()}</div>
  {/if}
</div>

<style>
  .wrap {
    position: relative;
    flex: 1;
    min-width: 0;
  }
  .zone {
    display: flex;
    flex-wrap: wrap;
    align-content: flex-start;
    gap: 6px;
    padding: 6px;
    min-height: calc(var(--tile) + 12px);
    width: 100%;
    height: 100%;
  }
  .item {
    outline: none;
  }
  .item.shadow > :global(.tile) {
    visibility: visible;
    opacity: 0.35;
    outline: 2px dashed var(--accent);
    outline-offset: -2px;
  }
  .item.shadow :global(.x) {
    display: none;
  }
  .empty {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    color: var(--muted);
    font-size: 14px;
    pointer-events: none;
    padding: 0 12px;
    text-align: center;
  }
</style>
