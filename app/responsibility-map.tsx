'use client';
import { useEffect, useRef, useState } from 'react';
import {
  MapPin,
  Search,
  Layers,
  BookOpen,
  Maximize,
  LocateFixed,
  X,
  ChevronRight,
  ArrowUpRight,
  Info,
  Mail,
  Phone,
} from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from '@/components/ui/collapsible';
import {
  problemTypes,
  responsibilitySummary,
  mapPane,
} from '@/lib/map-presentation';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import booleanPointInPolygon from '@turf/boolean-point-in-polygon';
import { contains } from '@/lib/map-spatial';
import type * as Leaflet from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './map-theme.css';

type F = any;
const categories = problemTypes;
const all = categories.map((c) => c[0]);
export default function ResponsibilityMap() {
  const node = useRef<HTMLDivElement>(null),
    map = useRef<Leaflet.Map | null>(null),
    Lref = useRef<typeof Leaflet | null>(null),
    layer = useRef<Leaflet.LayerGroup | null>(null),
    pin = useRef<Leaflet.CircleMarker | null>(null),
    selectRef = useRef<(lat: number, lng: number) => void>(() => {});
  const [data, setData] = useState<any>(null),
    [ready, setReady] = useState(false),
    [issues, setIssues] = useState(all),
    [org, setOrg] = useState('all'),
    [context, setContext] = useState(true),
    [details, setDetails] = useState(false),
    [query, setQuery] = useState(''),
    [tab, setTab] = useState('map'),
    [point, setPoint] = useState<number[] | null>(null),
    [hits, setHits] = useState<F[]>([]),
    [outside, setOutside] = useState(false),
    [message, setMessage] = useState(''),
    [legendOpen, setLegendOpen] = useState(false);
  const selected = (r: any) =>
    r.categories.some((c: string) => issues.includes(c)) &&
    (org === 'all' || r.org === org);
  const showDetails =
    details ||
    (issues.length === 1 && ['lighting', 'water'].includes(issues[0]));
  const matches = (f: F) =>
    (context || !f.properties.context) &&
    (!f.properties.detail || showDetails) &&
    f.properties.responsibilities.some(selected);
  useEffect(() => {
    let cancelled = false;
    let observer: ResizeObserver;
    (async () => {
      try {
        const [L, d, b] = await Promise.all([
          import('leaflet'),
          fetch('/data/responsibilities.json').then(async (r) => {
            if (!r.ok) throw Error();
            return (await r.json()) as any;
          }),
          fetch('/data/parish.geojson').then(async (r) => {
            if (!r.ok) throw Error();
            return (await r.json()) as any;
          }),
        ]);
        if (cancelled || !node.current) return;
        d.boundary = b;
        setData(d);
        Lref.current = L;
        const m = L.map(node.current, {
          zoomControl: false,
          minZoom: 12,
          maxZoom: 20,
        });
        map.current = m;
        for (const [name, z] of [
          ['enquiryAreas', 401],
          ['responsibilityAreas', 410],
          ['responsibilityRoads', 430],
          ['responsibilityPoints', 450],
          ['parishBoundary', 460],
        ] as const) {
          m.createPane(name).style.zIndex = String(z);
        }
        const tiles = L.tileLayer(
          'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          {
            maxZoom: 19,
            attribution:
              '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
          },
        ).addTo(m);
        let errors = 0;
        tiles.on('tileerror', () => {
          if (++errors === 4)
            setMessage(
              'Street tiles could not load. The responsibility layers and place list remain available.',
            );
        });
        L.geoJSON(b, {
          pane: 'parishBoundary',
          interactive: false,
          style: {
            color: '#344954',
            weight: 2,
            dashArray: '7 6',
            fillOpacity: 0.035,
          },
        }).addTo(m);
        layer.current = L.layerGroup().addTo(m);
        m.fitBounds(L.geoJSON(b).getBounds(), { padding: [25, 25] });
        L.control.zoom({ position: 'bottomright' }).addTo(m);
        L.control.scale({ imperial: false }).addTo(m);
        m.on('click', (e) => selectRef.current(e.latlng.lat, e.latlng.lng));
        observer = new ResizeObserver(() => m.invalidateSize());
        observer.observe(node.current);
        setReady(true);
      } catch {
        if (!cancelled)
          setMessage(
            'The map data could not load. Reload the page to try again.',
          );
      }
    })();
    return () => {
      cancelled = true;
      observer?.disconnect();
      map.current?.remove();
      map.current = null;
    };
  }, []);
  selectRef.current = (lat, lng) => {
    if (!data) return;
    setPoint([lat, lng]);
    setOutside(
      !data.boundary.features.some((f: F) =>
        booleanPointInPolygon([lng, lat], f),
      ),
    );
    setHits(data.features.filter((f: F) => contains(f, [lng, lat])));
    setTab('map');
    if (map.current && Lref.current) {
      pin.current?.remove();
      pin.current = Lref.current
        .circleMarker([lat, lng], {
          pane: 'responsibilityPoints',
          radius: 7,
          color: '#163542',
          weight: 3,
          fillColor: 'white',
          fillOpacity: 1,
        })
        .addTo(map.current);
    }
  };
  useEffect(() => {
    const L = Lref.current,
      g = layer.current;
    if (!data || !L || !g) return;
    map.current?.closePopup();
    g.clearLayers();
    data.features
      .filter(matches)
      .sort(
        (a: F, b: F) =>
          Number(!!b.properties.context) - Number(!!a.properties.context),
      )
      .forEach((f: F) => {
        const p = f.properties,
          r = p.responsibilities.find(selected),
          color = data.organisations[r.org].color;
        const geo = L.geoJSON(f, {
          pane: mapPane(f.geometry.type, p.context),
          style: {
            color,
            weight: p.context ? 1.5 : f.geometry.type.includes('Line') ? 7 : 2,
            fillColor: color,
            fillOpacity: p.context ? 0.06 : 0.25,
            dashArray:
              (p.geometryStatus === 'indicative' || p.context) &&
              !f.geometry.type.includes('Line')
                ? '6 4'
                : undefined,
          },
          pointToLayer: (_, ll) =>
            L.circleMarker(ll, {
              pane: 'responsibilityPoints',
              radius: p.detail ? 4 : 7,
              color: 'white',
              weight: 1.5,
              fillColor: color,
              fillOpacity: 1,
            }),
        });
        const summary = (areas: F[]) => {
          const box = document.createElement('div');
          box.className = 'responsibility-brief';
          for (const area of areas.slice(0, 5)) {
            const heading = document.createElement('strong');
            heading.className = 'brief-place';
            heading.textContent = area.properties.name;
            box.appendChild(heading);
            for (const row of responsibilitySummary(
              area.properties,
              issues,
              org,
            )) {
              const item = document.createElement('div');
              item.className = 'brief-scope';
              const who = document.createElement('b');
              who.textContent = data.organisations[row.org].name;
              item.appendChild(who);
              const what = document.createElement('span');
              what.textContent = row.label + ': ' + row.tasks.join('; ');
              item.appendChild(what);
              if (row.caveat) {
                const note = document.createElement('small');
                note.textContent = row.caveat;
                item.appendChild(note);
              }
              box.appendChild(item);
            }
          }
          if (areas.length > 5) {
            const more = document.createElement('small');
            more.textContent =
              'More matches and sources appear in the location details.';
            box.appendChild(more);
          }
          return box;
        };
        const near = (lat: number, lng: number) => {
          const nearby = data.features
            .filter(matches)
            .filter((a: F) => contains(a, [lng, lat]));
          const specific = nearby.filter((a: F) => !a.properties.context);
          return specific.length ? specific : nearby.length ? nearby : [f];
        };
        geo.bindTooltip(summary([f]), {
          sticky: true,
          className: 'scope-tooltip',
        });
        geo.on('mousemove', (e: Leaflet.LeafletMouseEvent) =>
          geo.setTooltipContent(summary(near(e.latlng.lat, e.latlng.lng))),
        );
        geo.on('click', (e: Leaflet.LeafletMouseEvent) => {
          selectRef.current(e.latlng.lat, e.latlng.lng);
          L.popup({
            maxWidth: 330,
            maxHeight: 260,
            autoPan: false,
            className: 'scope-popup',
          })
            .setLatLng(e.latlng)
            .setContent(summary(near(e.latlng.lat, e.latlng.lng)))
            .openOn(map.current!);
        });
        geo.addTo(g);
      });
    pin.current?.bringToFront();
  }, [data, ready, issues, org, context, showDetails]);
  useEffect(() => {
    const context = (
      document as Document & {
        modelContext?: {
          registerTool: (
            tool: unknown,
            options: { signal: AbortSignal },
          ) => unknown;
        };
      }
    ).modelContext;
    if (!data || !context?.registerTool) return;
    const lifecycle = new AbortController();
    try {
      void Promise.resolve(
        context.registerTool(
          {
            name: 'find_responsible_contacts',
            title: 'Find Northstowe maintenance contacts',
            description:
              'Read all matching contacts and evidence for a Northstowe location and problem. Does not submit a report or certify ownership.',
            inputSchema: {
              type: 'object',
              properties: {
                latitude: { type: 'number' },
                longitude: { type: 'number' },
                category: { type: 'string', enum: all },
              },
              required: ['latitude', 'longitude', 'category'],
              additionalProperties: false,
            },
            annotations: { readOnlyHint: true, untrustedContentHint: true },
            execute(input: unknown) {
              const x = input as {
                latitude?: number;
                longitude?: number;
                category?: string;
              };
              if (
                !x ||
                typeof x.latitude !== 'number' ||
                typeof x.longitude !== 'number' ||
                !Number.isFinite(x.latitude) ||
                !Number.isFinite(x.longitude) ||
                x.latitude < -90 ||
                x.latitude > 90 ||
                x.longitude < -180 ||
                x.longitude > 180 ||
                !all.includes(x.category || '')
              )
                throw Error(
                  'Provide valid latitude, longitude and a supported problem category.',
                );
              const location = [x.longitude, x.latitude];
              return {
                checked: data.checked,
                insideParish: data.boundary.features.some((f: F) =>
                  booleanPointInPolygon(location, f),
                ),
                notice:
                  'Approximate geographic matches; read scope and boundary caveats. No report has been submitted.',
                matches: data.features
                  .filter((f: F) => contains(f, location))
                  .flatMap((f: F) =>
                    f.properties.responsibilities
                      .filter((r: any) => r.categories.includes(x.category))
                      .map((r: any) => ({
                        place: f.properties.name,
                        status: f.properties.status,
                        geometryNote: f.properties.geometryNote,
                        organisation: data.organisations[r.org],
                        scope: r.note,
                        caveat: r.caveat,
                        sources: r.sources.map(
                          (id: string) => data.sources[id],
                        ),
                      })),
                  ),
              };
            },
          },
          { signal: lifecycle.signal },
        ),
      ).catch(() => {});
    } catch {
      /* Optional API; map remains fully usable. */
    }
    return () => lifecycle.abort();
  }, [data]);
  const focus = (f: F) => {
    if (f.properties.detail) setDetails(true);
    const L = Lref.current,
      m = map.current;
    if (!L || !m) return;
    const b = L.geoJSON(f).getBounds();
    m.fitBounds(b, { padding: [45, 45], maxZoom: 18 });
    const c = f.properties.anchor
      ? { lat: f.properties.anchor[1], lng: f.properties.anchor[0] }
      : b.getCenter();
    selectRef.current(c.lat, c.lng);
    if (!f.properties.searchOnly)
      setHits((prev) => [
        f,
        ...prev.filter((x) => x.properties.id !== f.properties.id),
      ]);
    setQuery('');
    document
      .getElementById('location-results')
      ?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  };
  const reset = () => {
    if (map.current && Lref.current && data)
      map.current.fitBounds(Lref.current.geoJSON(data.boundary).getBounds(), {
        padding: [25, 25],
      });
    setPoint(null);
    setHits([]);
    pin.current?.remove();
  };
  const locate = () => {
    if (!navigator.geolocation) {
      setMessage(
        'Location is unavailable in this browser. Search for a place instead.',
      );
      return;
    }
    setMessage('Finding your location…');
    navigator.geolocation.getCurrentPosition(
      (p) => {
        selectRef.current(p.coords.latitude, p.coords.longitude);
        map.current?.setView([p.coords.latitude, p.coords.longitude], 17);
        setMessage(
          `Location accuracy approximately ${Math.round(p.coords.accuracy)} m. Click the map to adjust the pin.`,
        );
      },
      () =>
        setMessage(
          'Location unavailable. Search for a place or select it on the map.',
        ),
      { timeout: 10000, enableHighAccuracy: true },
    );
  };
  const visible = data?.features.filter(matches) || [],
    shown = hits.filter(matches),
    results =
      query.trim() && data
        ? [...data.features, ...data.searchPlaces]
            .filter((f: F) =>
              f.properties.name
                .toLowerCase()
                .includes(query.trim().toLowerCase()),
            )
            .slice(0, 15)
        : [];
  return (
    <main className="map-app">
      <header className="app-header">
        <a href="/" className="brand">
          <span className="brand-mark">
            <MapPin size={24} />
          </span>
          <span>
            <strong>Northstowe</strong>
            <small>Who looks after this?</small>
          </span>
        </a>
        <span className="header-note">
          Public-source guide <span>12 September 2026</span>
        </span>
        <button className="header-button" onClick={() => setTab('sources')}>
          <BookOpen size={16} />
          Sources & gaps
        </button>
      </header>
      <div className="workspace">
        <aside className="control-panel">
          <div className="eyebrow">PUBLIC REALM RESPONSIBILITIES</div>
          <h1>Find the right contact.</h1>
          <p className="intro">
            Choose a problem, then select a place. A path, its lights and the
            land around it may have different contacts.
          </p>
          <div className="search-box">
            <Search size={18} />
            <Input
              aria-label="Search streets and named places"
              placeholder="Search a street, park or lake"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {query && (
              <button aria-label="Clear search" onClick={() => setQuery('')}>
                <X size={16} />
              </button>
            )}
          </div>
          {query.trim() && (
            <div className="search-results" aria-live="polite">
              {results.length ? (
                results.map((f: F) => (
                  <button key={f.properties.id} onClick={() => focus(f)}>
                    <MapPin size={14} />
                    <span>{f.properties.name}</span>
                    <ChevronRight size={14} />
                  </button>
                ))
              ) : (
                <p>No matching named place. Select a point on the map.</p>
              )}
            </div>
          )}
          <Tabs
            value={tab}
            onValueChange={(v) => setTab(String(v))}
            className="panel-tabs"
          >
            <TabsList variant="line">
              <TabsTrigger value="map">
                <Layers size={15} />
                Map layers
              </TabsTrigger>
              <TabsTrigger value="contacts">Contacts</TabsTrigger>
              <TabsTrigger value="sources">Sources</TabsTrigger>
            </TabsList>
            <TabsContent value="map">
              {issues.includes('bins') && (
                <div className="coverage-note">
                  <Info size={17} />
                  <p>
                    Public-bin emptying is separate from litter clearance and
                    household collections. Historical service areas are marked;
                    other areas show an enquiry contact until the bin’s operator
                    is confirmed.
                  </p>
                </div>
              )}
              <div className="row-heading">
                <h2>What needs attention?</h2>
                <button
                  onClick={() =>
                    setIssues(issues.length === all.length ? [] : all)
                  }
                >
                  {issues.length === all.length ? 'Clear' : 'Select all'}
                </button>
              </div>
              <div className="category-grid">
                {categories.map(([id, name]) => (
                  <label
                    key={id}
                    className={`category ${issues.includes(id) ? 'checked' : ''}`}
                  >
                    <Checkbox
                      checked={issues.includes(id)}
                      onCheckedChange={(v) =>
                        setIssues((prev) =>
                          v ? [...prev, id] : prev.filter((x) => x !== id),
                        )
                      }
                    />
                    <span>{name}</span>
                  </label>
                ))}
              </div>
              <label className="filter-label" htmlFor="org-filter">
                Responsible organisation
              </label>
              <Select value={org} onValueChange={(v) => setOrg(v || 'all')}>
                <SelectTrigger id="org-filter" className="org-select">
                  <SelectValue>
                    {org === 'all'
                      ? 'All organisations'
                      : data?.organisations[org]?.name}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All organisations</SelectItem>
                  {data &&
                    Object.entries(data.organisations).map(
                      ([id, o]: [string, any]) => (
                        <SelectItem key={id} value={id}>
                          {o.name}
                        </SelectItem>
                      ),
                    )}
                </SelectContent>
              </Select>
              <label className="context-toggle">
                <Checkbox
                  checked={context}
                  onCheckedChange={(v) => setContext(!!v)}
                />
                Include broad enquiry areas
              </label>
              <label className="context-toggle">
                <Checkbox
                  checked={showDetails}
                  onCheckedChange={(v) => setDetails(!!v)}
                  disabled={
                    issues.length === 1 &&
                    ['lighting', 'water'].includes(issues[0])
                  }
                />
                Show individual lights and drains
              </label>
              <div
                className="row-heading results-heading"
                id="location-results"
              >
                <h2>{point ? 'At this location' : 'Explore mapped places'}</h2>
                {point ? (
                  <button onClick={reset}>Clear location</button>
                ) : (
                  <small>
                    {visible.filter((f: F) => !f.properties.context).length}{' '}
                    areas / assets
                  </small>
                )}
              </div>
              {!point && (
                <div className="coverage-note">
                  <Info size={17} />
                  <p>
                    Full parish coverage; partial responsibility evidence.
                    Dashed areas need boundary or handover checks. Uncoloured
                    land is unresolved.
                  </p>
                </div>
              )}
              {point && (
                <p className="coordinates">
                  <MapPin size={13} />
                  {point[0].toFixed(5)}, {point[1].toFixed(5)}
                </p>
              )}
              {point && outside && (
                <div className="notice">
                  <strong>Outside Northstowe parish</strong>
                  <p>
                    This location is beyond the parish boundary. Nearby features
                    are included for context.
                  </p>
                </div>
              )}
              {point && !shown.length && (
                <div className="notice">
                  <strong>
                    {hits.length
                      ? 'No results with these filters'
                      : 'Responsibility not established here'}
                  </strong>
                  <p>
                    {hits.length
                      ? 'Try more problem types or choose all organisations.'
                      : 'The sources do not identify an exact maintainer at this point. Use the contacts tab for enquiry routes.'}
                  </p>
                </div>
              )}
              {point &&
                shown.length > 0 &&
                shown.every((f: F) => f.properties.context) && (
                  <div className="notice">
                    <strong>No asset-level maintainer confirmed</strong>
                    <p>
                      Only broad enquiry routes match this location and these
                      filters. Confirm the particular asset before reporting a
                      repair.
                    </p>
                  </div>
                )}
              {point && (
                <p className="geometry-note">
                  Lines match within about 14 m. Nearby point matches are
                  approximate; check the asset number on site.
                </p>
              )}
              {point &&
                shown.map((f: F) => (
                  <section className="feature-card" key={f.properties.id}>
                    <span
                      className={`status ${f.properties.status === 'published' ? 'published' : ''}`}
                    >
                      {f.properties.recordLabel ||
                        (f.properties.context
                          ? 'Enquiry route only'
                          : f.properties.status === 'published'
                            ? 'Responsibility identified in source'
                            : 'Confirmation needed')}
                    </span>
                    <h3>{f.properties.name}</h3>
                    <p className="geometry-note">{f.properties.geometryNote}</p>
                    {f.properties.responsibilities
                      .filter(selected)
                      .map((r: any, i: number) => (
                        <div className="responsibility" key={i}>
                          <h4>
                            <i
                              style={{
                                background: data.organisations[r.org].color,
                              }}
                            />
                            {data.organisations[r.org].name}
                          </h4>
                          {r.evidence === 'enquiry' && (
                            <span className="status">
                              Enquiry contact; bin service unconfirmed
                            </span>
                          )}
                          {r.evidence === 'historical' && (
                            <span className="status">
                              Historical record; confirm current service
                            </span>
                          )}
                          <small>
                            {r.categories
                              .filter((c: string) => issues.includes(c))
                              .map(
                                (c: string) =>
                                  categories.find((x) => x[0] === c)?.[1],
                              )
                              .join(' · ')}
                          </small>
                          <p>{r.note}</p>
                          {r.caveat && <p className="caution">{r.caveat}</p>}
                          <Contact
                            o={data.organisations[r.org]}
                            binService={
                              r.org === 'waste' &&
                              r.categories.includes('bins') &&
                              issues.includes('bins')
                            }
                          />
                          {r.sources.map((id: string) => (
                            <SourceLink key={id} s={data.sources[id]} />
                          ))}
                        </div>
                      ))}
                    {f.properties.geometryUrl && (
                      <a
                        className="source-link"
                        href={f.properties.geometryUrl}
                        target="_blank"
                        rel="noreferrer"
                      >
                        View geographic source <ArrowUpRight size={13} />
                      </a>
                    )}
                  </section>
                ))}
              {!point &&
                visible
                  .filter((f: F) => !f.properties.context)
                  .map((f: F) => (
                    <button
                      className="place-row"
                      key={f.properties.id}
                      onClick={() => focus(f)}
                    >
                      <i
                        style={{
                          background:
                            data.organisations[
                              f.properties.responsibilities.find(selected).org
                            ].color,
                        }}
                      />
                      <span>
                        <strong>{f.properties.name}</strong>
                        <small>
                          {f.properties.subtitle ||
                            data.organisations[
                              f.properties.responsibilities[0].org
                            ].name}
                        </small>
                      </span>
                      <ChevronRight size={16} />
                    </button>
                  ))}
              {!issues.length && (
                <p className="notice">
                  Select a problem type to show map areas.
                </p>
              )}
            </TabsContent>
            <TabsContent value="contacts">
              <h2 className="section-heading">Reporting contacts</h2>
              <p className="intro">
                Check the location and asset first. Council reporting and
                responsibility for clearing private land can be different.
              </p>
              {data &&
                Object.entries(data.organisations).map(
                  ([id, o]: [string, any]) => (
                    <section className="contact-card" key={id}>
                      <h3>
                        <i style={{ background: o.color }} />
                        {o.name}
                      </h3>
                      <p>{o.description}</p>
                      <Contact o={o} />
                      {o.source && <SourceLink s={data.sources[o.source]} />}
                    </section>
                  ),
                )}
            </TabsContent>
            <TabsContent value="sources">
              <h2 className="section-heading">Evidence & remaining gaps</h2>
              <p className="intro">
                Research checked on 12 September 2026. Sources describe
                different dates; handovers can change the answer.
              </p>
              <div className="notice">
                <strong>Evidence coverage</strong>
                <p>
                  The parish boundary is official. Asset shapes locate places
                  and do not establish legal ownership. Broad development areas
                  provide enquiry routes only. The county snapshot adds 50 owned
                  lights, 176 gully records, 6 adopted highway records, 2
                  prospective-adoption records and 11 rights-of-way records.
                </p>
              </div>
              <h3 className="subheading">Information still needed</h3>
              {data?.gaps.map((g: any) => (
                <section className="gap" key={g.id}>
                  <strong>{g.title}</strong>
                  <p>{g.detail}</p>
                  <small>Information holder: {g.holder}</small>
                </section>
              ))}
              <a
                className="download-link"
                href="/data/research-notes.md"
                download
              >
                Download the research & gap register <ArrowUpRight size={14} />
              </a>
              <a
                className="download-link"
                href="/data/responsibility-areas.geojson"
                download
              >
                Download mapped responsibilities (GeoJSON){' '}
                <ArrowUpRight size={14} />
              </a>
              <h3 className="subheading">Public sources</h3>
              {data &&
                Object.entries(data.sources).map(([id, s]: [string, any]) => (
                  <a
                    key={id}
                    className="evidence"
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <span>
                      <strong>{s.title}</strong>
                      <small>
                        {s.publisher} · {s.date}
                      </small>
                    </span>
                    <ArrowUpRight size={15} />
                  </a>
                ))}
              <p className="small-print">
                Boundary: ONS, December 2025. Contains OS and ONS data © Crown
                copyright and database right 2025. County assets: © Crown
                copyright and database rights 2026 OS AC0000822131. Geographic
                features © OpenStreetMap contributors, ODbL. Plan publishers
                retain copyright in their source plans. No issue reports or
                location data are stored by this guide. Street tiles are fetched
                from OpenStreetMap.
              </p>
            </TabsContent>
          </Tabs>
        </aside>
        <section
          className="map-section"
          aria-label="Interactive Northstowe map"
        >
          <div ref={node} className="map-canvas" />
          {!ready && !message && (
            <div className="loading">Loading Northstowe’s map…</div>
          )}
          <div className="map-top">
            <span className="map-title">
              <b />
              Northstowe parish
            </span>
            <div>
              <button
                onClick={reset}
                aria-label="Show whole parish"
                title="Show whole parish"
              >
                <Maximize size={18} />
              </button>
              <button
                onClick={locate}
                aria-label="Use my location"
                title="Use my location"
              >
                <LocateFixed size={18} />
              </button>
            </div>
          </div>
          {message && (
            <div className="map-message" role="status">
              {message}
              <button
                aria-label="Dismiss message"
                onClick={() => setMessage('')}
              >
                <X size={15} />
              </button>
            </div>
          )}
          <Collapsible
            className="legend"
            open={legendOpen}
            onOpenChange={setLegendOpen}
          >
            <CollapsibleTrigger className="legend-toggle">
              <Layers size={16} />
              {legendOpen ? 'Hide map key' : 'Show map key'}
              <ChevronRight size={15} className={legendOpen ? 'rotated' : ''} />
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="legend-items">
                {data &&
                  Object.entries(data.organisations)
                    .filter(([id]) =>
                      visible.some((f: F) =>
                        f.properties.responsibilities.some(
                          (r: any) => r.org === id && selected(r),
                        ),
                      ),
                    )
                    .map(([id, o]: [string, any]) => (
                      <span key={id}>
                        <i style={{ background: o.color }} />
                        {o.shortName || o.name}
                      </span>
                    ))}
              </div>
              <p>
                <b />
                Parish boundary <em />
                Indicative / enquiry area
              </p>
            </CollapsibleContent>
          </Collapsible>
          <div className="map-footer">
            <Info size={14} />
            Select a place to see contacts and exceptions
          </div>
        </section>
      </div>
    </main>
  );
}
function Contact({ o, binService = false }: { o: any; binService?: boolean }) {
  return (
    <div className="contact-links">
      {o.reportUrl && (
        <a
          className="report-link"
          href={
            binService
              ? 'https://greatercambridgewaste.org/litter-in-public-spaces/street-care-and-cleaning-south-cambs'
              : o.reportUrl
          }
          target="_blank"
          rel="noreferrer"
        >
          {binService
            ? 'Identify / report a council bin'
            : o.reportLabel || 'Report or contact'}
          <ArrowUpRight size={14} />
        </a>
      )}
      {o.email && (
        <a href={`mailto:${o.email}`}>
          <Mail size={14} />
          {o.email}
        </a>
      )}
      {o.phone && (
        <a href={`tel:${o.phone.replace(/[^+\d]/g, '')}`}>
          <Phone size={14} />
          {o.phone}
        </a>
      )}
    </div>
  );
}
function SourceLink({ s }: { s: any }) {
  return s ? (
    <a className="source-link" href={s.url} target="_blank" rel="noreferrer">
      {s.title} · {s.date}
      <ArrowUpRight size={13} />
    </a>
  ) : null;
}
