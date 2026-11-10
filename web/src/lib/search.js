const norm = (s) => s.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]/g, '')

export function index(companies) {
  return companies.map((c) => {
    const words = c.name.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean)
    return {
      c,
      name: norm(c.name),
      words,
      initials: words.map((w) => w[0]).join(''),
      id: c.id,
      category: norm(c.category),
    }
  })
}

function subsequence(q, s) {
  let i = 0
  for (const ch of s) if (ch === q[i]) i++
  return i === q.length
}

function score(e, q) {
  if (e.name === q || e.id === q) return 0
  if (e.name.startsWith(q) || e.id.startsWith(q)) return 1
  if (e.initials === q) return 1
  if (e.words.some((w) => w.startsWith(q))) return 2
  if (e.initials.startsWith(q) && q.length > 1) return 3
  if (e.name.includes(q) || e.id.includes(q)) return 4
  if (e.category.startsWith(q)) return 5
  if (q.length > 2 && subsequence(q, e.name)) return 6
  return -1
}

export function search(entries, query) {
  const q = norm(query)
  const sorted = (list) => list.sort((a, b) => a.c.name.localeCompare(b.c.name))
  if (!q) return sorted([...entries]).map((e) => e.c)
  return entries
    .map((e) => [score(e, q), e])
    .filter(([s]) => s >= 0)
    .sort(([a, x], [b, y]) => a - b || x.c.name.localeCompare(y.c.name))
    .map(([, e]) => e.c)
}
