"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Newspaper,
  Database,
  Target,
  Buildings,
  MagnifyingGlass,
  Play,
  Lightning,
  ArrowSquareOut,
  Spinner,
  CaretDown,
  UploadSimple,
  DownloadSimple,
  CheckCircle,
  Plus,
  Rows,
  CalendarBlank,
  Tag,
  TextAlignLeft,
  Hash,
} from "@phosphor-icons/react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types ───────────────────────────────────────────────────────

type Stats = {
  teletipos: number;
  articulos: number;
  matches: number;
  medios: number;
  scrapeados: number;
  matches_por_metodo: Record<string, number>;
};

type Match = {
  teletipo_id: string;
  teletipo_titular: string;
  articulo_titular: string;
  medio: string;
  url: string;
  score_titular: number;
  score_cuerpo: number | null;
  metodo: string;
  fecha_publicacion: string | null;
};

type Teletipo = {
  id: string;
  titular: string;
  cuerpo: string;
  fecha_emision: string;
  categoria: string;
};

type RunStatus = {
  running: boolean;
  last_result: Record<string, unknown> | null;
};

type Tab = "matches" | "teletipos";

// ─── Small Components ────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}) {
  return (
    <div className="py-5 px-1">
      <div className="flex items-center gap-2 mb-1.5">
        <Icon size={14} className="text-zinc-300" />
        <p className="text-[11px] font-mono uppercase tracking-wider text-zinc-400">
          {label}
        </p>
      </div>
      <p className="text-2xl md:text-3xl font-semibold tracking-tight text-zinc-900 font-mono">
        {typeof value === "number" ? value.toLocaleString("es-ES") : value}
      </p>
    </div>
  );
}

function MethodBadge({ metodo }: { metodo: string }) {
  const styles: Record<string, string> = {
    fuzzy: "bg-sky-50 text-sky-700 border-sky-200/60",
    fuente: "bg-emerald-50 text-emerald-700 border-emerald-200/60",
    scraping_fuzzy: "bg-amber-50 text-amber-700 border-amber-200/60",
  };
  return (
    <span
      className={`inline-flex items-center text-[11px] font-mono px-2 py-0.5 rounded-full border ${styles[metodo] ?? "bg-zinc-50 text-zinc-600 border-zinc-200"}`}
    >
      {metodo}
    </span>
  );
}

function ScoreBar({ score }: { score: number }) {
  const rounded = Math.round(score);
  const color =
    rounded >= 90
      ? "bg-emerald-500"
      : rounded >= 80
        ? "bg-sky-500"
        : "bg-amber-500";
  return (
    <div className="flex items-center gap-2.5">
      <span className="text-xs font-mono text-zinc-500 w-7 text-right">
        {rounded}
      </span>
      <div className="w-16 h-1.5 bg-zinc-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${rounded}%` }}
        />
      </div>
    </div>
  );
}

function Toast({ message }: { message: string }) {
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-20 inline-flex items-center gap-2 text-sm text-emerald-700 bg-white border border-emerald-200/60 shadow-[0_8px_30px_-10px_rgba(0,0,0,0.08)] px-5 py-3 rounded-2xl animate-[fadeUp_0.3s_ease-out]">
      <CheckCircle size={16} weight="fill" className="text-emerald-500" />
      {message}
    </div>
  );
}

// ─── Matches Tab ─────────────────────────────────────────────────

function MatchesTab({
  matches,
  matchTotal,
  loading,
  medios,
  filterMedio,
  setFilterMedio,
  filterMetodo,
  setFilterMetodo,
  runStatus,
  triggerRun,
}: {
  matches: Match[];
  matchTotal: number;
  loading: boolean;
  medios: Record<string, { nombre: string }>;
  filterMedio: string;
  setFilterMedio: (v: string) => void;
  filterMetodo: string;
  setFilterMetodo: (v: string) => void;
  runStatus: RunStatus;
  triggerRun: (full: boolean) => void;
}) {
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={() => triggerRun(false)}
          disabled={runStatus.running}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-xl bg-zinc-900 text-white transition-all duration-200 hover:bg-zinc-800 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {runStatus.running ? (
            <Spinner size={16} className="animate-spin" />
          ) : (
            <Play size={16} weight="fill" />
          )}
          {runStatus.running ? "Ejecutando..." : "Ciclo rapido"}
        </button>
        <button
          onClick={() => triggerRun(true)}
          disabled={runStatus.running}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-xl border border-zinc-200 text-zinc-700 bg-white transition-all duration-200 hover:border-zinc-300 hover:bg-zinc-50 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {runStatus.running ? (
            <Spinner size={16} className="animate-spin" />
          ) : (
            <Lightning size={16} weight="fill" />
          )}
          {runStatus.running ? "Ejecutando..." : "Ciclo completo"}
        </button>

        {runStatus.running && (
          <span className="inline-flex items-center text-xs font-mono text-zinc-400 ml-1">
            <span className="w-1.5 h-1.5 bg-sky-500 rounded-full animate-pulse mr-2" />
            Ingesta + matching en curso...
          </span>
        )}
      </div>

      <div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
          <div>
            <h2 className="text-base font-semibold tracking-tight text-zinc-900">
              Matches detectados
            </h2>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              {matchTotal} resultado{matchTotal !== 1 ? "s" : ""}
            </p>
          </div>
          <div className="flex gap-2">
            <SelectFilter
              value={filterMedio}
              onChange={setFilterMedio}
              placeholder="Todos los medios"
              options={Object.entries(medios).map(([id, m]) => ({
                value: id,
                label: m.nombre,
              }))}
            />
            <SelectFilter
              value={filterMetodo}
              onChange={setFilterMetodo}
              placeholder="Todos los metodos"
              options={[
                { value: "fuzzy", label: "fuzzy" },
                { value: "fuente", label: "fuente" },
                { value: "scraping_fuzzy", label: "scraping_fuzzy" },
              ]}
            />
          </div>
        </div>

        <div className="border border-zinc-200/60 rounded-2xl bg-white overflow-hidden">
          {loading ? (
            <div className="divide-y divide-zinc-100 px-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex gap-4 py-4 animate-pulse">
                  <div className="h-4 bg-zinc-100 rounded w-1/3" />
                  <div className="h-4 bg-zinc-100 rounded w-16" />
                  <div className="h-4 bg-zinc-100 rounded w-1/4" />
                  <div className="h-4 bg-zinc-100 rounded w-12" />
                </div>
              ))}
            </div>
          ) : matches.length === 0 ? (
            <div className="py-16 text-center">
              <MagnifyingGlass
                size={28}
                className="mx-auto mb-3 text-zinc-300"
              />
              <p className="text-sm text-zinc-400 max-w-[40ch] mx-auto leading-relaxed">
                Sin matches. Carga teletipos y ejecuta un ciclo para detectar
                publicaciones en medios.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-zinc-100">
                    {[
                      "Teletipo",
                      "Medio",
                      "Articulo publicado",
                      "Score",
                      "Metodo",
                      "Fecha",
                      "",
                    ].map((h) => (
                      <th
                        key={h}
                        className="text-[11px] font-mono font-medium text-zinc-400 uppercase tracking-wider px-4 py-3 first:pl-6"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-50">
                  {matches.map((m, i) => (
                    <tr
                      key={`${m.teletipo_id}-${i}`}
                      className="hover:bg-zinc-50/50 transition-colors duration-150"
                    >
                      <td className="pl-6 pr-4 py-3.5 text-sm text-zinc-800 max-w-[240px] truncate">
                        {m.teletipo_titular}
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-xs font-mono font-medium text-zinc-500 bg-zinc-100 px-2 py-0.5 rounded">
                          {m.medio}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-sm text-zinc-600 max-w-[240px] truncate">
                        {m.articulo_titular}
                      </td>
                      <td className="px-4 py-3.5">
                        <ScoreBar score={m.score_titular} />
                      </td>
                      <td className="px-4 py-3.5">
                        <MethodBadge metodo={m.metodo} />
                      </td>
                      <td className="px-4 py-3.5 text-xs font-mono text-zinc-400 whitespace-nowrap">
                        {m.fecha_publicacion
                          ? new Date(m.fecha_publicacion).toLocaleDateString(
                              "es-ES",
                              {
                                day: "2-digit",
                                month: "short",
                                hour: "2-digit",
                                minute: "2-digit",
                              }
                            )
                          : "\u2014"}
                      </td>
                      <td className="px-4 py-3.5">
                        <a
                          href={m.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-zinc-300 hover:text-zinc-600 transition-colors duration-150"
                        >
                          <ArrowSquareOut size={16} />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Teletipos Tab ───────────────────────────────────────────────

function TeletiposTab({
  onToast,
  onRefresh,
}: {
  onToast: (msg: string) => void;
  onRefresh: () => void;
}) {
  const [teletipos, setTeletipos] = useState<Teletipo[]>([]);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [scraping, setScraping] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [form, setForm] = useState({
    id: "",
    titular: "",
    cuerpo: "",
    fecha_emision: new Date().toISOString().slice(0, 16),
    categoria: "",
  });

  const fetchTeletipos = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/teletipos?limit=100`);
      setTeletipos(await res.json());
    } catch {
      /* silent */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTeletipos();
  }, [fetchTeletipos]);

  const importEP = async () => {
    setImporting(true);
    try {
      const res = await fetch(`${API}/api/teletipos/import-ep`, {
        method: "POST",
      });
      const data = await res.json();
      onToast(`${data.loaded} teletipos importados de Europa Press`);
      fetchTeletipos();
      onRefresh();
    } catch {
      onToast("Error al importar");
    } finally {
      setImporting(false);
    }
  };

  const uploadFile = async (file: File) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API}/api/teletipos/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      onToast(`${data.loaded} teletipos cargados desde ${data.filename}`);
      fetchTeletipos();
      onRefresh();
    } catch {
      onToast("Error al subir archivo");
    } finally {
      setUploading(false);
    }
  };

  const scrapeUrl = async () => {
    if (!urlInput.trim()) return;
    setScraping(true);
    try {
      const res = await fetch(`${API}/api/teletipos/from-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: urlInput.trim() }),
      });
      const data = await res.json();
      if (data.error) {
        onToast(data.error);
      } else {
        onToast(`Teletipo "${data.titular.slice(0, 50)}..." creado`);
        setUrlInput("");
        fetchTeletipos();
        onRefresh();
      }
    } catch {
      onToast("Error al scrapear la URL");
    } finally {
      setScraping(false);
    }
  };

  const saveTeletipo = async () => {
    if (!form.id || !form.titular || !form.fecha_emision) return;
    setSaving(true);
    try {
      await fetch(`${API}/api/teletipos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify([form]),
      });
      onToast(`Teletipo "${form.id}" guardado`);
      setForm({
        id: "",
        titular: "",
        cuerpo: "",
        fecha_emision: new Date().toISOString().slice(0, 16),
        categoria: "",
      });
      setShowForm(false);
      fetchTeletipos();
      onRefresh();
    } catch {
      onToast("Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Actions */}
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={importEP}
          disabled={importing}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-xl bg-sky-600 text-white transition-all duration-200 hover:bg-sky-500 active:scale-[0.98] disabled:opacity-40"
        >
          {importing ? (
            <Spinner size={16} className="animate-spin" />
          ) : (
            <DownloadSimple size={16} weight="bold" />
          )}
          {importing ? "Importando..." : "Importar Europa Press"}
        </button>

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-xl border border-zinc-200 text-zinc-700 bg-white transition-all duration-200 hover:border-zinc-300 hover:bg-zinc-50 active:scale-[0.98] disabled:opacity-40"
        >
          {uploading ? (
            <Spinner size={16} className="animate-spin" />
          ) : (
            <UploadSimple size={16} weight="bold" />
          )}
          Subir CSV / JSON
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) uploadFile(file);
            e.target.value = "";
          }}
        />

        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-xl border border-zinc-200 text-zinc-700 bg-white transition-all duration-200 hover:border-zinc-300 hover:bg-zinc-50 active:scale-[0.98]"
        >
          <Plus size={16} weight="bold" />
          Manual
        </button>
      </div>

      {/* URL Input */}
      <div className="flex gap-2">
        <input
          type="url"
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") scrapeUrl();
          }}
          placeholder="Pega una URL de Europa Press para crear un teletipo..."
          className="flex-1 text-sm text-zinc-800 bg-white border border-zinc-200 rounded-xl px-4 py-2.5 placeholder:text-zinc-300 focus:outline-none focus:border-zinc-400 transition-all duration-150"
        />
        <button
          onClick={scrapeUrl}
          disabled={scraping || !urlInput.trim()}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-xl bg-zinc-900 text-white transition-all duration-200 hover:bg-zinc-800 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {scraping ? (
            <Spinner size={16} className="animate-spin" />
          ) : (
            <DownloadSimple size={16} weight="bold" />
          )}
          {scraping ? "Extrayendo..." : "Crear teletipo"}
        </button>
      </div>

      {/* Inline Form */}
      {showForm && (
        <div className="border border-zinc-200/60 rounded-2xl bg-white p-6 md:p-8 space-y-5">
          <p className="text-sm font-semibold text-zinc-800 tracking-tight">
            Crear teletipo manualmente
          </p>
          <div className="grid grid-cols-1 md:grid-cols-[1fr_2fr] gap-5">
            <FormField
              label="ID"
              icon={Hash}
              value={form.id}
              onChange={(v) => setForm({ ...form, id: v })}
              placeholder="EP-2026-001"
            />
            <FormField
              label="Titular"
              icon={TextAlignLeft}
              value={form.titular}
              onChange={(v) => setForm({ ...form, titular: v })}
              placeholder="El Gobierno aprueba..."
            />
          </div>
          <FormField
            label="Cuerpo"
            icon={Rows}
            value={form.cuerpo}
            onChange={(v) => setForm({ ...form, cuerpo: v })}
            placeholder="Texto completo o primer parrafo del teletipo..."
            multiline
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <FormField
              label="Fecha emision"
              icon={CalendarBlank}
              value={form.fecha_emision}
              onChange={(v) => setForm({ ...form, fecha_emision: v })}
              type="datetime-local"
            />
            <FormField
              label="Categoria"
              icon={Tag}
              value={form.categoria}
              onChange={(v) => setForm({ ...form, categoria: v })}
              placeholder="politica, economia, sociedad..."
            />
          </div>
          <div className="flex gap-3 pt-1">
            <button
              onClick={saveTeletipo}
              disabled={saving || !form.id || !form.titular}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-xl bg-zinc-900 text-white transition-all duration-200 hover:bg-zinc-800 active:scale-[0.98] disabled:opacity-40"
            >
              {saving ? (
                <Spinner size={16} className="animate-spin" />
              ) : (
                <CheckCircle size={16} weight="bold" />
              )}
              Guardar
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-5 py-2.5 text-sm font-medium text-zinc-500 hover:text-zinc-700 transition-colors duration-150"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Teletipos List */}
      <div>
        <div className="mb-5">
          <h2 className="text-base font-semibold tracking-tight text-zinc-900">
            Teletipos cargados
          </h2>
          <p className="text-xs text-zinc-400 font-mono mt-0.5">
            {teletipos.length} teletipo{teletipos.length !== 1 ? "s" : ""}
          </p>
        </div>

        <div className="border border-zinc-200/60 rounded-2xl bg-white overflow-hidden">
          {loading ? (
            <div className="divide-y divide-zinc-100 px-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex gap-4 py-4 animate-pulse">
                  <div className="h-4 bg-zinc-100 rounded w-20" />
                  <div className="h-4 bg-zinc-100 rounded w-2/3" />
                  <div className="h-4 bg-zinc-100 rounded w-24" />
                </div>
              ))}
            </div>
          ) : teletipos.length === 0 ? (
            <div className="py-16 text-center">
              <Newspaper size={28} className="mx-auto mb-3 text-zinc-300" />
              <p className="text-sm text-zinc-400 max-w-[40ch] mx-auto leading-relaxed">
                Sin teletipos cargados. Importa desde Europa Press, sube un CSV
                o crea uno manualmente.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-zinc-100">
                    {["ID", "Titular", "Categoria", "Fecha emision"].map(
                      (h) => (
                        <th
                          key={h}
                          className="text-[11px] font-mono font-medium text-zinc-400 uppercase tracking-wider px-4 py-3 first:pl-6"
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-50">
                  {teletipos.map((t) => (
                    <tr
                      key={t.id}
                      className="hover:bg-zinc-50/50 transition-colors duration-150"
                    >
                      <td className="pl-6 pr-4 py-3 text-xs font-mono text-zinc-500">
                        {t.id}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-800 max-w-[500px] truncate">
                        {t.titular}
                      </td>
                      <td className="px-4 py-3">
                        {t.categoria ? (
                          <span className="text-xs font-mono text-zinc-500 bg-zinc-100 px-2 py-0.5 rounded">
                            {t.categoria}
                          </span>
                        ) : (
                          <span className="text-xs text-zinc-300">{"\u2014"}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs font-mono text-zinc-400 whitespace-nowrap">
                        {t.fecha_emision
                          ? new Date(t.fecha_emision).toLocaleDateString(
                              "es-ES",
                              {
                                day: "2-digit",
                                month: "short",
                                hour: "2-digit",
                                minute: "2-digit",
                              }
                            )
                          : "\u2014"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Shared UI ───────────────────────────────────────────────────

function SelectFilter({
  value,
  onChange,
  placeholder,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none text-xs font-mono pl-3 pr-7 py-2 rounded-lg border border-zinc-200 bg-white text-zinc-600 focus:outline-none focus:border-zinc-400 transition-colors duration-150"
      >
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <CaretDown
        size={12}
        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none"
      />
    </div>
  );
}

function FormField({
  label,
  icon: Icon,
  value,
  onChange,
  placeholder,
  type = "text",
  multiline = false,
}: {
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  multiline?: boolean;
}) {
  const cls =
    "w-full text-sm text-zinc-800 bg-zinc-50/80 border border-zinc-200 rounded-xl px-3.5 py-2.5 placeholder:text-zinc-300 focus:outline-none focus:border-zinc-400 focus:bg-white transition-all duration-150";
  return (
    <div className="space-y-1.5">
      <label className="flex items-center gap-1.5 text-xs font-mono text-zinc-500 uppercase tracking-wider">
        <Icon size={13} className="text-zinc-400" />
        {label}
      </label>
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={3}
          className={`${cls} resize-none`}
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={cls}
        />
      )}
    </div>
  );
}

// ─── Main Dashboard ──────────────────────────────────────────────

export function Dashboard() {
  const [tab, setTab] = useState<Tab>("matches");
  const [stats, setStats] = useState<Stats | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [matchTotal, setMatchTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatus>({
    running: false,
    last_result: null,
  });
  const [filterMedio, setFilterMedio] = useState("");
  const [filterMetodo, setFilterMetodo] = useState("");
  const [medios, setMedios] = useState<Record<string, { nombre: string }>>({});
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  };

  const fetchData = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filterMedio) params.set("medio", filterMedio);
      if (filterMetodo) params.set("metodo", filterMetodo);

      const [statsRes, matchesRes, mediosRes, statusRes] = await Promise.all([
        fetch(`${API}/api/stats`),
        fetch(`${API}/api/matches?${params}`),
        fetch(`${API}/api/medios`),
        fetch(`${API}/api/run/status`),
      ]);

      if (!statsRes.ok) throw new Error("API no disponible");

      setStats(await statsRes.json());
      const matchData = await matchesRes.json();
      setMatches(matchData.matches);
      setMatchTotal(matchData.total);
      setMedios(await mediosRes.json());
      setRunStatus(await statusRes.json());
      setError(null);
    } catch {
      setError(
        "No se pudo conectar con la API. Asegurate de que el servidor esta corriendo en localhost:8000"
      );
    } finally {
      setLoading(false);
    }
  }, [filterMedio, filterMetodo]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const triggerRun = async (full: boolean) => {
    await fetch(`${API}/api/${full ? "run-full" : "run"}`, { method: "POST" });
    setRunStatus({ running: true, last_result: null });
  };

  if (error) {
    return (
      <div className="max-w-[1400px] mx-auto px-4 md:px-8 py-12">
        <div className="rounded-2xl border border-red-200/60 bg-red-50/50 p-8">
          <p className="text-sm text-red-600 leading-relaxed">{error}</p>
          <p className="text-xs text-red-400 mt-3 font-mono">
            python -m uvicorn src.api:app --port 8000 --reload
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto px-4 md:px-8 py-8 md:py-12">
      {/* Header + Nav */}
      <header className="mb-10 md:mb-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
          <div>
            <p className="text-xs font-mono tracking-widest uppercase text-zinc-400 mb-2">
              Sistema de trazabilidad
            </p>
            <h1 className="text-3xl md:text-4xl font-semibold tracking-tighter text-zinc-900 leading-none">
              EP Trazabilidad
            </h1>
          </div>

          {/* Stats row */}
          <div className="flex gap-6 md:gap-10">
            <StatCard
              label="Teletipos"
              value={stats?.teletipos ?? 0}
              icon={Newspaper}
            />
            <StatCard
              label="Articulos"
              value={stats?.articulos ?? 0}
              icon={Database}
            />
            <StatCard
              label="Matches"
              value={stats?.matches ?? 0}
              icon={Target}
            />
            <div className="hidden md:block">
              <StatCard
                label="Medios"
                value={stats?.medios ?? 0}
                icon={Buildings}
              />
            </div>
          </div>
        </div>

        {stats?.matches_por_metodo &&
          Object.keys(stats.matches_por_metodo).length > 0 && (
            <div className="flex gap-4 mb-8">
              {Object.entries(stats.matches_por_metodo).map(([metodo, n]) => (
                <div key={metodo} className="flex items-center gap-2">
                  <MethodBadge metodo={metodo} />
                  <span className="text-xs font-mono text-zinc-400">{n}</span>
                </div>
              ))}
            </div>
          )}

        {/* Tab bar */}
        <nav className="flex gap-1 border-b border-zinc-200">
          {(
            [
              { id: "matches" as Tab, label: "Matches", icon: Target },
              { id: "teletipos" as Tab, label: "Teletipos", icon: Newspaper },
            ] as const
          ).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`relative inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors duration-150 ${
                tab === t.id
                  ? "text-zinc-900"
                  : "text-zinc-400 hover:text-zinc-600"
              }`}
            >
              <t.icon size={16} />
              {t.label}
              {tab === t.id && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-zinc-900 rounded-full" />
              )}
            </button>
          ))}
        </nav>
      </header>

      {/* Tab Content */}
      {tab === "matches" ? (
        <MatchesTab
          matches={matches}
          matchTotal={matchTotal}
          loading={loading}
          medios={medios}
          filterMedio={filterMedio}
          setFilterMedio={setFilterMedio}
          filterMetodo={filterMetodo}
          setFilterMetodo={setFilterMetodo}
          runStatus={runStatus}
          triggerRun={triggerRun}
        />
      ) : (
        <TeletiposTab onToast={showToast} onRefresh={fetchData} />
      )}

      {/* Toast */}
      {toast && <Toast message={toast} />}
    </div>
  );
}
