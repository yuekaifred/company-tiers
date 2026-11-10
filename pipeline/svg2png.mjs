import { Resvg } from '@resvg/resvg-js'
import { readFileSync, writeFileSync } from 'node:fs'
const [src, out, size = '512'] = process.argv.slice(2)
const r = new Resvg(readFileSync(src), { fitTo: { mode: 'width', value: +size }, background: 'rgba(0,0,0,0)' })
writeFileSync(out, r.render().asPng())
