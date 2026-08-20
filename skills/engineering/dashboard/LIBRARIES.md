# Dashboard wiring

The stack, and the wiring that has already survived a review round. Reach for a library at
each job rather than hand-rolling it — hand-rolled `<rect>` strings and bespoke CSS bars are
what produce "no context to the numbers" feedback, because the axis, the grid, and the
tooltip are exactly the parts hand-rolling skips.

| Job | Library | Why this one |
|---|---|---|
| Query surface | [DataTables](https://datatables.net/) | Sort, filter, page, and export over one `<table>`; the open questions live here |
| Charts | [Chart.js](https://www.chartjs.org/docs/latest/) | Stacking, grid, legend, and tooltips are config; the best-trodden path, so the answer to any question about it is one search away |
| Diagrams | [Mermaid](https://mermaid.js.org/) | Routes and architecture from text; keep to one diagram showing how the parts reach the page |
| Components | [Tailwind](https://tailwindcss.com/) + [DaisyUI](https://daisyui.com/components/) | Semantic class names — `modal`, `stats`, `card`, `badge` — instead of long utility strings |
| Icons | [Lucide](https://lucide.dev/icons/) | ~1600 icons, ISC licensed, no attribution; one script tag swaps `data-lucide` attributes for SVG |

DaisyUI carries components at ~3.8M downloads a month with a high-quality doc corpus, and its
semantic classes cost a fraction of the tokens an equivalent utility string does — which is why
a generated page stays legible. Bootstrap is larger at ~25.6M, but adopting it means dropping
Tailwind rather than adding to it, so take it only on a page with no Tailwind in play. On icons,
Font Awesome Free is bigger at ~10.0M, and Lucide wins anyway: every icon is free, and the ISC
licence asks for no attribution line on the page.

Chart.js is the default because familiarity compounds: ~52M npm downloads a month against
~2.4M for Observable Plot, so both the model writing the page and the human reading it have
seen far more of it. Reach past it only for a job it cannot do — [ECharts](https://echarts.apache.org/)
for in-chart zoom and brushing, [uPlot](https://github.com/leeoniya/uPlot) past ~100k points,
[Observable Plot](https://observablehq.com/plot/) when a terse grammar-of-graphics spec is
worth the thinner corpus. Raw D3 is for a genuinely custom mark, never for a bar chart.

## Charts that carry their own context

Stacking, gridlines, real dates, and a tooltip naming every value are the four things feedback
asks for, and all four are options. Stack by setting `stacked` on both scales
([bar charts](https://www.chartjs.org/docs/latest/charts/bar.html)); name the values with a
`label` callback ([tooltip](https://www.chartjs.org/docs/latest/configuration/tooltip.html)):

```js
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: days,                                  // pre-formatted dates: "Aug 4", "Aug 5", …
    datasets: [
      {label: 'Business hours', data: bh, backgroundColor: '#93c5fd', stack: 's'},
      {label: 'After hours',    data: ah, backgroundColor: '#1e3a8a', stack: 's'},
    ],
  },
  options: {
    responsive: true,
    interaction: {mode: 'index', intersect: false},   // hovering anywhere in the column reports it
    scales: {
      x: {stacked: true, title: {display: true, text: 'Date'}},
      y: {stacked: true, grid: {display: true}, title: {display: true, text: 'Messages'}},
    },
    plugins: {
      tooltip: {callbacks: {
        title: (items) => fullDate(items[0].label),                        // "Mon 4 Aug 2026"
        label: (c) => `${c.dataset.label}: ${c.parsed.y.toLocaleString()}`,
        footer: (items) => `total ${items.reduce((s, i) => s + i.parsed.y, 0).toLocaleString()}`,
      }},
    },
  },
});
```

Feed pre-formatted date strings as `labels` and keep the default category scale — 🤔 a real
time scale pulls in a separate date-adapter file, which costs the single-file property for no
gain when there is one bar per day.

## Drill from row to detail

The row answers "which of these is loudest"; the modal answers "what is actually in it". Give
the modal a DataTable of the matching records, one column per metadata field ordered by how
often the field varies, and the totals for that subset above it — and a chart too when the
breakdown only reads for that one row. Widen any column holding a long identifier —
`columnDefs` with a `width`, plus `table-layout: fixed` — because an auto-sized table squeezes
the column the reader most needs.

DaisyUI's modal is a native `<dialog>`, so ESC and the backdrop close it with no JS of yours
([modal](https://daisyui.com/components/modal/)):

```html
<dialog id="fam-erd-7" class="modal">
  <div class="modal-box max-w-5xl">
    <h3 class="text-lg font-bold">dams-apps-direct-s3-file-delivery-prd</h3>
    <div class="stats shadow-sm my-4">
      <div class="stat">
        <div class="stat-title">Messages</div>
        <div class="stat-value">114</div>
        <div class="stat-desc">4 Aug – 20 Aug 2026</div>
      </div>
    </div>
    <canvas id="fam-erd-7-chart"></canvas>
    <table id="fam-erd-7-tbl" class="table table-zebra"></table>
    <div class="modal-action">
      <form method="dialog"><button class="btn">Close</button></form>
    </div>
  </div>
</dialog>
```

Build the table and chart on first open, not at page load — 🤔 a canvas inside a closed dialog
has no layout size, so a chart constructed early renders at zero width:

```js
const built = new Set();
document.querySelectorAll('tr[data-fam]').forEach((tr) => tr.addEventListener('click', () => {
  const id = tr.dataset.fam, dlg = document.getElementById(id);
  if (!built.has(id)) { buildTable(id); buildChart(id); built.add(id); }
  dlg.showModal();
}));
```

Stat tiles use the same component on the page itself — `stats` wrapping `stat`, with
`stat-title`, `stat-value`, and `stat-desc` carrying the label, the number, and its window
([stat](https://daisyui.com/components/stat/)).

Icons render from one call after the DOM is in place:

```html
<span data-lucide="triangle-alert" class="w-4 h-4"></span>
<script src="https://cdn.jsdelivr.net/npm/lucide@latest"></script>
<script>lucide.createIcons();</script>
```

## Self-contained, including the data

The shipped page opens from disk with no network, so inline the CSS and JS rather than pointing
at a CDN. For a payload past a megabyte, embed it gzipped and base64'd and inflate it in the
page with [`DecompressionStream`](https://developer.mozilla.org/en-US/docs/Web/API/DecompressionStream)
— 53 MB of JSON reached the browser as a 3.9 MB file this way. Inject the app script only once
the payload has landed, so nothing races it:

```python
b64 = base64.b64encode(gzip.compress(json.dumps(payload, separators=(',', ':')).encode(), 9)).decode()
```

```js
new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')))
  .text().then((t) => { window.DATA = JSON.parse(t); runApp(); });
```

Mermaid is the authoring format for the diagram, but **pre-render it to SVG at build time**
and paste that SVG into the page. A diagram rendered by the build cannot fail to render in the
reader's browser, which retires the whole "this doesn't render" failure on its own, and it
keeps the offline promise that a CDN import would break:

```bash
npx -y @mermaid-js/mermaid-cli -i routes.mmd -o routes.svg -t neutral -b transparent
```

Keep the runtime path only for a page you are iterating on locally, where re-running the build
per edit is the slower loop:

```html
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  mermaid.initialize({startOnLoad: true, theme: "neutral"});
</script>
```

## One control, many questions

A single filter wired to every number in a section answers a whole class of open questions at
once — a business-hours/after-hours toggle that re-filters counts, ordering, charts, and modals
together turns "does the ranking change at night?" into one click. Recompute every number from
the same filtered set, so a total and a chart can never disagree.
