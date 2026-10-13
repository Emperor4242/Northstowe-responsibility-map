'use client';
import { useState } from 'react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { ArrowUpRight } from 'lucide-react';
type BinRecord = {
  id: string;
  locationDescription: string;
  binType: string;
  binNumber: string | null;
  collectionDay: string | null;
  locationStatus: string;
  coordinates: null | number[];
};
type Register = {
  records: BinRecord[];
  note: string;
  counts: {
    total: number;
    Wednesday: number;
    Thursday: number;
    geolocated: number;
  };
};
export default function BinRegister({
  register,
  email,
}: {
  register: Register;
  email: string;
}) {
  const [query, setQuery] = useState(''),
    [day, setDay] = useState('all');
  const rows = register.records.filter(
    (r) =>
      (day === 'all' || r.collectionDay === day) &&
      [r.locationDescription, r.binType, r.binNumber]
        .join(' ')
        .toLowerCase()
        .includes(query.toLowerCase().trim()),
  );
  return (
    <section className="bin-register">
      <h2 className="section-heading">Public-bin register</h2>
      <p className="intro">
        Collection schedules supplied for Northstowe. These entries are not map
        pins until their exact locations and service provider are confirmed.
      </p>
      <div className="register-stats">
        <span>
          <b>{register.counts.total}</b>records
        </span>
        <span>
          <b>{register.counts.Wednesday}</b>Wednesday
        </span>
        <span>
          <b>{register.counts.Thursday}</b>Thursday
        </span>
        <span>
          <b>{register.counts.geolocated}</b>geolocated
        </span>
      </div>
      <p className="notice">{register.note}</p>
      <label className="filter-label" htmlFor="bin-search">
        Find a bin record
      </label>
      <Input
        id="bin-search"
        placeholder="Location, bin type or supplied number"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <label className="filter-label" htmlFor="bin-day">
        Listed collection day
      </label>
      <Select value={day} onValueChange={(v) => setDay(v || 'all')}>
        <SelectTrigger id="bin-day">
          <SelectValue>{day === 'all' ? 'All days' : day}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All days</SelectItem>
          <SelectItem value="Wednesday">Wednesday</SelectItem>
          <SelectItem value="Thursday">Thursday</SelectItem>
        </SelectContent>
      </Select>
      <p className="geometry-note">
        {rows.length} of 48 records · Repeated descriptions may refer to
        different bins.
      </p>
      {rows.map((r) => (
        <details className="bin-record" key={r.id}>
          <summary>
            <strong>{r.locationDescription}</strong>
            <span>
              {r.collectionDay || 'Day not supplied'} · {r.binType}
            </span>
          </summary>
          <dl>
            <dt>Supplied bin number</dt>
            <dd>{r.binNumber || 'Not supplied'}</dd>
            <dt>Collection frequency</dt>
            <dd>Not confirmed</dd>
            <dt>Emptying contractor</dt>
            <dd>Not confirmed</dd>
            <dt>Repair / replacement</dt>
            <dd>Not confirmed</dd>
            <dt>Location</dt>
            <dd>{r.locationStatus}</dd>
          </dl>
          <a
            className="source-link"
            href={`mailto:${email}?subject=${encodeURIComponent('Identify Northstowe public bin: ' + r.locationDescription)}`}
          >
            Ask street care to identify this bin <ArrowUpRight size={13} />
          </a>
        </details>
      ))}
      {!rows.length && (
        <p className="notice">No records match these filters.</p>
      )}
      <a className="download-link" href="/data/bin-register.json" download>
        Download the supplied-record register <ArrowUpRight size={14} />
      </a>
      <p className="small-print">
        Reviewed 13 October 2026. Document effective date, service provider and
        individual coordinates were not supplied. This register does not change
        the mapped Anglian Water or Greenbelt collection evidence.
      </p>
    </section>
  );
}
