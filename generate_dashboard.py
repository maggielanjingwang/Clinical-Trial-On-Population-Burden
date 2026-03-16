"""
generate_dashboard.py
Reads processed_data.json and generates a self-contained dashboard.html
with embedded data, React, Recharts, D3, and Tailwind CSS.
"""

import json

with open("processed_data.json") as f:
    DATA_JSON = json.dumps(json.load(f), separators=(",", ":"))

REACT_APP = r"""
// ─── Constants ───────────────────────────────────────────────────────────────
const RISK_FACTORS = [
  'Metabolic risks',
  'High systolic blood pressure',
  'High LDL cholesterol',
  'High body-mass index',
  'High fasting plasma glucose',
  'Kidney dysfunction'
];

const RF_COLORS = {
  'Metabolic risks':              '#4e79a7',
  'High systolic blood pressure': '#e15759',
  'High LDL cholesterol':         '#f28e2b',
  'High body-mass index':         '#76b7b2',
  'High fasting plasma glucose':  '#59a14f',
  'Kidney dysfunction':           '#b07aa1'
};

const RF_SHORT = {
  'Metabolic risks':              'Metabolic',
  'High systolic blood pressure': 'Blood Pressure',
  'High LDL cholesterol':         'LDL Cholesterol',
  'High body-mass index':         'BMI / Obesity',
  'High fasting plasma glucose':  'Blood Glucose',
  'Kidney dysfunction':           'Kidney'
};

const PHASE_COLORS = {
  'EARLY_PHASE1': '#93c5fd',
  'PHASE1':       '#3b82f6',
  'PHASE2':       '#1d4ed8',
  'PHASE3':       '#1e3a8a'
};
const PHASE_LABELS = {
  'EARLY_PHASE1': 'Early Ph.1',
  'PHASE1':       'Phase 1',
  'PHASE2':       'Phase 2',
  'PHASE3':       'Phase 3'
};

const SPONSOR_COLORS = {
  'Industry':         '#f59e0b',
  'Academic/Other':   '#6b7280',
  'Government/NIH':   '#10b981'
};

const INTERVENTION_COLORS = {
  'Pharmacologic':    '#7c3aed',
  'Behavioral':       '#0ea5e9',
  'Device':           '#f97316',
  'Lifestyle/Other':  '#84cc16'
};

const FIPS_TO_STATE = {
  '01':'Alabama','02':'Alaska','04':'Arizona','05':'Arkansas','06':'California',
  '08':'Colorado','09':'Connecticut','10':'Delaware','11':'District of Columbia',
  '12':'Florida','13':'Georgia','15':'Hawaii','16':'Idaho','17':'Illinois',
  '18':'Indiana','19':'Iowa','20':'Kansas','21':'Kentucky','22':'Louisiana',
  '23':'Maine','24':'Maryland','25':'Massachusetts','26':'Michigan','27':'Minnesota',
  '28':'Mississippi','29':'Missouri','30':'Montana','31':'Nebraska','32':'Nevada',
  '33':'New Hampshire','34':'New Jersey','35':'New Mexico','36':'New York',
  '37':'North Carolina','38':'North Dakota','39':'Ohio','40':'Oklahoma',
  '41':'Oregon','42':'Pennsylvania','44':'Rhode Island','45':'South Carolina',
  '46':'South Dakota','47':'Tennessee','48':'Texas','49':'Utah','50':'Vermont',
  '51':'Virginia','53':'Washington','54':'West Virginia','55':'Wisconsin','56':'Wyoming'
};

const { useState, useEffect, useRef, useMemo, useCallback } = React;
const {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell,
  ResponsiveContainer
} = Recharts;

// ─── Utility: format numbers ──────────────────────────────────────────────────
const fmt = n => n >= 1000 ? (n/1000).toFixed(1)+'K' : n.toFixed(0);
const pct = n => (n*100).toFixed(1)+'%';
const score2cls = s => s > 1.2 ? 'text-blue-600 font-semibold'
                     : s < 0.8 ? 'text-red-600 font-semibold'
                     : 'text-green-600 font-semibold';
const score2label = s => s > 1.2 ? 'Overstudied' : s < 0.8 ? 'Understudied' : 'Balanced';

// ─── Custom Tooltip ──────────────────────────────────────────────────────────
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      {label && <p className="font-medium text-gray-700 mb-1">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || p.fill || '#374151' }}>
          {p.name}: <span className="font-semibold">
            {typeof p.value === 'number' && p.value > 100
              ? p.value.toLocaleString()
              : typeof p.value === 'number'
              ? p.value.toFixed(1)
              : p.value}
          </span>
        </p>
      ))}
    </div>
  );
}

// ─── MODULE 1: Population Risk Landscape ─────────────────────────────────────
function ChoroplethMap({ stateData }) {
  const svgRef = useRef();
  const [tooltip, setTooltip] = useState(null);
  const [usGeo, setUsGeo] = useState(null);

  useEffect(() => {
    fetch('https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json')
      .then(r => r.json())
      .then(us => setUsGeo(us))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!usGeo || !svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth || 500;
    const height = 300;
    const projection = d3.geoAlbersUsa().fitSize([width, height],
      topojson.feature(usGeo, usGeo.objects.states));
    const path = d3.geoPath().projection(projection);

    const maxVal = d3.max(Object.values(stateData)) || 1;
    const colorScale = d3.scaleSequential(d3.interpolateBlues).domain([0, maxVal]);

    svg.selectAll('path')
      .data(topojson.feature(usGeo, usGeo.objects.states).features)
      .enter().append('path')
        .attr('d', path)
        .attr('fill', d => {
          const name = FIPS_TO_STATE[String(d.id).padStart(2,'0')];
          const val = stateData[name] || 0;
          return val > 0 ? colorScale(val) : '#e5e7eb';
        })
        .attr('stroke', '#fff')
        .attr('stroke-width', 0.5)
        .on('mouseover', function(event, d) {
          const name = FIPS_TO_STATE[String(d.id).padStart(2,'0')];
          const val = stateData[name] || 0;
          setTooltip({ name, val, x: event.offsetX, y: event.offsetY });
          d3.select(this).attr('stroke', '#374151').attr('stroke-width', 1.5);
        })
        .on('mouseout', function() {
          setTooltip(null);
          d3.select(this).attr('stroke', '#fff').attr('stroke-width', 0.5);
        });
  }, [usGeo, stateData]);

  return (
    <div className="relative">
      <svg ref={svgRef} style={{ width: '100%', height: 300 }} />
      {tooltip && (
        <div className="absolute bg-white border border-gray-200 rounded shadow-md p-2 text-xs pointer-events-none z-10"
             style={{ left: tooltip.x + 10, top: tooltip.y - 10 }}>
          <p className="font-semibold">{tooltip.name}</p>
          <p>{tooltip.val.toLocaleString(undefined, {maximumFractionDigits:0})} deaths</p>
        </div>
      )}
      {!usGeo && (
        <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
          Loading map…
        </div>
      )}
    </div>
  );
}

function RiskLandscape({ selectedFactors }) {
  const [choroplethFactor, setChoroplethFactor] = useState('All Factors');

  const gbd = useMemo(
    () => DATA.gbd_summary.filter(d => selectedFactors.has(d.risk_factor)),
    [selectedFactors]
  );

  const barData = gbd.map(d => ({
    name: RF_SHORT[d.risk_factor],
    Deaths: Math.round(d.death_val),
    fullName: d.risk_factor,
    pct: pct(d.burden_share)
  }));

  // Build state totals for choropleth
  const stateData = useMemo(() => {
    const factors = choroplethFactor === 'All Factors'
      ? [...selectedFactors]
      : [choroplethFactor];
    const out = {};
    DATA.gbd_by_state
      .filter(d => factors.includes(d.risk_factor))
      .forEach(d => { out[d.location_name] = (out[d.location_name] || 0) + d.death_val; });
    return out;
  }, [selectedFactors, choroplethFactor]);

  const factorOptions = ['All Factors', ...RISK_FACTORS.filter(f => selectedFactors.has(f))];

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-sm text-blue-800">
        <strong>Module 1 — Population Risk Landscape:</strong> Total CVD deaths
        attributable to each risk factor across U.S. states (IHME GBD 2023).
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Bar chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="font-semibold text-gray-700 mb-4">
            Attributable Deaths by Risk Factor (National)
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData} layout="vertical" margin={{left:10, right:30}}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tickFormatter={v => (v/1000).toFixed(0)+'K'} fontSize={11} />
              <YAxis type="category" dataKey="name" width={110} fontSize={11} />
              <Tooltip content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const d = payload[0].payload;
                return (
                  <div className="bg-white border border-gray-200 rounded-lg shadow p-3 text-sm">
                    <p className="font-semibold text-gray-800">{d.fullName}</p>
                    <p className="text-gray-600">Deaths: <strong>{d.Deaths.toLocaleString()}</strong></p>
                    <p className="text-gray-600">Burden share: <strong>{d.pct}</strong></p>
                  </div>
                );
              }} />
              <Bar dataKey="Deaths" name="Attributable Deaths" radius={[0,4,4,0]}>
                {barData.map((d, i) => (
                  <Cell key={i} fill={RF_COLORS[d.fullName]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Choropleth */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-700">State-Level CVD Burden</h3>
            <select
              value={choroplethFactor}
              onChange={e => setChoroplethFactor(e.target.value)}
              className="text-xs border border-gray-200 rounded px-2 py-1 focus:outline-none"
            >
              {factorOptions.map(f => (
                <option key={f} value={f}>{f === 'All Factors' ? 'All Factors' : RF_SHORT[f] || f}</option>
              ))}
            </select>
          </div>
          <ChoroplethMap stateData={stateData} />
          <p className="text-xs text-gray-400 mt-2 text-center">
            Darker = more attributable deaths · Hover for state values
          </p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {gbd.map(d => (
          <div key={d.risk_factor}
               className="bg-white rounded-lg border border-gray-100 p-3 flex items-start gap-3 shadow-sm">
            <div className="w-3 h-3 rounded-full mt-1 flex-shrink-0"
                 style={{ backgroundColor: RF_COLORS[d.risk_factor] }} />
            <div>
              <p className="text-xs text-gray-500">{RF_SHORT[d.risk_factor]}</p>
              <p className="font-bold text-gray-800">{Math.round(d.death_val/1000).toLocaleString()}K</p>
              <p className="text-xs text-gray-400">burden share {pct(d.burden_share)}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── MODULE 2: Clinical Research Pipeline ────────────────────────────────────
function TrialPipeline({ selectedFactors }) {
  const [groupBy, setGroupBy] = useState('phase');

  const rawData = useMemo(() => {
    const map = { phase: DATA.trials_by_phase, sponsor: DATA.trials_by_sponsor,
                  intervention: DATA.trials_by_intervention };
    return map[groupBy].filter(d => selectedFactors.has(d.risk_factor));
  }, [selectedFactors, groupBy]);

  const colorMap = { phase: PHASE_COLORS, sponsor: SPONSOR_COLORS, intervention: INTERVENTION_COLORS };
  const labelMap = {
    phase: PHASE_LABELS,
    sponsor: Object.fromEntries(['Industry','Academic/Other','Government/NIH'].map(s => [s,s])),
    intervention: Object.fromEntries(['Pharmacologic','Behavioral','Device','Lifestyle/Other'].map(s => [s,s]))
  };

  // Pivot data: one row per risk_factor, columns = groupBy values
  const groups = [...new Set(rawData.map(d => d[groupBy] || d.phase || d.sponsor_type || d.intervention_type))];
  const pivoted = useMemo(() => {
    const map = {};
    rawData.forEach(d => {
      const rf = d.risk_factor;
      const grp = d[groupBy] || d.phase || d.sponsor_type || d.intervention_type;
      if (!map[rf]) map[rf] = { name: RF_SHORT[rf], fullName: rf };
      map[rf][grp] = (map[rf][grp] || 0) + d.count;
    });
    return Object.values(map).sort((a,b) => {
      const total = x => Object.entries(x).filter(([k])=>k!=='name'&&k!=='fullName').reduce((s,[,v])=>s+v,0);
      return total(b) - total(a);
    });
  }, [rawData, groupBy]);

  const colors = colorMap[groupBy];
  const labels = labelMap[groupBy];

  // Time trend data
  const trendData = useMemo(() => {
    const byYear = {};
    DATA.trials_by_year
      .filter(d => selectedFactors.has(d.risk_factor))
      .forEach(d => {
        if (!byYear[d.year]) byYear[d.year] = { year: d.year };
        byYear[d.year][RF_SHORT[d.risk_factor]] = (byYear[d.year][RF_SHORT[d.risk_factor]] || 0) + d.count;
      });
    return Object.values(byYear).sort((a,b) => a.year - b.year);
  }, [selectedFactors]);

  const rfKeys = RISK_FACTORS.filter(f => selectedFactors.has(f)).map(f => RF_SHORT[f]);

  const tabs = [
    { key: 'phase', label: 'By Phase' },
    { key: 'sponsor', label: 'By Sponsor' },
    { key: 'intervention', label: 'By Intervention' }
  ];

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-sm text-blue-800">
        <strong>Module 2 — Clinical Research Pipeline:</strong> Distribution of
        completed CVD interventional trials (2020–present) across risk factors.
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit">
        {tabs.map(t => (
          <button key={t.key}
            onClick={() => setGroupBy(t.key)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all
              ${groupBy === t.key ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Stacked bar chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="font-semibold text-gray-700 mb-4">
            Trial Count {groupBy === 'phase' ? 'by Phase' : groupBy === 'sponsor' ? 'by Sponsor' : 'by Intervention Type'}
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={pivoted} layout="vertical" margin={{left:10, right:20}}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" fontSize={11} />
              <YAxis type="category" dataKey="name" width={110} fontSize={11} />
              <Tooltip content={<ChartTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {Object.keys(colors).map(grp => (
                <Bar key={grp} dataKey={grp} name={labels[grp] || grp}
                     stackId="a" fill={colors[grp]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Time trend */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="font-semibold text-gray-700 mb-4">Trial Start Year Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trendData} margin={{left:5, right:10}}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" fontSize={11} />
              <YAxis fontSize={11} />
              <Tooltip content={<ChartTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {rfKeys.map(rf => (
                <Bar key={rf} dataKey={rf} stackId="b"
                     fill={RF_COLORS[Object.keys(RF_SHORT).find(k => RF_SHORT[k] === rf)] || '#888'} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary stats */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h3 className="font-semibold text-gray-700 mb-3">Trial Count Summary</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-2 pr-4 font-medium text-gray-500">Risk Factor</th>
                <th className="text-right py-2 pr-4 font-medium text-gray-500">Trials</th>
                <th className="text-right py-2 pr-4 font-medium text-gray-500">Trial Share</th>
                <th className="text-right py-2 font-medium text-gray-500">Burden Share</th>
              </tr>
            </thead>
            <tbody>
              {DATA.alignment
                .filter(d => selectedFactors.has(d.risk_factor))
                .sort((a,b) => b.trial_count - a.trial_count)
                .map(d => (
                  <tr key={d.risk_factor} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 pr-4 flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full inline-block"
                            style={{backgroundColor: RF_COLORS[d.risk_factor]}} />
                      {RF_SHORT[d.risk_factor]}
                    </td>
                    <td className="text-right py-2 pr-4 font-semibold">{d.trial_count}</td>
                    <td className="text-right py-2 pr-4">{pct(d.trial_share)}</td>
                    <td className="text-right py-2">{pct(d.burden_share)}</td>
                  </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── MODULE 3: Risk Factor Flow ───────────────────────────────────────────────
function RiskFlowSankey({ selectedFactors }) {
  const containerRef = useRef();
  const svgRef = useRef();
  const [tooltip, setTooltip] = useState(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const data = DATA.alignment
      .filter(d => selectedFactors.has(d.risk_factor))
      .sort((a, b) => b.death_val - a.death_val);
    if (!data.length) return;

    const W = containerRef.current.clientWidth || 760;
    const n = data.length;

    const HEADER_H = 44;
    const LEGEND_H = 38;
    const SLOT_H   = 54;
    const SLOT_GAP = 10;
    const CHART_H  = n * SLOT_H + (n - 1) * SLOT_GAP;
    const H = HEADER_H + CHART_H + LEGEND_H + 16;
    svg.attr('height', H);

    const NODE_W  = 14;
    const LABEL_W = 112;
    const RIGHT_MARGIN = 100;  // enough room for "CVD Burden" label above node

    const col1X = LABEL_W + 8;                          // trial nodes
    const col3X = W - NODE_W - RIGHT_MARGIN;             // CVD node
    const col2X = col1X + (col3X - col1X) * 0.46;       // death nodes

    const totalDeaths = d3.sum(data, d => d.death_val);
    const maxTrial    = d3.max(data, d => d.trial_count);
    const maxDeath    = d3.max(data, d => d.death_val);
    const nodeH1 = d => Math.max(5, (d.trial_count / maxTrial) * (SLOT_H - 10));
    const nodeH2 = d => Math.max(5, (d.death_val  / maxDeath)  * (SLOT_H - 10));
    const slotCY = i => HEADER_H + i * (SLOT_H + SLOT_GAP) + SLOT_H / 2;

    // CVD node layout — stacked slices per RF, proportional to death_val
    const cvdNodeH = CHART_H * 0.82;
    const cvdTop   = HEADER_H + (CHART_H - cvdNodeH) / 2;
    let cvdAccum = 0;
    const cvdSlices = data.map(d => {
      const h   = (d.death_val / totalDeaths) * cvdNodeH;
      const top = cvdTop + cvdAccum;
      cvdAccum += h;
      return { top, bot: top + h };
    });

    const alignColor = score =>
      score > 1.2 ? '#3b82f6' : score < 0.8 ? '#f97316' : '#10b981';

    // Filled Sankey band between two vertical segments
    const band = (x1, t1, b1, x2, t2, b2) => {
      const cx = (x1 + x2) / 2;
      return `M${x1},${t1} C${cx},${t1} ${cx},${t2} ${x2},${t2}` +
             ` L${x2},${b2} C${cx},${b2} ${cx},${b1} ${x1},${b1} Z`;
    };

    // ── Column headers ──
    [
      { x: col1X + NODE_W / 2, t: 'TRIAL COUNT' },
      { x: col2X + NODE_W / 2, t: 'GBD DEATHS'  },
      { x: col3X + NODE_W / 2, t: 'TOTAL CVD'   },
    ].forEach(h =>
      svg.append('text')
        .attr('x', h.x).attr('y', HEADER_H - 10)
        .attr('text-anchor', 'middle')
        .attr('font-size', 10).attr('font-weight', '700').attr('fill', '#9ca3af')
        .text(h.t)
    );

    // ── CVD node (drawn first so bands overlap it cleanly) ──
    svg.append('rect')
      .attr('x', col3X).attr('y', cvdTop)
      .attr('width', NODE_W).attr('height', cvdNodeH)
      .attr('fill', '#1e40af').attr('rx', 3);
    // Label ABOVE the node, centered
    svg.append('text')
      .attr('x', col3X + NODE_W / 2).attr('y', cvdTop - 6)
      .attr('text-anchor', 'middle')
      .attr('font-size', 10).attr('font-weight', '700').attr('fill', '#1e40af')
      .text('CVD Burden');

    // ── col2 → col3 Sankey bands (behind col2 nodes) ──
    data.forEach((d, i) => {
      const cy  = slotCY(i);
      const nh2 = nodeH2(d);
      svg.append('path')
        .attr('d', band(col2X + NODE_W, cy - nh2/2, cy + nh2/2,
                        col3X, cvdSlices[i].top, cvdSlices[i].bot))
        .attr('fill', RF_COLORS[d.risk_factor]).attr('opacity', 0.22)
        .style('pointer-events', 'none');
    });

    // ── col1 → col2 alignment bands ──
    data.forEach((d, i) => {
      const cy   = slotCY(i);
      const nh1  = nodeH1(d);
      const nh2  = nodeH2(d);
      const color = alignColor(d.alignment_score);
      const cpX   = (col1X + NODE_W + col2X) / 2;

      svg.append('path')
        .attr('d', band(col1X + NODE_W, cy - nh1/2, cy + nh1/2,
                        col2X, cy - nh2/2, cy + nh2/2))
        .attr('fill', color).attr('opacity', 0.38)
        .style('cursor', 'pointer')
        .on('mouseover', e => setTooltip({ x: e.clientX, y: e.clientY, d }))
        .on('mouseout',  () => setTooltip(null));

      // Score label centred on the band
      svg.append('text')
        .attr('x', cpX).attr('y', cy + 4)
        .attr('text-anchor', 'middle').attr('font-size', 9)
        .attr('fill', color).attr('font-weight', '700')
        .style('pointer-events', 'none')
        .text(d.alignment_score.toFixed(2) + '\u00d7');
    });

    // ── col1 and col2 nodes (drawn on top of bands) ──
    data.forEach((d, i) => {
      const cy   = slotCY(i);
      const nh1  = nodeH1(d);
      const nh2  = nodeH2(d);
      const color = RF_COLORS[d.risk_factor];

      // col1 node
      svg.append('rect')
        .attr('x', col1X).attr('y', cy - nh1/2)
        .attr('width', NODE_W).attr('height', nh1)
        .attr('fill', color).attr('rx', 3)
        .style('cursor', 'pointer')
        .on('mouseover', e => setTooltip({ x: e.clientX, y: e.clientY, d }))
        .on('mouseout',  () => setTooltip(null));

      // RF label left of col1
      svg.append('text')
        .attr('x', col1X - 8).attr('y', cy + 4)
        .attr('text-anchor', 'end').attr('font-size', 11).attr('fill', '#374151')
        .text(RF_SHORT[d.risk_factor]);

      // col1 value label (below node)
      svg.append('text')
        .attr('x', col1X + NODE_W/2).attr('y', cy + nh1/2 + 11)
        .attr('text-anchor', 'middle').attr('font-size', 9).attr('fill', '#9ca3af')
        .style('pointer-events', 'none').text(d.trial_count);

      // col2 node
      svg.append('rect')
        .attr('x', col2X).attr('y', cy - nh2/2)
        .attr('width', NODE_W).attr('height', nh2)
        .attr('fill', color).attr('rx', 3)
        .style('cursor', 'pointer')
        .on('mouseover', e => setTooltip({ x: e.clientX, y: e.clientY, d }))
        .on('mouseout',  () => setTooltip(null));

      // col2 value label (below node)
      svg.append('text')
        .attr('x', col2X + NODE_W/2).attr('y', cy + nh2/2 + 11)
        .attr('text-anchor', 'middle').attr('font-size', 9).attr('fill', '#9ca3af')
        .style('pointer-events', 'none')
        .text(Math.round(d.death_val / 1000) + 'K');
    });

    // ── Legend ──
    const legItems = [
      { color: '#3b82f6', label: 'Overstudied (> 1.2\u00d7)' },
      { color: '#10b981', label: 'Balanced (0.8\u20131.2\u00d7)' },
      { color: '#f97316', label: 'Understudied (< 0.8\u00d7)' },
    ];
    const legY     = H - 12;
    const legItemW = Math.min(190, (col3X - col1X) / 3);
    legItems.forEach((l, i) => {
      const lx = col1X + i * legItemW;
      svg.append('rect')
        .attr('x', lx).attr('y', legY - 9).attr('width', 18).attr('height', 11)
        .attr('fill', l.color).attr('opacity', 0.6).attr('rx', 2);
      svg.append('text')
        .attr('x', lx + 24).attr('y', legY)
        .attr('font-size', 10).attr('fill', '#6b7280').text(l.label);
    });

  }, [selectedFactors]);

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-sm text-blue-800">
        <strong>Module 3 — Risk Factor Flow:</strong> Sankey-style flow from trial counts (left)
        to GBD attributable deaths (center) to total CVD burden (right). Band color shows
        alignment between research effort and disease burden —{' '}
        <span style={{color:'#3b82f6',fontWeight:600}}>blue = overstudied</span>,{' '}
        <span style={{color:'#10b981',fontWeight:600}}>green = balanced</span>,{' '}
        <span style={{color:'#f97316',fontWeight:600}}>orange = understudied</span>.
        Score = trial share ÷ burden share. Hover nodes or bands for details.
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 relative" ref={containerRef}>
        <h3 className="font-semibold text-gray-700 mb-1">
          Trial Count → GBD Deaths → Total CVD Burden
        </h3>
        <p className="text-xs text-gray-400 mb-3">
          Node height ∝ magnitude · Band color = alignment · Score label = trial share ÷ burden share
        </p>
        <svg ref={svgRef} style={{ width: '100%', display: 'block' }} />
        {tooltip && (
          <div className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-xs pointer-events-none"
               style={{ left: tooltip.x + 14, top: tooltip.y - 10 }}>
            <p className="font-semibold text-gray-800 mb-1">{tooltip.d.risk_factor}</p>
            <p className="text-gray-500">Trial count: <strong>{tooltip.d.trial_count}</strong></p>
            <p className="text-gray-500">Trial share: <strong>{pct(tooltip.d.trial_share)}</strong></p>
            <p className="text-gray-500">GBD deaths: <strong>{Math.round(tooltip.d.death_val).toLocaleString()}</strong></p>
            <p className="text-gray-500">Burden share: <strong>{pct(tooltip.d.burden_share)}</strong></p>
            <p className="text-gray-500">Alignment: <strong>{tooltip.d.alignment_score.toFixed(2)}&times;</strong></p>
            <p className={`mt-1 font-medium ${score2cls(tooltip.d.alignment_score)}`}>
              {score2label(tooltip.d.alignment_score)}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── MODULE 4: Alignment Analysis ────────────────────────────────────────────
function AlignmentScatter({ selectedFactors }) {
  const svgRef = useRef();
  const [tooltip, setTooltip] = useState(null);
  const [hovered, setHovered] = useState(null);

  const data = useMemo(
    () => DATA.alignment.filter(d => selectedFactors.has(d.risk_factor)),
    [selectedFactors]
  );

  const W = 480, H = 380;
  const pad = { top: 40, right: 40, bottom: 60, left: 64 };
  const innerW = W - pad.left - pad.right;
  const innerH = H - pad.top - pad.bottom;

  const maxVal = 0.5;
  const xScale = v => (v / maxVal) * innerW;
  const yScale = v => innerH - (v / maxVal) * innerH;

  // Axis ticks
  const ticks = [0, 0.1, 0.2, 0.3, 0.4, 0.5];

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-sm text-blue-800">
        <strong>Module 4 — Alignment Analysis:</strong> Points on the 45° line indicate
        perfect alignment between disease burden and research attention.
        Points below = understudied; points above = overstudied.
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        {/* Scatter plot */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="font-semibold text-gray-700 mb-4">
            Burden Share vs. Trial Share
          </h3>
          <div className="relative" style={{ width: W, maxWidth: '100%' }}>
            <svg width={W} height={H} style={{ overflow: 'visible' }}>
              <g transform={`translate(${pad.left},${pad.top})`}>
                {/* Background regions */}
                {/* lower-right triangle: high burden, low trials = Understudied = red */}
                <polygon
                  points={`0,${yScale(0)} ${xScale(maxVal)},${yScale(maxVal)} ${xScale(maxVal)},${yScale(0)}`}
                  fill="#fef2f2" opacity="0.6"
                />
                {/* upper-left triangle: low burden, high trials = Overstudied = blue */}
                <polygon
                  points={`0,${yScale(0)} 0,${yScale(maxVal)} ${xScale(maxVal)},${yScale(maxVal)}`}
                  fill="#eff6ff" opacity="0.6"
                />

                {/* Grid */}
                {ticks.map(t => (
                  <g key={t}>
                    <line x1={xScale(t)} y1={0} x2={xScale(t)} y2={innerH}
                          stroke="#e5e7eb" strokeWidth={0.5} />
                    <line x1={0} y1={yScale(t)} x2={innerW} y2={yScale(t)}
                          stroke="#e5e7eb" strokeWidth={0.5} />
                  </g>
                ))}

                {/* 45° reference line */}
                <line x1={xScale(0)} y1={yScale(0)} x2={xScale(maxVal)} y2={yScale(maxVal)}
                      stroke="#6b7280" strokeDasharray="7 4" strokeWidth={1.5} />

                {/* Region labels */}
                {/* upper-left = low burden, high trials = Overstudied */}
                <text x={xScale(0.08)} y={yScale(0.38)} fontSize={10} fill="#3b82f6" opacity={0.7}
                      textAnchor="middle">Overstudied ↑</text>
                {/* lower-right = high burden, low trials = Understudied */}
                <text x={xScale(0.35)} y={yScale(0.04)} fontSize={10} fill="#ef4444" opacity={0.7}
                      textAnchor="middle">Understudied ↓</text>

                {/* Data points */}
                {data.map(d => {
                  const cx = xScale(d.burden_share);
                  const cy = yScale(d.trial_share);
                  const isHovered = hovered === d.risk_factor;
                  const color = RF_COLORS[d.risk_factor];
                  return (
                    <g key={d.risk_factor}
                       style={{ cursor: 'pointer' }}
                       onMouseEnter={e => { setHovered(d.risk_factor); setTooltip({ x: e.clientX, y: e.clientY, d }); }}
                       onMouseLeave={() => { setHovered(null); setTooltip(null); }}>
                      <circle cx={cx} cy={cy} r={isHovered ? 11 : 8}
                              fill={color} stroke="white" strokeWidth={2}
                              style={{ transition: 'r 0.15s' }} />
                      <text x={cx + 12} y={cy + 4} fontSize={10} fill="#374151"
                            style={{ pointerEvents: 'none' }}>
                        {RF_SHORT[d.risk_factor]}
                      </text>
                    </g>
                  );
                })}

                {/* X axis */}
                <line x1={0} y1={innerH} x2={innerW} y2={innerH} stroke="#9ca3af" />
                {ticks.map(t => (
                  <g key={t} transform={`translate(${xScale(t)},${innerH})`}>
                    <line y2={5} stroke="#9ca3af" />
                    <text y={16} textAnchor="middle" fontSize={10} fill="#6b7280">
                      {(t*100).toFixed(0)}%
                    </text>
                  </g>
                ))}
                <text x={innerW/2} y={innerH+40} textAnchor="middle" fontSize={12} fill="#374151">
                  Disease Burden Share (%)
                </text>

                {/* Y axis */}
                <line x1={0} y1={0} x2={0} y2={innerH} stroke="#9ca3af" />
                {ticks.map(t => (
                  <g key={t} transform={`translate(0,${yScale(t)})`}>
                    <line x2={-5} stroke="#9ca3af" />
                    <text x={-8} dy="0.35em" textAnchor="end" fontSize={10} fill="#6b7280">
                      {(t*100).toFixed(0)}%
                    </text>
                  </g>
                ))}
                <text transform={`translate(-48,${innerH/2})rotate(-90)`}
                      textAnchor="middle" fontSize={12} fill="#374151">
                  Trial Share (%)
                </text>

                {/* Perfect alignment label */}
                <text x={xScale(0.25)} y={yScale(0.27)} fontSize={9} fill="#6b7280"
                      transform={`rotate(-42,${xScale(0.25)},${yScale(0.27)})`}>
                  Perfect alignment
                </text>
              </g>
            </svg>

            {/* Floating tooltip */}
            {tooltip && (
              <div className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-xs pointer-events-none"
                   style={{ left: tooltip.x + 14, top: tooltip.y - 10 }}>
                <p className="font-semibold text-gray-800 mb-1">{tooltip.d.risk_factor}</p>
                <p className="text-gray-500">Burden share: <strong>{pct(tooltip.d.burden_share)}</strong></p>
                <p className="text-gray-500">Trial share: <strong>{pct(tooltip.d.trial_share)}</strong></p>
                <p className="text-gray-500">Alignment score: <strong>{tooltip.d.alignment_score?.toFixed(2)}</strong></p>
                <p className={`mt-1 font-medium ${score2cls(tooltip.d.alignment_score)}`}>
                  {score2label(tooltip.d.alignment_score)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right panel: alignment table + correlation */}
        <div className="space-y-4">
          {/* Alignment table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h3 className="font-semibold text-gray-700 mb-3">Alignment Scores</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-left">
                  <th className="py-1.5 pr-3 text-xs font-medium text-gray-500">Risk Factor</th>
                  <th className="py-1.5 pr-3 text-xs font-medium text-gray-500 text-right">Score</th>
                  <th className="py-1.5 text-xs font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.sort((a,b) => b.alignment_score - a.alignment_score).map(d => (
                  <tr key={d.risk_factor}
                      className={`border-b border-gray-50 transition-colors ${hovered===d.risk_factor ? 'bg-gray-50' : ''}`}
                      onMouseEnter={() => setHovered(d.risk_factor)}
                      onMouseLeave={() => setHovered(null)}>
                    <td className="py-2 pr-3 flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                            style={{ backgroundColor: RF_COLORS[d.risk_factor] }} />
                      <span className="text-xs text-gray-700">{RF_SHORT[d.risk_factor]}</span>
                    </td>
                    <td className="py-2 pr-3 text-right font-bold text-gray-800">
                      {d.alignment_score?.toFixed(2)}
                    </td>
                    <td className={`py-2 text-xs font-medium ${score2cls(d.alignment_score)}`}>
                      {score2label(d.alignment_score)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Priority gap table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h3 className="font-semibold text-gray-700 mb-3">Research Priority Gaps</h3>
            <p className="text-xs text-gray-400 mb-3">
              Positive gap = disease burden exceeds research attention
            </p>
            {data.sort((a,b) => b.priority_gap - a.priority_gap).map(d => (
              <div key={d.risk_factor} className="mb-2">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>{RF_SHORT[d.risk_factor]}</span>
                  <span className={d.priority_gap > 0.01 ? 'text-red-500 font-medium' :
                                   d.priority_gap < -0.01 ? 'text-blue-500 font-medium' : 'text-green-500 font-medium'}>
                    {d.priority_gap > 0 ? '+' : ''}{(d.priority_gap*100).toFixed(1)}pp
                  </span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all"
                       style={{
                         width: `${Math.min(100, Math.abs(d.priority_gap) * 200)}%`,
                         backgroundColor: d.priority_gap > 0.01 ? '#ef4444' :
                                          d.priority_gap < -0.01 ? '#3b82f6' : '#22c55e',
                         marginLeft: d.priority_gap < 0 ? 'auto' : undefined
                       }} />
                </div>
              </div>
            ))}
          </div>

          {/* Correlation card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
            <h3 className="font-semibold text-gray-700 mb-3">Spearman Correlation</h3>
            <p className="text-xs text-gray-500 mb-3">
              Trial count vs. attributable deaths across risk factors
            </p>
            <div className="flex items-center gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-600">{DATA.correlation.spearman_rho.toFixed(2)}</p>
                <p className="text-xs text-gray-400 mt-1">ρ (rho)</p>
              </div>
              <div className="flex-1 text-sm">
                <p className="text-gray-600 mb-1">p = {DATA.correlation.p_value.toFixed(3)}</p>
                <p className="text-gray-500 text-xs">{DATA.correlation.interpretation}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Introduction Page ────────────────────────────────────────────────────────
function IntroPage({ onStart }) {
  const totalDeaths = DATA.gbd_summary.reduce((s, d) => s + d.death_val, 0);
  const totalMappings = DATA.alignment.reduce((s, d) => s + d.trial_count, 0);
  const rfCount = DATA.gbd_summary.length;

  const moduleInfo = [
    {
      num: 1,
      title: 'Population Risk Landscape',
      desc: 'CVD attributable deaths per risk factor across all 50 U.S. states. Interactive choropleth map and national burden rankings using IHME GBD 2023 data.',
    },
    {
      num: 2,
      title: 'Clinical Research Pipeline',
      desc: 'Distribution of completed interventional trials (2020–present) by phase, sponsor type, and intervention category.',
    },
    {
      num: 3,
      title: 'Risk Factor Flow',
      desc: 'Sankey diagram tracing the flow from intervention type to risk factor to total CVD burden, revealing research concentration patterns.',
    },
    {
      num: 4,
      title: 'Alignment Analysis',
      desc: 'Burden share vs. trial share scatter plot and alignment scores — identifying which risk factors are understudied or overstudied relative to their disease impact.',
    },
  ];

  return (
    <div className="max-w-4xl mx-auto py-10">

      {/* Hero */}
      <div className="text-center mb-10">
        <span className="inline-block bg-blue-100 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full mb-4 uppercase tracking-wide">
          UW Biomedical Informatics · 2025
        </span>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          CVD Research Alignment Dashboard
        </h2>
        <p className="text-base text-gray-600 max-w-2xl mx-auto leading-relaxed">
          Are clinical trials investigating the risk factors that cause the most cardiovascular deaths?
          This platform compares U.S. CVD disease burden against the clinical research pipeline
          to identify where research effort is aligned — and where gaps remain.
        </p>
      </div>

      {/* Key stats */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        {[
          { value: Math.round(totalDeaths / 1000).toLocaleString() + 'K', label: 'CVD Attributable Deaths / Year', sub: '6 cardiometabolic risk factors' },
          { value: rfCount,          label: 'Risk Factors Analyzed',     sub: 'IHME GBD 2023' },
          { value: totalMappings,    label: 'Trial–Risk Mappings',        sub: 'ClinicalTrials.gov 2020–present' },
        ].map((s, i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 text-center">
            <p className="text-3xl font-bold text-blue-700">{s.value}</p>
            <p className="text-sm text-gray-600 mt-1 font-medium">{s.label}</p>
            <p className="text-xs text-gray-400 mt-0.5">{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Background */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl p-6 mb-8">
        <h3 className="font-semibold text-blue-900 mb-2">Background & Motivation</h3>
        <p className="text-blue-800 text-sm leading-relaxed">
          Cardiovascular disease (CVD) remains the leading cause of death in the United States,
          with multiple distinct risk factors — from high blood pressure to metabolic syndrome —
          contributing differently across states and populations. Yet clinical research funding and
          trial activity may not be proportional to this burden. Using the IHME Global Burden of
          Disease 2023 dataset alongside completed interventional trial data from ClinicalTrials.gov,
          this dashboard quantifies the alignment between population-level CVD risk factor burden
          and the clinical research response, surfacing potential gaps in research priority.
        </p>
      </div>

      {/* Module cards */}
      <h3 className="font-semibold text-gray-700 mb-3 text-sm uppercase tracking-wide">Dashboard Modules</h3>
      <div className="grid grid-cols-2 gap-4 mb-10">
        {moduleInfo.map(m => (
          <div
            key={m.num}
            className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 cursor-pointer hover:border-blue-300 hover:shadow-md transition-all group"
            onClick={() => onStart(m.num)}
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="w-7 h-7 rounded-full bg-blue-600 group-hover:bg-blue-700 text-white text-xs font-bold flex items-center justify-center flex-shrink-0 transition-colors">
                {m.num}
              </span>
              <h4 className="font-semibold text-gray-800 text-sm group-hover:text-blue-700 transition-colors">{m.title}</h4>
            </div>
            <p className="text-xs text-gray-500 leading-relaxed pl-10">{m.desc}</p>
          </div>
        ))}
      </div>

      {/* Data sources */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-5 mb-8">
        <h3 className="font-semibold text-gray-700 mb-3 text-sm">Data Sources</h3>
        <div className="grid grid-cols-2 gap-6 text-xs text-gray-500">
          <div>
            <p className="font-semibold text-gray-700 mb-1">IHME Global Burden of Disease 2023</p>
            <p>CVD attributable deaths by risk factor, sex, age group, and U.S. state. Filtered to all-ages, both-sexes, cardiovascular diseases cause.</p>
          </div>
          <div>
            <p className="font-semibold text-gray-700 mb-1">ClinicalTrials.gov</p>
            <p>Completed interventional trials with start date 2020–present, adult/older-adult population, valid trial phase (Early Phase 1 through Phase 3). Risk factor classification via keyword matching on outcomes and study summaries.</p>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="text-center">
        <button
          onClick={() => onStart(1)}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-full text-sm shadow-md hover:shadow-lg transition-all"
        >
          Explore Dashboard →
        </button>
      </div>

    </div>
  );
}

// ─── App Shell ────────────────────────────────────────────────────────────────
function App() {
  const [selectedFactors, setSelectedFactors] = useState(new Set(RISK_FACTORS));
  const [activeModule, setActiveModule] = useState(0);

  const toggleFactor = useCallback(rf => {
    setSelectedFactors(prev => {
      const next = new Set(prev);
      if (next.has(rf)) { if (next.size > 1) next.delete(rf); }
      else next.add(rf);
      return next;
    });
  }, []);

  const modules = [
    { id: 0, label: 'Overview' },
    { id: 1, label: 'Population Risk', sub: 'GBD burden by state' },
    { id: 2, label: 'Clinical Trial Research Pipeline', sub: 'Trial distribution' },
    { id: 3, label: 'Risk Factor Flow', sub: 'Sankey diagram' },
    { id: 4, label: 'Alignment Analysis', sub: 'Burden vs. research' }
  ];

  const totalDeaths = useMemo(() =>
    DATA.gbd_summary
      .filter(d => selectedFactors.has(d.risk_factor))
      .reduce((s, d) => s + d.death_val, 0),
    [selectedFactors]
  );
  const totalTrials = useMemo(() =>
    DATA.alignment
      .filter(d => selectedFactors.has(d.risk_factor))
      .reduce((s, d) => s + d.trial_count, 0),
    [selectedFactors]
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-900 to-blue-700 text-white px-6 py-5 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-xl font-bold tracking-tight">
            CVD Research Alignment Platform
          </h1>
          <p className="text-blue-200 text-sm mt-0.5">
            Population Cardiometabolic Risk Burden vs. Clinical Research Activity · GBD 2023 + ClinicalTrials.gov
          </p>
        </div>
      </header>

      {/* Control bar — hidden on Overview */}
      <div className={`bg-white border-b border-gray-200 px-6 py-3 shadow-sm sticky top-0 z-20 ${activeModule === 0 ? 'hidden' : ''}`}>
        <div className="max-w-7xl mx-auto flex flex-wrap items-center gap-4">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Risk Factors
          </span>
          <div className="flex flex-wrap gap-2">
            {RISK_FACTORS.map(rf => (
              <button
                key={rf}
                onClick={() => toggleFactor(rf)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-all
                  ${selectedFactors.has(rf)
                    ? 'text-white border-transparent shadow-sm'
                    : 'bg-white text-gray-400 border-gray-200'}`}
                style={selectedFactors.has(rf) ? { backgroundColor: RF_COLORS[rf] } : {}}
              >
                {RF_SHORT[rf]}
              </button>
            ))}
          </div>
          <div className="ml-auto flex gap-4 text-xs text-gray-500">
            <span>
              <strong className="text-gray-800">{Math.round(totalDeaths/1000).toLocaleString()}K</strong> deaths
            </span>
            <span>
              <strong className="text-gray-800">{totalTrials}</strong> trial mappings
            </span>
          </div>
        </div>
      </div>

      {/* Module nav */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="max-w-7xl mx-auto flex gap-0">
          {modules.map(m => (
            <button
              key={m.id}
              onClick={() => setActiveModule(m.id)}
              className={`px-5 py-3 text-sm font-medium border-b-2 transition-all
                ${activeModule === m.id
                  ? 'border-blue-600 text-blue-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              {m.id > 0 && <span className="mr-1 font-bold text-gray-400">{m.id}</span>}
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Module content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {activeModule === 0 && <IntroPage onStart={setActiveModule} />}
        {activeModule === 1 && <RiskLandscape selectedFactors={selectedFactors} />}
        {activeModule === 2 && <TrialPipeline selectedFactors={selectedFactors} />}
        {activeModule === 3 && <RiskFlowSankey selectedFactors={selectedFactors} />}
        {activeModule === 4 && <AlignmentScatter selectedFactors={selectedFactors} />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 mt-8 px-6 py-4 text-center text-xs text-gray-400">
        Data: IHME Global Burden of Disease 2023 · ClinicalTrials.gov (completed interventional trials, 2020–present)
        · Analysis by UW Biomedical Informatics
        · Author: Maggie Wang
      </footer>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
"""

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CVD Research Alignment Platform</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/prop-types/prop-types.min.js"></script>
  <script src="https://unpkg.com/recharts@2.10.4/umd/Recharts.js"></script>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/d3-sankey@0.12.3/dist/d3-sankey.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone@7.23.10/babel.min.js"></script>
  <link href="https://unpkg.com/tailwindcss@2/dist/tailwind.min.css" rel="stylesheet">
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; }}
  </style>
</head>
<body class="bg-gray-50">
  <div id="root"><p id="loading" style="padding:2rem;font-family:sans-serif;color:#666">Loading dashboard…</p></div>
  <div id="error-box" style="display:none;padding:1rem 2rem;background:#fef2f2;color:#b91c1c;font-family:monospace;white-space:pre-wrap;font-size:13px;border-top:2px solid #f87171"></div>
  <script>
    window.onerror = function(msg, src, line, col, err) {{
      var box = document.getElementById('error-box');
      box.style.display = 'block';
      box.textContent = 'JS Error: ' + msg + '\\n' + (err && err.stack ? err.stack : '') + '\\nAt: ' + src + ':' + line + ':' + col;
    }};
  </script>
  <script>
    const DATA = {DATA_JSON};
  </script>
  <script type="text/babel" data-presets="react">
{REACT_APP}
  </script>
</body>
</html>
"""

with open("dashboard.html", "w") as f:
    f.write(HTML)

print("dashboard.html generated successfully.")
print(f"File size: {len(HTML)/1024:.1f} KB")
